"""Blackmagic Design — Camera REST API (Pocket Cinema Camera 4K/6K/6K Pro/6K G2, URSA Broadcast G2, URSA Mini…).

Written from Blackmagic's official "Developer Information — REST API for Blackmagic Cameras" (base path /control/api/v1).
NOT tested on a real camera by the author. Needs the camera on the same network (Ethernet/USB-C network) with its
web media manager reachable, e.g. http://my-camera.local. The REST API has no live-view stream: use the video-input monitor.
"""
from .base import Adapter, AdapterError, Unsupported, blank_state, http


class BlackmagicREST(Adapter):
    id = "blackmagic_rest"
    name = "Blackmagic (REST API)"
    tested = False
    status_note = "Written from the official Blackmagic REST doc. Untested on real hardware."
    docs_url = "https://documents.blackmagicdesign.com/DeveloperManuals/RESTAPIforBlackmagicCameras.pdf"
    capabilities = ("record", "iso", "aperture", "shutter", "wb", "kelvin", "zoom", "focus")
    fields = [
        {"key": "host", "label": "Camera address", "default": "", "help": "IP or name, e.g. 192.168.1.50 or ursa.local"},
        {"key": "scheme", "label": "http or https", "default": "http", "help": "Try http first."},
    ]

    def _u(self, path):
        return "%s://%s/control/api/v1%s" % (self.cfg["scheme"], self.cfg["host"], path)

    def _get(self, path):
        return http("GET", self._u(path), insecure=True)

    def _put(self, path, body):
        return http("PUT", self._u(path), body, insecure=True)

    def poll(self):
        st = blank_state()
        try:
            prod = self._get("/system/product")
            st["model"] = prod.get("productName") or prod.get("deviceName")
            st["connected"] = True
            st["recording"] = bool(self._get("/transports/0/record").get("recording"))
        except AdapterError:
            return st
        probes = (("iso", "/video/iso", lambda j: j.get("iso"), "/video/supportedISOs", "supportedISOs"),
                  ("kelvin", "/video/whiteBalance", lambda j: j.get("whiteBalance"), None, None))
        for key, path, pick, opath, okey in probes:
            try:
                entry = {"value": pick(self._get(path))}
                if opath:
                    entry["options"] = self._get(opath).get(okey, [])
                elif key == "kelvin":
                    r = self._get("/video/whiteBalance/description").get("whiteBalance", {})
                    entry.update({"min": r.get("min", 2500), "max": r.get("max", 10000), "step": 50})
                st["settings"][key] = entry
            except AdapterError:
                pass
        try:
            sh = self._get("/video/shutter")
            st["settings"]["shutter"] = {"value": ("1/%s" % sh["shutterSpeed"]) if sh.get("shutterSpeed") else sh.get("shutterAngle")}
        except AdapterError:
            pass
        try:
            ir = self._get("/lens/iris")
            st["settings"]["aperture"] = {"value": ir.get("apertureStop")}
        except AdapterError:
            pass
        return st

    def record(self, start):
        if start:
            http("POST", self._u("/transports/0/record"), {}, insecure=True)
        else:
            self._put("/transports/0/record", {"recording": False})   # PUT is deprecated but is the explicit "stop recording"

    def set(self, key, value):
        if key == "iso":
            self._put("/video/iso", {"iso": int(value)})
        elif key == "kelvin":
            self._put("/video/whiteBalance", {"whiteBalance": int(value)})
        elif key == "shutter":
            v = str(value)
            self._put("/video/shutter", {"shutterSpeed": int(v.split("/")[1])} if "/" in v else {"shutterAngle": float(v)})
        elif key == "aperture":
            self._put("/lens/iris", {"apertureStop": float(value)})
        else:
            raise Unsupported(key)

    def zoom(self, direction):
        if direction == "stop":
            return
        self._put("/lens/zoom", {"adjustmentNormalised": 0.05 if direction == "tele" else -0.05})

    def focus(self, action):
        if action == "af":
            self._put("/lens/focus/doAutoFocus", {"x": 0.5, "y": 0.5})
        else:
            raise Unsupported("manual focus nudge")
