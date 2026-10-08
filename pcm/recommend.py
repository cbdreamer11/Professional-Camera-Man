"""From the studio profile to concrete advice. Pure functions, no network, no camera — easy to test.

Everything here is standard lighting/camera practice (180° shutter rule, mains-flicker-safe shutters, inverse-square
law, key:fill ratios) turned into numbers for YOUR distances. The numbers are estimates, not measurements:
the Look panel in the studio measures the real picture.
"""
import math

STYLES = {
    "corporate_clean": {"key_az": (30, 45), "key_elev": (12, 30), "ratio": (1.5, 2.5), "kelvin": 5600, "aperture": "f/2.8–f/4",
                        "face_luma": (140, 160), "bg": "evenly lit, about one stop under the face"},
    "podcast_warm":    {"key_az": (35, 50), "key_elev": (10, 25), "ratio": (2, 3), "kelvin": 4500, "aperture": "f/2–f/2.8",
                        "face_luma": (130, 155), "bg": "warm practical lights, a bit darker than the face"},
    "cinematic_moody": {"key_az": (55, 75), "key_elev": (20, 35), "ratio": (4, 8), "kelvin": 5000, "aperture": "f/1.8–f/2.8",
                        "face_luma": (100, 135), "bg": "dark, with a rim/back light for separation"},
    "high_key_bright": {"key_az": (0, 25), "key_elev": (10, 20), "ratio": (1, 1.5), "kelvin": 5600, "aperture": "f/4–f/5.6",
                        "face_luma": (160, 185), "bg": "bright and clean, almost as bright as the face"},
    "tech_cool":       {"key_az": (30, 45), "key_elev": (12, 30), "ratio": (2, 3), "kelvin": 5600, "aperture": "f/2.8–f/4",
                        "face_luma": (135, 155), "bg": "cool accent lights (blue/teal) behind, darker than the face"},
    "custom":          {"key_az": (30, 55), "key_elev": (12, 30), "ratio": (1.5, 4), "kelvin": 5600, "aperture": "f/2.8–f/4",
                        "face_luma": (130, 160), "bg": "whatever your reference photo shows"},
}
GAMMA = 2.4

