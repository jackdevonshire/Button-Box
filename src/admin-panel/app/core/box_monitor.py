import datetime
import ipaddress
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

BOX_PORT = 8000
PROBE_INTERVAL_SECONDS = 5
PROBE_TIMEOUT_SECONDS = 1.5
SCAN_TIMEOUT_SECONDS = 0.6
SCAN_COOLDOWN_SECONDS = 60
FAILED_PROBES_BEFORE_SCAN = 3


def is_button_box(ip, timeout=PROBE_TIMEOUT_SECONDS):
    """
    The box only accepts POSTs to /display, so a GET returns 405 without touching the screen.
    That makes it a safe way to both detect the box and check it's online.
    """
    try:
        response = requests.get(f"http://{ip}:{BOX_PORT}/display", timeout=timeout)
        return response.status_code == 405
    except requests.RequestException:
        return False


def get_local_ip():
    # Connecting a UDP socket sends nothing, but tells us which local interface would be used for the LAN
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("192.168.0.1", 1))
            return s.getsockname()[0]
        except OSError:
            return None


class BoxMonitor:
    """
    Tracks whether the button box is reachable, and finds it on the local network when its IP is unknown or
    it has stopped responding (e.g. it was given a new IP by the router).
    """

    def __init__(self, get_ip, on_box_found):
        self.__get_ip = get_ip
        self.__on_box_found = on_box_found
        self.__failed_probes = 0
        self.__last_scan = 0
        self.__scan_lock = threading.Lock()

        self.online = False
        self.latency_ms = None
        self.last_seen = None
        self.last_event = None
        self.scanning = False

    def start(self):
        threading.Thread(target=self.__run, name="box-monitor", daemon=True).start()

    def record_event(self):
        self.last_event = datetime.datetime.now()
        self.last_seen = self.last_event
        self.online = True
        self.__failed_probes = 0

    def get_status(self):
        return {
            "Online": self.online,
            "LatencyMs": self.latency_ms,
            "LastSeen": self.last_seen.isoformat() if self.last_seen else None,
            "LastEvent": self.last_event.isoformat() if self.last_event else None,
            "Scanning": self.scanning,
            "ButtonBoxIP": self.__get_ip(),
        }

    def __run(self):
        while True:
            try:
                self.__probe()
            except Exception as e:
                print(f"Box Monitor - Probe failed: {e}")
            time.sleep(PROBE_INTERVAL_SECONDS)

    def __probe(self):
        ip = self.__get_ip()
        if ip:
            start = time.perf_counter()
            if is_button_box(ip):
                self.latency_ms = round((time.perf_counter() - start) * 1000)
                self.online = True
                self.last_seen = datetime.datetime.now()
                self.__failed_probes = 0
                return
            self.__failed_probes += 1

        self.online = False
        self.latency_ms = None
        if not ip or self.__failed_probes >= FAILED_PROBES_BEFORE_SCAN:
            if time.time() - self.__last_scan > SCAN_COOLDOWN_SECONDS:
                self.scan()

    def scan(self, wait=False):
        """
        Scans the local /24 network for the button box. Returns the IP found, or None.
        If a scan is already running, returns None straight away unless wait is set.
        """
        if not self.__scan_lock.acquire(blocking=wait):
            return None

        try:
            self.scanning = True
            self.__last_scan = time.time()

            local_ip = get_local_ip()
            if not local_ip:
                return None

            network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
            candidates = [str(host) for host in network.hosts() if str(host) != local_ip]

            # Check the last known IP first so a quick reconnect doesn't wait on the whole sweep
            known_ip = self.__get_ip()
            if known_ip in candidates:
                candidates.remove(known_ip)
                candidates.insert(0, known_ip)

            print(f"Box Monitor - Scanning {network} for the button box")
            with ThreadPoolExecutor(max_workers=64) as pool:
                for ip, found in zip(candidates, pool.map(lambda c: is_button_box(c, SCAN_TIMEOUT_SECONDS), candidates)):
                    if found:
                        print(f"Box Monitor - Found button box at {ip}")
                        self.online = True
                        self.last_seen = datetime.datetime.now()
                        self.__failed_probes = 0
                        self.__on_box_found(ip)
                        return ip

            print("Box Monitor - Button box not found")
            return None
        finally:
            self.scanning = False
            self.__scan_lock.release()
