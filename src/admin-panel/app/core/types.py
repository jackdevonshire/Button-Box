from enum import Enum, IntEnum
from flask import jsonify, make_response

class ErrorMessage:
    Generic = "Whoops something went wrong. Please try again later!"

class HttpStatusCode(IntEnum):
    Success = 200
    BadRequest = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    Conflict = 409
    InternalServerError = 500


class NetworkResponse:
    has_error = False
    message = ""
    data = {}
    status_code = 200

    def with_data(self, data):
        self.data = data
        return self

    def with_error(self, message, code: HttpStatusCode):
        self.has_error = True
        self.message = message
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
    UP = 0
    DOWN = 1


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
