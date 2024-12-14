from flask import Flask, request
import json
from display_service import DisplayService
from key_service import KeyService
from user_scripts import UserScripts

app = Flask(__name__)
configuration = {}
try:
    with open('configuration.json') as json_file:
        configuration = json.load(json_file)
except:
    with open('example_configuration.json') as json_file:
        configuration = json.load(json_file)

display_service = DisplayService(configuration["ButtonBoxHostIP"])
script_service = UserScripts(display_service)
key_service = KeyService(configuration["Configurations"], configuration["Integrations"], display_service, script_service)

@app.route('/event', methods=["POST"])
def handle_event():
    if True:
        event = request.json["Event"]
        button_reference = request.json["ButtonReference"]
        key_service.handle_key_event(button_reference, event)

        return "Success", 200
    else:
        display_service.display_temporary_message(["", "Error:", "Unknown", ""], 2)
        return "Error", 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
