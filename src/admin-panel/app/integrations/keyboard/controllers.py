from flask import Blueprint
from app.core.core_service import CoreService
from app import db

bp_keyboard = Blueprint('bp_keyboard', __name__, url_prefix='/integration/keyboard')

# Standard Routes (the same across all integrations
@bp_keyboard.route("/configure")
def configure():
    return "Hello World", 200 # TODO - Will return a page in the future specifically for configuring this integration

# None standard routes - Any API routes specific for THIS integration

