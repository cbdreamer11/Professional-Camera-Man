"""Sony — Camera Remote API (JSON-RPC over HTTP), the older Wi-Fi API.

Written from Sony's public Camera Remote API beta documentation. NOT tested on real hardware by the author.
IMPORTANT: this is the LEGACY API (Alpha 5000/5100/6000, QX series, RX100 and others that run the "Smart Remote Control"
app). Newer bodies (a7 IV, a7S III, FX3/FX30, ZV-E1, a1…) expose Sony's *Camera Remote SDK*, a native library, not this HTTP
API — for those use the video-input monitor, or contribute an adapter around the SDK.
"""
import threading

from .base import Adapter, AdapterError, Unsupported, blank_state, http


class SonyRemote(Adapter):
    id = "sony_remote"
    name = "Sony (Camera Remote API, legacy Wi-Fi)"
    tested = False
    status_note = "Written from Sony's public docs. Untested. Legacy models only; new Alphas need Sony's SDK."
    docs_url = "https://developer.sony.com/develop/cameras/"
    capabilities = ("record", "liveview", "iso", "shutter", "wb", "zoom")
    fields = [
        {"key": "host", "label": "Camera address", "default": "192.168.122.1", "help": "Usually 192.168.122.1 on the camera's own Wi-Fi."},
        {"key": "port", "label": "Port", "default": 8080, "help": "8080."},
    ]

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._rec_mode = False
        self._live_url = None
        self._id = 0
        self._lock = threading.Lock()

    def _rpc(self, method, params=None, version="1.0", service="camera"):
        with self._lock:
            self._id += 1
            req = {"method": method, "params": params or [], "id": self._id, "version": version}
        j = http("POST", "http://%s:%s/sony/%s" % (self.cfg["host"], self.cfg["port"], service), req)
        if "error" in j:
            raise AdapterError("Sony error %s" % (j["error"],))
        return j.get("result", [])

    def _ensure_rec_mode(self):
        if not self._rec_mode:
            apis = self._rpc("getAvailableApiList")
            if apis and "startRecMode" in apis[0]:
                self._rpc("startRecMode")
            self._rec_mode = True

    def poll(self):
        st = blank_state()
        try:
            self._ensure_rec_mode()
            ev = self._rpc("getEvent", [False], version="1.0")
        except AdapterError:
            self._rec_mode = False
            return st
        st["connected"] = True
        st["model"] = "Sony (Remote API)"
        for item in ev:
            if not isinstance(item, dict):
                continue
            t = item.get("type")
            if t == "cameraStatus":
                st["recording"] = item.get("cameraStatus") in ("MovieRecording", "MovieWaitRecStart")
            elif t == "isoSpeedRate":
                st["settings"]["iso"] = {"value": item.get("currentIsoSpeedRate"), "options": item.get("isoSpeedRateCandidates", [])}
            elif t == "shutterSpeed":
                st["settings"]["shutter"] = {"value": item.get("currentShutterSpeed"), "options": item.get("shutterSpeedCandidates", [])}
            elif t == "whiteBalance":
                st["settings"]["wb"] = {"value": item.get("currentWhiteBalanceMode"),
                                        "options": [c.get("whiteBalanceMode") for c in item.get("whiteBalanceCandidates", []) if isinstance(c, dict)]}
        return st

    def record(self, start):
        self._ensure_rec_mode()
        self._rpc("startMovieRec" if start else "stopMovieRec")

    def set(self, key, value):
        if key == "iso":
            self._rpc("setIsoSpeedRate", [str(value)])
        elif key == "shutter":
            self._rpc("setShutterSpeed", [str(value)])
        elif key == "wb":
            self._rpc("setWhiteBalance", [str(value), False, -1])
        else:
            raise Unsupported(key)

    def zoom(self, direction):
        if direction == "stop":
            self._rpc("actZoom", ["in", "stop"])
        else:
            self._rpc("actZoom", ["in" if direction == "tele" else "out", "start"])

    # Live view: Sony returns a URL; the stream is packets = 8-byte common header + 128-byte payload header + JPEG.
    def frame(self):
        import urllib.request
        try:
            self._ensure_rec_mode()
            if not self._live_url:
                self._live_url = self._rpc("startLiveview")[0]
            if not hasattr(self, "_stream") or self._stream is None:
                self._stream = urllib.request.urlopen(self._live_url, timeout=6)
            r = self._stream
            common = r.read(8)
            if len(common) < 8 or common[0] != 0xFF:
                self._stream = None
                return None
            payload_type = common[1]
            head = r.read(128)
            size = int.from_bytes(head[4:7], "big")
            pad = head[7]
            data = r.read(size)
            r.read(pad)
            return data if payload_type == 0x01 else None
        except (AdapterError, OSError):
            self._stream, self._live_url = None, None
            return None

    def close(self):
        s = getattr(self, "_stream", None)
        if s:
            s.close()
