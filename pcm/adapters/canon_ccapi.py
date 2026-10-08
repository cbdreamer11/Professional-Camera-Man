"""Canon — Camera Control API (CCAPI), over Wi-Fi.

VERIFIED on a Canon EOS R50 V (firmware 1.2.0). Other CCAPI cameras (R5 C, R6 II, R7, R10, R100, R50, R8, R5, 1D X III…)
speak the same API, but only the R50 V was tested by the author.
How to enable it and every trap found: docs/CANON_CCAPI.md
"""
import http.client
import json
import ssl
import threading
import time

from .base import Adapter, AdapterError, blank_state

_CTX = ssl._create_unverified_context()   # the camera uses a self-signed certificate

# What to read when we connect. After that, /event/polling reports only what changed.
_BASE = ["/ccapi/ver100/shooting/settings", "/ccapi/ver110/devicestatus/storage",
         "/ccapi/ver110/devicestatus/batterylist", "/ccapi/ver100/devicestatus/lens",
         "/ccapi/ver100/devicestatus/temperature", "/ccapi/ver100/devicestatus/powerzoomstatus",
         "/ccapi/ver100/shooting/control/moviemode"]
_WRAP = {"/lens": "lens", "/temperature": "temperature", "/powerzoomstatus": "powerzoomstatus", "/moviemode": "moviemode"}
_RAW_KEY = {"iso": "iso", "aperture": "av", "shutter": "tv", "wb": "wb", "kelvin": "colortemperature"}


