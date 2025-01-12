from flask import Blueprint, render_template
from app.core.core_service import CoreService
from app.core.display_service import DisplayService
from app.core.key_service import KeyService
from app import db

core = Blueprint('core', __name__, url_prefix='')
core_service = CoreService(db)
key_service = KeyService(db)

@core.route("/", methods=["GET"])
def dashboard():
    return render_template("core/dashboard.html", data=core_service.get_dashboard_data())