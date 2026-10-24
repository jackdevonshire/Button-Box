"""
The sound engine: sits between your microphone and the game, mixing sound clips in with your voice.

    mic ──► (delay) ──┬──► game output (a virtual cable the game uses as its mic)
    clips ────────────┤
                      └──► monitor output (your headphones - clips only, so you hear them too)

It also does push-to-talk: as every block of mic audio passes through, it knows when you're talking, and holds the
game's push-to-talk key while you are or while a clip plays. The mic can be delayed a little so the key is already down
when your first word reaches the game, rather than cutting it off. Or, for games where simulated key presses are a
worry, it can press nothing and gate your voice instead - only letting it through while you talk, with the game set to
open mic.

Each device runs its own audio stream with a callback on its own thread. The callbacks only do quick numpy work;
pressing keys and tidying up happens on a separate control thread.
"""
import math
import threading
import time
import traceback

import numpy as np
import sounddevice as sd

from app.joystick.output import held_keys
from app.sound import apps, clips, devices

SAMPLE_RATE = clips.SAMPLE_RATE
BLOCK = 480                     # 10 ms - audio is handled, and talking detected, in blocks this size
JITTER_SAMPLES = BLOCK * 2      # Extra mic audio kept buffered, so timing differences between devices don't cause gaps
CONTROL_SECONDS = 0.01          # How often the control thread checks whether to hold push-to-talk
PUBLISH_SECONDS = 0.1           # Live state (the mic meter) is sent to the UI at most this often
FOCUS_CHECK_SECONDS = 0.25      # How often to check which app is in front
RETRY_SECONDS = 5               # How often to retry devices that couldn't be opened (e.g. a headset unplugged)
ATTACK_BLOCKS = 2               # Blocks in a row above the threshold before it counts as talking, so clicks don't
CLIP_PREROLL_MS = 120           # Push-to-talk is held this long before a clip reaches the game, so its start isn't lost
CLIP_TAIL_MS = 150              # And kept held this long after it ends
DUCK_ATTACK_SECONDS = 0.05      # How quickly sounds drop when you start talking
DUCK_RELEASE_SECONDS = 0.4      # And come back up after you stop
CABLE_SECONDS = 0.1             # Roughly how long audio takes to come out of a virtual cable (measured with VB-Cable)
SILENCE_DB = -100
PTT_HOLDER = ("sound", "push-to-talk")
STREAMS = ("mic", "game", "monitor", "listen")

DEFAULT_SETTINGS = {
    "micDevice": None,       # Your microphone
    "gameDevice": None,      # Where your voice and clips go - a virtual cable's input, which the game uses as its mic
    "monitorDevice": None,   # Your headphones, to hear clips yourself
    "micVolume": 1.0,
    "clipVolume": 0.8,       # Clips into the game
    "duckVolume": 0.2,       # Clips in the game drop to this (of their volume) while you talk, so you're heard. 1 = off
    "monitorVolume": 0.5,    # Clips in your headphones
    "pushToTalk": {
        "enabled": False,
        # "key" holds the game's push-to-talk key. "gate" presses nothing - your voice is only sent while you talk,
        # with the game set to open mic - for games where simulated key presses are a worry
        "method": "key",
        "key": "k",
        "onVoice": True,     # Hold the key while you talk
        "onClips": True,     # Hold the key while a clip plays
        "threshold": -40,    # dB - louder than this counts as talking
        "releaseMs": 500,    # Keep holding this long after you stop talking, so it doesn't drop between words
        "micDelayMs": 60,    # Delay your voice by this much, so the key is down before your first word arrives
        "focusApp": "",      # Only hold the key while this app (e.g. "Wardogs.exe") is in front. Empty for any app
    },
}


class SoundError(Exception):
    pass


