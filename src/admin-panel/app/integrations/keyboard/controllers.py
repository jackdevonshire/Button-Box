from app.integrations.keyboard.service import KeyboardService

keyboard_service = KeyboardService()
bp_keyboard = keyboard_service.blueprint


# Standard Routes (the same across all integrations
@bp_keyboard.route("/configure")
def configure():
    return "Hello World", 200 # TODO - Will return a page in the future specifically for configuring this integration

# None standard routes - Any API routes specific for THIS integration

