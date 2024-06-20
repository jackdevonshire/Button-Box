#
# Requirements:
# In Raspberry Pi preferences, enable the I2C interface
#

from client import Client
from config import HOST_IP, AUTH_TOKEN, BUTTONS
from display_service import DisplayService

display = DisplayService()
client = Client(HOST_IP, AUTH_TOKEN, display)

client.setup()

# Initialise button states
button_states = {}
for button_reference, button in BUTTONS.items():

while True:
    for button_reference, button in BUTTONS.items():
        try:
            is_pressed = button.is_pressed()
            existing_is_pressed_state = button_states[button_reference]

            if is_pressed != existing_is_pressed_state:
                if is_pressed:
                    client.handle_event("ON", button_reference)
                else:
                    client.handle_event("OFF", button_reference)

                button_states[button_reference] = is_pressed

        except:
            continue

pause()