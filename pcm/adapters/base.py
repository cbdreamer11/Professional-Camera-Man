"""Base class every camera adapter extends.

An adapter is the ONLY place that knows how one camera brand talks. The server and the web app speak a small,
normalized language, and the adapter translates it. To add a camera, copy `custom_json.py` or `canon_ccapi.py`,
change what it sends, and drop it in this folder (or in `data/adapters/`): it is discovered automatically.

Normalized state returned by `poll()`:

    {
      "connected": bool,
      "model": str | None,
      "recording": bool | None,
      "battery": int | None,                 # percent
      "storage": {"free": bytes, "total": bytes, "remaining_s": seconds | None} | None,
      "settings": {                          # any subset of: iso, aperture, shutter, wb, kelvin
          "iso":      {"value": "1250", "options": ["100", "125", ...]},
          "kelvin":   {"value": 5600, "min": 2500, "max": 10000, "step": 100},
      },
      "advanced": {"some_brand_key": {"value": ..., "options": [...]}},   # shown in the Advanced dialog
      "extra": {"lens": "...", "temperature": "normal", "mic_external": True},
    }
"""
import json
import ssl
import urllib.error
import urllib.request


class AdapterError(Exception):
    """The camera answered with an error, or the operation is not supported by this adapter."""


class Unsupported(AdapterError):
    pass


STANDARD_KEYS = ("iso", "aperture", "shutter", "wb", "kelvin")


class Adapter:
    id = "base"
    name = "Base adapter"
    tested = False           # True ONLY when the author verified it on real hardware
    status_note = ""         # one honest line about how far it has been verified
    docs_url = ""
    capabilities = ()        # record, liveview, iso, aperture, shutter, wb, kelvin, zoom, focus, battery, storage, release
    fields = []              # [{key, label, default, help}] -> the setup wizard builds its form from this

    def __init__(self, cfg=None):
        self.cfg = {**self.defaults(), **{k: v for k, v in (cfg or {}).items() if v not in (None, "")}}

    @classmethod
    def defaults(cls):
        return {f["key"]: f.get("default", "") for f in cls.fields}

    @classmethod
    def describe(cls):
        return {"id": cls.id, "name": cls.name, "tested": cls.tested, "status_note": cls.status_note,
                "docs_url": cls.docs_url, "capabilities": list(cls.capabilities), "fields": cls.fields}

    # ---- what a subclass implements ----
    def poll(self):
        """Return the normalized state (see module docstring). Called about once per second. Must not raise."""
        raise Unsupported("poll")

    def frame(self):
        """Return one live-view JPEG as bytes, or None. Called in a loop while someone is watching."""
        return None

    def record(self, start):
        raise Unsupported("record")

    def set(self, key, value):
        raise Unsupported("set " + key)

    def zoom(self, direction):       # "tele" | "wide" | "stop"
        raise Unsupported("zoom")

    def focus(self, action):         # "af" | "near" | "far"
        raise Unsupported("focus")

    def release(self):               # let the camera's own menu work again (some cameras lock while live view is on)
        raise Unsupported("release")

    def take(self):
        raise Unsupported("take")

    def close(self):
        pass


def blank_state(model=None):
    return {"connected": False, "model": model, "recording": None, "battery": None, "storage": None,
            "settings": {}, "advanced": {}, "extra": {}}


_INSECURE = ssl._create_unverified_context()   # cameras ship self-signed certificates


def http(method, url, body=None, headers=None, timeout=6, insecure=False, raw=False):
    """Tiny HTTP helper for adapters. JSON in, JSON out (or raw bytes). Raises AdapterError."""
    data, h = None, dict(headers or {})
    if body is not None:
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_INSECURE if insecure else None) as r:
            payload = r.read()
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read() or b"{}").get("message", "")
        except ValueError:
            pass
        raise AdapterError("HTTP %d %s" % (e.code, detail)) from e
    except (urllib.error.URLError, OSError) as e:
        raise AdapterError("no connection: %s" % e) from e
    if raw:
        return payload
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except ValueError:
        return {"_text": payload.decode(errors="replace")}


def split_jpegs(buffer):
    """Pull complete JPEG images out of a byte buffer (multipart or raw). Returns (list_of_jpegs, leftover)."""
    out = []
    while True:
        a = buffer.find(b"\xff\xd8")
        if a < 0:
            return out, b""
        b = buffer.find(b"\xff\xd9", a + 2)
        if b < 0:
            return out, buffer[a:]
        out.append(buffer[a:b + 2])
        buffer = buffer[b + 2:]
