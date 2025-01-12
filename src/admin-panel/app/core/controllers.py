from flask import Blueprint, render_template
from app.core.core_service import CoreService
from app.core.key_service import KeyService
from app import db

core = Blueprint('core', __name__, url_prefix='')
key_service = KeyService(db)
core_service = CoreService(db, key_service)

@core.route("/", methods=["GET"])
def dashboard():
    nav_links = core_service.get_nav_links()
    data = core_service.get_dashboard_data()
    return render_template("core/dashboard.html", nav_links=nav_links, data=data)