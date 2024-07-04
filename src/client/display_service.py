import liquidcrystal_i2c
from datetime import datetime

cols = 20
rows = 4


class DisplayService():
    def __init__(self):
        self.__lcd = liquidcrystal_i2c.LiquidCrystal_I2C(0x27, 1, numlines=rows)
        self.__default_message = "Default Message"

        self.waiting_to_display_default_message = False
        self.duration_to_wait = 0
        self.time_started_waiting = datetime.now()

    def __set_lcd(self, lines, centre_align=True):
        if len(lines) > 4:
            lines = lines[:3]

        while len(lines) < 4:
            lines.append("")

        temp_lines = lines
        lines = []
        for line in temp_lines:
            if len(line) > 20:
                line = line[:19]
            lines.append(line)

        if centre_align:
            self.__lcd.printline(0, lines[0].center(cols))
            self.__lcd.printline(1, lines[1].center(cols))
            self.__lcd.printline(2, lines[2].center(cols))
            self.__lcd.printline(3, lines[3].center(cols))
        else:
            self.__lcd.printline(0, lines[0].rjust(cols))
            self.__lcd.printline(1, lines[1].rjust(cols))
            self.__lcd.printline(2, lines[2].rjust(cols))
            self.__lcd.printline(3, lines[3].rjust(cols))

    def display_message(self, message):
        self.__set_lcd(message)

    def set_default_message(self, message, duration_to_wait):
        self.__default_message = message
        self.duration_to_wait = duration_to_wait
        self.time_started_waiting = datetime.now()
        self.waiting_to_display_default_message = True

    def check_and_update_default_message(self):
        if not self.waiting_to_display_default_message:
            return

        current_time = datetime.now()
        total_time_waited = (current_time-self.time_started_waiting).total_seconds()

        if total_time_waited >= self.duration_to_wait:
            self.__set_lcd(self.__default_message)
            self.waiting_to_display_default_message = False
