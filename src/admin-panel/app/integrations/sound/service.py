import copy
import json

import pydirectinput

from app import app, db
from app.core.button_box_service import ButtonBoxService
from app.core.display_service import DisplayService
from app.core.events import event_bus
from app.core.models import IntegrationAction, Setting
from app.core.types import NetworkResponse
from app.integrations.integration import BaseIntegrationService
from app.sound import clips, devices, hotkeys
from app.sound.engine import DEFAULT_SETTINGS, SoundEngine

SETTINGS_KEY = "Sound"
AGAIN_OPTIONS = ("restart", "stop", "overlap")
STOP_ALL = {"stopAll": True}


class SoundService(BaseIntegrationService):
    """
    A soundboard and voice push-to-talk. Each sound clip is an action, so the box and joystick can play them like any
    other action. Clips play into the game through a virtual cable (mixed with your mic) and in your headphones.
    Everything else - devices, volumes and push-to-talk - is set up on the Sound page.
    """

    def __init__(self):
        super().__init__()
        # Core details - must be present for EVERY integration
        self.id = 6
        self.name = "Sound"
        self.description = "Play sounds into games and voice chat, and push-to-talk when you speak"
        self.is_active = True
        self.configuration = {}

        self.ui_icon = "volume"
        self.engine = None
        self.hotkeys = None

    def initialise_service(self):
        self.engine = SoundEngine(event_bus)
        self.engine.start()
        self.engine.configure(self.load_settings(), bool(self.is_active))
        self.hotkeys = hotkeys.HotkeyListener(self.__on_hotkey)
        self.hotkeys.start()
        self.refresh_hotkeys()

    def set_active(self, is_active):
        super().set_active(is_active)
        self.engine.configure(self.load_settings(), bool(is_active))
        self.refresh_hotkeys()

    # region Keyboard shortcuts

    def refresh_hotkeys(self):
        """Registers every sound's shortcut with Windows (none while Sound is turned off)"""
        if self.hotkeys is None:
            return
        shortcuts = {}
        if self.is_active:
            with app.app_context():
                for action in IntegrationAction.query.filter_by(integration_id=self.id):
                    if action.configuration.get("hotkey"):
                        shortcuts[action.id] = action.configuration["hotkey"]
        self.hotkeys.set(shortcuts)

    def hotkey_error(self, action_id):
        return self.hotkeys.errors.get(action_id) if self.hotkeys else None

    def __on_hotkey(self, action_id):
        with app.app_context():
            action = db.session.get(IntegrationAction, action_id)
            if action is None:
                return
            shortcut = hotkeys.label(action.configuration["hotkey"])
            event_bus.log("press", f"{shortcut} → {action.name}")
        self.core_service.button_box_service.queue_action(action_id)

    # endregion

    def describe(self):
        description = super().describe()
        count = IntegrationAction.query.filter_by(integration_id=self.id).count() - 1  # Not counting "stop all"
        description["note"] = f"{count} {'sound' if count == 1 else 'sounds'}. Set them up on the Sound page."
        return description

    # region Settings

    def load_settings(self):
        with app.app_context():
            row = db.session.get(Setting, SETTINGS_KEY)
            if row is None:
                # First run - start with the default mic and speakers, and a virtual cable if there is one
                settings = {**copy.deepcopy(DEFAULT_SETTINGS), **devices.default_names()}
                db.session.add(Setting(key=SETTINGS_KEY, value=json.dumps(settings), visible=False))
                db.session.commit()
                return settings
            saved = json.loads(row.value)
        settings = {**copy.deepcopy(DEFAULT_SETTINGS), **saved}
        settings["pushToTalk"] = {**DEFAULT_SETTINGS["pushToTalk"], **saved.get("pushToTalk", {})}
        return settings

    def update_settings(self, changes):
        """Validates and saves changed settings, returning them. Raises ValueError with a message for the user."""
        settings = self.load_settings()
        for key in ("micDevice", "gameDevice", "monitorDevice"):
            if key in changes:
                value = changes[key] or None
                if value is not None and not isinstance(value, str):
                    raise ValueError("Choose a device")
                settings[key] = value
        for key in ("micVolume", "clipVolume", "monitorVolume"):
            if key in changes:
                settings[key] = _number(changes[key], 0, 2, "Volume")
        if settings["gameDevice"] and settings["gameDevice"] == settings["monitorDevice"]:
            raise ValueError("Sounds for the game and your headphones need to go to different devices")

        if "pushToTalk" in changes:
            ptt = settings["pushToTalk"]
            new = changes["pushToTalk"]
            if not isinstance(new, dict):
                raise ValueError("Push-to-talk settings aren't valid")
            for key in ("enabled", "onVoice", "onClips"):
                if key in new:
                    ptt[key] = bool(new[key])
            if "method" in new:
                if new["method"] not in ("key", "gate"):
                    raise ValueError("Choose how the game hears you")
                ptt["method"] = new["method"]
            if "key" in new:
                if new["key"] not in pydirectinput.KEYBOARD_MAPPING:
                    raise ValueError(f"'{new['key']}' isn't a key that can be held")
                ptt["key"] = new["key"]
            if "threshold" in new:
                ptt["threshold"] = _number(new["threshold"], -80, 0, "The threshold")
            if "releaseMs" in new:
                ptt["releaseMs"] = int(_number(new["releaseMs"], 0, 3000, "The release time"))
            if "micDelayMs" in new:
                ptt["micDelayMs"] = int(_number(new["micDelayMs"], 0, 500, "The mic delay"))
            if "focusApp" in new:
                ptt["focusApp"] = str(new["focusApp"] or "").strip()

        row = db.session.get(Setting, SETTINGS_KEY)
        row.value = json.dumps(settings)
        db.session.commit()
        self.engine.configure(settings, bool(self.is_active))
        return settings

    # endregion

    # region Actions - one per clip, plus "stop all sounds"

    def sync_actions(self):
        if not any(action.configuration.get("stopAll") for action in
                   IntegrationAction.query.filter_by(integration_id=self.id)):
            db.session.add(IntegrationAction(integration_id=self.id, name="Stop all sounds",
                                             description="Stops every sound that's playing", configuration=STOP_ALL))
            db.session.commit()
        self.refresh_hotkeys()  # Sounds may have been restored from a backup

    def validate_action_configuration(self, configuration):
        if not isinstance(configuration, dict):
            raise ValueError("Choose a sound")
        hotkey = configuration.get("hotkey") or None
        if hotkey is not None:
            hotkeys.parse(hotkey)  # Raises ValueError if it isn't a usable shortcut
        if configuration.get("stopAll"):
            return {**STOP_ALL, "hotkey": hotkey}
        try:
            clips.path_for(configuration.get("file"))
        except ValueError as e:
            raise ValueError(str(e))
        again = configuration.get("again", "restart")
        if again not in AGAIN_OPTIONS:
            raise ValueError("Choose what pressing it again does")
        return {"file": configuration["file"], "volume": _number(configuration.get("volume", 1.0), 0, 2, "Volume"),
                "again": again, "hotkey": hotkey}

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        config = action.configuration
        if config.get("stopAll"):
            self.engine.stop()
            return NetworkResponse()

        if not clips.exists(config["file"]):
            raise FileNotFoundError(f"The sound file for {action.name} is missing")
        if self.engine.play(action.id, config["file"], config["volume"], config["again"]):
            display.display_temporary_message(["", "Playing", action.name, ""], 2)
        return NetworkResponse()

    # endregion


def _number(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}")
    return value
