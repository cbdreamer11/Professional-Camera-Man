"""Tiny fake cameras that speak (a subset of) each documented protocol, so the adapters can be tested without hardware."""
import http.server
import json
import threading

JPEG = b"\xff\xd8\xff\xe0FAKEJPEGDATA\xff\xd9"


class Mock:
    def __init__(self, fn):
        self.calls = []
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _go(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n) if n else b""
                try:
                    body = json.loads(raw) if raw else None
                except ValueError:
                    body = None
                outer.calls.append((self.command, self.path, body))
                status, out = fn(self.command, self.path, body)
                data = out if isinstance(out, bytes) else (json.dumps(out).encode() if out is not None else b"")
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PUT = do_DELETE = _go

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


def canon_mock():
    state = {"rec": False, "live": False}
    settings = {"iso": {"value": "1250", "ability": ["800", "1250", "1600"]},
                "av": {"value": "f4.5", "ability": ["f4", "f4.5", "f5.6"]},
                "tv": {"value": "1/60", "ability": ["1/50", "1/60"]},
                "wb": {"value": "auto", "ability": ["auto", "colortemp"]},
                "colortemperature": {"value": 5600, "ability": {"min": 2500, "max": 10000, "step": 100}},
                "soundrecording_mode_extmic": {"value": "auto", "ability": ["auto", "manual"]}}

    def fn(method, path, body):
        if path == "/ccapi/ver100/shooting/settings":
            return 200, settings
        if path.startswith("/ccapi/ver100/shooting/settings/") and method == "PUT":
            k = path.rsplit("/", 1)[1]
            settings[k]["value"] = body["value"]
            return 200, {}
        if path == "/ccapi/ver110/devicestatus/storage":
            return 200, {"storagelist": [{"path": "/ccapi/ver140/contents/card1", "spacesize": 1000, "maxsize": 2000}]}
        if path == "/ccapi/ver110/devicestatus/batterylist":
            return 200, {"batterylist": [{"level": "80"}]}
        if path == "/ccapi/ver100/devicestatus/lens":
            return 200, {"name": "RF-S14-30mm"}
        if path == "/ccapi/ver100/devicestatus/temperature":
            return 200, {"status": "normal"}
        if path == "/ccapi/ver100/devicestatus/powerzoomstatus":
            return 200, {"location": "wide"}
        if path == "/ccapi/ver100/shooting/control/moviemode":
            return 200, {"status": "on"}
        if path == "/ccapi/ver100/deviceinformation":
            return 200, {"productname": "Mock R50 V"}
        if path == "/ccapi/ver110/event/polling":
            return 200, {"recbutton": {"status": "start" if state["rec"] else "stop"}, "recordable": {"remainingtime": 3600}}
        if path == "/ccapi/ver100/shooting/liveview" and method == "POST":
            state["live"] = body["liveviewsize"] != "off"
            return 200, {}
        if path == "/ccapi/ver100/shooting/liveview/flip":
            return (200, JPEG) if state["live"] else (503, {"message": "Mode not supported"})
        if path == "/ccapi/ver100/shooting/control/recbutton":
            if not state["live"]:
                return 503, {"message": "Device busy"}
            state["rec"] = body["action"] == "start"
            return 200, {}
        if path.startswith("/ccapi/ver100/shooting/control/"):
            return 200, {}
        return 404, {"message": "nope " + path}

    m = Mock(fn)
    m.state, m.settings = state, settings
    return m


