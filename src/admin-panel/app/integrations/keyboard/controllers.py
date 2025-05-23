from app.integrations.keyboard.service import KeyboardService
from flask import Blueprint, render_template, request
from app.core.types import HttpStatusCode, NetworkResponse

keyboard_service = KeyboardService()
bp_keyboard = keyboard_service.blueprint


# Standard Routes (the same across all integrations
@bp_keyboard.route("/", methods=["GET"])
def home():
    nav_links = keyboard_service.core_service.get_nav_links()
    action_records = keyboard_service.get_actions()
    actions = []
    for action in action_records:
        actions.append(action.to_api_response())
    data = {"Actions": actions}

    return render_template("integrations/keyboard.html", nav_links=nav_links, data=data)


# None standard routes - Any API routes specific for THIS integration
@bp_keyboard.route("/action", methods=["POST"])
def api_create_keyboard_action():
    data = request.get_json()
    if not data:
        return NetworkResponse().with_error("No data provided", HttpStatusCode.BadRequest).get()

    name = data.get("Name")
    keys = data.get("Keys")
    description = data.get("Description")

    if not name or not keys:
        return NetworkResponse().with_error("Please provide both name and keys", HttpStatusCode.BadRequest).get()

    return keyboard_service.add_action(name, description, keys).get()


@bp_keyboard.route("/action/<int:action_id>", methods=["DELETE"])
def api_remove_keyboard_action(action_id):
    return keyboard_service.remove_action(action_id).get()
