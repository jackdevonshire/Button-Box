from flask import Blueprint
from app.core.core_service import CoreService
from app import db

core = Blueprint('core', __name__, url_prefix='')
core_service = CoreService(db)


# POST /event - To get button events from Button Box
# GET /integrations - To get a list of all integrations
# GET /co

# GET /configuraton - To get all configurations, with the active one marked with an "Active" flag
# POST /