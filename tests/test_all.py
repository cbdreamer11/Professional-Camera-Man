import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
os.environ["PCM_DATA"] = tempfile.mkdtemp(prefix="pcm-test-")

import mocks  # noqa: E402
from pcm import profile, recommend  # noqa: E402
from pcm.adapters import discover  # noqa: E402
from pcm.adapters.base import AdapterError, split_jpegs  # noqa: E402

A = discover()


def wait(fn, t=5):
    end = time.time() + t
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(0.05)
    return fn()


class TestCanon(unittest.TestCase):
    def setUp(self):
        self.m = mocks.canon_mock()
        self.c = A["canon_ccapi"]({"host": "127.0.0.1", "port": self.m.port, "scheme": "http"})

    def tearDown(self):
        self.c.close()
        self.m.close()

    def test_state_is_normalized(self):
        st = self.c.poll()
        self.assertTrue(st["connected"])
        self.assertEqual(st["model"], "Mock R50 V")
        self.assertEqual(st["settings"]["iso"]["value"], "1250")
        self.assertEqual(st["settings"]["iso"]["options"], ["800", "1250", "1600"])
        self.assertEqual(st["settings"]["aperture"]["value"], "f4.5")
        self.assertEqual(st["settings"]["kelvin"]["max"], 10000)
        self.assertEqual(st["battery"], 80)
        self.assertEqual(st["storage"]["free"], 1000)
        self.assertTrue(st["extra"]["mic_external"])
        self.assertFalse(st["recording"])

    def test_record_turns_live_view_on_first(self):
        self.c.poll()
        self.c.record(True)
        paths = [p for _, p, _ in self.m.calls]
        self.assertLess(paths.index("/ccapi/ver100/shooting/liveview"), paths.index("/ccapi/ver100/shooting/control/recbutton"))
        self.assertTrue(self.c.poll()["recording"])
        self.c.record(False)
        self.assertFalse(self.c.poll()["recording"])

    def test_kelvin_switches_wb_to_colortemp_first(self):
        self.c.poll()
        self.c.set("kelvin", 6000)
        puts = [(p.rsplit("/", 1)[1], b["value"]) for m, p, b in self.m.calls if m == "PUT"]
        self.assertEqual(puts, [("wb", "colortemp"), ("colortemperature", 6000)])

    def test_set_and_frame_and_zoom(self):
        self.c.poll()
        self.c.set("iso", "1600")
        self.assertEqual(self.m.settings["iso"]["value"], "1600")
        self.assertEqual(self.c.frame(), mocks.JPEG)
        self.c.zoom("tele")
        self.assertIn(("POST", "/ccapi/ver100/shooting/control/powerzoom", {"value": "tele"}), self.m.calls)

    def test_release_stops_live_view(self):
        self.c.poll()
        self.c.frame()
        self.c.release()
        self.assertFalse(self.m.state["live"])
        self.assertIsNone(self.c.frame())

    def test_disconnected_when_nothing_listens(self):
        dead = A["canon_ccapi"]({"host": "127.0.0.1", "port": 9, "scheme": "http"})
        st = dead.poll()
        self.assertFalse(st["connected"])


