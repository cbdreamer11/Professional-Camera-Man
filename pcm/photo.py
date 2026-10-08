"""Measure a reference photo from the command line (same boxes and formulas as web/look.js). Needs Pillow: pip install pillow.
The web wizard does this in the browser with no dependency; this exists for the terminal wizard and for Claude."""
BOX = {"face": (0.35, 0.15, 0.65, 0.55), "left": (0.36, 0.25, 0.49, 0.50), "right": (0.51, 0.25, 0.64, 0.50)}


def _mean(img, box):
    w, h = img.size
    x0, y0, x1, y1 = int(round(box[0] * w)), int(round(box[1] * h)), int(round(box[2] * w)), int(round(box[3] * h))
    px = img.crop((x0, y0, max(x1, x0 + 1), max(y1, y0 + 1))).getdata()
    n = r = g = b = l = sat = 0
    for R, G, B in px:
        r += R; g += G; b += B; l += 0.2126 * R + 0.7152 * G + 0.0722 * B
        mx = max(R, G, B); sat += (mx - min(R, G, B)) / mx if mx else 0; n += 1
    n = n or 1
    return {"r": r / n, "g": g / n, "b": b / n, "l": l / n, "sat": sat / n}


def analyze(path):
    from PIL import Image                               # imported here so the rest of the app never needs Pillow
    img = Image.open(path).convert("RGB")
    img.thumbnail((320, 320))
    f, L, R = _mean(img, BOX["face"]), _mean(img, BOX["left"]), _mean(img, BOX["right"])
    bg = (_mean(img, (0, 0, 0.12, 1))["l"] + _mean(img, (0.88, 0, 1, 1))["l"]) / 2
    lum = sorted(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in list(img.getdata())[::4])
    p = lambda q: lum[min(len(lum) - 1, int(len(lum) * q))]
    ratio = max(L["l"], R["l"]) / max(1.0, min(L["l"], R["l"]))
    return {"face_luma": round(f["l"]), "luma_mean": round(sum(lum) / len(lum)), "bg_luma": round(bg),
            "cheek_ratio": round(ratio, 2), "bright_side": "even" if ratio < 1.04 else ("left" if L["l"] > R["l"] else "right"),
            "rb_ratio": round(f["r"] / max(1.0, f["b"]), 2), "saturation": round(f["sat"], 2), "contrast": round(p(0.95) / max(1.0, p(0.05)), 1)}
