"""GoPro — Open GoPro HTTP API (HERO9 and newer).

Endpoints taken from GoPro's own open-source SDK (github.com/gopro/OpenGoPro, `http_commands.py`) and its status IDs.
NOT tested on a real GoPro by the author — an adapter this complete deserves a real-camera report; please send one.

Reaching the camera
  * USB: the camera appears as a network device at 172.2X.1YZ.51 (XYZ = last 3 digits of its serial). Send once
    `GET /gopro/camera/control/wired_usb?p=1` if control is refused.
  * Wi-Fi AP: 10.5.5.9 — the Wi-Fi must first be switched on over Bluetooth (not done here).
Port 8080.

What it does: record, battery, remaining card time/space, overheating, resolution and frame rate (read + set),
digital zoom, keep-alive, and live view — the camera streams MPEG-TS over UDP and, if `ffmpeg` is installed, this adapter
turns it into JPEG frames. Without ffmpeg use GoPro "Webcam mode" and the app's *video input* monitor.
"""
import shutil
import subprocess
import threading
import time

from .base import Adapter, AdapterError, Unsupported, blank_state, http, split_jpegs

RESOLUTION = {"4K": 1, "2.7K": 4, "2.7K 4:3": 6, "1440p": 7, "1080p": 9, "720p": 12, "4K 4:3": 18, "5.3K": 100, "5K": 24, "5.6K": 21, "8K": 31}
FPS = {"240": 0, "120": 1, "100": 2, "90": 3, "60": 5, "50": 6, "30": 8, "25": 9, "24": 10, "200": 13}
S_OVERHEATING, S_ENCODING, S_REMAINING_VIDEO, S_SD_REMAINING, S_BATTERY = "6", "10", "35", "54", "70"


def _label(table, value):
    for k, v in table.items():
        if v == value:
            return k
    return None if value is None else "id %s" % value


class GoProHTTP(Adapter):
    id = "gopro_http"
    name = "GoPro (Open GoPro HTTP)"
    tested = False
    status_note = "Endpoints from GoPro's official SDK. Untested on real hardware."
    docs_url = "https://gopro.github.io/OpenGoPro/"
    capabilities = ("record", "battery", "storage", "zoom")
    fields = [
        {"key": "host", "label": "Camera address", "default": "10.5.5.9", "help": "10.5.5.9 over Wi-Fi, or the USB address (172.2X.1YZ.51)."},
        {"key": "port", "label": "Port", "default": 8080, "help": "8080."},
        {"key": "stream_port", "label": "Live-view UDP port", "default": 8554, "help": "Needs ffmpeg installed. Leave 8554."},
    ]

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._n = 0
        self._zoom = 0
        self._proc, self._buf, self._plock = None, b"", threading.Lock()
        self._ffmpeg = shutil.which("ffmpeg")
        if self._ffmpeg:
            self.capabilities = tuple(self.capabilities) + ("liveview",)

    def _u(self, path):
        return "http://%s:%s%s" % (self.cfg["host"], self.cfg["port"], path)

    def _get(self, path, **kw):
        return http("GET", self._u(path), **kw)

    def poll(self):
        st = blank_state()
        try:
            state = self._get("/gopro/camera/state")
        except AdapterError:
            return st
        self._n += 1
        if self._n % 3 == 1:                       # the camera goes to sleep without a keep-alive every few seconds
            try:
                self._get("/gopro/camera/keep_alive")
            except AdapterError:
                pass
        status, sett = state.get("status", {}), state.get("settings", {})
        st["connected"] = True
        st["recording"] = bool(status.get(S_ENCODING))
        pct = status.get(S_BATTERY)
        st["battery"] = pct if isinstance(pct, int) else None
        rem, free = status.get(S_REMAINING_VIDEO), status.get(S_SD_REMAINING)
        if rem is not None or free is not None:
            st["storage"] = {"free": free * 1024 if isinstance(free, int) else None, "total": None, "remaining_s": rem}
        st["extra"]["temperature"] = "hot" if status.get(S_OVERHEATING) else "normal"
        for key, sid, table in (("resolution", "2", RESOLUTION), ("fps", "3", FPS)):
            if sid in sett:
                lab = _label(table, sett[sid])
                st["advanced"][key] = {"value": lab, "options": list(table)}
        if self._n == 1:
            try:
                st["model"] = self._get("/gopro/camera/info").get("info", {}).get("model_name")
            except AdapterError:
                pass
        self._model = st["model"] = st["model"] or getattr(self, "_model", None)
        return st

    def record(self, start):
        self._get("/gopro/camera/shutter/" + ("start" if start else "stop"))

    def set(self, key, value):
        table = {"resolution": (2, RESOLUTION), "fps": (3, FPS)}.get(key)
        if not table:
            raise Unsupported(key)
        sid, tbl = table
        if str(value) not in tbl:
            raise AdapterError("unknown %s %r (options: %s)" % (key, value, ", ".join(tbl)))
        self._get("/gopro/camera/setting?setting=%d&option=%d" % (sid, tbl[str(value)]))

    def zoom(self, direction):                      # digital zoom 0–100 %, in steps while the button is held
        if direction == "stop":
            return
        self._zoom = max(0, min(100, self._zoom + (10 if direction == "tele" else -10)))
        self._get("/gopro/camera/digital_zoom?percent=%d" % self._zoom)

    # ---- live view: camera → UDP MPEG-TS → ffmpeg → JPEG frames ----
    def _start_stream(self):
        port = int(self.cfg["stream_port"])
        self._get("/gopro/camera/stream/start?port=%d" % port)
        self._proc = subprocess.Popen(
            [self._ffmpeg, "-hide_banner", "-loglevel", "error", "-fflags", "nobuffer", "-flags", "low_delay",
             "-probesize", "500000", "-analyzeduration", "500000",
             "-i", "udp://0.0.0.0:%d?fifo_size=5000000&overrun_nonfatal=1&timeout=4000000" % port, "-an",
             "-vf", "fps=15,scale=960:-2", "-q:v", "5", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self._buf = b""

    def frame(self):
        if not self._ffmpeg:
            return None
        try:
            if self._proc is None or self._proc.poll() is not None:
                self._start_stream()
            while True:
                chunk = self._proc.stdout.read1(65536) if hasattr(self._proc.stdout, "read1") else self._proc.stdout.read(65536)
                if not chunk:
                    self._stop_proc()
                    return None
                frames, self._buf = split_jpegs(self._buf + chunk)
                if frames:
                    return frames[-1]
        except (AdapterError, OSError):
            self._stop_proc()
            time.sleep(1)
            return None

    def _stop_proc(self):
        p, self._proc = self._proc, None
        if p and p.poll() is None:
            p.kill()

    def close(self):
        if self._proc is not None:
            try:
                self._get("/gopro/camera/stream/stop")
            except AdapterError:
                pass
            self._stop_proc()