class TestOthers(unittest.TestCase):
    def test_blackmagic(self):
        m = mocks.blackmagic_mock()
        try:
            b = A["blackmagic_rest"]({"host": "127.0.0.1:%d" % m.port, "scheme": "http"})
            st = b.poll()
            self.assertTrue(st["connected"])
            self.assertEqual(st["model"], "Blackmagic Mock 6K")
            self.assertEqual(st["settings"]["iso"]["options"], [200, 400, 800])
            self.assertEqual(st["settings"]["shutter"]["value"], "1/50")
            b.record(True)
            self.assertTrue(b.poll()["recording"])
            b.record(False)
            self.assertFalse(b.poll()["recording"])
            b.set("iso", "800")
            self.assertEqual(m.state["iso"], 800)
            b.set("kelvin", 4300)
            self.assertEqual(m.state["wb"], 4300)
        finally:
            m.close()

    def test_gopro(self):
        m = mocks.gopro_mock()
        try:
            g = A["gopro_http"]({"host": "127.0.0.1", "port": m.port})
            st = g.poll()
            self.assertEqual((st["connected"], st["battery"], st["model"], st["recording"]), (True, 77, "HERO12 Mock", False))
            self.assertEqual(st["storage"]["remaining_s"], 5400)
            self.assertEqual(st["advanced"]["resolution"]["value"], "4K")
            self.assertEqual(st["advanced"]["fps"]["value"], "30")
            self.assertEqual(m.state["keep"], 1)
            g.record(True)
            self.assertTrue(g.poll()["recording"])
            g.record(False)
            self.assertFalse(g.poll()["recording"])
            g.set("resolution", "1080p")
            g.set("fps", "60")
            self.assertEqual((m.state["res"], m.state["fps"]), (9, 5))
            with self.assertRaises(AdapterError):
                g.set("fps", "999")
            g.zoom("tele")
            g.zoom("tele")
            self.assertEqual(m.state["zoom"], "20")
            g.zoom("wide")
            self.assertEqual(m.state["zoom"], "10")
        finally:
            m.close()

    def test_sony(self):
        m = mocks.sony_mock()
        try:
            s = A["sony_remote"]({"host": "127.0.0.1", "port": m.port})
            st = s.poll()
            self.assertTrue(st["connected"])
            self.assertEqual(st["settings"]["iso"]["value"], "400")
            s.record(True)
            self.assertTrue(s.poll()["recording"])
            s.record(False)
            s.set("iso", "100")
            self.assertEqual(m.state["iso"], "100")
        finally:
            m.close()

    def test_sony_liveview_packet_parser(self):
        # 8-byte common header + 128-byte payload header + JPEG, as in Sony's documentation
        jpeg = mocks.JPEG
        payload = b"\x24\x35\x68\x79" + len(jpeg).to_bytes(3, "big") + b"\x00" + b"\x00" * 120
        packet = b"\xff\x01\x00\x01\x00\x00\x00\x00" + payload + jpeg

        def fn(method, path, body):
            return 200, packet

        m = mocks.Mock(fn)
        try:
            s = A["sony_remote"]({"host": "127.0.0.1", "port": m.port})
            s._rec_mode = True
            s._live_url = "http://127.0.0.1:%d/live" % m.port
            self.assertEqual(s.frame(), jpeg)
        finally:
            m.close()

    def test_osc(self):
        m = mocks.osc_mock()
        try:
            o = A["osc_http"]({"host": "127.0.0.1", "port": m.port})
            st = o.poll()
            self.assertEqual((st["connected"], st["model"], st["battery"]), (True, "OSC Mock", 50))
            self.assertEqual(st["settings"]["iso"]["options"], [100, 200, 400])
            o.record(True)
            self.assertTrue(o.poll()["recording"])
        finally:
            m.close()

    def test_custom_json(self):
        calls = []

        def fn(method, path, body):
            calls.append((method, path, body))
            if path == "/status":
                return 200, {"ok": True, "rec": {"active": True}, "battery": {"percent": 42}, "device": {"name": "Mine"}}
            return 200, {}

        m = mocks.Mock(fn)
        try:
            spec = {"base_url": "http://127.0.0.1:%d" % m.port,
                    "actions": {"record_start": {"method": "POST", "path": "/rec", "json": {"on": True}},
                                "record_stop": {"method": "POST", "path": "/rec", "json": {"on": False}}},
                    "set": {"iso": {"method": "PUT", "path": "/iso", "json": {"value": "{value}"}}},
                    "status": {"path": "/status", "map": {"connected": "ok", "recording": "rec.active",
                                                          "battery": "battery.percent", "model": "device.name"}}}
            c = A["custom_json"]({"spec": spec})
            self.assertIn("record", c.capabilities)
            self.assertIn("iso", c.capabilities)
            st = c.poll()
            self.assertEqual((st["connected"], st["recording"], st["battery"], st["model"]), (True, True, 42, "Mine"))
            c.record(True)
            c.set("iso", 800)
            self.assertIn(("POST", "/rec", {"on": True}), calls)
            self.assertIn(("PUT", "/iso", {"value": 800}), calls)
        finally:
            m.close()

    def test_video_input_is_always_connected(self):
        self.assertTrue(A["video_input"]().poll()["connected"])

    def test_split_jpegs(self):
        a, b = mocks.JPEG, b"\xff\xd8xx\xff\xd9"
        got, rest = split_jpegs(b"junk" + a + b"--b\r\n" + b + b"\xff\xd8partial")
        self.assertEqual(got, [a, b])
        self.assertEqual(rest, b"\xff\xd8partial")


