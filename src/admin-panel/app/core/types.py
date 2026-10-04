from enum import Enum, IntEnum
from flask import jsonify, make_response

class ErrorMessage:
    Generic = "Whoops an error occurred. Please try again later"

class HttpStatusCode(IntEnum):
    Success = 200
    BadRequest = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    Conflict = 409
    InternalServerError = 500


class NetworkResponse:
    def __init__(self):
        self.has_error = False
        self.message = ""
        self.data = {}
        self.status_code = 200

    def with_data(self, data):
        self.data = data
        return self

    def with_error(self, message, code: HttpStatusCode):
        self.has_error = True
        self.message = message
        self.status_code = code.value
        return self

    def with_status_code(self, code: HttpStatusCode):
        self.status_code = code.value
        return self

    def get(self):
        if self.has_error and self.status_code == 200:
            self.status_code = 500

        response = {
            "HasError": self.has_error,
            "Message": self.message
        }

        for key, value in self.data.items():
            response[key] = value

        flask_response = make_response(jsonify(response))
        flask_response.status_code = self.status_code
        return flask_response


class EventType(Enum):
    OFF = 0
    ON = 1

    @staticmethod
    def map_from_on_off(value):
        if value == "On":
            return EventType.ON
        else:
            return EventType.OFF


class PhysicalKey(Enum):
    BTN_1 = 0
    BTN_2 = 1
    BTN_3 = 2
    BTN_4 = 3
    BTN_5 = 4
    BTN_6 = 5
    BTN_7 = 6
    BTN_8 = 7
    BTN_9 = 8
    BTN_10 = 9
    SWITCH_1 = 10
    SWITCH_2 = 11
    SWITCH_3 = 12
    SWITCH_4 = 13
    SWITCH_5 = 14
    PROTECTED_1 = 15
    PROTECTED_2 = 16
    PROTECTED_3 = 17
    PROTECTED_4 = 18

    @classmethod
    def to_dict(cls):
        return {key.name: key.value for key in cls}


class Gesture(Enum):
    SINGLE = "single"
    # Planned: LONG = "long", DOUBLE = "double"


class ControlKind(Enum):
    BUTTON = "button"        # Momentary push button - on while held
    TOGGLE = "toggle"        # Toggle switch - stays on or off
    PROTECTED = "protected"  # Toggle switch under a flip-up safety cover


# Where each control sits on the physical panel, as a grid of 4 rows. Columns 1-5 are the main area and columns 7-8
# the right-hand cluster. The LCD occupies columns 2-5 of rows 1-2.
CONTROLS = [
    {"id": "BTN_1", "kind": ControlKind.BUTTON, "label": "Button 1", "row": 1, "column": 1},
    {"id": "BTN_2", "kind": ControlKind.BUTTON, "label": "Button 2", "row": 1, "column": 7},
    {"id": "BTN_3", "kind": ControlKind.BUTTON, "label": "Button 3", "row": 1, "column": 8},
    {"id": "BTN_4", "kind": ControlKind.BUTTON, "label": "Button 4", "row": 2, "column": 7},
    {"id": "BTN_5", "kind": ControlKind.BUTTON, "label": "Button 5", "row": 2, "column": 8},
    {"id": "BTN_6", "kind": ControlKind.BUTTON, "label": "Button 6", "row": 3, "column": 1},
    {"id": "BTN_7", "kind": ControlKind.BUTTON, "label": "Button 7", "row": 3, "column": 2},
    {"id": "BTN_8", "kind": ControlKind.BUTTON, "label": "Button 8", "row": 3, "column": 3},
    {"id": "BTN_9", "kind": ControlKind.BUTTON, "label": "Button 9", "row": 3, "column": 4},
    {"id": "BTN_10", "kind": ControlKind.BUTTON, "label": "Button 10", "row": 3, "column": 5},
    {"id": "SWITCH_1", "kind": ControlKind.TOGGLE, "label": "Switch 1", "row": 4, "column": 1},
    {"id": "SWITCH_2", "kind": ControlKind.TOGGLE, "label": "Switch 2", "row": 4, "column": 2},
    {"id": "SWITCH_3", "kind": ControlKind.TOGGLE, "label": "Switch 3", "row": 4, "column": 3},
    {"id": "SWITCH_4", "kind": ControlKind.TOGGLE, "label": "Switch 4", "row": 4, "column": 4},
    {"id": "SWITCH_5", "kind": ControlKind.TOGGLE, "label": "Switch 5", "row": 4, "column": 5},
    {"id": "PROTECTED_1", "kind": ControlKind.PROTECTED, "label": "Protected 1", "row": 3, "column": 7},
    {"id": "PROTECTED_2", "kind": ControlKind.PROTECTED, "label": "Protected 2", "row": 3, "column": 8},
    {"id": "PROTECTED_3", "kind": ControlKind.PROTECTED, "label": "Protected 3", "row": 4, "column": 7},
    {"id": "PROTECTED_4", "kind": ControlKind.PROTECTED, "label": "Protected 4", "row": 4, "column": 8},
]