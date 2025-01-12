from flask import Blueprint, render_template, request
from app.core.core_service import CoreService
from app.core.button_box_service import ButtonBoxService
from app import db
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage

core = Blueprint('core', __name__, url_prefix='')
button_box_service = ButtonBoxService(db)
core_service = CoreService(db, button_box_service)

@core.route("/", methods=["GET"])
def dashboard_page():
    nav_links = core_service.get_nav_links()
    data = core_service.get_dashboard_data()
    return render_template("core/dashboard.html", nav_links=nav_links, data=data)


@core.route("/configuration/<id>", methods=["GET"])
def configuration_page(id):
    nav_links = core_service.get_nav_links()
    data = core_service.get_configuration_data(id)
    return render_template("core/configuration.html", nav_links=nav_links, data=data)

# Handles all button presses from the button box
@core.route("/event", methods=["POST"])
def api_handle_event():
    data = request.json

    if True:
        return button_box_service.api_handle_event(data["ButtonReference"], data["Event"])
    else:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()

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


@core.route("/api/button/create", methods=["POST"])
def api_create_button():
    data = request.json
    try:
        return core_service.api_create_button(data["ConfigurationId"], data["ButtonName"], data["PhysicalButton"],
                                              data["EventType"], data["IntegrationActionId"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()


@core.route("/api/button/remove", methods=["POST"])
def api_remove_button():
    data = request.json
    try:
        return core_service.api_remove_button(data["ButtonId"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()


@core.route("/api/ip", methods=["POST"])
def api_change_ip():
    data = request.json
    try:
        return button_box_service.api_change_ip(data["ButtonBoxIP"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()

@core.route("/configuration/active", methods=["POST"])
def api_change_active_configuration():
    data = request.json
    try:
        return button_box_service.api_change_active_configuration(data["ConfigurationId"])
    except:
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()

