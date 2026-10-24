"""
Audio devices, through Windows' WASAPI. Devices are remembered by name rather than index, as indexes change when
devices are plugged in or out.
"""
import sounddevice as sd

CABLE_HINTS = ("cable", "voicemeeter")  # Virtual cables - VB-Audio Virtual Cable, or VoiceMeeter's inputs


def _wasapi():
    for index, api in enumerate(sd.query_hostapis()):
        if api["name"] == "Windows WASAPI":
            return index, api
    raise RuntimeError("Windows audio (WASAPI) isn't available")


def is_cable(name):
    return any(hint in name.lower() for hint in CABLE_HINTS)


def list_devices():
    """Microphones and outputs, with which ones are Windows' defaults and which are virtual cables"""
    api_index, api = _wasapi()
    inputs, outputs = [], []
    for index, device in enumerate(sd.query_devices()):
        if device["hostapi"] != api_index or "16ch" in device["name"]:
            continue  # VB-Cable also adds a 16 channel version of itself, which only gets in the way here
        entry = {"name": device["name"], "isCable": is_cable(device["name"])}
        if device["max_input_channels"] > 0:
            inputs.append({**entry, "isDefault": index == api["default_input_device"]})
        if device["max_output_channels"] > 0:
            outputs.append({**entry, "isDefault": index == api["default_output_device"]})
    return {"inputs": inputs, "outputs": outputs}


def find_device(name, kind):
    """The device index for a name, or None if it isn't connected. kind is "input" or "output"."""
    if not name:
        return None
    api_index, _ = _wasapi()
    channels = "max_input_channels" if kind == "input" else "max_output_channels"
    for index, device in enumerate(sd.query_devices()):
        if device["hostapi"] == api_index and device["name"] == name and device[channels] > 0:
            return index
    return None


def recording_side(name):
    """
    The input a virtual cable's output comes back out of - what the game hears - e.g. "CABLE Input (VB-Audio Virtual
    Cable)" comes out of "CABLE Output (VB-Audio Virtual Cable)". None if there isn't one.
    """
    inputs = {device["name"] for device in list_devices()["inputs"]}
    for candidate in (name.replace("Input", "Output"), name.replace("input", "output")):
        if candidate != name and candidate in inputs:
            return candidate
    return None


def output_channels(index):
    return max(1, min(2, sd.query_devices(index)["max_output_channels"]))


def default_names():
    """Sensible devices to start with: the default mic and speakers, and the virtual cable if there is one"""
    devices = list_devices()
    mic = next((d["name"] for d in devices["inputs"] if d["isDefault"] and not d["isCable"]), None)
    monitor = next((d["name"] for d in devices["outputs"] if d["isDefault"] and not d["isCable"]), None)
    cable = next((d["name"] for d in devices["outputs"] if d["isCable"]), None)
    return {"micDevice": mic, "gameDevice": cable, "monitorDevice": monitor}
