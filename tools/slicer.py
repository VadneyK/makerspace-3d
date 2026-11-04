"""Drive Bambu Studio's CLI with an assemble list: several plates, each plate a
set of colored multi-part objects, optional per-object settings and per-height
layer ranges. Returns Bambu's own slice report (time and grams per filament).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = os.path.join(HERE, "presets")
BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
SLOT = {"BLACK": 1, "JADE-WHITE": 2, "SILK-GOLD": 3}

NOZZLE = {
    0.4: ("Bambu Lab X1 Carbon 0.4 nozzle.json",
          ["slot1 PLA Basic Black.json", "slot2 PLA Basic Jade White.json", "slot3 PLA Silk+ Gold.json"]),
    0.2: ("Bambu Lab X1 Carbon 0.2 nozzle.json",
          ["n02 slot1 PLA Basic Black.json", "n02 slot2 PLA Basic Jade White.json", "n02 slot3 PLA Silk+ Gold.json"]),
}


# Same Bambu presets, different display colors, for the green set. The names and
# settings are untouched, only filament_colour, so Bambu Studio maps each slot to
# whatever spool is loaded. Slot 1 is the body color: Black, or Deep Green.
PALETTE_02 = {"black": None,
              "green": ["green slot1 PLA Basic Deep Green.json", "green slot2 PLA Basic Jade White.json",
                        "green slot3 PLA Silk+ Gold.json"]}


def slot_of(path):
    return SLOT[os.path.splitext(os.path.basename(path))[0].rsplit("_", 1)[1]]


def piece(parts, center_xy, print_params=None, height_ranges=None):
    """One object on a plate: a list of (mesh, stl_name) parts that keep their
    shared frame, placed with its footprint centered at center_xy."""
    return dict(parts=parts, center=center_xy, print_params=print_params or {},
                height_ranges=height_ranges or [])


def build_list(plates, tmp):
    """plates: [(plate_name, [piece, ...], tower_xy)] -> assemble_list.json path."""
    out = {"plates": []}
    idx = 0
    for pname, pieces, tower in plates:
        objs = []
        for pc in pieces:
            idx += 1
            meshes = [m for m, _ in pc["parts"]]
            lo = [min(m.bounds[0][i] for m in meshes) for i in range(3)]
            hi = [max(m.bounds[1][i] for m in meshes) for i in range(3)]
            dx = pc["center"][0] - (lo[0] + hi[0]) / 2
            dy = pc["center"][1] - (lo[1] + hi[1]) / 2
            for m, name in pc["parts"]:
                mm = m.copy()
                mm.apply_translation((dx, dy, -lo[2]))
                p = os.path.join(tmp, f"{idx:02d}_{name}.stl")
                mm.export(p)
                o = {"path": p, "count": 1, "filaments": [slot_of(name)], "assemble_index": [idx],
                     "pos_x": [0.0], "pos_y": [0.0], "pos_z": [0.0]}
                if pc["print_params"]:
                    o["print_params"] = pc["print_params"]
                if pc["height_ranges"]:
                    o["height_ranges"] = pc["height_ranges"]
                objs.append(o)
        out["plates"].append({"plate_name": pname, "need_arrange": False, "objects": objs,
                              "plate_params": {"wipe_tower_x": f"{tower[0]}", "wipe_tower_y": f"{tower[1]}"}})
    path = os.path.join(tmp, "assemble_list.json")
    json.dump(out, open(path, "w"), indent=1)
    return path


def run(plates, process, nozzle=0.4, out_3mf=None, slice_it=True, keep=None, palette="black"):
    machine, fils = NOZZLE[nozzle]
    if PALETTE_02[palette]:
        assert nozzle == 0.4, "green palette presets are for the 0.4 nozzle"
        fils = PALETTE_02[palette]
    tmp = tempfile.mkdtemp(prefix="bbl_")
    try:
        alist = build_list(plates, tmp)
        name = "out.3mf"
        cmd = [BAMBU, "--debug", "1", "--load-settings", f"{machine};{process}",
               "--load-filaments", ";".join(fils), "--load-assemble-list", alist,
               "--outputdir", tmp, "--export-3mf", name]
        if slice_it:
            cmd += ["--slice", "0"]
        r = subprocess.run(cmd, cwd=PRESETS, capture_output=True, text=True)
        res = os.path.join(tmp, "result.json")
        info = json.load(open(res)) if os.path.exists(res) else {}
        if r.returncode != 0:
            raise RuntimeError(f"exit {r.returncode}: {info.get('error_string')} | {r.stdout[-1500:]}")
        path = os.path.join(tmp, name)
        report = slice_report(path) if slice_it else None
        if out_3mf:
            shutil.copy2(path, out_3mf)
        if keep:
            shutil.copy2(path, keep)
        return report
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_gcode(g, label):
    """The printed body must come after Bambu's own start routine. On 2026-09-24
    the generic fdm_machine_common start G-code shipped instead (see
    bambu_presets.templates) and hotends blobbed."""
    body = g.find("; CHANGE_LAYER")
    # executed lines only: the "; key = value" settings dump quotes the templates
    head = "\n".join(ln for ln in g[:body].split("\n") if not ln.startswith("; "))
    need = {"AMS filament load": r"^M620 S\d+A", "void printing detection": r"^M976 S3 P2",
            "runout detection": r"^M412 S1", "nozzle wipe": r"^M1002 gcode_claim_action : 14",
            "bed wait": r"^M190 S\d+", "first-layer nozzle temp": r"^M109 S2[1-3]\d"}
    missing = [k for k, p in need.items() if not re.search(p, head, re.M)]
    if missing:
        raise RuntimeError(f"{label}: start G-code missing {missing}")
    problems = check_motion(g[body:])
    if problems:
        raise RuntimeError(f"{label}: unsafe print body: {problems}")


# X1C geometry (Bambu Lab X1 Carbon machine preset and its start G-code)
BED = 256.0
EXCLUDE = (18.0, 28.0)        # bed_exclude_area: front-left lidar calibration marker
PURGE_STRIP_Y = 14.0          # start G-code draws its purge and flow-calibration lines at Y 0 to 12
MAX_Z = 250.0
NOZZLE_C = (190, 240)         # PLA Basic and PLA Silk+ ranges
BED_C = (35, 65)


def check_motion(body):
    """Walk the printed body (after the start routine) and refuse anything that
    can hurt the printer or wreck the first layer: extrusion off the bed or on
    the lidar marker, a first layer on top of the start purge lines, a hot end
    or bed outside the PLA window, or Z near the top of the frame."""
    x = y = z = 0.0
    layer = 0
    first_min_y = BED
    out = set()
    swap = False              # inside Bambu's color-change routine (M620 ... M621): it purges into the chute
    for ln in body.split("\n"):
        if ln.startswith("; CHANGE_LAYER"):
            layer += 1
            continue
        if not ln or ln[0] == ";":
            continue
        cmd = ln.split(";")[0].split()
        if not cmd:
            continue
        op = cmd[0]
        args = {a[0]: a[1:] for a in cmd[1:] if len(a) > 1}
        if op == "M620" and "S" in args:
            swap = True
        elif op == "M621":
            swap = False
        if op in ("M104", "M109") and "S" in args:
            t = float(args["S"])
            if t and not NOZZLE_C[0] <= t <= NOZZLE_C[1] + 10:   # color changes flush 10 C hotter
                out.add(f"nozzle {t:g} C")
        elif op in ("M140", "M190") and "S" in args:
            t = float(args["S"])
            if t and not BED_C[0] <= t <= BED_C[1]:
                out.add(f"bed {t:g} C")
        elif op in ("G0", "G1", "G2", "G3"):
            x = float(args.get("X", x)); y = float(args.get("Y", y)); z = float(args.get("Z", z))
            if z > MAX_Z:
                out.add(f"Z {z:g}")
            if op != "G0" and not swap and float(args.get("E", 0) or 0) > 0:
                if not (0 <= x <= BED and 0 <= y <= BED):
                    out.add(f"extrudes off the bed at X{x:g} Y{y:g} Z{z:g}")
                    continue
                if x < EXCLUDE[0] and y < EXCLUDE[1]:
                    out.add(f"extrudes on the lidar marker at X{x:g} Y{y:g}")
                if layer == 1:
                    first_min_y = min(first_min_y, y)
    if first_min_y < PURGE_STRIP_Y:
        out.add(f"first layer reaches Y{first_min_y:.1f}, over the start purge lines (keep Y >= {PURGE_STRIP_Y})")
    return sorted(out)


def slice_report(path):
    """Per plate: hours, grams per filament slot, layer count and heights used."""
    plates = []
    with zipfile.ZipFile(path) as z:
        info = z.read("Metadata/slice_info.config").decode()
        names = z.namelist()
        gcodes = sorted(n for n in names if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))
        blocks = re.findall(r"<plate>(.*?)</plate>", info, re.S)
        for i, b in enumerate(blocks):
            pred = re.search(r'key="prediction" value="(\d+)"', b)
            fil = re.findall(r'<filament id="(\d+)"[^>]*used_g="([\d.]+)"', b)
            layers = heights = None
            if i < len(gcodes):
                g = z.read(gcodes[i]).decode(errors="ignore")
                check_gcode(g, gcodes[i])
                zs = sorted(set(round(float(v), 3) for v in re.findall(r"^; Z_HEIGHT: ([\d.]+)", g, re.M)))
                layers = len(zs)
                steps = [round(b2 - a2, 3) for a2, b2 in zip([0.0] + zs[:-1], zs)]
                heights = {h: steps.count(h) for h in sorted(set(steps))}
            plates.append(dict(hours=int(pred.group(1)) / 3600 if pred else None,
                               grams={int(k): float(v) for k, v in fil}, layers=layers, heights=heights))
    return plates


def load(stem):
    import trimesh   # only the mesh helpers need it; check_gcode and the reports do not
    return trimesh.load(os.path.join(HERE, "stl", stem + ".stl"))


def add_height_ranges(path_3mf, ranges_by_object, out_path, settings=None):
    """Write Bambu's Height Range Modifier block (Metadata/layer_config_ranges.xml)
    into a CLI-exported 3MF. ranges_by_object: {object_number(1-based): [(min_z,
    max_z, {opt_key: value})]}. Bambu Studio shows these as height-range
    modifiers in the object list, so the mentor can see and edit them."""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<objects>"]
    for oid, ranges in sorted(ranges_by_object.items()):
        lines.append(f' <object id="{oid}">')
        for lo, hi, opts in ranges:
            lines.append(f'  <range min_z="{lo:g}" max_z="{hi:g}">')
            for k, v in opts.items():
                lines.append(f'   <option opt_key="{k}">{v}</option>')
            lines.append("  </range>")
        lines.append(" </object>")
    lines.append("</objects>")
    xml = "\n".join(lines) + "\n"
    with zipfile.ZipFile(path_3mf) as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "Metadata/layer_config_ranges.xml":
                continue
            data = zin.read(item.filename)
            if item.filename == "Metadata/project_settings.config" and settings:
                cfg = json.loads(data)
                cfg.update(settings)
                data = json.dumps(cfg, indent=4).encode()
            zout.writestr(item, data)
        zout.writestr("Metadata/layer_config_ranges.xml", xml)
    return out_path


def slice_3mf(path_3mf, keep=None):
    """Slice an existing project 3MF with its own embedded settings."""
    tmp = tempfile.mkdtemp(prefix="bbl_")
    try:
        cmd = [BAMBU, "--debug", "1", "--slice", "0", "--outputdir", tmp, "--export-3mf", "out.3mf", path_3mf]
        r = subprocess.run(cmd, capture_output=True, text=True)
        res = os.path.join(tmp, "result.json")
        info = json.load(open(res)) if os.path.exists(res) else {}
        if r.returncode != 0:
            raise RuntimeError(f"exit {r.returncode}: {info.get('error_string')} | {r.stdout[-1500:]}")
        out = os.path.join(tmp, "out.3mf")
        if keep:
            shutil.copy2(out, keep)
        return slice_report(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
