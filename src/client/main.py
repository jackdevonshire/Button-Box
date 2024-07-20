#
# Requirements:
# In Raspberry Pi preferences, enable the I2C interface
#
from flask import Flask, request
from client import Client
from config import BUTTONS
from display_service import DisplayService
import threading
import os

retrieved_host_ip = False

app = Flask(__name__)
display_service = DisplayService()
client = Client(display_service)

@app.route('/display', methods=["POST"])
def display():
    global retrieved_host_ip
    if retrieved_host_ip == False:
        retrieved_host_ip = True
        host_ip = request.remote_addr
        host_ip_file = os.getcwd() + "/host_ip.txt"
        with open(host_ip_file, 'a') as the_file:
            the_file.write(host_ip)

    display_service.display_message(request.json["ScreenMessage"])

    return "Success", 200

def run_display_update_server():
    app.run(host="0.0.0.0", port=8000)

# Setup Client
display_server_thread = threading.Thread(target=run_display_update_server)
display_server_thread.start()
client.setup()

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