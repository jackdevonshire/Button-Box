from flask import Flask, request, jsonify, make_response
import json
from key_service import KeyService

app = Flask(__name__)
configuration = {}
with open('configuration.json') as json_file:
    configuration = json.load(json_file)

key_service = KeyService(configuration["Configurations"])


@app.route('/event', methods=["POST"])
def handle_event():
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return make_response(jsonify({
                "ScreenMessage": ["", "Error:", "Invalid Auth", ""],
                "ScreenDuration": 2
            }))

        event = request.json["Event"]
        button_reference = request.json["ButtonReference"]
        return key_service.handle_key_event(button_reference, event)
    except:
        return make_response(jsonify({
            "ScreenMessage": ["", "Error:", "Unknown", ""],
            "ScreenDuration": 2
        }))


@app.route('/configuration', methods=["POST"])
def switch_configuration():
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return make_response(jsonify({
                "ScreenMessage": ["", "Error:", "Invalid Auth", ""],
                "ScreenDuration": 2
            }))

        return key_service.switch_configuration(configuration_id)
    except:
        return make_response(jsonify({
            "ScreenMessage": ["", "Error:", "Unknown", ""],
            "ScreenDuration": 2
        }))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
