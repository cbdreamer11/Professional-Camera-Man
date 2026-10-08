"""The studio profile: what the person told the setup wizard (style, camera, lights, distances, reference photo)."""
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("PCM_DATA") or os.path.join(ROOT, "data")
PROFILE = os.path.join(DATA, "profile.json")
SCENES = os.path.join(DATA, "scenes.json")

ROLES = ("key", "fill", "back", "background", "practical", "other")

DEFAULT = {
    "version": 1,
    "lang": "en",
    "style": "corporate_clean",
    "use": "",
    "fps": 29.97,
    "mains_hz": 60,
    "camera": {"adapter": "video_input", "cfg": {}, "lens": "", "distance_cm": 200, "height_vs_eyes_cm": 0},
    "subject": {"background_distance_cm": 150},
    "lights": [],
    "reference": None,
    "prefs": {"countdown": 5, "camera_offset": 3},
}


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _num(v, default=None, lo=None, hi=None):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def normalize(p):
    """Fill defaults and clamp numbers. Never trusts the input shape."""
    p = p if isinstance(p, dict) else {}
    out = json.loads(json.dumps(DEFAULT))
    out["lang"] = p.get("lang") if p.get("lang") in ("en", "es") else out["lang"]
    out["style"] = str(p.get("style") or out["style"])[:40]
    out["use"] = str(p.get("use") or "")[:40]
    out["fps"] = _num(p.get("fps"), 29.97, 1, 240)
    out["mains_hz"] = 50 if _num(p.get("mains_hz"), 60) == 50 else 60
    cam = p.get("camera") if isinstance(p.get("camera"), dict) else {}
    out["camera"].update({"adapter": str(cam.get("adapter") or "video_input")[:40],
                          "cfg": cam.get("cfg") if isinstance(cam.get("cfg"), dict) else {},
                          "lens": str(cam.get("lens") or "")[:80],
                          "distance_cm": _num(cam.get("distance_cm"), 200, 20, 3000),
                          "height_vs_eyes_cm": _num(cam.get("height_vs_eyes_cm"), 0, -200, 200)})
    sub = p.get("subject") if isinstance(p.get("subject"), dict) else {}
    out["subject"]["background_distance_cm"] = _num(sub.get("background_distance_cm"), 150, 0, 3000)
    for l in (p.get("lights") if isinstance(p.get("lights"), list) else [])[:12]:
        if not isinstance(l, dict):
            continue
        out["lights"].append({
            "name": str(l.get("name") or "Light")[:60],
            "role": l.get("role") if l.get("role") in ROLES else "other",
            "modifier": str(l.get("modifier") or "")[:40],
            "side": "right" if l.get("side") == "right" else "left",
            "azimuth_deg": _num(l.get("azimuth_deg"), 40, 0, 180),
            "height_cm": _num(l.get("height_cm"), 0, -200, 400),
            "distance_cm": _num(l.get("distance_cm"), 100, 10, 2000),
            "power_pct": _num(l.get("power_pct"), 100, 1, 100),
            "kelvin": _num(l.get("kelvin"), None, 1500, 12000),
        })
    ref = p.get("reference")
    if isinstance(ref, dict):
        out["reference"] = {k: ref[k] for k in ("filename", "face_luma", "luma_mean", "bg_luma", "cheek_ratio", "bright_side",
                                                "rb_ratio", "saturation", "contrast", "notes") if k in ref}
    pr = p.get("prefs") if isinstance(p.get("prefs"), dict) else {}
    out["prefs"] = {"countdown": int(_num(pr.get("countdown"), 5, 0, 30)), "camera_offset": int(_num(pr.get("camera_offset"), 3, 0, 30))}
    return out


def load():
    p = read_json(PROFILE, None)
    return normalize(p) if p else None


def save(p):
    p = normalize(p)
    p["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    write_json(PROFILE, p)
    return p
