from gpiozero import Button

# All the buttons. The key is the button reference (customisable), the value is the GPIO pin for that button
BUTTONS = {
    "BTN_1": Button(14),
    "BTN_2": Button(15),
    "BTN_3": Button(18),
    "BTN_4": Button(23),
    "BTN_5": Button(24),
    "BTN_6": Button(25),
    "BTN_7": Button(8),
    "BTN_8": Button(7),
    "BTN_9": Button(12),
    "BTN_10": Button(16),
    "SWITCH_1": Button(17),
    "SWITCH_2": Button(27),
    "SWITCH_3": Button(22),
    "SWITCH_4": Button(10),
    "SWITCH_5": Button(9),
    "PROTECTED_1": Button(5),
    "PROTECTED_2": Button(6),
    "PROTECTED_3": Button(13),
    "PROTECTED_4": Button(19)
}
