"""Flatten Bambu Studio's bundled X1C presets (they chain via "inherits") into
standalone JSON files the Bambu Studio CLI can load. Output: presets/*.json
"""
import json
import os

PROFILES = "/Applications/BambuStudio.app/Contents/Resources/profiles/BBL"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")


def index(kind):
    idx = {}
    root = os.path.join(PROFILES, kind)
    for dp, _, files in os.walk(root):
        for f in files:
            if f.endswith(".json"):
                p = os.path.join(dp, f)
                try:
                    d = json.load(open(p))
                except Exception:
                    continue
                if "name" in d:
                    idx[d["name"]] = p
    return idx


def templates(path, name):
    """Newer Bambu Studio keeps the machine G-code (start, color change, end,
    timelapse) in sibling files named "<preset> template <key>.json" that no
    "inherits" chain points to. Missing them silently leaves the generic
    fdm_machine_common start G-code: no AMS load, no nozzle wipe before Z
    probing, no first-layer scan, no void-printing detection, 205 C nozzle.
    That shipped on 2026-09-23/24 and blobbed hotends."""
    out = {}
    prefix = name + " template "
    folder = os.path.dirname(path)
    for f in os.listdir(folder):
        if f.startswith(prefix) and f.endswith(".json"):
            t = json.load(open(os.path.join(folder, f)))
            out.update({k: v for k, v in t.items() if k.endswith("gcode")})
    return out


def flatten(kind, name, idx):
    d = json.load(open(idx[name]))
    parent = d.get("inherits")
    base = flatten(kind, parent, idx) if parent else {}
    base.update(d)
    base.update(templates(idx[name], name))
    return base


def check_machine(d):
    """Refuse a machine preset whose start G-code is not Bambu's own."""
    s = d.get("machine_start_gcode", "")
    if "M620" not in s or "M976" not in s or len(s) < 10000:
        raise SystemExit(f"{d.get('name')}: start G-code is not Bambu's X1C routine ({len(s)} chars)")


def make(kind, name, overrides=None, fname=None):
    idx = index(kind)
    d = flatten(kind, name, idx)
    d.pop("inherits", None)
    d["from"] = "system"
    d["is_custom_defined"] = "1"
    d.update(overrides or {})
    if kind == "machine":
        check_machine(d)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, (fname or name) + ".json")
    json.dump(d, open(p, "w"), indent=1)
    return p


PROCESS = {"wall_loops": "4", "top_shell_layers": "7", "bottom_shell_layers": "5",
           "sparse_infill_density": "15%", "sparse_infill_pattern": "gyroid",
           "top_surface_pattern": "concentric", "bottom_surface_pattern": "concentric",
           "wall_generator": "arachne", "enable_support": "0", "enable_prime_tower": "1",
           "brim_type": "no_brim", "flush_into_infill": "1"}


def fil(name, colour, fname):
    return make("filament", name, {"filament_colour": [colour]}, fname)


def main():
    paths = {
        # 0.4 nozzle (recommended)
        "machine": make("machine", "Bambu Lab X1 Carbon 0.4 nozzle"),
        "p04_008": make("process", "0.08mm Extra Fine @BBL X1C", PROCESS, "p04 0.08"),
        "p04_012": make("process", "0.12mm Fine @BBL X1C", PROCESS, "p04 0.12"),
        "p04_016": make("process", "0.16mm Optimal @BBL X1C", PROCESS, "p04 0.16"),
        "p04_020": make("process", "0.20mm Standard @BBL X1C", PROCESS, "p04 0.20"),
        "black": fil("Bambu PLA Basic @BBL X1C", "#000000", "slot1 PLA Basic Black"),
        "white": fil("Bambu PLA Basic @BBL X1C", "#FFFFFF", "slot2 PLA Basic Jade White"),
        "gold": fil("Bambu PLA Silk+ @BBL X1C", "#D4A637", "slot3 PLA Silk+ Gold"),
        # 0.2 nozzle (for comparison only)
        "machine02": make("machine", "Bambu Lab X1 Carbon 0.2 nozzle"),
        "p02_006": make("process", "0.06mm High Quality @BBL X1C 0.2 nozzle", PROCESS, "p02 0.06"),
        "p02_014": make("process", "0.14mm Standard @BBL X1C 0.2 nozzle", PROCESS, "p02 0.14"),
        "black02": fil("Bambu PLA Basic @BBL X1C 0.2 nozzle", "#000000", "n02 slot1 PLA Basic Black"),
        "white02": fil("Bambu PLA Basic @BBL X1C 0.2 nozzle", "#FFFFFF", "n02 slot2 PLA Basic Jade White"),
        "gold02": fil("Bambu PLA Silk+ @BBL X1C 0.2 nozzle", "#D4A637", "n02 slot3 PLA Silk+ Gold"),
    }
    for k, v in paths.items():
        print(k, os.path.basename(v))


if __name__ == "__main__":
    main()
