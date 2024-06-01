from flask import jsonify, session, make_response
from enum import IntEnum


class HttpStatusCode(IntEnum):
    Success = 200
    Forbidden = 403
    NotFound = 404
    InternalServerError = 500


class EventResponse:
    def success(self, message):
        response = {
            "HasError": False,
            "Message": message
        }

        flask_response = make_response(jsonify(response))
        flask_response.status_code = HttpStatusCode.Success
        return flask_response

    def error(self, status_code, message):
        response = {
            "HasError": True,
            "Message": message
        }

        flask_response = make_response(jsonify(response))
        flask_response.status_code = status_code
        return flask_response
