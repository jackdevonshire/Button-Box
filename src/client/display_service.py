import time

import liquidcrystal_i2c
from datetime import datetime

cols = 20
rows = 4


class DisplayService():
    def __init__(self):
        self.__lcd = liquidcrystal_i2c.LiquidCrystal_I2C(0x27, 1, numlines=rows)
        self.changing_screen = False
        self.line_one = ""
        self.line_two = ""
        self.line_three = ""
        self.line_four = ""

    def __set_lcd(self, lines):
        count = 0
        while self.changing_screen:
            time.sleep(0.2)
            count += 1
            if count >= 5:
                return

        self.changing_screen = True

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

        if self.line_one != lines[0]:
            self.__lcd.printline(0, lines[0].center(cols))
        if self.line_two != lines[1]:
            self.__lcd.printline(1, lines[1].center(cols))
        if self.line_three != lines[2]:
            self.__lcd.printline(2, lines[2].center(cols))
        if self.line_four != lines[3]:
            self.__lcd.printline(3, lines[3].center(cols))

        self.line_one, self.line_two, self.line_three, self.line_four = lines[0], lines[1], lines[2], lines[3]

        self.changing_screen = False

    def display_message(self, message):
        self.__set_lcd(message)