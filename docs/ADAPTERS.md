# Adding your camera's API

Everything brand-specific lives in an **adapter**. The server and the web app only speak a small normalized language; the adapter translates it into what your camera understands.

## Option A — no code: the Custom adapter

1. Copy [`profiles/custom_api_example.json`](../profiles/custom_api_example.json) to anywhere (e.g. `data/my_camera.json`).
2. Fill in your camera's address and endpoints:
   * `actions` — `record_start`, `record_stop`, `zoom_tele`, `zoom_wide`, `zoom_stop`, `focus_af`. Each is `{method, path, json}`.
   * `set` — one entry per setting the app can change: `iso`, `aperture`, `shutter`, `wb`, `kelvin`. Use `"{value}"` where the new value goes.
   * `status` — an endpoint the app reads every second, and a `map` of dotted paths into its JSON (`connected`, `recording`, `battery`, `model`).
   * `liveview` — an endpoint returning one JPEG per request (optional).
3. In the setup wizard choose **Custom** and enter the file path.

The dials and buttons you see are generated from what your description defines — a camera that only records gets a REC button and nothing else.

## Option B — a Python adapter

Create `pcm/adapters/my_brand.py` (or `data/adapters/my_brand.py` to keep it private — it is git-ignored):

```python
from pcm.adapters.base import Adapter, AdapterError, blank_state, http

class MyBrand(Adapter):
    id = "my_brand"                      # unique
    name = "My Brand (HTTP)"
    tested = False                       # True ONLY after you verified it on the real camera
    status_note = "Written from the vendor doc."
    capabilities = ("record", "iso")     # what the UI should offer
    fields = [{"key": "host", "label": "Camera address", "default": "192.168.1.50", "help": ""}]

    def poll(self):                      # called ~once a second; must not raise
        st = blank_state()
        try:
            j = http("GET", "http://%s/status" % self.cfg["host"])
        except AdapterError:
            return st                    # connected stays False
        st["connected"] = True
        st["recording"] = bool(j.get("rec"))
        st["settings"]["iso"] = {"value": j["iso"], "options": [100, 200, 400]}
        return st

    def record(self, start):
        http("POST", "http://%s/rec" % self.cfg["host"], {"on": start})

    def set(self, key, value):
        http("PUT", "http://%s/iso" % self.cfg["host"], {"iso": value})
```

Run `python3 pcm.py adapters` — it should be listed. Then pick it in the wizard (its `fields` become the form).

### The contract

* `poll()` returns the normalized state (see `pcm/adapters/base.py`): `connected`, `model`, `recording`, `battery`, `storage`, `settings` (`iso`, `aperture`, `shutter`, `wb`, `kelvin`; each with `value` and either `options` or `min/max/step`), `advanced`, `extra`.
* Optional: `frame()` → JPEG bytes (live view), `zoom("tele"|"wide"|"stop")`, `focus("af"|"near"|"far")`, `release()`/`take()`.
* Raise `AdapterError` for camera errors, `Unsupported` for things the camera can't do.
* The server calls adapter methods from several threads: if your camera hates parallel connections, guard them with a lock (see Canon).
* Write a test: `tests/mocks.py` has tiny fake cameras. Copy one, speak your camera's protocol, assert the normalized state. An adapter that has never touched real hardware must say `tested = False`.

## Cameras with no network API at all

Pick **"No API — use a video input"**. The app gets the picture through the browser (webcam, HDMI capture card, USB-webcam modes) and you keep the monitor, grid, Look match, white-card helper and teleprompter. You operate the camera by hand.
