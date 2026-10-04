"""
JSON API used by the web UI. Responses are plain JSON with camelCase keys; errors use HTTP status codes and a body of
{"error": "message for the user"}.
"""
import datetime
import ipaddress
import os
import queue
import traceback

import desktop

from flask import Blueprint, Response, jsonify, request, stream_with_context
from sqlalchemy.orm import joinedload

from app import db
from app.core.backup_service import BackupService, BackupError
from app.core.button_box_service import LEARN_SECONDS
from app.core.controllers import button_box_service, core_service, display_service, integration_factory
from app.core.display_service import DisplayService, LCD_COLS, LCD_ROWS
from app.core.events import event_bus, format_sse
from app.core.models import ActivityEntry, Binding, Configuration, IntegrationAction, Setting
from app.core.types import CONTROLS, EventType, Gesture, PhysicalKey

api = Blueprint("api", __name__, url_prefix="/api")
backup_service = BackupService(db, integration_factory, button_box_service, core_service,
                               backup_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups"))

SSE_KEEPALIVE_SECONDS = 15


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@api.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status


@api.errorhandler(Exception)
def handle_unexpected_error(error):
    traceback.print_exc()
    return jsonify({"error": "Something went wrong. Check the log for details."}), 500


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Expected a JSON object")
    return data


def get_or_404(model, id, name):
    item = db.session.get(model, id) if isinstance(id, int) else None
    if item is None:
        raise ApiError(f"{name} doesn't exist", 404)
    return item


def require_text(data, key, label, required=True):
    value = data.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ApiError(f"Enter a {label}")
    return value.strip()


def validate_display_lines(lines):
    if lines is None:
        return None
    if not isinstance(lines, list) or len(lines) > LCD_ROWS or not all(isinstance(line, str) for line in lines):
        raise ApiError(f"The screen has {LCD_ROWS} lines")
    if any(len(line) > LCD_COLS for line in lines):
        raise ApiError(f"Each screen line fits {LCD_COLS} characters")
    return DisplayService.normalise_message(lines)


def refresh_after_change():
    """Bindings are cached for fast matching, so reload them after anything they depend on changes"""
    button_box_service.refresh_current_configuration()
    event_bus.publish("changed")


# region Status, controls and the box

def status_json():
    status = button_box_service.get_status()
    return {
        "online": status["Online"],
        "latencyMs": status["LatencyMs"],
        "lastSeen": status["LastSeen"],
        "lastEvent": status["LastEvent"],
        "scanning": status["Scanning"],
        "buttonBoxIp": status["ButtonBoxIP"],
        "activeConfigurationId": button_box_service.current_configuration.id,
        "states": {control: event.lower() for control, event in status["States"].items()},
        "display": display_service.default_message,
    }


@api.get("/status")
def get_status():
    return status_json()


@api.get("/controls")
def get_controls():
    return jsonify([{**control, "kind": control["kind"].value} for control in CONTROLS])


@api.post("/box/find")
def find_box():
    ip = button_box_service.monitor.scan(wait=True)
    if not ip:
        raise ApiError("Couldn't find the button box on your network. Check it's switched on.", 404)
    return status_json()


@api.post("/box/display")
def preview_display():
    """Shows a message on the box's screen for a few seconds - used to preview custom screens"""
    data = body()
    lines = validate_display_lines(data.get("lines"))
    seconds = min(max(int(data.get("seconds", 5)), 1), 30)
    display_service.display_temporary_message(lines, seconds)
    return {"ok": True}


@api.post("/learn")
def start_learning():
    button_box_service.start_learning()
    return {"ok": True, "seconds": LEARN_SECONDS}


@api.get("/learn")
def get_learned():
    return button_box_service.get_learned()

# endregion

# region Configurations

def configuration_json(configuration, include_bindings=False):
    data = configuration.to_json()
    data["active"] = configuration.id == button_box_service.current_configuration.id
    if include_bindings:
        bindings = Binding.query.options(
            joinedload(Binding.integration_action).joinedload(IntegrationAction.integration)
        ).filter_by(configuration_id=configuration.id).order_by(Binding.id).all()
        data["bindings"] = [binding.to_json() for binding in bindings]
    else:
        data["bindingCount"] = Binding.query.filter_by(configuration_id=configuration.id).count()
    return data


@api.get("/configurations")
def list_configurations():
    return jsonify([configuration_json(c) for c in Configuration.query.order_by(Configuration.id)])


@api.post("/configurations")
def create_configuration():
    data = body()
    configuration = Configuration(name=require_text(data, "name", "name"),
                                  description=(data.get("description") or "").strip(),
                                  display_lines=validate_display_lines(data.get("displayLines")))
    db.session.add(configuration)
    db.session.commit()
    core_service.sync_integration_actions()
    refresh_after_change()
    return configuration_json(configuration, include_bindings=True), 201


@api.get("/configurations/<int:id>")
def get_configuration(id):
    return configuration_json(get_or_404(Configuration, id, "Configuration"), include_bindings=True)


@api.patch("/configurations/<int:id>")
def update_configuration(id):
    configuration = get_or_404(Configuration, id, "Configuration")
    data = body()
    if "name" in data:
        configuration.name = require_text(data, "name", "name")
    if "description" in data:
        configuration.description = (data.get("description") or "").strip()
    if "displayLines" in data:
        configuration.display_lines = validate_display_lines(data["displayLines"])
    db.session.commit()
    core_service.sync_integration_actions()  # Keeps "switch to" action names in line with the configuration name
    refresh_after_change()
    return configuration_json(configuration, include_bindings=True)


@api.delete("/configurations/<int:id>")
def delete_configuration(id):
    configuration = get_or_404(Configuration, id, "Configuration")
    if configuration.id == button_box_service.current_configuration.id:
        raise ApiError("You can't delete the active configuration. Switch to another one first.")
    if Configuration.query.count() <= 1:
        raise ApiError("You need at least one configuration")

    Binding.query.filter_by(configuration_id=id).delete()
    db.session.delete(configuration)
    db.session.commit()
    core_service.sync_integration_actions()
    refresh_after_change()
    return {"ok": True}


@api.post("/configurations/<int:id>/activate")
def activate_configuration(id):
    get_or_404(Configuration, id, "Configuration")
    button_box_service.api_change_active_configuration(id)
    return status_json()


@api.post("/configurations/<int:id>/duplicate")
def duplicate_configuration(id):
    source = get_or_404(Configuration, id, "Configuration")
    data = request.get_json(silent=True) or {}
    copy = Configuration(name=(data.get("name") or f"{source.name} (copy)").strip(), description=source.description,
                         display_lines=source.display_lines)
    db.session.add(copy)
    db.session.flush()
    for binding in Binding.query.filter_by(configuration_id=id).all():
        db.session.add(Binding(configuration_id=copy.id, name=binding.name, physical_key=binding.physical_key,
                               event_type=binding.event_type, integration_action_id=binding.integration_action_id,
                               modifiers=binding.modifiers, gesture=binding.gesture, enabled=binding.enabled))
    db.session.commit()
    core_service.sync_integration_actions()
    refresh_after_change()
    return configuration_json(copy, include_bindings=True), 201

# endregion

# region Bindings

def apply_binding_fields(binding, data, partial):
    if not partial or "control" in data:
        control = data.get("control")
        if control not in PhysicalKey.__members__:
            raise ApiError("Choose a control")
        binding.physical_key = PhysicalKey[control].value
    if not partial or "event" in data:
        if data.get("event") not in ("on", "off"):
            raise ApiError("Choose when the binding fires")
        binding.event_type = EventType.ON.value if data["event"] == "on" else EventType.OFF.value
    if not partial or "actionId" in data:
        get_or_404(IntegrationAction, data.get("actionId"), "Action")
        binding.integration_action_id = data["actionId"]
    if "name" in data:
        binding.name = (data.get("name") or "").strip()
    if "modifiers" in data:
        modifiers = data.get("modifiers") or []
        if not isinstance(modifiers, list) or not set(modifiers) <= set(PhysicalKey.__members__):
            raise ApiError("Modifiers must be controls on the box")
        binding.modifiers = sorted(set(modifiers))
    if "gesture" in data:
        if data["gesture"] not in {gesture.value for gesture in Gesture}:
            raise ApiError("That gesture isn't supported yet")
        binding.gesture = data["gesture"]
    if "enabled" in data:
        binding.enabled = bool(data["enabled"])

    if PhysicalKey(binding.physical_key).name in (binding.modifiers or []):
        raise ApiError("A control can't be its own modifier")


@api.post("/configurations/<int:configuration_id>/bindings")
def create_binding(configuration_id):
    get_or_404(Configuration, configuration_id, "Configuration")
    binding = Binding(configuration_id=configuration_id, modifiers=[], gesture=Gesture.SINGLE.value, enabled=True)
    apply_binding_fields(binding, body(), partial=False)
    db.session.add(binding)
    db.session.commit()
    refresh_after_change()
    return binding.to_json(), 201


@api.patch("/bindings/<int:id>")
def update_binding(id):
    binding = get_or_404(Binding, id, "Binding")
    apply_binding_fields(binding, body(), partial=True)
    db.session.commit()
    refresh_after_change()
    return binding.to_json()


@api.delete("/bindings/<int:id>")
def delete_binding(id):
    db.session.delete(get_or_404(Binding, id, "Binding"))
    db.session.commit()
    refresh_after_change()
    return {"ok": True}

# endregion

# region Integrations and actions

def get_integration(id):
    try:
        return integration_factory.get_integration_by_id(id)
    except KeyError:
        raise ApiError("Integration doesn't exist", 404)


@api.get("/integrations")
def list_integrations():
    return jsonify([integration.describe() for integration in integration_factory.get_all_integrations()])


@api.patch("/integrations/<int:id>")
def update_integration(id):
    integration = get_integration(id)
    data = body()
    if "active" in data:
        integration.set_active(bool(data["active"]))
        event_bus.log("system", f"{integration.name} turned {'on' if integration.is_active else 'off'}")
    refresh_after_change()
    return integration.describe()


@api.get("/actions")
def list_actions():
    query = IntegrationAction.query.options(joinedload(IntegrationAction.integration))
    if request.args.get("integrationId"):
        query = query.filter_by(integration_id=int(request.args["integrationId"]))
    return jsonify([action.to_json() for action in query.order_by(IntegrationAction.name)])


def validated_action_configuration(integration, configuration):
    try:
        return integration.validate_action_configuration(configuration)
    except ValueError as e:
        raise ApiError(str(e))


@api.post("/actions")
def create_action():
    data = body()
    integration = get_integration(data.get("integrationId"))
    if not integration.user_actions:
        raise ApiError(f"{integration.name} actions are created automatically")
    action = IntegrationAction(integration_id=integration.id, name=require_text(data, "name", "name"),
                               description=(data.get("description") or "").strip(),
                               configuration=validated_action_configuration(integration, data.get("configuration")))
    db.session.add(action)
    db.session.commit()
    event_bus.publish("changed")
    return action.to_json(), 201


@api.get("/actions/<int:id>")
def get_action(id):
    return get_or_404(IntegrationAction, id, "Action").to_json()


@api.patch("/actions/<int:id>")
def update_action(id):
    action = get_or_404(IntegrationAction, id, "Action")
    integration = get_integration(action.integration_id)
    if not integration.user_actions:
        raise ApiError(f"{integration.name} actions are managed automatically")
    data = body()
    if "name" in data:
        action.name = require_text(data, "name", "name")
    if "description" in data:
        action.description = (data.get("description") or "").strip()
    if "configuration" in data:
        action.configuration = validated_action_configuration(integration, data["configuration"])
    db.session.commit()
    refresh_after_change()
    return action.to_json()


@api.delete("/actions/<int:id>")
def delete_action(id):
    action = get_or_404(IntegrationAction, id, "Action")
    if not get_integration(action.integration_id).user_actions:
        raise ApiError("This action is managed automatically")
    removed_bindings = Binding.query.filter_by(integration_action_id=id).delete()
    db.session.delete(action)
    db.session.commit()
    refresh_after_change()
    return {"ok": True, "removedBindings": removed_bindings}


@api.post("/actions/<int:id>/test")
def test_action(id):
    response = button_box_service.api_test_action(id)
    if response.has_error:
        raise ApiError(response.message, response.status_code)
    return {"ok": True}

# endregion

# region Activity, settings and backups

@api.get("/activity")
def list_activity():
    limit = min(int(request.args.get("limit", 100)), 500)
    query = ActivityEntry.query
    if request.args.get("before"):
        query = query.filter(ActivityEntry.id < int(request.args["before"]))
    if request.args.get("kind"):
        query = query.filter_by(kind=request.args["kind"])
    return jsonify([entry.to_json() for entry in query.order_by(ActivityEntry.id.desc()).limit(limit)])


@api.delete("/activity")
def clear_activity():
    ActivityEntry.query.delete()
    db.session.commit()
    return {"ok": True}


@api.get("/settings")
def get_settings():
    return {
        "buttonBoxIp": db.session.get(Setting, "ButtonBoxIP").value,
        "startWithWindows": desktop.starts_with_windows(),
        "panelUrl": desktop.PANEL_URL,
        "logPath": desktop.LOG_PATH,
        "backupDir": backup_service.backup_dir,
    }


@api.patch("/settings")
def update_settings():
    data = body()
    if "buttonBoxIp" in data:
        ip = str(data["buttonBoxIp"] or "").strip()
        if ip:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ApiError("Enter an IP address, like 192.168.1.50")
        button_box_service.api_change_ip(ip)
    if "startWithWindows" in data:
        desktop.set_start_with_windows(bool(data["startWithWindows"]))
    return get_settings()


@api.post("/system/open-log")
def open_log():
    desktop.open_log()
    return {"ok": True}


@api.get("/export")
def export_backup():
    stamp = datetime.date.today().isoformat()
    response = jsonify(backup_service.export())
    response.headers["Content-Disposition"] = f'attachment; filename="button-box-backup-{stamp}.json"'
    return response


@api.post("/import")
def import_backup():
    try:
        result = backup_service.import_replace(request.get_json(silent=True))
    except BackupError as e:
        raise ApiError(str(e))
    event_bus.log("system", "Imported a backup", detail=f"Previous setup saved to {result['backupPath']}")
    event_bus.publish("changed")
    return result

# endregion

# region Live events

@api.get("/events")
def stream_events():
    """Server-sent events: button presses, activity, status and configuration changes as they happen"""
    subscriber = event_bus.subscribe()

    def generate():
        try:
            yield format_sse({"type": "status", "data": status_json()})
            while True:
                try:
                    message = subscriber.get(timeout=SSE_KEEPALIVE_SECONDS)
                    if message["type"] == "status":
                        message = {**message, "data": status_json()}
                    yield format_sse(message)
                except queue.Empty:
                    yield ": keepalive\n\n"  # Also lets the server notice when the browser has gone
        finally:
            event_bus.unsubscribe(subscriber)

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# endregion
