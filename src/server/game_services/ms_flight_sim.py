# Sim Connect Available Variables
# https://docs.flightsimulator.com/html/Programming_Tools/SimVars/Aircraft_SimVars/Aircraft_AutopilotAssistant_Variables.htm
import time

from SimConnect import *
from display_service import DisplayService
import threading

class MicrosoftFlightSimulator:
    def __init__(self, display_service: DisplayService):
        self.display_service = display_service
        self.setup = False
        self.sm = None
        self.aq = None

        self.active_thread = False

    def setup_sim_connect(self):
        try:
            self.sm = SimConnect()
            self.aq = AircraftRequests(self.sm, _time=500)
            self.setup = True
            return True
        except:
            self.sm = None
            self.aq = None

        return False

    def __update_display_thread(self, title, sim_connect_reference):
        self.active_thread = True
        while True:
            if not self.active_thread:
                return

            value = self.aq.get(sim_connect_reference)

            # Rounding to whole number if provided with a decimal
            try:
                number = float(value)
                value = int(number)
            except:
                pass
            self.display_service.display_permanent(["", title, str(value), ""])
            time.sleep(1)

    def __start_updating_display(self, title, sim_connect_reference):
        self.stop_updating_display()
        thread = threading.Thread(target=self.__update_display_thread, args=(title, sim_connect_reference))
        thread.start()

    def stop_updating_display(self):
        if self.active_thread:
            self.active_thread = False

    def handle(self, action):
        action = action.lower()
        if not self.setup:
            check = self.setup_sim_connect()
            if not check:
                return

        # Ifs for display actions
        if action == "get_altitude":
            self.__start_updating_display("Current Altitude", "PLANE_ALTITUDE")

        # Ifs for control actions

        pass


    #
    # Below are just my own wrapper methods for the MS Flight Sim Connect API, utilising the Python-SimConnect library
    #