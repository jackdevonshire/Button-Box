#
# Requirements:
# In Raspberry Pi preferences, enable the I2C interface
#
from flask import Flask, request
from client import Client
from config import HOST_IP, AUTH_TOKEN, BUTTONS
from display_service import DisplayService
import threading

app = Flask(__name__)
display = DisplayService()
client = Client(HOST_IP, AUTH_TOKEN)

@app.route('/display', methods=["POST"])
def display(self):
    auth_token = request.json["AuthenticationToken"]
    if auth_token != AUTH_TOKEN["AUTH_TOKEN"]:
        return "Invalid Auth", 401

    display.display_message(request.json["ScreenMessage"])

    return "Success", 200

def run_display_update_server():
    app.run(host="0.0.0.0", port=80)

# Setup Client
client.setup()
display_server_thread = threading.Thread(target=run_display_update_server)
display_server_thread.start()

# Initialise button states
button_states = {}
for button_reference, button in BUTTONS.items():
    button_states[button_reference] = False

while True:
    for button_reference, button in BUTTONS.items():
        try:
            is_pressed = button.is_pressed
            existing_is_pressed_state = button_states[button_reference]

            if is_pressed != existing_is_pressed_state:
                if is_pressed:
                    client.handle_event("On", button_reference)
                else:
                    client.handle_event("Off", button_reference)

                button_states[button_reference] = is_pressed
        except:
            continue

pause()