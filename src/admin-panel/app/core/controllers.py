from flask import Blueprint
from app.core.service import CoreService
from app import db

core = Blueprint('core', __name__, url_prefix='')
core_service = CoreService(db)