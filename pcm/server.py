"""The local studio server: one camera adapter, one MJPEG live view, a small JSON API, and the web app."""
import http.server
import json
import os
import re
import socket
import threading
import time
import urllib.parse

from . import CREDIT, CREDIT_URL, __version__, profile as prof, recommend
from .adapters import AdapterError, Unsupported, discover
from .adapters.base import blank_state

WEB = os.path.join(prof.ROOT, "web")
SETTING_ORDER = ("wb", "kelvin", "aperture", "shutter", "iso")     # what changes the limits of the others goes first


class Studio:
    """Owns the active adapter. A polling thread keeps `state` fresh; a frame thread feeds the live view while watched."""

    def __init__(self):
        self.classes = discover(os.path.join(prof.DATA, "adapters"))
        self.adapter, self.adapter_id = None, None
        self.state = blank_state()
        self.state["error"] = "no camera configured"
        self.cond = threading.Condition()
        self.frame, self.frame_n, self.fps = None, 0, 0.0
        self.last_viewer = 0.0
        self.released = False
        self._stop = threading.Event()
        threading.Thread(target=self._poll_loop, daemon=True).start()
        threading.Thread(target=self._frame_loop, daemon=True).start()

    def configure(self, p):
        cam = (p or {}).get("camera") or {}
        old, self.adapter = self.adapter, None
        if old:
            try:
                old.close()
            except Exception:
                pass
        cls = self.classes.get(cam.get("adapter"))
        self.released = False
        if not cls:
            self.adapter_id = None
            self.state = {**blank_state(), "error": "unknown adapter %r" % cam.get("adapter")}
            return
        try:
            self.adapter = cls(cam.get("cfg"))
            self.adapter_id = cls.id
            self.state = {**blank_state(), "error": "connecting…"}
        except AdapterError as e:
            self.adapter_id = None
            self.state = {**blank_state(), "error": str(e)}

    def _poll_loop(self):
        while not self._stop.is_set():
            a = self.adapter
            if a:
                try:
                    st = a.poll()
                    st.setdefault("error", None)
                except Exception as e:                       # an adapter must never kill the loop
                    st = {**blank_state(), "error": "%s: %s" % (e.__class__.__name__, e)}
                self.state = st
            time.sleep(1.0)

    def _frame_loop(self):
        t0, n = time.time(), 0
        while not self._stop.is_set():
            a = self.adapter
            if not a or "liveview" not in a.capabilities or self.released or time.time() - self.last_viewer > 5:
                self.fps = 0.0
                time.sleep(0.25)
                continue
            try:
                f = a.frame()
            except Exception:
                f = None
            if not f:
                time.sleep(0.5)
                continue
            with self.cond:
                self.frame, self.frame_n = f, self.frame_n + 1
                self.cond.notify_all()
            n += 1
            if time.time() - t0 >= 2:
                self.fps, t0, n = n / (time.time() - t0), time.time(), 0

    def public_state(self):
        a = self.adapter
        return {**self.state, "adapter": self.adapter_id, "capabilities": list(a.capabilities) if a else [],
                "adapter_tested": bool(a and a.tested), "fps": round(self.fps, 1), "released": self.released}


studio = Studio()
_p = prof.load()
if _p:
    studio.configure(_p)