class CanonCCAPI(Adapter):
    id = "canon_ccapi"
    name = "Canon (CCAPI, Wi-Fi)"
    tested = True
    status_note = "Verified on a Canon EOS R50 V. Other CCAPI models should work but are untested."
    docs_url = "docs/CANON_CCAPI.md"
    capabilities = ("record", "liveview", "iso", "aperture", "shutter", "wb", "kelvin", "zoom", "focus",
                    "battery", "storage", "release")
    fields = [
        {"key": "host", "label": "Camera address", "default": "",
         "help": "The IP the camera shows in Menu → Network → Camera Control API (e.g. 192.168.1.40, or an IPv6 like fe80::1234%en0)."},
        {"key": "port", "label": "Port", "default": 443, "help": "443 unless you changed it."},
        {"key": "scheme", "label": "https or http", "default": "https", "help": "Leave as https."},
        {"key": "liveviewsize", "label": "Live view size", "default": "small",
         "help": "small ≈ 24 fps, medium sharper but ≈ 8 fps."},
    ]

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._lock = threading.RLock()       # the camera chokes on parallel connections: one at a time
        self._conn = None
        self._last_ok = 0.0
        self._est = {}                        # merged camera state (settings + events)
        self._model = None
        self._base_loaded = False
        self._live_on = False
        self._released = False

    # ---------- connection ----------
    def _do(self, method, path, body=None):
        with self._lock:
            for attempt in (1, 2):            # the camera sometimes drops the persistent connection: reopen once
                try:
                    if self._conn is None:
                        cls = http.client.HTTPSConnection if self.cfg["scheme"] == "https" else http.client.HTTPConnection
                        kw = {"context": _CTX} if self.cfg["scheme"] == "https" else {}
                        self._conn = cls(str(self.cfg["host"]), int(self.cfg["port"]), timeout=6, **kw)
                    payload = json.dumps(body) if body is not None else None
                    self._conn.request(method, path, payload, {"Content-Type": "application/json"} if payload else {})
                    r = self._conn.getresponse()
                    data = r.read()
                    self._last_ok = time.time()
                    return r.status, data
                except (OSError, http.client.HTTPException) as e:
                    if self._conn:
                        self._conn.close()
                    self._conn = None
                    if attempt == 2:
                        raise AdapterError("no connection with the camera (%s)" % e.__class__.__name__) from e

    def _json(self, method, path, body=None):
        s, d = self._do(method, path, body)
        try:
            j = json.loads(d) if d else {}
        except ValueError:
            j = {}
        if s >= 400:
            raise AdapterError(j.get("message") or "HTTP %d" % s)
        return j

    # ---------- state ----------
    def _apply(self, d):
        for k, v in d.items():
            if k == "batterylist":
                self._est["batterylist"] = v.get("batterylist", v) if isinstance(v, dict) else v
            elif k == "storage":
                self._est["storagelist"] = v.get("storagelist", []) if isinstance(v, dict) else v
            else:
                self._est[k] = v

    def _load_base(self):
        for path in _BASE:
            s, d = self._do("GET", path)
            if s != 200:
                return False
            j = json.loads(d)
            for suffix, wrap in _WRAP.items():
                if path.endswith(suffix):
                    j = {wrap: j}
            self._apply(j)
        if not self._model:
            s, d = self._do("GET", "/ccapi/ver100/deviceinformation")
            if s == 200:
                self._model = json.loads(d).get("productname")
        s, d = self._do("GET", "/ccapi/ver110/event/polling")   # first call returns everything
        if s == 200:
            self._apply(json.loads(d or b"{}"))
        self._est.setdefault("recbutton", {"status": "stop"})
        return True

    def poll(self):
        if self._released:
            st = blank_state(self._model)
            st["connected"] = time.time() - self._last_ok < 5
            st["extra"]["released"] = True
            return st
        try:
            if not self._base_loaded:
                self._base_loaded = self._load_base()
            else:
                s, d = self._do("GET", "/ccapi/ver110/event/polling")
                if s == 200:
                    self._apply(json.loads(d or b"{}"))
                else:
                    self._base_loaded = False
        except (AdapterError, ValueError):
            self._base_loaded = False
        return self._normalize()

    def _opts(self, raw):
        ab = (self._est.get(raw) or {}).get("ability")
        return ab if isinstance(ab, list) else None

    def _normalize(self):
        st = blank_state(self._model)
        st["connected"] = self._base_loaded and time.time() - self._last_ok < 5
        if not st["connected"]:
            return st
        e = self._est
        for norm, raw in _RAW_KEY.items():
            item = e.get(raw)
            if not isinstance(item, dict) or "value" not in item:
                continue
            ab = item.get("ability")
            entry = {"value": item["value"]}
            if isinstance(ab, list):
                entry["options"] = ab
            elif isinstance(ab, dict) and "min" in ab:
                entry.update({"min": ab["min"], "max": ab["max"], "step": ab.get("step", 1)})
            st["settings"][norm] = entry
        mapped = set(_RAW_KEY.values())
        for k, item in e.items():
            if k not in mapped and isinstance(item, dict) and "value" in item:
                ab = item.get("ability")
                st["advanced"][k] = {"value": item["value"], **({"options": ab} if isinstance(ab, list) else {})}
        st["recording"] = (e.get("recbutton") or {}).get("status") == "start"
        bat = (e.get("batterylist") or [{}])[0]
        try:
            st["battery"] = int(str(bat.get("level", "")).rstrip("%"))
        except ValueError:
            st["battery"] = None
        sd = (e.get("storagelist") or [None])[0]
        if sd:
            rem = (e.get("recordable") or {}).get("remainingtime")
            st["storage"] = {"free": sd.get("spacesize"), "total": sd.get("maxsize"), "remaining_s": rem}
        st["extra"] = {"lens": (e.get("lens") or {}).get("name"), "temperature": (e.get("temperature") or {}).get("status"),
                       "mic_external": bool(self._opts("soundrecording_mode_extmic")),
                       "zoom": (e.get("powerzoomstatus") or {}).get("location")}
        return st

    # ---------- live view ----------
    def _ensure_live(self):
        if not self._live_on:
            self._json("POST", "/ccapi/ver100/shooting/liveview",
                       {"liveviewsize": self.cfg["liveviewsize"], "cameradisplay": "on"})
            self._live_on = True

    def frame(self):
        if self._released:
            return None
        try:
            self._ensure_live()
            s, d = self._do("GET", "/ccapi/ver100/shooting/liveview/flip")
            if s != 200:
                self._live_on = False
                return None
            return d
        except AdapterError:
            self._live_on = False
            time.sleep(0.5)
            return None

    def release(self):
        """While live view runs over the API the camera kicks you out of its own menu. Releasing turns it off."""
        self._released = True
        self._live_on = False
        try:
            self._json("POST", "/ccapi/ver100/shooting/liveview", {"liveviewsize": "off", "cameradisplay": "on"})
        except AdapterError:
            pass

    def take(self):
        self._released = False
        self._live_on = False

    # ---------- commands ----------
    def record(self, start):
        # Do NOT send recbutton while the camera sits on its network screen: it answers "Device busy" and can lock until
        # power-cycled. The server turns live view on first, which takes the camera out of that screen.
        if start and not self._released:
            self._ensure_live()
        for i in range(7):
            try:
                self._json("POST", "/ccapi/ver100/shooting/control/recbutton", {"action": "start" if start else "stop"})
                self._est["recbutton"] = {"status": "start" if start else "stop"}
                return
            except AdapterError as e:
                if start or "busy" not in str(e).lower() or i == 6:   # stopping right after starting can say "busy"
                    raise
                time.sleep(0.8)

    def set(self, key, value):
        raw = _RAW_KEY.get(key, key)
        if key == "kelvin" and (self._est.get("wb") or {}).get("value") != "colortemp":
            self._json("PUT", "/ccapi/ver100/shooting/settings/wb", {"value": "colortemp"})
        if key == "kelvin":
            value = int(value)
        self._json("PUT", "/ccapi/ver100/shooting/settings/" + raw, {"value": value})
        if raw in self._est and isinstance(self._est[raw], dict):
            self._est[raw]["value"] = value

    def zoom(self, direction):
        # settings/powerzoom is the zoom SPEED, not the position. The position moves with control/powerzoom.
        self._json("POST", "/ccapi/ver100/shooting/control/powerzoom", {"value": direction})

    def focus(self, action):
        if action in ("near", "far"):
            self._json("POST", "/ccapi/ver100/shooting/control/drivefocus", {"value": action + "1"})
            return
        try:
            self._json("POST", "/ccapi/ver100/shooting/control/af", {"action": "start"})
        except AdapterError as e:
            if "already" not in str(e).lower():
                raise
            self._json("POST", "/ccapi/ver100/shooting/control/af", {"action": "stop"})
            self._json("POST", "/ccapi/ver100/shooting/control/af", {"action": "start"})
        threading.Timer(1.2, lambda: self._safe_af_stop()).start()

    def _safe_af_stop(self):
        try:
            self._json("POST", "/ccapi/ver100/shooting/control/af", {"action": "stop"})
        except AdapterError:
            pass

    def close(self):
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
