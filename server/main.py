from flask import Flask, request, jsonify, make_response
import json
from key_service import KeyService

app = Flask(__name__)
configuration = {}
with open('data.json') as json_file:
    configuration = json.load("configuration.json")

key_service = KeyService(configuration)


@app.route('/event', methods=["POST"])
def handle_event():
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return make_response(jsonify({
                "ScreenMessage": "\nError\nInvalid Auth\n",
                "ScreenDuration": 2
            }))

        event = request.json["Event"]
        button_reference = request.json["ButtonReference"]
        return key_service.handle_key_event(button_reference, event)
    except:
        return make_response(jsonify({
            "ScreenMessage": "\nError\nUnknown\n",
            "ScreenDuration": 2
        }))


@app.route('/configuration', methods=["POST"])
def switch_configuration(configuration_id):
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return make_response(jsonify({
                "ScreenMessage": "\nError\nInvalid Auth\n",
                "ScreenDuration": 2
            }))

        return key_service.switch_configuration(configuration_id)
    except:
        return make_response(jsonify({
            "ScreenMessage": "\nError\nUnknown\n",
            "ScreenDuration": 2
        }))



if __name__ == '__main__':
    app.run()
