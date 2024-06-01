from enum import IntEnum

from flask import jsonify, make_response


class HttpStatusCode(IntEnum):
    Success = 200
    Forbidden = 403
    NotFound = 404
    BadRequest = 400
    InternalServerError = 500


class NetworkResponse:
    has_error = False
    log = False
    message = ""
    data = {}
    status_code = 200

    def with_data(self, json):
        self.data = json
        return self

    def with_error(self, message, log=False):
        self.has_error = True
        self.log = log
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