class _RingBuffer:
    """A fixed size FIFO of samples, written by the mic's thread and read by the game output's"""

    def __init__(self, size):
        self.__data = np.zeros(size, np.float32)
        self.__start = 0
        self.__count = 0
        self.__lock = threading.Lock()

    @property
    def available(self):
        return self.__count

    def write(self, samples):
        with self.__lock:
            size = len(self.__data)
            samples = samples[-size:]
            n = len(samples)
            overflow = self.__count + n - size
            if overflow > 0:
                self.__start = (self.__start + overflow) % size
                self.__count -= overflow
            end = (self.__start + self.__count) % size
            first = min(n, size - end)
            self.__data[end:end + first] = samples[:first]
            self.__data[:n - first] = samples[first:]
            self.__count += n

    def read(self, n):
        """The next n samples, or None if there aren't that many yet"""
        with self.__lock:
            if self.__count < n:
                return None
            size = len(self.__data)
            first = min(n, size - self.__start)
            out = np.empty(n, np.float32)
            out[:first] = self.__data[self.__start:self.__start + first]
            out[first:] = self.__data[:n - first]
            self.__start = (self.__start + n) % size
            self.__count -= n
            return out

    def drop(self, n):
        with self.__lock:
            n = min(n, self.__count)
            self.__start = (self.__start + n) % len(self.__data)
            self.__count -= n

    def clear(self):
        with self.__lock:
            self.__start = self.__count = 0


class _Voice:
    """One clip playing. Each output keeps its own position, as they run on separate clocks."""

    def __init__(self, action_id, samples, volume, outputs, game_delay):
        self.action_id = action_id
        self.samples = samples
        self.volume = volume
        self.positions = {output: -game_delay if output == "game" else 0 for output in outputs}
        self.stopped = False

    def finished(self):
        return self.stopped or all(position >= len(self.samples) for position in self.positions.values())

    def mix_into(self, output, buffer):
        position = self.positions.get(output)
        if position is None or self.stopped:
            return
        frames = len(buffer)
        start = max(position, 0)
        offset = start - position  # Silence first, while push-to-talk gets going
        count = min(frames - offset, len(self.samples) - start)
        if count > 0:
            buffer[offset:offset + count] += self.samples[start:start + count] * self.volume
        self.positions[output] = position + frames


