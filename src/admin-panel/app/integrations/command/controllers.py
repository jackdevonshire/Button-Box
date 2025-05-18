from app.core.types import NetworkResponse, HttpStatusCode
from app.integrations.command.service import CommandService
from flask import render_template, request

command_service = CommandService()
bp_command = command_service.blueprint


# Standard Routes (the same across all integrations
@bp_command.route("/", methods=["GET"])
def home():
    nav_links = command_service.core_service.get_nav_links()
    action_records = command_service.get_actions()
    actions = []
    for action in action_records:
        actions.append(action.to_api_response())
    data = {"Actions": actions}

    return render_template("integrations/command.html", nav_links=nav_links, data=data)


# None standard routes - Any API routes specific for THIS integration
@bp_command.route("/action", methods=["POST"])
def api_create_command_action():
    data = request.get_json()
    if not data:
        return NetworkResponse().with_error("No data provided", HttpStatusCode.BadRequest).get()

    name = data.get("Name")
    description = data.get("Description")
    action_command = data.get("ActionCommand")

    if not name or not action_command:
        return NetworkResponse().with_error("Please provide both name and command to run",
                                            HttpStatusCode.BadRequest).get()

    return command_service.add_action(name, description, action_command).get()


@bp_command.route("/action/<int:action_id>", methods=["DELETE"])
def api_remove_keyboard_action(action_id):
    return command_service.remove_action(action_id).get()