class TestRecommend(unittest.TestCase):
    def test_shutter(self):
        self.assertEqual(recommend.shutter_for(24, 60), "1/60")
        self.assertEqual(recommend.shutter_for(24, 50), "1/50")
        self.assertEqual(recommend.shutter_for(25, 50), "1/50")
        self.assertEqual(recommend.shutter_for(29.97, 60), "1/60")
        self.assertEqual(recommend.shutter_for(30, 50), "1/50")
        self.assertEqual(recommend.shutter_for(59.94, 60), "1/120")

    def test_falloff_and_inverse_square(self):
        self.assertAlmostEqual(recommend.falloff_stops(100), 0.4, places=1)
        self.assertGreater(recommend.falloff_stops(50), recommend.falloff_stops(150))
        k = {"power_pct": 100, "distance_cm": 100}
        f = {"power_pct": 100, "distance_cm": 200}
        self.assertAlmostEqual(recommend.intensity(k) / recommend.intensity(f), 4.0)

    def test_advice_for_a_bad_set(self):
        p = profile.normalize({"style": "corporate_clean", "fps": 24, "lights": [
            {"role": "key", "side": "left", "azimuth_deg": 10, "height_cm": 0, "distance_cm": 100, "power_pct": 100, "kelvin": 5600},
            {"role": "fill", "side": "right", "azimuth_deg": 40, "height_cm": 0, "distance_cm": 100, "power_pct": 100, "kelvin": 3200}],
            "camera": {"distance_cm": 60}, "subject": {"background_distance_cm": 40}})
        r = recommend.recommend(p)
        text = " ".join(r["warnings"])
        for needle in ("span 3200", "10° off", "above eye level", "60 cm away", "40 cm from the background"):
            self.assertIn(needle, text)
        self.assertEqual(r["camera"]["kelvin"], 5600)
        self.assertEqual(r["ratio_estimate"], 1.0)

    def test_spanish(self):
        p = profile.normalize({"lang": "es", "lights": []})
        self.assertIn("luz principal", " ".join(recommend.recommend(p)["warnings"]))

    def test_white_card(self):
        self.assertTrue(recommend.white_card_shift(200, 200, 200)["neutral"])
        bluish = recommend.white_card_shift(190, 200, 215)
        self.assertGreater(bluish["suggest_kelvin_delta"], 0)       # bluish card -> raise Kelvin
        self.assertLess(recommend.white_card_shift(220, 200, 190)["suggest_kelvin_delta"], 0)

    def test_profile_normalize_clamps_garbage(self):
        p = profile.normalize({"fps": "abc", "mains_hz": 99, "lights": [{"role": "banana", "distance_cm": -5}, "x"], "camera": "no"})
        self.assertEqual(p["fps"], 29.97)
        self.assertEqual(p["mains_hz"], 60)
        self.assertEqual(p["lights"][0]["role"], "other")
        self.assertEqual(p["lights"][0]["distance_cm"], 10)
        self.assertEqual(len(p["lights"]), 1)


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pcm import server
        cls.server = server
        cls.cam = mocks.canon_mock()
        import http.server
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.cam.close()

    def call(self, method, path, body=None, headers=None):
        h = {"Content-Type": "application/json", **(headers or {})}
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), method=method, headers=h,
                                     data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read() or b"{}"), r.headers
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}"), e.headers

    def test_end_to_end(self):
        s, meta, hdr = self.call("GET", "/api/meta")
        self.assertEqual(s, 200)
        self.assertEqual(hdr["X-Created-By"], "Created by Caleb Elizondo")
        self.assertIn("canon_ccapi", [a["id"] for a in meta["adapters"]])
        self.assertEqual(self.call("GET", "/api/profile")[1], {})

        s, r, _ = self.call("POST", "/api/connect-test", {"adapter": "canon_ccapi",
                                                          "cfg": {"host": "127.0.0.1", "port": self.cam.port, "scheme": "http"}})
        self.assertTrue(r["connected"])
        self.assertEqual(r["model"], "Mock R50 V")

        prof = {"lang": "en", "style": "corporate_clean", "camera": {"adapter": "canon_ccapi",
                "cfg": {"host": "127.0.0.1", "port": self.cam.port, "scheme": "http"}}}
        self.assertEqual(self.call("POST", "/api/profile", prof)[0], 200)
        st = wait(lambda: (lambda x: x if x["connected"] else None)(self.call("GET", "/api/state")[1]))
        self.assertTrue(st["connected"])
        self.assertIn("record", st["capabilities"])

        self.assertEqual(self.call("POST", "/api/rec", {"action": "start"})[0], 200)
        self.assertTrue(self.cam.state["rec"])
        self.assertEqual(self.call("POST", "/api/rec", {"action": "stop"})[0], 200)
        s, r, _ = self.call("POST", "/api/apply", {"settings": {"iso": "1600", "kelvin": 5900, "shutter": "1/50"}})
        self.assertEqual((s, r["failed"]), (200, []))
        self.assertEqual(self.cam.settings["iso"]["value"], "1600")
        self.assertEqual(self.cam.settings["colortemperature"]["value"], 5900)

        self.assertEqual(self.call("POST", "/api/scenes", {"name": "Mine", "settings": {"iso": "800"}})[1]["Mine"], {"iso": "800"})
        self.assertEqual(self.call("DELETE", "/api/scenes/Mine")[1], {})
        self.assertIn("warnings", self.call("GET", "/api/recommend")[1])

    def test_blocked_from_other_sites(self):
        s, r, _ = self.call("POST", "/api/rec", {"action": "start"}, {"Origin": "http://evil.example"})
        self.assertEqual(s, 403)
        s, r, _ = self.call("POST", "/api/rec", {"action": "start"}, {"Host": "evil.example"})
        self.assertEqual(s, 403)
        req = urllib.request.Request("http://127.0.0.1:%d/api/rec" % self.port, method="POST", data=b"{}", headers={"Content-Type": "text/plain"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 403)

    def test_no_camera_errors_are_clean(self):
        self.server.studio.adapter = None
        s, r, _ = self.call("POST", "/api/rec", {"action": "start"})
        self.assertEqual(s, 502)
        self.assertIn("error", r)


if __name__ == "__main__":
    unittest.main()