M = {  # message catalog: code -> {lang: template}
    "shutter_flicker": {"en": "Shutter {sh}: the closest to the 180° rule that is flicker-safe on {hz} Hz mains. Avoid 1/48 and 1/125 under LED/fluorescent light.",
                        "es": "Obturador {sh}: lo más cercano a la regla de 180° que no parpadea con red de {hz} Hz. Evita 1/48 y 1/125 con luz LED/fluorescente."},
    "wb": {"en": "White balance: set {k} K (the colour temperature of your key/fill lights). Check it with the white-card helper in the studio.",
           "es": "Balance de blancos: pon {k} K (la temperatura de color de tu luz principal y de relleno). Compruébalo con la hoja blanca en el estudio."},
    "mixed": {"en": "Your key/fill/back lights span {lo}–{hi} K. Mixed colour temperatures make skin go orange on one side and blue on the other. Match them (or gel/dial them) unless it is a deliberate accent.",
              "es": "Tus luces principal/relleno/contra van de {lo} a {hi} K. Mezclar temperaturas pinta la piel naranja de un lado y azul del otro. Igúalas (o usa gelatinas/regúlalas) salvo que sea un acento intencional."},
    "no_key": {"en": "No key light defined. Add one: it is the single most important light.",
               "es": "No definiste luz principal. Agrega una: es la luz más importante."},
    "key_az_low": {"en": "Key light is {a}° off the camera axis; for this style use {lo}–{hi}°. Swing it {d}° farther out on the {side} side.",
                   "es": "La luz principal está a {a}° del eje de la cámara; para este estilo usa {lo}–{hi}°. Ábrela {d}° más del lado {side}."},
    "key_az_high": {"en": "Key light is {a}° off axis; for this style use {lo}–{hi}°. Bring it {d}° closer to the camera axis.",
                    "es": "La luz principal está a {a}° del eje; para este estilo usa {lo}–{hi}°. Acércala {d}° al eje de la cámara."},
    "key_az_ok": {"en": "Key light angle ({a}°) is right for this style.", "es": "El ángulo de tu luz principal ({a}°) es correcto para este estilo."},
    "key_elev_low": {"en": "Key light is only {e}° above eye level; aim for {lo}–{hi}° (about {h} cm higher at your distance). Too low looks like a flashlight under the chin.",
                     "es": "La luz principal está a solo {e}° sobre los ojos; busca {lo}–{hi}° (unos {h} cm más arriba a tu distancia). Muy baja parece linterna bajo la barbilla."},
    "key_elev_high": {"en": "Key light is {e}° above eye level; aim for {lo}–{hi}° (lower it ~{h} cm). Too high drops dark shadows into the eye sockets.",
                      "es": "La luz principal está a {e}° sobre los ojos; busca {lo}–{hi}° (bájala ~{h} cm). Muy alta mete sombras oscuras en las cuencas de los ojos."},
    "falloff": {"en": "At {d} cm the light falls off ≈{s} stops across the width of a face. Closer = softer light but a bigger difference between the near and far cheek.",
                "es": "A {d} cm la luz cae ≈{s} pasos de diafragma a lo ancho de una cara. Más cerca = luz más suave pero más diferencia entre la mejilla cercana y la lejana."},
    "ratio": {"en": "Estimated key:fill ≈ {r}:1 (assumes similar lights; the Look panel measures the real one). Target for this style: {lo}–{hi}:1.",
              "es": "Proporción principal:relleno estimada ≈ {r}:1 (supone luces parecidas; el panel de Look mide la real). Meta de este estilo: {lo}–{hi}:1."},
    "ratio_fix_dist": {"en": "To reach about {t}:1, move the fill light to ~{d} cm (or set its power to ~{p}%).",
                       "es": "Para llegar a ~{t}:1 mueve el relleno a ~{d} cm (o bájale/súbele la potencia a ~{p}%)."},
    "no_fill": {"en": "No fill light: the shadow side depends on room bounce. A white card or a dim panel opposite the key controls it.",
                "es": "No hay luz de relleno: el lado de sombra depende del rebote del cuarto. Una cartulina blanca o un panel tenue frente a la principal lo controla."},
    "back_missing": {"en": "No back/rim light. A light behind and above the subject separates hair and shoulders from the background.",
                     "es": "No hay luz de contra. Una luz detrás y arriba del sujeto separa pelo y hombros del fondo."},
    "back_az": {"en": "Back light '{n}' is at {a}°; it works best behind the subject (130–170°).",
                "es": "La luz de contra '{n}' está a {a}°; funciona mejor detrás del sujeto (130–170°)."},
    "bg_close": {"en": "The subject is only {d} cm from the background. Aim for 120+ cm so the background stays soft and the key light does not light it.",
                 "es": "El sujeto está a solo {d} cm del fondo. Busca 120+ cm para que el fondo quede suave y la luz principal no lo alumbre."},
    "cam_close": {"en": "The camera is only {d} cm away: wide angles that close stretch the face. Back up to 150+ cm and zoom in (50 mm equivalent or longer).",
                  "es": "La cámara está a solo {d} cm: los gran angulares tan cerca deforman la cara. Aléjate a 150+ cm y haz zoom (50 mm equivalentes o más)."},
    "cam_height": {"en": "Put the lens at eye level or slightly above (now {h} cm {w} the eyes).",
                   "es": "Pon el lente a la altura de los ojos o apenas arriba (ahora {h} cm {w} los ojos)."},
    "ref_side": {"en": "Your reference photo looks lit from the {side} (cheek ratio ≈ {c}:1, light ratio ≈ {r}:1).",
                 "es": "Tu foto de referencia parece iluminada desde el lado {side} (mejillas ≈ {c}:1, luz ≈ {r}:1)."},
    "ref_side_mismatch": {"en": "Your key light is on the {mine} but the reference photo is lit from the {theirs}. Swap sides to match it.",
                          "es": "Tu luz principal está del lado {mine} pero la referencia está iluminada del {theirs}. Cámbiala de lado para igualarla."},
    "iso": {"en": "ISO: start low and let the key light do the work. Raise ISO only until the face lands in the target brightness ({lo}–{hi}/255). The Look panel tells you.",
            "es": "ISO: empieza bajo y deja que la luz principal haga el trabajo. Súbelo solo hasta que la cara caiga en el brillo meta ({lo}–{hi}/255). El panel de Look te lo dice."},
}


