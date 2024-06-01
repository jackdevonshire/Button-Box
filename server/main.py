from flask import Flask, request
import json
from types import HttpStatusCode, NetworkResponse
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
            return NetworkResponse.with_error("Invalid Auth Token").with_status_code(HttpStatusCode.Forbidden).get()

        event = request.json["Event"]
        button_reference = request.json["ButtonReference"]
        return key_service.handle_key_event(button_reference, event)
    except:
        return NetworkResponse.with_error("An unknown error occurred").get()


@app.route('/configuration/set/{id}', methods=["GET"])
def set_configuration(configuration_id):
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return NetworkResponse.with_error("Invalid Auth Token").with_status_code(HttpStatusCode.Forbidden).get()

        return key_service.set_configuration(configuration_id)
    except:
        return NetworkResponse.with_error("An unknown error occurred").get()


@app.route('/configuration/current', methods=["GET"])
def get_current_configuration():
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return NetworkResponse.with_error("Invalid Auth Token").with_status_code(HttpStatusCode.Forbidden).get()

        return key_service.get_current_configuration()
    except:
        return NetworkResponse.with_error("An unknown error occurred").get()

@app.route('/configuration/all', methods=["GET"])
def get_all_configurations():
    try:
        auth_token = request.json["AuthenticationToken"]
        if auth_token != configuration["AuthenticationToken"]:
            return NetworkResponse.with_error("Invalid Auth Token").with_status_code(HttpStatusCode.Forbidden).get()

        return key_service.get_all_configurations()
    except:
        return NetworkResponse.with_error("An unknown error occurred").get()


if __name__ == '__main__':
    app.run()
