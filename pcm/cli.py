"""Command line: run the studio, ask the setup questions in the terminal, print the advice."""
import argparse
import json
import sys

from . import CREDIT, CREDIT_URL, __version__, profile as prof, recommend
from .adapters import discover

T = {
    "en": {
        "lang": "Language / Idioma (en/es)", "style": "Which look do you want?", "fps": "Frames per second you record at (24, 25, 30, 60)",
        "mains": "Mains frequency where you are: 60 Hz (Americas, Japan…) or 50 Hz (Europe, most of the world)?",
        "cam": "Which camera?", "ask_host": "{label}", "lights": "Now your lights. Add them one by one (empty name to finish).",
        "lname": "  Light name (e.g. 'softbox left')", "role": "  Role: key / fill / back / background / practical",
        "side": "  Side as seen FROM THE CAMERA: left / right", "az": "  Angle from the camera axis in degrees (0 = next to the camera, 90 = beside you, 180 = behind you)",
        "h": "  Height relative to your eyes in cm (negative = lower)", "d": "  Distance from your face in cm", "pw": "  Power % (100 if unsure)",
        "k": "  Colour temperature in K (empty if unknown)", "camd": "Distance from camera to you in cm", "bgd": "Distance from you to the background in cm",
        "ref": "Path to a reference photo with the look you want (empty to skip; the web wizard analyses it for you)",
        "saved": "Saved to {p}", "advice": "\nWhat to change:", "tips": "\nGood to know:", "ok": "Nothing to fix — your setup matches the style."},
    "es": {
        "lang": "Language / Idioma (en/es)", "style": "¿Qué estilo quieres?", "fps": "Cuadros por segundo con los que grabas (24, 25, 30, 60)",
        "mains": "Frecuencia de la luz eléctrica donde vives: 60 Hz (América, Japón…) o 50 Hz (Europa y casi todo el mundo)",
        "cam": "¿Qué cámara tienes?", "ask_host": "{label}", "lights": "Ahora tus luces. Agrégalas una por una (nombre vacío para terminar).",
        "lname": "  Nombre de la luz (ej. 'softbox izquierdo')", "role": "  Función: key (principal) / fill (relleno) / back (contra) / background (fondo) / practical",
        "side": "  Lado visto DESDE LA CÁMARA: left / right", "az": "  Ángulo respecto al eje de la cámara en grados (0 = junto a la cámara, 90 = a tu lado, 180 = detrás de ti)",
        "h": "  Altura respecto a tus ojos en cm (negativo = más abajo)", "d": "  Distancia a tu cara en cm", "pw": "  Potencia % (100 si no sabes)",
        "k": "  Temperatura de color en K (vacío si no sabes)", "camd": "Distancia de la cámara a ti en cm", "bgd": "Distancia de ti al fondo en cm",
        "ref": "Ruta de una foto de referencia con el look que quieres (vacío para saltar; el asistente web la analiza por ti)",
        "saved": "Guardado en {p}", "advice": "\nQué cambiar:", "tips": "\nBueno saber:", "ok": "Nada que corregir: tu set coincide con el estilo."},
}


def ask(q, default=""):
    a = input("%s%s: " % (q, " [%s]" % default if default != "" else "")).strip()
    return a or str(default)


def choose(q, options, default=0):
    print(q)
    for i, (key, label) in enumerate(options, 1):
        print("  %d) %s" % (i, label))
    while True:
        a = input("> [%d] " % (default + 1)).strip() or str(default + 1)
        if a.isdigit() and 1 <= int(a) <= len(options):
            return options[int(a) - 1][0]


