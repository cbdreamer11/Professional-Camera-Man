# Roadmap / help wanted

* **Verify the untested adapters on real cameras** (Blackmagic, GoPro, Sony legacy, OSC) and flip `tested`.
* **Sony Camera Remote SDK adapter** for current Alphas (native library; probably a small helper process).
* **Panasonic LUMIX / Fujifilm / Nikon** HTTP-or-USB adapters.
* **GoPro**: Bluetooth Wi-Fi enable, presets, and more settings (white balance, ISO limits) — verify the current adapter on a real camera first.
* **Audio check after each take** (download the first MBs of the new clip and measure with `ffmpeg volumedetect`) — it caught a silent take on the original studio; needs ffmpeg and clip-download handling that is safe on each camera.
* **Remote for the teleprompter** (phone as a controller) and Roku/Apple TV display targets.
* **PDF import** for the teleprompter.
* **A Look-match that can sample a draggable region** instead of the fixed centre box.
* Translations beyond English/Spanish (`web/common.js` has the dictionary).
