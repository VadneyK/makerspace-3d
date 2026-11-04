"""Offline pre-print check of a Bambu Studio project 3MF. No Bambu Studio
needed: it reads the settings the 3MF carries, compares them with Bambu's
published material limits (skills/3d-print-design/FILAMENTS.md, sources
listed there) and the maker space rules (PRINTER_SETUP.md), and runs the
check_gcode safety gate on every sliced plate it finds.

    python3 preflight.py file.3mf [--plate-installed "Textured PEI Plate"]
                                  [--nozzle 0.4] [--json]

Exit code 1 when any check fails, 0 otherwise. Warnings do not fail.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slicer  # noqa: E402

# Bambu's bed type names (curr_bed_type) and the preset keys they read.
PLATE_KEY = {
    "Cool Plate": "cool_plate_temp",
    "Engineering Plate": "eng_plate_temp",
    "High Temp Plate": "hot_plate_temp",
    "Textured PEI Plate": "textured_plate_temp",
    "Supertack Plate": "supertack_plate_temp",
}

# Limits per filament_type, from FILAMENTS.md (Bambu material table and the
# X1C presets). bed: {plate: (lo, hi)} or None when Bambu says "not
# recommended"; nozzle: wiki range in C.
LIMITS = {
    "PLA": {"nozzle": (190, 250),
            "bed": {"Cool Plate": (35, 45), "High Temp Plate": (45, 65), "Textured PEI Plate": (45, 65),
                    "Engineering Plate": (45, 65), "Supertack Plate": (35, 45)}},
    "PETG": {"nozzle": (230, 270),
             "bed": {"Cool Plate": None, "High Temp Plate": (60, 80), "Textured PEI Plate": (60, 80),
                     "Engineering Plate": (60, 80), "Supertack Plate": (60, 80)}},
    "ABS": {"nozzle": (240, 280),
            "bed": {"Cool Plate": None, "High Temp Plate": (90, 100), "Textured PEI Plate": (90, 100),
                    "Engineering Plate": (90, 100), "Supertack Plate": None}},
}
# Preset names that need a hotter nozzle than the PLA family range allows.
HOT_PLA = ("Tough+",)


class Report:
    def __init__(self):
        self.rows = []

    def add(self, area, check, status, note=""):
        self.rows.append({"area": area, "check": check, "status": status, "note": str(note)})

    def ok(self, area, check, note=""):
        self.add(area, check, "pass", note)

    def warn(self, area, check, note=""):
        self.add(area, check, "warn", note)

    def fail(self, area, check, note=""):
        self.add(area, check, "fail", note)

    @property
    def failed(self):
        return any(r["status"] == "fail" for r in self.rows)

    def text(self):
        w = [max(len(r[k]) for r in self.rows + [{"area": "Area", "check": "Check", "status": "Status", "note": "Note"}])
             for k in ("area", "check", "status", "note")]
        lines = ["| " + " | ".join(h.ljust(n) for h, n in zip(("Area", "Check", "Status", "Note"), w)) + " |",
                 "|" + "|".join("-" * (n + 2) for n in w) + "|"]
        for r in self.rows:
            lines.append("| " + " | ".join(r[k].ljust(n) for k, n in zip(("area", "check", "status", "note"), w)) + " |")
        lines.append("Verdict: " + ("NO-GO" if self.failed else "GO"))
        return "\n".join(lines)


def _list(v):
    return v if isinstance(v, list) else [v]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def read_3mf(path):
    """Return (project_settings dict, model_settings XML root or None, plate gcodes {name: text})."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ps = json.loads(z.read("Metadata/project_settings.config")) if "Metadata/project_settings.config" in names else {}
        ms = ET.fromstring(z.read("Metadata/model_settings.config")) if "Metadata/model_settings.config" in names else None
        gcodes = {n: z.read(n).decode(errors="ignore") for n in sorted(names)
                  if re.fullmatch(r"Metadata/plate_\d+\.gcode", n)}
    return ps, ms, gcodes


def plate_types(ps, ms):
    """Plate type per plate: the per-plate bed_type in model_settings wins over curr_bed_type."""
    default = ps.get("curr_bed_type", "")
    out = {}
    if ms is not None:
        for plate in ms.iter("plate"):
            meta = {m.get("key"): m.get("value") for m in plate.findall("metadata")}
            pid = meta.get("plater_id") or str(len(out) + 1)
            out[pid] = meta.get("bed_type") or default
    return out or {"1": default}


