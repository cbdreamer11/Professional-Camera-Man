# Camera support — what is real

"Tested" means the author ran it against a physical camera. Everything else is written from public documentation and checked only against simulated cameras (see `tests/`).

| Brand / family | Adapter | Controls | Live view in the app | Status |
|---|---|---|---|---|
| Canon EOS R50 V | `canon_ccapi` | record, zoom, focus/AF, ISO, aperture, shutter, WB/Kelvin, battery, card, mic-dropped, release | ✅ MJPEG from the camera | ✅ tested |
| Other Canon bodies that Canon lists as supporting CCAPI | `canon_ccapi` | same API family; settings that don't exist are simply not shown | ✅ | ⚠️ untested |
| Blackmagic Pocket / URSA | `blackmagic_rest` | record, ISO, WB, shutter, iris, zoom, AF | ❌ (no stream in the REST API → use a video input) | ⚠️ untested |
| GoPro HERO9+ | `gopro_http` | record, battery, card time/space, overheating, resolution + fps (Advanced dialog), digital zoom | ✅ if `ffmpeg` is installed (UDP MPEG-TS → JPEG; verified with a simulated stream). Otherwise use GoPro *Webcam mode* as video input | ⚠️ untested on a real camera |
| Sony, legacy Wi-Fi bodies (a5000/5100/6000, QX, RX100…) | `sony_remote` | record, ISO, shutter, WB, zoom | ✅ (Sony live-view packets) | ⚠️ untested |
| Sony current Alphas (a7 IV, a7S III, FX3/FX30, ZV-E1, a1…) | — | Sony's control interface is the native **Camera Remote SDK**, not an HTTP API | via USB-webcam/UVC mode as video input | 🔧 adapter wanted |
| Ricoh Theta, Insta360 (OSC mode) | `osc_http` | record, ISO, shutter, WB, battery | ✅ | ⚠️ untested |
| DJI Osmo Pocket / Action | none | As far as we know DJI publishes no local network control API for these cameras (control is Bluetooth LE with a proprietary protocol; DJI's published SDKs target drones and Ronin/payload products). Unofficial reverse-engineered BLE projects exist; none is included here. | ✅ **as a video input**, on models that offer a USB webcam mode (e.g. Osmo Pocket 3) | 🖥 monitor only |
| Panasonic LUMIX, Nikon, Fujifilm, others | none yet | Some expose HTTP/Wi-Fi interfaces documented by the community or vendor | via USB-webcam modes as video input | 🔧 adapters wanted |
| Anything else with an HTTP API | `custom_json` | whatever you describe | optional (one JPEG per request) | ⚠️ yours to verify |
| Any webcam / HDMI capture card | `video_input` | none (browser monitor only) | ✅ | ✅ |

If you verify an adapter on real hardware, open a pull request that flips `tested = True`, updates the table above and says which model/firmware you used.
