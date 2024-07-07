import time

import pydirectinput

from button.default_button import DefaultButton

TEAMS_KEYS = {
    "settings": {
        "key": "ctrl,comma",
        "message": ["", "Opening", "Settings", ""]
    },
    "help": {
        "key": "f1",
        "message": ["", "Opening", "Help", ""]
    },
    "close": {
        "key": "esc",
        "message": ["", "Closing", "Teams", ""]
    },
    "endcall": {
        "key": "ctrl,shift,h",
        "message": ["", "Ending", "Call", ""]
    },
    "togglemute": {
        "key": "ctrl,shift,m",
        "message": ["", "Toggle", "Mute", ""]
    },
    "togglevideo": {
        "key": "ctrl,shift,o",
        "message": ["", "Toggle", "Video", ""]
    },
    "togglehand": {
        "key": "ctrl,shift,k",
        "message": ["", "Toggle", "Hand", ""]
    },
    "acceptscreenshare": {
        "key": "ctrl,shift,a",
        "message": ["", "Accept", "Screenshare", ""]
    },
    "declinescreenshare": {
        "key": "ctrl,shift,d",
        "message": ["", "Decline", "Screenshare", ""]
    },
    "admitfromlobby": {
        "key": "ctrl,shift,y",
        "message": ["", "Admit", "From Lobby", ""]
    },
    "openchat": {
        "key": "ctrl,shift,r",
        "message": ["", "Open", "Chat", ""]
    }
}


class MSTeamsButton(DefaultButton):
    def handle(self):
        action = self.event_configuration["Action"].lower()
        teams_keys = TEAMS_KEYS[action]

        keys_to_activate = teams_keys["key"].split(",")

        for key_to_activate in keys_to_activate:
            key_to_activate = key_to_activate.replace("comma", ",")
            pydirectinput.keyDown(key_to_activate)

        time.sleep(0.1)
        for key_to_activate in keys_to_activate:
            key_to_activate = key_to_activate.replace("comma", ",")
            pydirectinput.keyUp(key_to_activate)

        return teams_keys["message"], 2