def object_settings(ms):
    """{object id: {key: value}} from model_settings.config."""
    out = {}
    if ms is None:
        return out
    for obj in ms.iter("object"):
        out[obj.get("id")] = {m.get("key"): m.get("value") for m in obj.findall("metadata")}
    return out


def check(path, plate_installed=None, nozzle=None):
    rep = Report()
    ps, ms, gcodes = read_3mf(path)
    if not ps:
        rep.fail("File", "project_settings.config present", "missing: not a Bambu Studio project 3MF")
        return rep

    # Printer and nozzle
    printer = ps.get("printer_settings_id", "")
    file_nozzle = _num(_list(ps.get("nozzle_diameter", [""]))[0])
    if "X1 Carbon" in printer:
        rep.ok("Nozzle", "Printer preset is an X1 Carbon", printer)
    else:
        rep.fail("Nozzle", "Printer preset is an X1 Carbon", printer or "(none)")
    if nozzle is not None:
        if file_nozzle == nozzle:
            rep.ok("Nozzle", "File nozzle equals installed nozzle", f"{file_nozzle:g} mm")
        else:
            rep.fail("Nozzle", "File nozzle equals installed nozzle", f"file {file_nozzle} mm, printer {nozzle:g} mm")
    else:
        rep.warn("Nozzle", "File nozzle equals installed nozzle", f"file says {file_nozzle} mm; confirm the hotend")
    start = ps.get("machine_start_gcode", "")
    first = start.split("\n", 1)[0].strip()
    want = f";===== machine: X1-{file_nozzle:g}" if file_nozzle else ";===== machine: X1-"
    if first.startswith(want) and "M620" in start and "M976" in start and len(start) >= 10000:
        rep.ok("File", "Start G-code is Bambu's X1C routine", f"{len(start)} chars, {first}")
    else:
        rep.fail("File", "Start G-code is Bambu's X1C routine",
                 f"first line {first!r}, {len(start)} chars (want {want}..., M620, M976, 10000+ chars)")

    # Plates
    plates = plate_types(ps, ms)
    for pid, ptype in sorted(plates.items()):
        if ptype not in PLATE_KEY:
            rep.fail("Plate", f"Plate {pid} type is a Bambu plate name", ptype or "(empty)")
            continue
        if plate_installed:
            if ptype == plate_installed:
                rep.ok("Plate", f"Plate {pid} type equals installed plate", ptype)
            else:
                rep.fail("Plate", f"Plate {pid} type equals installed plate", f"file {ptype}, printer {plate_installed}")
        else:
            rep.warn("Plate", f"Plate {pid} type equals installed plate", f"file says {ptype}; confirm on the printer")
        if file_nozzle == 0.2 and ptype == "Textured PEI Plate":
            rep.warn("Plate", f"Plate {pid}: 0.2 nozzle on textured plate",
                     "PRINTER_SETUP: 0.1 mm first layer drags in the texture, use Smooth PEI (High Temp Plate)")

    # Filaments
    types = _list(ps.get("filament_type", []))
    ids = _list(ps.get("filament_settings_id", []))
    first_t = _list(ps.get("nozzle_temperature_initial_layer", []))
    other_t = _list(ps.get("nozzle_temperature", []))
    used = set()
    for obj in object_settings(ms).values():
        if obj.get("extruder"):
            used.add(int(obj["extruder"]) - 1)
    idx = sorted(used) if used else list(range(len(types)))
    used_types = set()
    for i in idx:
        if i >= len(types):
            continue
        t, name = types[i], ids[i] if i < len(ids) else ""
        used_types.add(t)
        lim = LIMITS.get(t)
        if not lim:
            rep.warn("Filament", f"Slot {i + 1} ({t}) known material", f"{name}: no limits on file for {t}, check FILAMENTS.md")
            continue
        lo, hi = lim["nozzle"]
        if any(h in name for h in HOT_PLA):
            lo, hi = 220, 250
        for label, arr in (("first layer", first_t), ("other layers", other_t)):
            v = _num(arr[i]) if i < len(arr) else None
            if v is None:
                rep.warn("Filament", f"Slot {i + 1} {t} nozzle {label}", "not in file")
            elif lo <= v <= hi:
                rep.ok("Filament", f"Slot {i + 1} {t} nozzle {label}", f"{v:g} C in {lo} to {hi}")
            else:
                rep.fail("Filament", f"Slot {i + 1} {t} nozzle {label}", f"{v:g} C outside Bambu's {lo} to {hi} C")
        for pid, ptype in sorted(plates.items()):
            key = PLATE_KEY.get(ptype)
            if not key:
                continue
            rng = lim["bed"].get(ptype)
            bed = _list(ps.get(key + "_initial_layer", ps.get(key, [])))
            v = _num(bed[i]) if i < len(bed) else None
            label = f"Plate {pid}, slot {i + 1}: {t} bed temp on {ptype}"
            if rng is None:
                rep.fail("Bed", f"Plate {pid}, slot {i + 1}: {t} on {ptype}", "Bambu: not recommended for this material")
            elif v is None or v == 0:
                rep.fail("Bed", label, "0 C: Bambu Studio treats the filament as incompatible")
            elif rng[0] <= v <= rng[1]:
                rep.ok("Bed", label, f"{v:g} C in {rng[0]} to {rng[1]}")
            else:
                rep.warn("Bed", label, f"{v:g} C outside Bambu's {rng[0]} to {rng[1]} C")
        if "Silk" in name and file_nozzle in (0.6, 0.8):
            rep.fail("Nozzle", f"Slot {i + 1} silk on {file_nozzle:g} nozzle", "Bambu: Silk and Silk+ on 0.2 or 0.4 only")
        if "Translucent" in name:
            rep.warn("Filament", f"Slot {i + 1} PETG Translucent dried", "must be dried before every use, desiccant during the print")
        if "Tough+" in name and str(ps.get("enable_support", "0")) == "1":
            rep.warn("Supports", f"Slot {i + 1} Tough+ with supports", "Bambu recommends a dedicated support filament as interface")
    if len(used_types) > 1 and used_types & {"ABS", "PETG"} and "PLA" in used_types:
        rep.fail("Filament", "One bed temperature fits every material on the plate", ", ".join(sorted(used_types)))
    if "ABS" in used_types:
        rep.warn("Filament", "ABS fumes", "enclosed, door closed, ventilate; styrene warning on Bambu's page")

    # Supports, brim, first layer
    sup = str(ps.get("enable_support", "0")) == "1"
    rep.add("Supports", "Supports enabled", "pass", f"{'yes' if sup else 'no'}; type {ps.get('support_type', '?')}" if sup else "no (confirm overhangs were checked)")
    objs = object_settings(ms)
    obj_brim = [o for o, s in objs.items() if s.get("brim_type") and s["brim_type"] != "no_brim"]
    rep.add("Supports", "Brim", "pass", f"project {ps.get('brim_type', '?')}; on {len(obj_brim)} object(s)")
    h0 = _num(ps.get("initial_layer_print_height"))
    w0 = ps.get("initial_layer_line_width", "?")
    rep.add("First layer", "First layer height / line width", "pass", f"{h0} mm / {w0} mm (Bambu's fallback for a marginal first layer: 0.25 / 0.5)")
    heights = {o: s.get("layer_height") for o, s in objs.items() if s.get("layer_height")}
    if len(set(heights.values())) > 1:
        rep.fail("Supports", "Objects share one layer height", f"per-object layer heights {heights} break the prime tower (PRINTER_SETUP)")

    # GUI persistence
    dsts = _list(ps.get("different_settings_to_system", []))
    if any(str(x).strip() for x in dsts):
        rep.ok("File", "different_settings_to_system filled", "GUI keeps the project values")
    else:
        rep.warn("File", "different_settings_to_system filled", "empty: Bambu Studio reloads stock presets on open (PRINTER_SETUP)")

    # Safety gate
    if not gcodes:
        rep.warn("File", "check_gcode on every plate", "no sliced plates in this 3MF; slice first")
    for name, g in gcodes.items():
        try:
            slicer.check_gcode(g, name)
            rep.ok("File", f"check_gcode {name}", "start routine and motion OK")
        except RuntimeError as e:
            rep.fail("File", f"check_gcode {name}", str(e))
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--plate-installed", help='plate on the printer, e.g. "Textured PEI Plate"')
    ap.add_argument("--nozzle", type=float, help="nozzle on the printer in mm")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rep = check(a.path, a.plate_installed, a.nozzle)
    print(json.dumps(rep.rows, indent=1) if a.json else rep.text())
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