def setup():
    lang = ask(T["en"]["lang"], "en").lower()[:2]
    lang = lang if lang in T else "en"
    t = T[lang]
    classes = discover()
    p = {"lang": lang, "lights": [], "camera": {}, "subject": {}}
    style_names = {"corporate_clean": ("Corporate & clean", "Corporativo y limpio"), "podcast_warm": ("Podcast, warm", "Podcast, cálido"),
                   "cinematic_moody": ("Cinematic, moody", "Cinematográfico, dramático"), "high_key_bright": ("Bright & airy (high key)", "Brillante y limpio (high key)"),
                   "tech_cool": ("Tech, cool tones", "Tech, tonos fríos"), "custom": ("Match my reference photo", "Igualar mi foto de referencia")}
    p["style"] = choose(t["style"], [(k, v[0 if lang == "en" else 1]) for k, v in style_names.items()])
    p["fps"] = float(ask(t["fps"], 30))
    p["mains_hz"] = int(ask(t["mains"], 60))
    cid = choose(t["cam"], [(c.id, c.name + ("" if c.tested else "  (untested)")) for c in classes.values()], 0)
    cfg = {}
    for f in classes[cid].fields:
        v = ask(t["ask_host"].format(label=f["label"], d=f.get("default", "")), f.get("default", ""))
        cfg[f["key"]] = v
    p["camera"] = {"adapter": cid, "cfg": cfg, "distance_cm": float(ask(t["camd"], 200))}
    p["subject"] = {"background_distance_cm": float(ask(t["bgd"], 150))}
    print(t["lights"])
    while True:
        name = ask(t["lname"])
        if not name:
            break
        p["lights"].append({"name": name, "role": ask(t["role"], "key"), "side": ask(t["side"], "left"),
                            "azimuth_deg": float(ask(t["az"], 40)), "height_cm": float(ask(t["h"], 20)),
                            "distance_cm": float(ask(t["d"], 100)), "power_pct": float(ask(t["pw"], 100)),
                            "kelvin": float(ask(t["k"], 0)) or None})
    ref = ask(t["ref"], "")
    if ref:
        try:
            from . import photo
            p["reference"] = {"filename": ref.split("/")[-1], **photo.analyze(ref.strip().strip("'\""))}
        except ImportError:
            print("  (Pillow is not installed: run  pip install pillow  or use the web wizard, which needs nothing.)")
        except OSError as e:
            print("  (could not read the photo: %s)" % e)
    saved = prof.save(p)
    print(t["saved"].format(p=prof.PROFILE))
    show(saved)


def show(p):
    r = recommend.recommend(p)
    t = T[p["lang"]]
    print(t["advice"] if r["warnings"] else "\n" + t["ok"])
    for w in r["warnings"]:
        print("  ⚠ " + w)
    print(t["tips"])
    for n in r["notes"]:
        print("  • " + n)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pcm", description="Professional Camera Man — %s" % CREDIT)
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="start the studio (default)")
    r.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to reach it from a tablet/phone on your network (no password!)")
    r.add_argument("--port", type=int, default=8770)
    sub.add_parser("setup", help="answer the setup questions in the terminal")
    sub.add_parser("advice", help="print advice for your saved profile")
    sub.add_parser("adapters", help="list the camera adapters")
    a = sub.add_parser("analyze-photo", help="measure a reference photo (needs Pillow) and print the numbers as JSON")
    a.add_argument("path")
    ip = sub.add_parser("import-profile", help="validate a profile JSON file and save it as your studio profile")
    ip.add_argument("path")
    ap.add_argument("--version", action="version", version="%s (%s — %s)" % (__version__, CREDIT, CREDIT_URL))
    args = ap.parse_args(argv)
    cmd = args.cmd or "run"
    if cmd == "setup":
        setup()
    elif cmd == "advice":
        p = prof.load()
        show(p) if p else print("No profile yet: run  python3 pcm.py setup")
    elif cmd == "analyze-photo":
        from . import photo
        print(json.dumps(photo.analyze(args.path), indent=1))
    elif cmd == "import-profile":
        with open(args.path, encoding="utf-8") as f:
            saved = prof.save(json.load(f))
        print("Saved to %s" % prof.PROFILE)
        show(saved)
    elif cmd == "adapters":
        for c in discover(prof.DATA + "/adapters").values():
            print("%-18s %-45s %s" % (c.id, c.name, "TESTED" if c.tested else "untested"))
    else:
        from .server import serve
        serve(getattr(args, "host", "127.0.0.1"), getattr(args, "port", 8770))
    return 0


if __name__ == "__main__":
    sys.exit(main())
