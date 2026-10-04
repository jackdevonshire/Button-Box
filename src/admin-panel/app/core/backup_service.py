"""
Export and import of everything you've set up - configurations, bindings, joystick mappings, actions and which
integrations are on.

Exports use references instead of database ids, so they can be imported into any panel. Mode selection actions aren't
exported (they're generated per configuration) - bindings to them are saved as "switch to configuration X" instead.
The box's IP isn't exported as it belongs to the network, not the setup.
"""
import datetime
import json
import os

from app.core.models import Configuration, Binding, IntegrationAction, Integration, JoystickMapping
from app.core.types import PhysicalKey, Gesture

BACKUP_FORMAT = "button-box-backup"
BACKUP_VERSION = 2  # 2 added joystick mappings
MODE_SELECTION_INTEGRATION_ID = 2


class BackupError(ValueError):
    pass


class BackupService:
    def __init__(self, db, integration_factory, button_box_service, core_service, backup_dir):
        self.db = db
        self.integration_factory = integration_factory
        self.button_box_service = button_box_service
        self.core_service = core_service
        self.backup_dir = backup_dir

    def export(self):
        actions = IntegrationAction.query.filter(IntegrationAction.integration_id != MODE_SELECTION_INTEGRATION_ID).all()
        active_id = self.button_box_service.current_configuration.id

        def action_reference(action):
            if action.integration_id == MODE_SELECTION_INTEGRATION_ID:
                return {"switchTo": action.configuration["ConfigurationId"]}
            return {"action": action.id}

        configurations = []
        for configuration in Configuration.query.order_by(Configuration.id).all():
            bindings = []
            for binding in Binding.query.filter_by(configuration_id=configuration.id).order_by(Binding.id).all():
                target = action_reference(binding.integration_action)
                bindings.append({
                    "name": binding.name or "",
                    "control": PhysicalKey(binding.physical_key).name,
                    "event": "on" if binding.event_type == 1 else "off",
                    "modifiers": binding.modifiers or [],
                    "gesture": binding.gesture,
                    "enabled": binding.enabled,
                    **target,
                })
            configurations.append({
                "ref": configuration.id,
                "name": configuration.name,
                "description": configuration.description,
                "displayLines": configuration.display_lines,
                "active": configuration.id == active_id,
                "bindings": bindings,
                "joystickMappings": [self.__export_mapping(mapping, action_reference) for mapping in
                                     JoystickMapping.query.filter_by(configuration_id=configuration.id)
                                     .order_by(JoystickMapping.id)],
            })

        return {
            "format": BACKUP_FORMAT,
            "version": BACKUP_VERSION,
            "exportedAt": datetime.datetime.now().isoformat(timespec="seconds"),
            "integrations": [{"id": i.id, "active": i.is_active} for i in Integration.query.order_by(Integration.id)],
            "actions": [{
                "ref": action.id,
                "integrationId": action.integration_id,
                "name": action.name,
                "description": action.description or "",
                "configuration": action.configuration,
            } for action in actions],
            "configurations": configurations,
        }

    def __export_mapping(self, mapping, action_reference):
        output = dict(mapping.output)
        if mapping.output_type == "action":
            action = self.db.session.get(IntegrationAction, output.pop("actionId"))
            output.update(action_reference(action))
        return {"name": mapping.name, "device": mapping.device, "inputType": mapping.input_type,
                "input": mapping.input, "outputType": mapping.output_type, "output": output,
                "enabled": mapping.enabled}

    def save_backup_file(self, reason):
        os.makedirs(self.backup_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(self.backup_dir, f"backup_{stamp}_{reason}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.export(), f, indent=2)
        return path

    def import_replace(self, data):
        """Replaces everything with the contents of a backup. Saves a backup of the current setup first."""
        plan = self.__validate(data)
        backup_path = self.save_backup_file("before-import")

        session = self.db.session
        JoystickMapping.query.delete()
        Binding.query.delete()
        IntegrationAction.query.delete()
        Configuration.query.delete()
        session.flush()

        configuration_ids = {}
        active_configuration_id = None
        for item in plan["configurations"]:
            configuration = Configuration(name=item["name"], description=item["description"],
                                          display_lines=item["displayLines"])
            session.add(configuration)
            session.flush()
            configuration_ids[item["ref"]] = configuration.id
            if item["active"]:
                active_configuration_id = configuration.id

        action_ids = {}
        for item in plan["actions"]:
            action = IntegrationAction(integration_id=item["integrationId"], name=item["name"],
                                       description=item["description"], configuration=item["configuration"])
            session.add(action)
            session.flush()
            action_ids[item["ref"]] = action.id

        for integration in plan["integrations"]:
            self.integration_factory.get_integration_by_id(integration["id"]).set_active(integration["active"])

        session.commit()
        self.core_service.sync_integration_actions()  # Creates the "switch to" action for each configuration

        switch_actions = {action.configuration["ConfigurationId"]: action.id for action in
                          IntegrationAction.query.filter_by(integration_id=MODE_SELECTION_INTEGRATION_ID)}
        for item in plan["configurations"]:
            for binding in item["bindings"]:
                if "switchTo" in binding:
                    action_id = switch_actions[configuration_ids[binding["switchTo"]]]
                else:
                    action_id = action_ids[binding["action"]]
                session.add(Binding(
                    configuration_id=configuration_ids[item["ref"]],
                    name=binding["name"],
                    physical_key=PhysicalKey[binding["control"]].value,
                    event_type=1 if binding["event"] == "on" else 0,
                    integration_action_id=action_id,
                    modifiers=binding["modifiers"],
                    gesture=binding["gesture"],
                    enabled=binding["enabled"],
                ))
            for mapping in item["joystickMappings"]:
                output = {key: value for key, value in mapping["output"].items() if key not in ("action", "switchTo")}
                if mapping["outputType"] == "action":
                    if "switchTo" in mapping["output"]:
                        output["actionId"] = switch_actions[configuration_ids[mapping["output"]["switchTo"]]]
                    else:
                        output["actionId"] = action_ids[mapping["output"]["action"]]
                session.add(JoystickMapping(
                    configuration_id=configuration_ids[item["ref"]],
                    name=mapping.get("name") or "",
                    device=mapping["device"],
                    input_type=mapping["inputType"],
                    input=str(mapping["input"]),
                    output_type=mapping["outputType"],
                    output=output,
                    enabled=mapping.get("enabled", True),
                ))
        session.commit()

        self.button_box_service.api_change_active_configuration(
            active_configuration_id or configuration_ids[plan["configurations"][0]["ref"]])

        return {"backupPath": backup_path, "configurations": len(configuration_ids), "actions": len(action_ids)}

    def __validate(self, data):
        """Checks the whole backup before anything is changed, so a bad file can't leave a half-imported setup"""
        if not isinstance(data, dict) or data.get("format") != BACKUP_FORMAT:
            raise BackupError("This isn't a Button Box backup file")
        if data.get("version", 0) > BACKUP_VERSION:
            raise BackupError("This backup was made by a newer version of the panel")

        integrations = {integration.id: integration for integration in self.integration_factory.get_all_integrations()}

        actions = []
        for item in data.get("actions", []):
            integration = integrations.get(item.get("integrationId"))
            if integration is None or not integration.user_actions:
                raise BackupError(f"Action '{item.get('name')}' is for an integration this panel doesn't have")
            try:
                configuration = integration.validate_action_configuration(item.get("configuration"))
            except ValueError as e:
                raise BackupError(f"Action '{item.get('name')}' is invalid: {e}")
            actions.append({"ref": item.get("ref"), "integrationId": integration.id,
                            "name": str(item.get("name") or "Untitled action"),
                            "description": str(item.get("description") or ""), "configuration": configuration})
        action_refs = {action["ref"] for action in actions}

        configurations = data.get("configurations") or []
        if not configurations:
            raise BackupError("The backup doesn't contain any configurations")
        configuration_refs = {item.get("ref") for item in configurations}
        controls = set(PhysicalKey.__members__)
        gestures = {gesture.value for gesture in Gesture}

        for item in configurations:
            name = item.get("name") or "Untitled"
            for binding in item.get("bindings", []):
                if binding.get("control") not in controls or binding.get("event") not in ("on", "off"):
                    raise BackupError(f"A binding in '{name}' uses an unknown control or event")
                if not set(binding.get("modifiers") or []) <= controls:
                    raise BackupError(f"A binding in '{name}' uses an unknown modifier")
                if binding.get("gesture", "single") not in gestures:
                    raise BackupError(f"A binding in '{name}' uses an unsupported gesture")
                if "switchTo" in binding:
                    if binding["switchTo"] not in configuration_refs:
                        raise BackupError(f"A binding in '{name}' switches to a configuration that isn't in the backup")
                elif binding.get("action") not in action_refs:
                    raise BackupError(f"A binding in '{name}' uses an action that isn't in the backup")
                binding.setdefault("name", "")
                binding.setdefault("modifiers", [])
                binding.setdefault("gesture", "single")
                binding.setdefault("enabled", True)
            for mapping in item.setdefault("joystickMappings", []):
                if mapping.get("inputType") not in ("hat", "button") or mapping.get("outputType") not in (
                        "mouse", "keys", "action") or not isinstance(mapping.get("output"), dict) or not mapping.get("device"):
                    raise BackupError(f"A joystick mapping in '{name}' isn't valid")
                if mapping["outputType"] == "action":
                    target = mapping["output"]
                    if "switchTo" in target:
                        if target["switchTo"] not in configuration_refs:
                            raise BackupError(f"A joystick mapping in '{name}' switches to a configuration that isn't in the backup")
                    elif target.get("action") not in action_refs:
                        raise BackupError(f"A joystick mapping in '{name}' uses an action that isn't in the backup")
            item["name"] = name
            item["description"] = item.get("description") or ""
            item.setdefault("displayLines", None)
            item.setdefault("active", False)
            item.setdefault("bindings", [])

        return {
            "actions": actions,
            "configurations": configurations,
            "integrations": [i for i in data.get("integrations", []) if i.get("id") in integrations],
        }
