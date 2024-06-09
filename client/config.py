# The Local IP Address of the machine hosting the Python Flask Server
HOST_IP = ""

# This should match the servers auth token
AUTH_TOKEN = ""

# The reference of the button to control switching the controller configuration
CONFIGURATION_BUTTON_REFERENCE = "PUSH_BTN_CONFIG"

# All the buttons. The key is the button reference (customisable), the value is the GPIO pin for that button
BUTTONS = {
    "PUSH_BTN_CONFIG": 0,
    "PUSH_BTN_1": 0,
    "PUSH_BTN_2": 0,
    "PUSH_BTN_3": 0,
    "PUSH_BTN_4": 0,
    "GANG_A_1": 0,
    "GANG_A_2": 0,
    "GANG_A_3": 0,
    "GANG_A_4": 0,
    "GANG_A_5": 0,
    "GANG_A_6": 0,
    "GANG_B_1": 0,
    "GANG_B_2": 0,
    "GANG_B_3": 0,
    "GANG_B_4": 0,
    "GANG_B_5": 0,
    "GANG_B_6": 0,
    "PROTECTED_1": 0,
    "PROTECTED_2": 0,
    "PROTECTED_3": 0,
    "PROTECTED_4": 0
}