def msg(code, lang, **p):
    t = M[code].get(lang) or M[code]["en"]
    return t.format(**p)


def shutter_for(fps, mains_hz):
    """180° rule, snapped to a value that does not flicker under mains-powered light."""
    f = round(float(fps))
    if f <= 25:
        if f == 25 or mains_hz == 50:
            return "1/50"
        return "1/60"          # 24p on 60 Hz mains: 1/48 flickers, 1/60 is the nearest safe one
    if f <= 30:
        return "1/60" if mains_hz == 60 else "1/50"
    if f <= 50:
        return "1/100"
    return "1/120"


def elevation_deg(light):
    d = max(light["distance_cm"], 1)
    return math.degrees(math.atan2(light["height_cm"], d))


def falloff_stops(distance_cm, face_depth_cm=15.0):
    near, far = max(distance_cm - face_depth_cm / 2, 1), distance_cm + face_depth_cm / 2
    return round(2 * math.log2(far / near), 1)


def intensity(light):
    return (light["power_pct"] / 100.0) / (light["distance_cm"] / 100.0) ** 2


def recommend(profile, lang=None):
    lang = lang or profile.get("lang", "en")
    style = STYLES.get(profile.get("style"), STYLES["custom"])
    ref = profile.get("reference") or {}
    lights = profile.get("lights", [])
    notes, warns = [], []

    # ---- camera ----
    sh = shutter_for(profile.get("fps", 29.97), profile.get("mains_hz", 60))
    temps = [l["kelvin"] for l in lights if l["role"] in ("key", "fill", "back") and l.get("kelvin")]
    key_k = next((l["kelvin"] for l in lights if l["role"] == "key" and l.get("kelvin")), None)
    kelvin = key_k or (round(sum(temps) / len(temps) / 50) * 50 if temps else style["kelvin"])
    cam = {"shutter": sh, "kelvin": int(kelvin), "aperture_hint": style["aperture"], "fps": profile.get("fps"),
           "iso_note": msg("iso", lang, lo=style["face_luma"][0], hi=style["face_luma"][1])}
    notes.append(msg("shutter_flicker", lang, sh=sh, hz=profile.get("mains_hz", 60)))
    notes.append(msg("wb", lang, k=cam["kelvin"]))
    if temps and max(temps) - min(temps) > 600:
        warns.append(msg("mixed", lang, lo=int(min(temps)), hi=int(max(temps))))

    # ---- lights ----
    keys = [l for l in lights if l["role"] == "key"]
    fills = [l for l in lights if l["role"] == "fill"]
    backs = [l for l in lights if l["role"] == "back"]
    lo, hi = style["key_az"]
    elo, ehi = style["key_elev"]
    key = keys[0] if keys else None
    if not key:
        warns.append(msg("no_key", lang))
    else:
        a = key["azimuth_deg"]
        side = {"left": "izquierdo" if lang == "es" else "left", "right": "derecho" if lang == "es" else "right"}[key["side"]]
        if a < lo:
            warns.append(msg("key_az_low", lang, a=round(a), lo=lo, hi=hi, d=round(lo - a), side=side))
        elif a > hi:
            warns.append(msg("key_az_high", lang, a=round(a), lo=lo, hi=hi, d=round(a - hi)))
        else:
            notes.append(msg("key_az_ok", lang, a=round(a)))
        e = elevation_deg(key)
        if e < elo:
            warns.append(msg("key_elev_low", lang, e=round(e), lo=elo, hi=ehi,
                             h=round(math.tan(math.radians(elo)) * key["distance_cm"] - key["height_cm"])))
        elif e > ehi:
            warns.append(msg("key_elev_high", lang, e=round(e), lo=elo, hi=ehi,
                             h=round(key["height_cm"] - math.tan(math.radians(ehi)) * key["distance_cm"])))
        notes.append(msg("falloff", lang, d=round(key["distance_cm"]), s=falloff_stops(key["distance_cm"])))
        if ref.get("bright_side") in ("left", "right") and key["side"] != ref["bright_side"]:
            names = {"left": ("izquierdo", "izquierdo"), "right": ("derecho", "derecho")} if lang == "es" else {"left": ("left",) * 2, "right": ("right",) * 2}
            warns.append(msg("ref_side_mismatch", lang, mine=names[key["side"]][0], theirs=names[ref["bright_side"]][0]))

    ratio_est = None
    rlo, rhi = style["ratio"]
    if key and fills:
        fill = fills[0]
        ratio_est = intensity(key) / max(intensity(fill), 1e-6)
        r = round(ratio_est, 1)
        notes.append(msg("ratio", lang, r=r, lo=rlo, hi=rhi))
        target = (rlo + rhi) / 2
        if not (rlo <= ratio_est <= rhi):
            new_d = math.sqrt((fill["power_pct"] / 100.0) * (key["distance_cm"] / 100.0) ** 2 * target / (key["power_pct"] / 100.0)) * 100
            new_p = (key["power_pct"] / 100.0) / ((fill["distance_cm"] / 100.0) ** 2 * target) * 100
            notes.append(msg("ratio_fix_dist", lang, t=round(target, 1), d=round(new_d), p=max(1, min(100, round(new_p)))))
    elif key:
        notes.append(msg("no_fill", lang))

    if not backs:
        notes.append(msg("back_missing", lang))
    for b in backs:
        if not 130 <= b["azimuth_deg"] <= 175:
            warns.append(msg("back_az", lang, n=b["name"], a=round(b["azimuth_deg"])))

    bgd = profile.get("subject", {}).get("background_distance_cm", 150)
    if bgd < 120:
        warns.append(msg("bg_close", lang, d=round(bgd)))
    cd = profile.get("camera", {}).get("distance_cm", 200)
    if cd < 100:
        warns.append(msg("cam_close", lang, d=round(cd)))
    hv = profile.get("camera", {}).get("height_vs_eyes_cm", 0)
    if abs(hv) > 25:
        w = ("sobre" if hv > 0 else "bajo") if lang == "es" else ("above" if hv > 0 else "below")
        warns.append(msg("cam_height", lang, h=abs(round(hv)), w=w))

    # ---- targets for the Look panel ----
    ratio_for_cheek = (rlo + rhi) / 2
    targets_style = {"face_luma": list(style["face_luma"]), "cheek_ratio": [round(rlo ** (1 / GAMMA), 2), round(rhi ** (1 / GAMMA), 2)],
                     "kelvin": cam["kelvin"], "bg": style["bg"]}
    targets_ref = None
    if ref.get("face_luma") is not None:
        fl = float(ref["face_luma"])
        cr = float(ref.get("cheek_ratio") or 1.0)
        targets_ref = {"face_luma": [round(fl * 0.93), round(fl * 1.07)], "cheek_ratio": [round(max(1.0, cr * 0.9), 2), round(cr * 1.1, 2)],
                       "rb_ratio": ref.get("rb_ratio"), "bright_side": ref.get("bright_side")}
        if ref.get("bright_side") in ("left", "right"):
            names = {"left": "izquierdo" if lang == "es" else "left", "right": "derecho" if lang == "es" else "right"}
            notes.append(msg("ref_side", lang, side=names[ref["bright_side"]], c=round(cr, 2), r=round(cr ** GAMMA, 1)))

    return {"style": profile.get("style"), "camera": cam, "notes": notes, "warnings": warns,
            "ratio_estimate": round(ratio_est, 2) if ratio_est else None,
            "targets_style": targets_style, "targets_reference": targets_ref,
            "scene": {"shutter": sh, "kelvin": cam["kelvin"]}}


def white_card_shift(r, g, b, lang="en"):
    """Given the mean RGB of a white card seen by the camera, say which way to move the white balance (Kelvin).
    A bluish card (b > r) means the camera is under-correcting: RAISE the Kelvin setting. Reddish: lower it."""
    if min(r, g, b) <= 0:
        return {"ok": False}
    cast = (b - r) / ((r + g + b) / 3.0) * 100.0      # +% = bluish, -% = reddish
    steps = round(cast / 1.0) * 100                      # rule of thumb: ~100 K per 1 % of imbalance, then re-measure
    return {"ok": True, "cast_pct": round(cast, 1), "suggest_kelvin_delta": int(steps) if abs(cast) > 0.8 else 0,
            "neutral": abs(cast) <= 0.8}