def lan_addresses():
    out = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            out.add(info[4][0])
    except OSError:
        pass
    return out


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".webmanifest": "application/manifest+json", ".js": "text/javascript", ".mjs": "text/javascript"}
    allowed_hosts = set()

    def __init__(self, *a, **k):
        super().__init__(*a, directory=WEB, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("X-Created-By", CREDIT)
        super().end_headers()

    # ---- helpers ----
    def send_json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000:
            raise ValueError("body too large")
        try:
            return json.loads(self.rfile.read(n) or b"{}") if n else {}
        except ValueError:
            return {}

    def host_ok(self):
        h = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return h in ("localhost", "127.0.0.1", "::1") or h in self.allowed_hosts

    def write_ok(self):
        """State-changing calls only from a page served by this same server (blocks other sites and DNS rebinding)."""
        if not self.host_ok() or not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin.split("://", 1)[-1] == self.headers.get("Host")

    # ---- GET ----
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if not self.host_ok():
            return self.send_json(403, {"error": "host not allowed"})
        if path == "/live.mjpg":
            return self.live()
        if path == "/api/meta":
            return self.send_json(200, {"version": __version__, "credit": CREDIT, "credit_url": CREDIT_URL,
                                        "adapters": [c.describe() for c in studio.classes.values()],
                                        "styles": {k: {"key_az": v["key_az"], "ratio": v["ratio"], "kelvin": v["kelvin"]} for k, v in recommend.STYLES.items()}})
        if path == "/api/state":
            return self.send_json(200, studio.public_state())
        if path == "/api/profile":
            return self.send_json(200, prof.load() or {})
        if path == "/api/recommend":
            p = prof.load()
            return self.send_json(200, recommend.recommend(p) if p else {})
        if path == "/api/scenes":
            return self.send_json(200, prof.read_json(prof.SCENES, {}))
        if path == "/api/health":
            return self.send_json(200, {"ok": True})
        return super().do_GET()

    def live(self):
        if not studio.adapter or "liveview" not in studio.adapter.capabilities:
            return self.send_json(404, {"error": "this camera has no live view over its API; use the video input"})
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        seen = -1
        try:
            while True:
                studio.last_viewer = time.time()
                with studio.cond:
                    studio.cond.wait_for(lambda: studio.frame_n != seen, timeout=2)
                    f, seen = studio.frame, studio.frame_n
                if f is None:
                    continue
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(f))
                self.wfile.write(f + b"\r\n")
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    # ---- POST / DELETE ----
    def do_POST(self):
        if not self.write_ok():
            return self.send_json(403, {"error": "only from the studio page itself"})
        path = urllib.parse.urlparse(self.path).path
        try:
            d = self.body()
            return self.route_post(path, d)
        except Unsupported as e:
            return self.send_json(400, {"error": "not supported by this camera: %s" % e})
        except AdapterError as e:
            return self.send_json(502, {"error": str(e)})
        except (ValueError, KeyError, TypeError) as e:
            return self.send_json(400, {"error": "bad request: %s" % e})

    def need(self):
        if not studio.adapter:
            raise AdapterError("no camera configured: run the setup")
        return studio.adapter

    def route_post(self, path, d):
        if path == "/api/profile":
            p = prof.save(d)
            studio.configure(p)
            return self.send_json(200, p)
        if path == "/api/recommend":
            return self.send_json(200, recommend.recommend(prof.normalize(d)))
        if path == "/api/rec":
            self.need().record(d.get("action") == "start")
            return self.send_json(200, {"ok": True})
        if path == "/api/set":
            self.need().set(str(d["key"]), d["value"])
            return self.send_json(200, {"ok": True})
        if path == "/api/apply":
            failed = []
            order = [k for k in SETTING_ORDER if k in d["settings"]] + [k for k in d["settings"] if k not in SETTING_ORDER]
            for k in order:
                try:
                    self.need().set(k, d["settings"][k])
                except (AdapterError, Unsupported) as e:
                    failed.append({"key": k, "error": str(e)})
            return self.send_json(200, {"failed": failed})
        if path == "/api/zoom":
            self.need().zoom(d["dir"])
            return self.send_json(200, {"ok": True})
        if path == "/api/focus":
            self.need().focus(d["action"])
            return self.send_json(200, {"ok": True})
        if path == "/api/release":
            a = self.need()
            if d.get("release"):
                a.release()
                studio.released = True
            else:
                a.take()
                studio.released = False
            return self.send_json(200, {"released": studio.released})
        if path == "/api/connect-test":
            cls = studio.classes.get(d.get("adapter"))
            if not cls:
                raise ValueError("unknown adapter")
            probe = cls(d.get("cfg"))
            try:
                st = {}
                for _ in range(3):                      # some adapters need a first call to load their base state
                    st = probe.poll()
                    if st.get("connected"):
                        break
                    time.sleep(0.6)
            finally:
                probe.close()
            return self.send_json(200, {"connected": bool(st.get("connected")), "model": st.get("model"),
                                        "settings": sorted(st.get("settings", {}))})
        if path == "/api/scenes":
            scenes = prof.read_json(prof.SCENES, {})
            name = str(d["name"]).strip()[:60]
            if not name:
                raise ValueError("name")
            scenes[name] = d["settings"]
            prof.write_json(prof.SCENES, scenes)
            return self.send_json(200, scenes)
        if path == "/api/white-card":
            return self.send_json(200, recommend.white_card_shift(float(d["r"]), float(d["g"]), float(d["b"])))
        return self.send_json(404, {"error": "unknown route"})

    def do_DELETE(self):
        if not self.write_ok() and not (self.host_ok() and self.headers.get("Origin") is None):
            return self.send_json(403, {"error": "only from the studio page itself"})
        m = re.fullmatch(r"/api/scenes/(.+)", urllib.parse.urlparse(self.path).path)
        if m:
            scenes = prof.read_json(prof.SCENES, {})
            scenes.pop(urllib.parse.unquote(m.group(1)), None)
            prof.write_json(prof.SCENES, scenes)
            return self.send_json(200, scenes)
        self.send_json(404, {"error": "unknown route"})


def serve(host="127.0.0.1", port=8770):
    if host not in ("127.0.0.1", "localhost", "::1"):
        Handler.allowed_hosts = lan_addresses() | {host} | {n for n in os.environ.get("PCM_ALLOW_HOST", "").split(",") if n}
        print("⚠  Listening on the network (%s). Anyone on this network can control the camera. There is no password." % host)
    http.server.ThreadingHTTPServer.daemon_threads = True
    srv = http.server.ThreadingHTTPServer((host, port), Handler)
    print("Professional Camera Man %s — %s (%s)" % (__version__, CREDIT, CREDIT_URL))
    print("Open http://localhost:%d" % port + ("" if prof.load() else "   (first run: it opens the setup wizard)"))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
