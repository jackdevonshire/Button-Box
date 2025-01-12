from flask import Blueprint
from app import db

url_prefix = "/integration/keyboard"
bp_keyboard = Blueprint('bp_keyboard', __name__, url_prefix=url_prefix)

# Standard Routes (the same across all integrations
@bp_keyboard.route("/configure")
def configure():
    return "Hello World", 200 # TODO - Will return a page in the future specifically for configuring this integration

# None standard routes - Any API routes specific for THIS integration

