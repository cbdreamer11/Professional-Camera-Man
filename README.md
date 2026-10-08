# Professional Camera Man

**Your own camera crew in a browser tab.** One screen that shows your camera, starts and stops the recording, rolls your teleprompter script at the right moment, and tells you — with numbers, for *your* room — what to change in your lights and settings so the picture looks the way you want.

🇪🇸 [Léeme en español](README.es.md) · Created by [Caleb Elizondo](https://github.com/cbdreamer11)

> **Honest status.** The **Canon (CCAPI)** adapter was built and tested on a real Canon EOS R50 V. The Blackmagic, GoPro, Sony, OSC and Custom adapters are written from the vendors' public documentation or SDK source and covered by automated tests against simulated cameras — **not yet tested on real hardware**. The app labels each adapter *tested* or *untested* on screen. Reports and fixes are very welcome.

## What it does

| | |
|---|---|
| 🎥 **Studio screen** | Live monitor, REC button, zoom, focus, ISO / aperture / shutter / white balance, scenes (saved looks), battery, card space, microphone-dropped warning. Built for a TV or monitor next to the camera, works on a phone/tablet too. |
| 📜 **Teleprompter** | Upload `.txt`, `.md` or `.docx` (or paste). Speed in words per minute, text size, mirror mode for beam-splitter glass, a gap under the lens so you read *at* the camera. `[text in brackets]` is a cue, shown dim and not counted. Works **on its own, with no server and no camera** — try it online (see below). |
| 🎬 **One-button take** | Press REC: a count-in runs, the camera starts a few seconds before the text so you get clean head-room to edit, the text starts rolling. Press again and everything stops. |
| 💡 **Setup wizard** | Asks your **look** (corporate, podcast, cinematic, bright, tech, or "match my reference photo"), measures a **reference photo** (brightness, which side the light comes from, cheek contrast, warmth), asks for your **camera and its API**, and your **lights and their distances** — then draws your set from above and tells you what to change. |
| 🎯 **Look match** | Measures the live monitor against your reference/style: face brightness, cheek ratio, light side, warmth. Says things like *"Face is 21% under the target: ≈ +0.8 stop — raise ISO to ~1600, or move the key light from 100 to ~75 cm."* |
| ⚪ **White-card helper** | Hold a white sheet up, press *Measure*: it tells you whether to raise or lower Kelvin. |
| 🔌 **Bring your own camera API** | Every camera brand is an *adapter* (a small Python file). Or describe any HTTP camera in a JSON file — no code. |
| 🖥 **No API? No problem** | Choose "video input": any webcam, HDMI capture card, DJI/GoPro/Sony in USB-webcam mode shows up as the monitor, with grid, Look match and teleprompter. |

## Quick start (2 minutes)

You need **Python 3.8+**. No other dependencies, no accounts, nothing to `pip install`.

```bash
git clone https://github.com/cbdreamer11/Professional-Camera-Man.git
cd Professional-Camera-Man
./install.sh          # macOS / Linux.  Windows:  py pcm.py
```

It asks how you want to describe your studio (browser wizard or terminal), then opens <http://localhost:8770>.

**Want to see it first, with no camera?**

```bash
python3 tests/demo.py        # fake camera + sample set → http://localhost:8771
```

**Just the teleprompter?** Open [`web/teleprompter.html`](web/teleprompter.html) in any browser, or use the hosted copy: <https://cbdreamer11.github.io/Professional-Camera-Man/teleprompter.html> (your scripts stay in your browser; nothing is uploaded).

## Setting up with Claude (optional)

Open the folder in [Claude Code](https://claude.com/claude-code) and run **`/setup-studio`**. Claude interviews you in plain language — style, reference photo, camera brand and address, every light and how far it is — writes your profile, tests the connection and explains the advice. Same questions as the wizard, same profile file.

## Cameras

| Adapter | How it talks | Status |
|---|---|---|
| **Canon** EOS R50 V (and other CCAPI bodies) | Camera Control API over Wi-Fi | ✅ **tested** on R50 V — [notes & traps](docs/CANON_CCAPI.md) |
| **Blackmagic** Pocket / URSA | REST API (`/control/api/v1`) | ⚠️ untested — from the official doc |
| **GoPro** HERO9+ | Open GoPro HTTP (endpoints from GoPro's own SDK) | ⚠️ untested — record, battery, card time, resolution/fps, digital zoom, live view (needs `ffmpeg`; live-view pipeline verified with a simulated stream) |
| **Sony** (legacy Wi-Fi models) | Camera Remote API (JSON-RPC) | ⚠️ untested — newer Alphas need Sony's SDK, see [CAMERAS](docs/CAMERAS.md) |
| **OSC** (Ricoh Theta, some Insta360…) | Open Spherical Camera | ⚠️ untested |
| **Custom** | Your own JSON description | ⚠️ works as far as your description is right |
| **Video input** (DJI Osmo, GoPro webcam mode, capture cards, any webcam) | The browser's camera access | ✅ works with anything the browser can see |

Details, what each adapter can and cannot do, and the DJI situation: [docs/CAMERAS.md](docs/CAMERAS.md).

## Add your own camera API

* **No code:** copy [`profiles/custom_api_example.json`](profiles/custom_api_example.json), describe your camera's endpoints, pick "Custom" in the wizard.
* **Python:** copy `pcm/adapters/canon_ccapi.py`, change what it sends, and drop the file in `pcm/adapters/` (or `data/adapters/` to keep it private). It is discovered automatically.

Full guide: [docs/ADAPTERS.md](docs/ADAPTERS.md).

## How the advice is calculated

Standard practice turned into numbers for *your* distances: the 180° shutter rule snapped to a flicker-safe speed for your mains frequency, key-light angle and height ranges per style, the inverse-square law for the key:fill ratio and for "move the fill to X cm", falloff across the width of a face, mixed-colour-temperature warnings, camera-distance and background-separation checks. See [docs/LIGHTING.md](docs/LIGHTING.md). They are *estimates* — the Look panel measures the real picture.

## Other commands

```bash
python3 pcm.py                 # run the studio (http://localhost:8770)
python3 pcm.py setup           # answer the setup questions in the terminal
python3 pcm.py advice          # print the advice for your saved profile
python3 pcm.py adapters        # list camera adapters
python3 pcm.py analyze-photo a.jpg   # measure a reference photo (needs: pip install pillow)
python3 pcm.py run --host 0.0.0.0    # reach it from a tablet/phone on your Wi-Fi (NO password: trusted networks only)
python3 -m unittest discover -s tests -v
```

Your profile, scenes and private adapters live in `data/`, which is git-ignored.

## Safety notes

* The server listens on `localhost` only, unless you pass `--host`. State-changing calls are accepted only from the studio page itself (blocks other websites and DNS-rebinding).
* A camera can lock up if you send it commands in the wrong state (see the Canon notes). Test with the camera idle, and don't use this as the only safeguard for a recording you can't redo.
* Don't test recording on a camera someone else is using.

## License & credit

[**Professional Camera Man License** — MIT + Attribution](LICENSE). Free for personal **and commercial** use, modify it, sell what you build with it. **One condition: keep the "Created by Caleb Elizondo" credit visible in the interface** (it is the footer of every page, already in place). Camera brand names belong to their owners; this project is independent of all of them. No warranty.

© 2026 Caleb Elizondo · <https://github.com/cbdreamer11>
