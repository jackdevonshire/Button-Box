# Sim Connect Available Variables
# https://docs.flightsimulator.com/html/Programming_Tools/SimVars/Aircraft_SimVars/Aircraft_AutopilotAssistant_Variables.htm
# https://docs.flightsimulator.com/html/Programming_Tools/SimVars/Simulation_Variables.htm#h
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

    def stop_service(self):
        self.active_thread = False
        self.sm = None
        self.aq = None
        self.setup = False

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

    def __update_display_thread(self, title, sim_connect_reference, units=None):
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

            value = str(value)
            if units is not None:
                value += units

            self.display_service.display_permanent(["", title, value, ""])
            time.sleep(1)

    def __update_display_general_stats_thread(self):
        self.active_thread = True
        while True:
            if not self.active_thread:
                return

            try:
                alt = int(self.aq.get("PLANE_ALTITUDE"))
                speed = int(self.aq.get("AIRSPEED_INDICATED"))
                vertical = int(self.aq.get("VERTICAL_SPEED"))
            except:
                continue

            self.display_service.display_permanent([
                "Altitude: " + str(alt) + "m",
                "Airspeed: " + str(speed) + " knots",
                "V-Speed: " + str(vertical) + " ft/s",
                ""], True)
            time.sleep(1)

    def __start_updating_display(self, title, sim_connect_reference, units=None):
        self.stop_updating_display()
        thread = threading.Thread(target=self.__update_display_thread, args=(title, sim_connect_reference, units))
        thread.start()

    def __start_updating_display_with_general_stats(self):
        self.stop_updating_display()
        thread = threading.Thread(target=self.__update_display_general_stats_thread)
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

        # Display Actions - General
        if action == "display_altitude":
            return self.__start_updating_display("Altitude", "PLANE_ALTITUDE", "metres")
        elif action == "display_airspeed":
            return self.__start_updating_display("Air Speed", "AIRSPEED_INDICATED", "knots")
        elif action == "display_verticalspeed":
            return self.__start_updating_display("Vertical Speed", "VERTICAL_SPEED", " ft/s")
        elif action == "display_stats":
            return self.__start_updating_display_with_general_stats()

        # Control Actions - Control Surfaces
        if action == "flaps_increase":
            return self.__increase_flaps()
        elif action == "flaps_decrease":
            return self.__decrease_flaps()
        elif action == "spoilers_on":
            return self.__spoilers_on()
        elif action == "spoilers_off":
            return self.__spoilers_off()

    #
    # Below are just my own wrapper methods for the MS Flight Sim Connect API, utilising the Python-SimConnect library
    #

    def __increase_flaps(self):
        max_flaps = self.aq.get("FLAPS_NUM_HANDLE_POSITIONS")
        current_flaps = self.aq.get("FLAPS_HANDLE_INDEX")

        current_flaps += 1
        if current_flaps > max_flaps:
            return self.display_service.display_temporary_message(["", "Flaps Set", str(max_flaps), ""], 2)

        self.aq.set("FLAPS_HANDLE_INDEX", current_flaps)
        return self.display_service.display_temporary_message(["", "Flaps Set", str(current_flaps), ""], 2)

    def __decrease_flaps(self):
        current_flaps = self.aq.get("FLAPS_HANDLE_INDEX")
        current_flaps -= 1

        if current_flaps < 0:
            return self.display_service.display_temporary_message(["", "Flaps Set", "0", ""], 2)

        self.aq.set("FLAPS_HANDLE_INDEX", current_flaps)
        return self.display_service.display_temporary_message(["", "Flaps Set", str(current_flaps), ""], 2)

    def __spoilers_on(self):
        self.aq.set("SPOILERS_HANDLE_POSITION", 1)
        self.display_service.display_temporary_message(["", "Spoilers", "On", ""], 2)

    def __spoilers_off(self):
        self.aq.set("SPOILERS_HANDLE_POSITION", 0)
        self.display_service.display_temporary_message(["", "Spoilers", "Off", ""], 2)
