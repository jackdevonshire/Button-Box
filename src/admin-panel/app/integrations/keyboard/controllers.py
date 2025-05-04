from app.integrations.keyboard.service import KeyboardService
from flask import Blueprint, render_template, request

keyboard_service = KeyboardService()
bp_keyboard = keyboard_service.blueprint


# Standard Routes (the same across all integrations
@bp_keyboard.route("/", methods=["GET"])
def home():
    nav_links = keyboard_service.core_service.get_nav_links()
    data = {"Actions": []}
    return render_template("integrations/keyboard/keyboard.html", nav_links=nav_links, data=data)

# None standard routes - Any API routes specific for THIS integration

