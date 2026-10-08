#!/usr/bin/env python3
"""Try the whole app with NO camera: a fake Canon-style camera + the real server + a sample profile.

    python3 tests/demo.py        then open http://localhost:8771

Nothing here touches a real camera or your real data (it uses a temporary data folder).
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
os.environ["PCM_DATA"] = tempfile.mkdtemp(prefix="pcm-demo-")

import mocks  # noqa: E402
from pcm import profile  # noqa: E402

with open(os.path.join(ROOT, "tests", "demo_frame.jpg"), "rb") as f:
    mocks.JPEG = f.read()
cam = mocks.canon_mock()
profile.save({"lang": "en", "style": "corporate_clean", "fps": 29.97, "camera": {"adapter": "canon_ccapi", "distance_cm": 220,
              "cfg": {"host": "127.0.0.1", "port": cam.port, "scheme": "http"}}, "subject": {"background_distance_cm": 160},
              "lights": [{"name": "Softbox", "role": "key", "side": "left", "azimuth_deg": 38, "height_cm": 30, "distance_cm": 100, "power_pct": 80, "kelvin": 5600, "modifier": "softbox"},
                         {"name": "Panel", "role": "fill", "side": "right", "azimuth_deg": 35, "height_cm": 10, "distance_cm": 170, "power_pct": 40, "kelvin": 5600},
                         {"name": "Hair light", "role": "back", "side": "right", "azimuth_deg": 150, "height_cm": 90, "distance_cm": 150, "power_pct": 50, "kelvin": 5600}]})
from pcm.server import serve  # noqa: E402

print("DEMO MODE — fake camera on port %d, temp data in %s" % (cam.port, os.environ["PCM_DATA"]))
serve("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8771)
