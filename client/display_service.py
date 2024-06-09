import time

import liquidcrystal_i2c

cols = 20
rows = 4


class DisplayService():
    def __init__(self):
        self.__lcd = liquidcrystal_i2c.LiquidCrystal_I2C(0x27, 1, numlines=rows)
        self.__default_lines = []

    def ____set_lcd(self, lines, centre_align=True):
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

    @staticmethod
    def __string_to_lines(message):
        return message.split("\n")

    def set_default_message(self, message):
        self.__default_lines = self.__string_to_lines(message)

    def set_temporary_message(self, message, duration):
        temporary_lines = self.__string_to_lines(message)
        self.__set_lcd(temporary_lines)

        if duration is None: # Do not switch back to default message until instructed if duration not set
            return True

        time.sleep(duration)
        self.__set_lcd(self.__default_lines)

