"""Open Spherical Camera (OSC) API — Ricoh Theta, Insta360 (OSC mode) and other cameras that implement it.

Written from the public OSC spec (https://developers.google.com/streetview/open-spherical-camera). NOT tested by the author.
Not only for 360 cameras: any camera exposing /osc/commands/execute works. Option names differ per camera: use the
"Advanced" dialog to see what yours reports.
"""
import json
import urllib.request

from .base import Adapter, AdapterError, Unsupported, blank_state, http, split_jpegs


class OSCHTTP(Adapter):
    id = "osc_http"
    name = "Open Spherical Camera (OSC)"
    tested = False
    status_note = "Written from the public OSC spec. Untested."
    docs_url = "https://developers.google.com/streetview/open-spherical-camera"
    capabilities = ("record", "liveview", "iso", "shutter", "wb", "battery")
    fields = [
        {"key": "host", "label": "Camera address", "default": "192.168.1.1", "help": "Often 192.168.1.1 on the camera's own Wi-Fi."},
        {"key": "port", "label": "Port", "default": 80, "help": "80."},
    ]
    _OPT = {"iso": "iso", "shutter": "shutterSpeed", "wb": "whiteBalance"}

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._stream, self._buf = None, b""

    def _u(self, path):
        return "http://%s:%s%s" % (self.cfg["host"], self.cfg["port"], path)

    def _cmd(self, name, params=None):
        j = http("POST", self._u("/osc/commands/execute"), {"name": name, "parameters": params or {}})
        if j.get("state") == "error":
            raise AdapterError((j.get("error") or {}).get("message", "OSC error"))
        return j

    def poll(self):
        st = blank_state()
        try:
            info = http("GET", self._u("/osc/info"))
            state = http("POST", self._u("/osc/state"), {}).get("state", {})
        except AdapterError:
            return st
        st["connected"], st["model"] = True, info.get("model")
        lvl = state.get("batteryLevel")
        st["battery"] = round(lvl * 100) if isinstance(lvl, (int, float)) else None
        st["recording"] = state.get("_captureStatus") == "shooting" or state.get("captureStatus") == "shooting"
        try:
            opts = self._cmd("camera.getOptions", {"optionNames": list(self._OPT.values()) +
                                                   [o + "Support" for o in self._OPT.values()]})
            res = opts.get("results", {}).get("options", {})
            for norm, name in self._OPT.items():
                if name in res:
                    entry = {"value": res[name]}
                    sup = res.get(name + "Support")
                    if isinstance(sup, list):
                        entry["options"] = sup
                    st["settings"][norm] = entry
        except AdapterError:
            pass
        return st

    def record(self, start):
        self._cmd("camera.startCapture" if start else "camera.stopCapture")

    def set(self, key, value):
        if key not in self._OPT:
            raise Unsupported(key)
        self._cmd("camera.setOptions", {"options": {self._OPT[key]: value}})

    def frame(self):
        try:
            if self._stream is None:
                req = urllib.request.Request(self._u("/osc/commands/execute"), method="POST",
                                             data=json.dumps({"name": "camera.getLivePreview"}).encode(),
                                             headers={"Content-Type": "application/json"})
                self._stream, self._buf = urllib.request.urlopen(req, timeout=6), b""
            while True:
                chunk = self._stream.read(4096)
                if not chunk:
                    self._stream = None
                    return None
                frames, self._buf = split_jpegs(self._buf + chunk)
                if frames:
                    return frames[-1]
        except OSError:
            self._stream = None
            return None
