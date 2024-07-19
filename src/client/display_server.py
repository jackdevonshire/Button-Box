from config import AUTH_TOKEN
from display_service import DisplayService

display_service = DisplayService()
app = Flask(__name__)


@app.route('/display', methods=["POST"])
def display(self):
    auth_token = request.json["AuthenticationToken"]
    if auth_token != AUTH_TOKEN["AUTH_TOKEN"]:
        return "Invalid Auth", 401

    self.display_service.display_message(request.json["ScreenMessage"])

    return "Success", 200

class DisplayServer():
    def __init__(self, display_service):
        self.display_service = display_service

    def start(self):
        app.run(host="0.0.0.0", port=80)