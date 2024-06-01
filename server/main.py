from flask import Flask, request
import json
from types import HttpStatusCode, EventResponse

app = Flask(__name__)
configuration = {}
with open('data.json') as json_file:
    configuration = json.load("configuration.json")

@app.route('/event', methods=["POST"])
def handle_event():
    try:
        auth_token = request.json["AuthenticationToken"]
        if (auth_token != configuration["AuthenticationToken"]):
            return EventResponse.error(HttpStatusCode.Forbidden, "Invalid Authentication Token")
    except:
        return EventResponse.error(HttpStatusCode.InternalServerError, "An unexpected error occurred")


if __name__ == '__main__':
    app.run()