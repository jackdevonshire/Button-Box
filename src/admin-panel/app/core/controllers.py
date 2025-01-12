from flask import Blueprint, render_template, request
from app.core.core_service import CoreService
from app.core.key_service import KeyService
from app import db
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage

core = Blueprint('core', __name__, url_prefix='')
key_service = KeyService(db)
core_service = CoreService(db, key_service)

@core.route("/", methods=["GET"])
def dashboard():
    nav_links = core_service.get_nav_links()
    data = core_service.get_dashboard_data()
    print(data)
    return render_template("core/dashboard.html", nav_links=nav_links, data=data)



@core.route("/api/configuration/create", methods=["POST"])
def api_create_configuration():
    data = request.json
    try:
        return core_service.api_create_configuration(data["ConfigurationName"], data["ConfigurationDescription"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()


@core.route("/api/configuration/remove", methods=["POST"])
def api_remove_configuration():
    data = request.json
    try:
        return core_service.api_remove_configuration(data["ConfigurationId"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()