def blackmagic_mock():
    st = {"recording": False, "iso": 400, "wb": 5600}

    def fn(method, path, body):
        p = path.replace("/control/api/v1", "")
        if p == "/system/product":
            return 200, {"productName": "Blackmagic Mock 6K", "deviceName": "Cam A"}
        if p == "/transports/0/record":
            if method == "GET":
                return 200, {"recording": st["recording"]}
            st["recording"] = True if method == "POST" else bool(body["recording"])
            return 204, None
        if p == "/video/iso":
            if method == "PUT":
                st["iso"] = body["iso"]
                return 204, None
            return 200, {"iso": st["iso"]}
        if p == "/video/supportedISOs":
            return 200, {"supportedISOs": [200, 400, 800]}
        if p == "/video/whiteBalance":
            if method == "PUT":
                st["wb"] = body["whiteBalance"]
                return 204, None
            return 200, {"whiteBalance": st["wb"]}
        if p == "/video/whiteBalance/description":
            return 200, {"whiteBalance": {"min": 2500, "max": 10000}}
        if p == "/video/shutter":
            return 200, {"shutterSpeed": 50}
        if p == "/lens/iris":
            return 200, {"apertureStop": 2.8}
        return 404, {}

    m = Mock(fn)
    m.state = st
    return m


def gopro_mock():
    st = {"rec": False, "res": 1, "fps": 8, "zoom": None, "keep": 0, "setcalls": []}

    def fn(method, path, body):
        p = path.split("?")[0]
        if p == "/gopro/camera/state":
            return 200, {"status": {"6": 0, "10": 1 if st["rec"] else 0, "35": 5400, "54": 100000, "70": 77},
                         "settings": {"2": st["res"], "3": st["fps"]}}
        if p == "/gopro/camera/info":
            return 200, {"info": {"model_name": "HERO12 Mock"}}
        if p == "/gopro/camera/keep_alive":
            st["keep"] += 1
            return 200, {}
        if p == "/gopro/camera/shutter/start":
            st["rec"] = True
            return 200, {}
        if p == "/gopro/camera/shutter/stop":
            st["rec"] = False
            return 200, {}
        if p == "/gopro/camera/setting":
            q = dict(x.split("=") for x in path.split("?")[1].split("&"))
            st["setcalls"].append(q)
            st["res" if q["setting"] == "2" else "fps"] = int(q["option"])
            return 200, {}
        if p in ("/gopro/camera/stream/start", "/gopro/camera/stream/stop"):
            st["stream"] = p.rsplit("/", 1)[1] + "?" + (path.split("?")[1] if "?" in path else "")
            return 200, {}
        if p == "/gopro/camera/digital_zoom":
            st["zoom"] = path.split("percent=")[1]
            return 200, {}
        return 404, {}

    m = Mock(fn)
    m.state = st
    return m


def sony_mock():
    st = {"rec": False, "iso": "400"}

    def fn(method, path, body):
        m_ = (body or {}).get("method")
        if m_ == "getAvailableApiList":
            return 200, {"result": [["startRecMode", "getEvent"]], "id": 1}
        if m_ == "startRecMode":
            return 200, {"result": [0]}
        if m_ == "getEvent":
            return 200, {"result": [{"type": "cameraStatus", "cameraStatus": "MovieRecording" if st["rec"] else "IDLE"},
                                    {"type": "isoSpeedRate", "currentIsoSpeedRate": st["iso"], "isoSpeedRateCandidates": ["100", "400"]}]}
        if m_ == "startMovieRec":
            st["rec"] = True
            return 200, {"result": [0]}
        if m_ == "stopMovieRec":
            st["rec"] = False
            return 200, {"result": ["thumb.jpg"]}
        if m_ == "setIsoSpeedRate":
            st["iso"] = body["params"][0]
            return 200, {"result": [0]}
        return 200, {"error": [12, "No Such Method"], "id": 1}

    m = Mock(fn)
    m.state = st
    return m


def osc_mock():
    st = {"cap": "idle"}

    def fn(method, path, body):
        if path == "/osc/info":
            return 200, {"model": "OSC Mock"}
        if path == "/osc/state":
            return 200, {"state": {"batteryLevel": 0.5, "captureStatus": st["cap"]}}
        if path == "/osc/commands/execute":
            n = body["name"]
            if n == "camera.startCapture":
                st["cap"] = "shooting"
            elif n == "camera.stopCapture":
                st["cap"] = "idle"
            elif n == "camera.getOptions":
                return 200, {"state": "done", "results": {"options": {"iso": 200, "isoSupport": [100, 200, 400]}}}
            return 200, {"state": "done"}
        return 404, {}

    m = Mock(fn)
    m.state = st
    return m
