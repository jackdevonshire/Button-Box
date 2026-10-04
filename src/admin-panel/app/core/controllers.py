from flask import Blueprint, request
import traceback
from app.core.core_service import CoreService
from app.core.button_box_service import ButtonBoxService
from app.core.display_service import DisplayService
from app.integrations.integration_factory import IntegrationFactory
from app import db
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage

core = Blueprint('core', __name__, url_prefix='')
integration_factory = IntegrationFactory()
button_box_service = ButtonBoxService(db)
core_service = CoreService(db, button_box_service, integration_factory)
display_service = DisplayService()

# Handles all button presses from the button box
@core.route("/event", methods=["POST"])
def api_handle_event():
    data = request.json

    try:
        button_box_service.note_box_address(request.remote_addr)
        return button_box_service.api_handle_event(data["ButtonReference"], data["Event"]).get()
    except:
        traceback.print_exc()
        return NetworkResponse().with_error(ErrorMessage.Generic, HttpStatusCode.InternalServerError).get()
