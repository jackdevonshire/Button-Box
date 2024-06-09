#
# Requirements:
# In Raspberry Pi preferences, enable the I2C interface
#

from display_service import DisplayService
from client import Client
from config import HOST_IP, AUTH_TOKEN, BUTTONS, CONFIGURATION_BUTTON_REFERENCE
from gpiozero import Button
from signal import pause

display = DisplayService()
client = Client(HOST_IP, AUTH_TOKEN, display)

functional_buttons = {}

client.switch_configuration() # First call to initialise permanent display message

# Initial Setup
for button_reference, button_gpio in BUTTONS.items():
    functional_button = Button(button_gpio)
    functional_buttons[button_reference] = functional_button

    if (button_reference == CONFIGURATION_BUTTON_REFERENCE):
        functional_button.when_activated = client.switch_configuration()
        continue

    functional_button.when_activated = client.handle_event("On", button_reference)
    functional_button.when_deactivated = client.handle_event("Off", button_reference)

pause()