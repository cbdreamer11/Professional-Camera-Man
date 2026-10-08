"""Bring your own API — describe any HTTP camera in a JSON file, no Python needed.

In the setup wizard choose "Custom (describe it in JSON)" and point it to a file, or put the same JSON under
`camera.cfg.spec` in data/profile.json. Example (also in profiles/custom_api_example.json):

{
  "base_url": "http://192.168.1.60:8000",
  "headers": {"Authorization": "Bearer YOUR_TOKEN"},
  "model": "My camera",
  "actions": {
    "record_start": {"method": "POST", "path": "/rec", "json": {"on": true}},
    "record_stop":  {"method": "POST", "path": "/rec", "json": {"on": false}},
    "zoom_tele":    {"method": "POST", "path": "/zoom/in"},
    "zoom_wide":    {"method": "POST", "path": "/zoom/out"},
    "zoom_stop":    {"method": "POST", "path": "/zoom/stop"},
    "focus_af":     {"method": "POST", "path": "/af"}
  },
  "set": {
    "iso":     {"method": "PUT", "path": "/settings/iso",    "json": {"value": "{value}"}},
    "kelvin":  {"method": "PUT", "path": "/settings/wb",     "json": {"kelvin": "{value}"}}
  },
  "status": {"method": "GET", "path": "/status",
             "map": {"connected": "ok", "recording": "rec.active", "battery": "battery.percent", "model": "device.name"}},
  "liveview": {"path": "/preview.jpg"}
}

`{value}` is replaced by what the app sends. `map` values are dotted paths into the status JSON.
"""
import json
import os

from .base import Adapter, AdapterError, Unsupported, blank_state, http


def _dig(obj, dotted):
    for part in str(dotted).split("."):
        if isinstance(obj, list):
            try:
                obj = obj[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def _fill(obj, value):
    if isinstance(obj, str):
        return obj.replace("{value}", str(value)) if obj != "{value}" else value
    if isinstance(obj, dict):
        return {k: _fill(v, value) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fill(v, value) for v in obj]
    return obj


class CustomJSON(Adapter):
    id = "custom_json"
    name = "Custom (describe it in JSON)"
    tested = False
    status_note = "Generic. Works as far as your description is right."
    docs_url = "docs/ADAPTERS.md"
    capabilities = ("record", "liveview", "iso", "aperture", "shutter", "wb", "kelvin", "zoom", "focus", "battery")
    fields = [
        {"key": "spec_file", "label": "Path to your JSON description", "default": "",
         "help": "See profiles/custom_api_example.json. Relative paths start from the project folder."},
    ]

    def __init__(self, cfg=None):
        super().__init__(cfg)
        spec = self.cfg.get("spec")
        if not spec and self.cfg.get("spec_file"):
            path = os.path.expanduser(self.cfg["spec_file"])
            try:
                with open(path, encoding="utf-8") as f:
                    spec = json.load(f)
            except (OSError, ValueError) as e:
                raise AdapterError("cannot read %s: %s" % (path, e)) from e
        self.spec = spec or {}
        self.capabilities = tuple(self._caps())

    def _caps(self):
        s, caps = self.spec, []
        if "record_start" in s.get("actions", {}):
            caps.append("record")
        if s.get("liveview"):
            caps.append("liveview")
        if "zoom_tele" in s.get("actions", {}):
            caps.append("zoom")
        if "focus_af" in s.get("actions", {}):
            caps.append("focus")
        caps += [k for k in s.get("set", {}) if k in ("iso", "aperture", "shutter", "wb", "kelvin")]
        if "battery" in s.get("status", {}).get("map", {}):
            caps.append("battery")
        return caps

    def _call(self, action, value=None):
        a = _fill(action, value) if value is not None else action
        url = self.spec.get("base_url", "").rstrip("/") + a["path"]
        return http(a.get("method", "GET"), url, a.get("json"), self.spec.get("headers"), insecure=True)

    def poll(self):
        st = blank_state(self.spec.get("model"))
        status = self.spec.get("status")
        try:
            j = self._call(status) if status else {}
        except AdapterError:
            return st
        m = (status or {}).get("map", {})
        st["connected"] = bool(_dig(j, m["connected"])) if "connected" in m else True
        for k in ("recording", "battery", "model"):
            if k in m:
                v = _dig(j, m[k])
                st[k] = bool(v) if k == "recording" else v if v is not None else st[k]
        for key, path in (status or {}).get("settings", {}).items():
            st["settings"][key] = {"value": _dig(j, path)}
        return st

    def record(self, start):
        self._call(self.spec["actions"]["record_start" if start else "record_stop"])

    def set(self, key, value):
        if key not in self.spec.get("set", {}):
            raise Unsupported(key)
        self._call(self.spec["set"][key], value)

    def zoom(self, direction):
        self._call(self.spec["actions"]["zoom_" + direction])

    def focus(self, action):
        self._call(self.spec["actions"]["focus_" + action])

    def frame(self):
        lv = self.spec.get("liveview")
        if not lv:
            return None
        try:
            return http(lv.get("method", "GET"), self.spec["base_url"].rstrip("/") + lv["path"], None,
                        self.spec.get("headers"), insecure=True, raw=True)
        except AdapterError:
            return None
