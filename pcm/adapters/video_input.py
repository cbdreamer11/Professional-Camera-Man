"""No camera API — just a video input.

For anything without a usable network API: DJI Osmo / Pocket (UVC webcam mode), GoPro Webcam mode, Sony / Panasonic / Fuji /
Nikon / Canon USB-streaming modes, HDMI capture cards, phones used as webcams. The monitor, the grid, the look-matching and
the teleprompter all work; the camera itself is operated by hand (or use OBS / the vendor app to record).
"""
from .base import Adapter, blank_state


class VideoInput(Adapter):
    id = "video_input"
    name = "No API — use a video input (webcam / HDMI capture / DJI / USB mode)"
    tested = True
    status_note = "Browser-only monitor. Works with anything the browser can see as a camera."
    docs_url = "docs/ADAPTERS.md"
    capabilities = ()
    fields = []

    def poll(self):
        st = blank_state("Video input (browser)")
        st["connected"] = True
        return st
