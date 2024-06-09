from flask import jsonify, make_response


class NetworkResponse:
    data = {}

    def with_data(self, json):
        self.data = json
        return self

    def get(self):
        response = {}
        for key, value in self.data.items():
            response[key] = value

        flask_response = make_response(jsonify(response))
        flask_response.status_code = 200
        return flask_response
