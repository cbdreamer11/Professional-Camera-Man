# The studio profile (`data/profile.json`)

Written by the wizard, `python3 pcm.py setup`, or `/setup-studio`. You can also edit it by hand or import one: `python3 pcm.py import-profile file.json` (it validates and clamps everything). It lives in `data/`, which is git-ignored.

```jsonc
{
  "lang": "en",                      // "en" | "es"
  "style": "corporate_clean",        // corporate_clean | podcast_warm | cinematic_moody | high_key_bright | tech_cool | custom
  "use": "youtube",
  "fps": 29.97,                      // frames per second you record at
  "mains_hz": 60,                    // 60 or 50 (your electricity: decides flicker-safe shutter)
  "camera": {
    "adapter": "canon_ccapi",        // see: python3 pcm.py adapters
    "cfg": { "host": "192.168.1.40", "port": 443, "scheme": "https" },   // the adapter's `fields`
    "lens": "RF 24-70 f/2.8",        // free text
    "distance_cm": 200,              // camera → you
    "height_vs_eyes_cm": 5           // lens height relative to your eyes (negative = lower)
  },
  "subject": { "background_distance_cm": 150 },     // you → wall behind
  "lights": [
    { "name": "Softbox", "role": "key",              // key | fill | back | background | practical | other
      "modifier": "softbox",
      "side": "left",                                // as seen FROM THE CAMERA: left | right
      "azimuth_deg": 40,                             // 0 = beside the camera, 90 = beside you, 180 = behind you
      "height_cm": 30,                               // above(+)/below(−) your eyes
      "distance_cm": 100,                            // light → your face
      "power_pct": 80, "kelvin": 5600 }
  ],
  "reference": {                     // optional: numbers measured from your reference photo (the photo itself is never saved)
    "filename": "ref.jpg", "face_luma": 150, "cheek_ratio": 1.3, "bright_side": "left", "rb_ratio": 1.25,
    "bg_luma": 60, "luma_mean": 90, "saturation": 0.3, "contrast": 8.0
  },
  "prefs": { "countdown": 5, "camera_offset": 3 }    // REC: count 5 s; the camera starts at second 3; text starts at 5
}
```
