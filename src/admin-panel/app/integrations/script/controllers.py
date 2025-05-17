from app.core.types import NetworkResponse, HttpStatusCode
from app.integrations.script.service import ScriptService
from flask import render_template, request

script_service = ScriptService()
bp_script = script_service.blueprint


# Standard Routes (the same across all integrations
@bp_script.route("/", methods=["GET"])
def home():
    nav_links = script_service.core_service.get_nav_links()
    action_records = script_service.get_actions()
    actions = []
    for action in action_records:
        actions.append(action.to_api_response())
    data = {"Actions": actions}

    return render_template("integrations/script.html", nav_links=nav_links, data=data)


# None standard routes - Any API routes specific for THIS integration
@bp_script.route("/action", methods=["POST"])
def api_create_script_action():
    data = request.get_json()
    if not data:
        return NetworkResponse().with_error("No data provided", HttpStatusCode.BadRequest).get()

    name = data.get("Name")
    description = data.get("Description")
    python_script = data.get("PythonScript")

    if not name or not python_script:
        return NetworkResponse().with_error("Please provide both name and python script",
                                            HttpStatusCode.BadRequest).get()

    return script_service.add_action(name, description, python_script).get()


@bp_script.route("/action/<int:action_id>", methods=["DELETE"])
def api_remove_script_action(action_id):
    return script_service.remove_action(action_id).get()