class SoundEngine:
    def __init__(self, event_bus):
        self.__event_bus = event_bus
        self.__settings = DEFAULT_SETTINGS
        self.__enabled = False
        self.__lock = threading.RLock()  # Guards starting and stopping streams, and the list of clips playing

        self.__streams = {}          # "mic" / "game" / "monitor" / "listen" -> open stream
        self.__stream_devices = {}   # The device name each stream should be using (None when it shouldn't run)
        self.__errors = {}           # Stream -> a problem to show, like a device not being connected
        self.__last_retry = 0.0

        self.__mic_buffer = _RingBuffer(SAMPLE_RATE * 2)
        self.__priming = True        # Building the mic delay back up before sending the mic to the game
        self.__listening = False     # Playing the cable's output in your headphones, to hear what the game hears
        self.__listen_buffer = _RingBuffer(SAMPLE_RATE * 2)
        self.__listen_priming = True
        self.__cable_level_db = SILENCE_DB  # How loud what comes out of the cable is - what the game hears
        self.__voices = ()           # Clips playing - replaced, never changed in place, so callbacks can read it freely

        self.__level_db = SILENCE_DB
        self.__loud_blocks = 0
        self.__last_talk = -math.inf    # When talking was last heard
        self.__clips_until = -math.inf  # Push-to-talk stays held for clips until this time
        self.__key = None               # The key held for push-to-talk, if any
        self.__gate_gain = 1.0          # 1 while your voice is let through to the game, 0 while gated
        self.__duck_gain = 1.0          # How much of the clips' volume reaches the game - lowered while you talk
        self.__focus_ok = True
        self.__last_focus_check = 0.0
        self.__last_publish = 0.0
        self.__published = None

    def start(self):
        threading.Thread(target=self.__control_loop, name="sound-control", daemon=True).start()

    # region Settings and streams

    def configure(self, settings, enabled):
        """Applies settings. Streams are only restarted when the devices they use change."""
        with self.__lock:
            previous_delay = self.__mic_delay_samples()
            self.__settings = settings
            self.__enabled = enabled
            if self.__mic_delay_samples() != previous_delay:
                self.__priming = True  # Rebuild the buffer to the new delay
            self.__apply_streams()

    def __desired_devices(self):
        settings = self.__settings
        if not self.__enabled:
            return {name: None for name in STREAMS}
        ptt = settings["pushToTalk"]
        # The mic is only needed when sending it to the game, or listening for talking
        mic_needed = settings["gameDevice"] or (ptt["enabled"] and ptt["onVoice"])
        # The cable's output is always read when sending to a cable, for its level meter - and played in your
        # headphones while listening
        listen = devices.recording_side(settings["gameDevice"]) if settings["gameDevice"] else None
        if listen is None and self.__listening:
            listen = f"The recording side of {settings['gameDevice']}"
        return {
            "mic": settings["micDevice"] if mic_needed else None,
            "game": settings["gameDevice"],
            "monitor": settings["monitorDevice"],
            "listen": listen,
        }

    def set_listening(self, listening):
        """Plays what comes out of the cable - what the game hears - in your headphones, or stops"""
        with self.__lock:
            if listening and not self.__listening:
                self.__listen_buffer.clear()  # Start from now, not from what built up while not listening
                self.__listen_priming = True
            self.__listening = listening
            self.__apply_streams()

    def __apply_streams(self, retry_only=False):
        for name, device in self.__desired_devices().items():
            running = name in self.__streams
            if retry_only:
                if running or not device:
                    continue
            elif self.__stream_devices.get(name) == device and (running or not device):
                continue
            self.__close(name)
            self.__stream_devices[name] = device
            if device:
                self.__open(name, device)

    def __open(self, name, device):
        kind = "input" if name in ("mic", "listen") else "output"
        index = devices.find_device(device, kind)
        if index is None:
            self.__errors[name] = f"{device} isn't connected"
            return
        try:
            options = dict(device=index, samplerate=SAMPLE_RATE, blocksize=BLOCK, dtype="float32", latency="low",
                           extra_settings=sd.WasapiSettings(auto_convert=True))
            if name == "mic":
                stream = sd.InputStream(channels=1, callback=self.__mic_callback, **options)
                self.__mic_buffer.clear()
                self.__priming = True
            elif name == "listen":
                stream = sd.InputStream(channels=1, callback=self.__listen_callback, **options)
                self.__listen_buffer.clear()
                self.__listen_priming = True
            else:
                callback = self.__game_callback if name == "game" else self.__monitor_callback
                stream = sd.OutputStream(channels=devices.output_channels(index), callback=callback, **options)
            stream.start()
        except Exception as e:
            self.__errors[name] = f"Couldn't open {device}: {e}"
            print(f"Sound - couldn't open {name} device {device}:\n{traceback.format_exc()}")
            return
        self.__streams[name] = stream
        self.__errors.pop(name, None)

    def __close(self, name):
        stream = self.__streams.pop(name, None)
        self.__errors.pop(name, None)
        if stream:
            try:
                stream.close()
            except Exception:
                pass

    def __talk_hold_seconds(self):
        """How long talking counts for after the last loud block - long enough for your delayed voice to get through"""
        hold = self.__settings["pushToTalk"]["releaseMs"] / 1000 + self.__mic_delay_samples() / SAMPLE_RATE
        if "game" in self.__streams and not self.__gating():
            hold += CABLE_SECONDS  # Your voice also takes a moment to come out of the virtual cable after the key
        return hold

    def __gating(self):
        """Whether your voice is only let through while you talk, rather than a key being held"""
        ptt = self.__settings["pushToTalk"]
        return self.__enabled and ptt["enabled"] and ptt["method"] == "gate"

    def __mic_delay_samples(self):
        ptt = self.__settings["pushToTalk"]
        if ptt["enabled"] and (ptt["onVoice"] or ptt["method"] == "gate"):
            return int(ptt["micDelayMs"] * SAMPLE_RATE / 1000)
        return 0

    # endregion

    # region Audio callbacks - these run on the audio threads, so keep them quick

    def __mic_callback(self, indata, frames, time_info, status):
        samples = indata[:, 0] * self.__settings["micVolume"]
        rms = float(np.sqrt(np.mean(samples * samples))) if frames else 0.0
        level = 20 * math.log10(rms) if rms > 1e-5 else SILENCE_DB
        self.__level_db = level

        if level >= self.__settings["pushToTalk"]["threshold"]:
            self.__loud_blocks += 1
            if self.__loud_blocks >= ATTACK_BLOCKS:
                self.__last_talk = time.perf_counter()
        else:
            self.__loud_blocks = 0

        if "game" in self.__streams:
            self.__mic_buffer.write(samples.astype(np.float32, copy=False))

    def __game_callback(self, outdata, frames, time_info, status):
        mix = np.zeros(frames, np.float32)

        if "mic" in self.__streams:
            delay = self.__mic_delay_samples()
            if self.__priming and self.__mic_buffer.available >= delay + JITTER_SAMPLES + frames:
                self.__priming = False
            if not self.__priming:
                voice = self.__mic_buffer.read(frames)
                if voice is None:
                    self.__priming = True  # Ran dry - build the delay back up rather than crackle
                else:
                    if self.__gating():
                        # Fade over the block rather than switching instantly, which would click
                        target = 1.0 if time.perf_counter() - self.__last_talk < self.__talk_hold_seconds() else 0.0
                        if target != self.__gate_gain:
                            voice *= np.linspace(self.__gate_gain, target, frames, dtype=np.float32)
                        elif target == 0.0:
                            voice[:] = 0
                        self.__gate_gain = target
                    else:
                        self.__gate_gain = 1.0
                    mix += voice
                    # The mic and the cable tick at very slightly different rates - drop any audio piling up
                    excess = self.__mic_buffer.available - (delay + JITTER_SAMPLES * 2)
                    if excess > BLOCK:
                        self.__mic_buffer.drop(excess)

        clip_mix = np.zeros(frames, np.float32)
        for voice in self.__voices:
            voice.mix_into("game", clip_mix)
        mix += clip_mix * (self.__duck_gains(frames) * self.__settings["clipVolume"])

        np.clip(mix, -1, 1, out=mix)
        outdata[:] = mix[:, None]

    def __duck_gains(self, frames):
        """
        The clips' volume for this block: lowered while you're talking so your voice comes through, fading rather
        than jumping. A single number when it's steady, or a ramp across the block while fading.
        """
        duck = self.__settings.get("duckVolume", 1.0)
        talking = "mic" in self.__streams and time.perf_counter() - self.__last_talk < self.__talk_hold_seconds()
        target = duck if talking else 1.0
        start = self.__duck_gain
        if start == target:
            return start
        seconds = DUCK_ATTACK_SECONDS if target < start else DUCK_RELEASE_SECONDS
        step = max(1.0 - duck, 0.01) * frames / SAMPLE_RATE / seconds
        end = max(target, start - step) if target < start else min(target, start + step)
        self.__duck_gain = end
        return np.linspace(start, end, frames, dtype=np.float32)

    def __monitor_callback(self, outdata, frames, time_info, status):
        mix = np.zeros(frames, np.float32)
        if self.__listening and "listen" in self.__streams:
            # Hearing the cable already includes the clips, so they're not played directly as well
            if self.__listen_priming and self.__listen_buffer.available >= JITTER_SAMPLES + frames:
                self.__listen_priming = False
            if not self.__listen_priming:
                heard = self.__listen_buffer.read(frames)
                if heard is None:
                    self.__listen_priming = True
                else:
                    mix += heard
                    excess = self.__listen_buffer.available - JITTER_SAMPLES * 2
                    if excess > BLOCK:
                        self.__listen_buffer.drop(excess)
            # Clips still move along here, so they finish
            unheard = np.zeros(frames, np.float32)
            for voice in self.__voices:
                voice.mix_into("monitor", unheard)
        else:
            for voice in self.__voices:
                voice.mix_into("monitor", mix)
        mix *= self.__settings["monitorVolume"]
        np.clip(mix, -1, 1, out=mix)
        outdata[:] = mix[:, None]

    def __listen_callback(self, indata, frames, time_info, status):
        samples = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(samples * samples))) if frames else 0.0
        self.__cable_level_db = 20 * math.log10(rms) if rms > 1e-5 else SILENCE_DB
        if self.__listening:
            self.__listen_buffer.write(samples)

    # endregion

    # region Clips

    def play(self, action_id, file, volume=1.0, again="restart"):
        """
        Plays a clip. again says what happens if it's already playing: "restart" it, "stop" it, or "overlap" - play
        another copy over the top. Returns False if this stopped the clip rather than playing it.
        """
        samples = clips.load(file)
        with self.__lock:
            outputs = [name for name in ("game", "monitor") if name in self.__streams]
            if not outputs:
                raise SoundError("Choose where sounds play on the Sound page")

            playing = [voice for voice in self.__voices if voice.action_id == action_id and not voice.finished()]
            if playing and again in ("restart", "stop"):
                for voice in playing:
                    voice.stopped = True
                if again == "stop":
                    return False

            ptt = self.__settings["pushToTalk"]
            preroll = 0
            if self.__enabled and ptt["enabled"] and ptt["method"] == "key" and ptt["onClips"] and self.__key is None and \
                    self.__focus_ok:
                preroll = int(CLIP_PREROLL_MS * SAMPLE_RATE / 1000)
                # Covers the gap until the control thread sees the clip playing
                self.__clips_until = time.perf_counter() + CLIP_PREROLL_MS / 1000 + 0.05
            voice = _Voice(action_id, samples, volume, outputs, preroll)
            self.__voices = tuple(v for v in self.__voices if not v.finished()) + (voice,)
        return True

    def stop(self, action_id=None):
        """Stops one clip, or every clip"""
        with self.__lock:
            for voice in self.__voices:
                if action_id is None or voice.action_id == action_id:
                    voice.stopped = True

    # endregion

    # region Control loop - push-to-talk, tidying up and publishing live state

    def __control_loop(self):
        while True:
            try:
                self.__control(time.perf_counter())
            except Exception:
                print(f"Sound engine error:\n{traceback.format_exc()}")
                time.sleep(1)
            time.sleep(CONTROL_SECONDS)

    def __control(self, now):
        settings = self.__settings
        ptt = settings["pushToTalk"]

        with self.__lock:
            # Streams stop by themselves if their device goes away - notice, and try again now and then
            for name, stream in list(self.__streams.items()):
                if not stream.active:
                    self.__close(name)
                    self.__errors[name] = f"{self.__stream_devices.get(name)} stopped. Was it unplugged?"
            if now - self.__last_retry > RETRY_SECONDS:
                self.__last_retry = now
                self.__apply_streams(retry_only=True)

            if any(voice.finished() for voice in self.__voices):
                self.__voices = tuple(voice for voice in self.__voices if not voice.finished())

        playing = [voice for voice in self.__voices if not voice.finished()]
        if any("game" in voice.positions for voice in playing):
            self.__clips_until = max(self.__clips_until, now + CLIP_TAIL_MS / 1000)
        talking = "mic" in self.__streams and now - self.__last_talk < self.__talk_hold_seconds()

        if not ptt["focusApp"]:
            self.__focus_ok = True
        elif now - self.__last_focus_check > FOCUS_CHECK_SECONDS:
            self.__last_focus_check = now
            self.__focus_ok = (apps.foreground_app() or "").lower() == ptt["focusApp"].lower()

        wanted = self.__enabled and ptt["enabled"] and ptt["method"] == "key" and self.__focus_ok and (
            (ptt["onVoice"] and talking) or (ptt["onClips"] and now < self.__clips_until))
        key = ptt["key"] if wanted else None
        if key != self.__key:
            if self.__key:
                held_keys.release(self.__key, PTT_HOLDER)
            if key:
                held_keys.press(key, PTT_HOLDER)
            self.__key = key

        if now - self.__last_publish > PUBLISH_SECONDS:
            self.__last_publish = now
            state = self.live_state(talking=talking, playing=playing)
            if state != self.__published:
                self.__published = state
                self.__event_bus.publish("sound", state)

    def live_state(self, talking=None, playing=None):
        if talking is None:
            talking = "mic" in self.__streams and time.perf_counter() - self.__last_talk < self.__talk_hold_seconds()
        if playing is None:
            playing = [voice for voice in self.__voices if not voice.finished()]
        return {
            "level": round(self.__level_db, 1) if "mic" in self.__streams else None,
            "talking": talking,
            "keyHeld": self.__key is not None,
            "listening": self.__listening and "listen" in self.__streams,
            "cableLevel": round(self.__cable_level_db, 1) if "listen" in self.__streams else None,
            "gateOpen": self.__gating() and "game" in self.__streams and self.__gate_gain > 0,
            "focusOk": self.__focus_ok,
            "playing": sorted({voice.action_id for voice in playing}),
        }

    def status(self):
        with self.__lock:
            return {
                "running": {name: self.__stream_devices.get(name) for name in self.__streams},
                "errors": dict(self.__errors),
                **self.live_state(),
            }

    # endregion
