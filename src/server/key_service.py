from display_service import DisplayService
from user_scripts import UserScripts
from game_services.ms_flight_sim import MicrosoftFlightSimulator

from button.keybind_button import KeybindButton
from button.script_button import ScriptButton
from button.command_button import CommandButton
from button.msteams_button import MSTeamsButton
from button.msflightsim_button import MSFlightSimButton
from button.tapo_button import TapoButton
from button.broadlink_button import BroadlinkButton

class KeyService:
    def __init__(self, configurations, integrations, display_service : DisplayService, script_service: UserScripts):
        self.configurations = configurations
        self.current_configuration = self.configurations[0]
        self.initialised_configuration = False
        self.button_states = {}
        self.integrations = integrations

        self.display_service = display_service
        self.script_service = script_service

        self.ms_flight_sim_service = MicrosoftFlightSimulator(display_service)

        # Initialise self
        self.__initialise()

    def __initialise(self):
        self.__initialise_button_states()
        self.switch_configuration()
    def __initialise_button_states(self):
        for configuration in self.configurations:
            for button in configuration["Buttons"]:
                button_reference = button["Reference"]

                if button_reference not in self.button_states:
                    self.button_states[button_reference] = "OFF"

    def __cleanup(self):
        # Stopping any user scripts that are constantly updating the display
        self.script_service.stop_current_script()
        self.ms_flight_sim_service.stop_updating_display()
    def handle_key_event(self, button_reference, event):
        # On any button event we want to stop any processes that are actively updating the display
        self.__cleanup()

        current_button_config = {}
        for button in self.current_configuration["Buttons"]:
            if button["Reference"] == button_reference:
                current_button_config = button
                break

        if len(current_button_config.items()) == 0:
            return self.display_service.display_temporary_message(["", "Error:", "Invalid Button", button_reference], 2)

        event_configuration = current_button_config[event]
        if event_configuration == None:
            return

        self.button_states[button_reference] = event
        event_type = event_configuration["Type"].lower()

        if event_type == "mode":
            return self.switch_configuration()

        if "Requirements" in event_configuration:
            for requirement in event_configuration["Requirements"]:
                req_button_ref = requirement["ButtonReference"]
                req_state = requirement["RequiredState"]

                if self.button_states[req_button_ref] != req_state:
                    return self.display_service.display_temporary_message(requirement["ErrorMessage"], 2)

        if event_type == "keybind":
            button = KeybindButton(event_configuration, self.display_service)
        elif event_type == "script":
            button = ScriptButton(event_configuration, self.display_service, self.script_service)
        elif event_type == "command":
            button = CommandButton(event_configuration, self.display_service)
        elif event_type == "teams":
            button = MSTeamsButton(event_configuration, self.display_service)
        elif event_type == "msflightsim":
            button = MSFlightSimButton(event_configuration, self.display_service, self.ms_flight_sim_service)
        elif event_type == "tapo":
            button = TapoButton(event_configuration, self.display_service, self.integrations["Tapo"])
        elif event_type == "broadlink":
            button = BroadlinkButton(event_configuration, self.display_service, self.integrations["Broadlink"])

        return button.handle()

    def switch_configuration(self):
        self.ms_flight_sim_service.stop_service()

        if self.initialised_configuration:
            # Switch to next configuration
            for x in range(0, len(self.configurations)):
                if self.configurations[x]["Id"] == self.current_configuration["Id"]:
                    try:
                        self.current_configuration = self.configurations[x + 1]
                    except:
                        self.current_configuration = self.configurations[0]

                    break
        else:
            self.initialised_configuration = True

        self.display_service.set_default_message(self.current_configuration["DefaultScreenMessage"])
        self.display_service.force_default_message()