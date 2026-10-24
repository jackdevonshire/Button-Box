"""
Sound clip files: where they're kept, reading them and converting them to the engine's format (mono, 48 kHz).
"""
import os
import re
import threading

import numpy as np
import soundfile

SAMPLE_RATE = 48000
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds")
EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac"}
MAX_SECONDS = 600
SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+\.(wav|mp3|ogg|flac)$")

_cache = {}  # File -> (modified time, samples)
_lock = threading.Lock()


def path_for(file):
    if not SAFE_NAME.match(file or ""):
        raise ValueError("That isn't a sound file the panel saved")
    return os.path.join(SOUNDS_DIR, file)


def exists(file):
    try:
        return os.path.isfile(path_for(file))
    except ValueError:
        return False


def describe(file):
    """Length in seconds, or None if the file is missing or unreadable"""
    try:
        info = soundfile.info(path_for(file))
        return round(info.frames / info.samplerate, 2)
    except (ValueError, RuntimeError, OSError, soundfile.LibsndfileError):
        return None


def check(path):
    """Makes sure an uploaded file can be played, raising ValueError with a message for the user if not"""
    try:
        info = soundfile.info(path)
    except (RuntimeError, soundfile.LibsndfileError):
        raise ValueError("That file couldn't be read as audio. Try a WAV, MP3, OGG or FLAC file.")
    if info.frames / info.samplerate > MAX_SECONDS:
        raise ValueError(f"Sounds can be up to {MAX_SECONDS // 60} minutes long")


def load(file):
    """A clip's samples as mono float32 at 48 kHz, cached until the file changes"""
    path = path_for(file)
    modified = os.path.getmtime(path)
    with _lock:
        cached = _cache.get(file)
        if cached and cached[0] == modified:
            return cached[1]

    data, rate = soundfile.read(path, dtype="float32", always_2d=True)
    samples = data.mean(axis=1)
    if rate != SAMPLE_RATE and len(samples) > 1:
        # Linear resampling is plenty for sound effects and voice clips
        length = int(len(samples) * SAMPLE_RATE / rate)
        samples = np.interp(np.linspace(0, len(samples) - 1, length), np.arange(len(samples)), samples)
    samples = np.ascontiguousarray(samples, dtype=np.float32)

    with _lock:
        _cache[file] = (modified, samples)
    return samples


def forget(file):
    with _lock:
        _cache.pop(file, None)
