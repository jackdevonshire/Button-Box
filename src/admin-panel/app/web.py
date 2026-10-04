"""
Serves the web UI - the React app built from web/ into app/static/web. Every page of the app is served the same
index.html, and the app's router shows the right page.
"""
import os

from flask import Blueprint, send_file

WEB_BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "web")
INDEX_PATH = os.path.join(WEB_BUILD_DIR, "index.html")

# Pages handled by the web UI's router
CLIENT_ROUTES = ["/", "/configurations", "/actions/<editor>", "/activity", "/integrations", "/settings"]

web = Blueprint("web", __name__)


def serve_app(**_):
    if not os.path.exists(INDEX_PATH):
        return ("The web UI hasn't been built yet. Run start.bat, or `npm run build` in the web folder.", 503,
                {"Content-Type": "text/plain"})
    # Never cache index.html - it points at the latest build's assets, which have unique names
    return send_file(INDEX_PATH, max_age=0)


for index, route in enumerate(CLIENT_ROUTES):
    web.add_url_rule(route, endpoint=f"page_{index}", view_func=serve_app)
