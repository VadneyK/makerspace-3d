"""Builders for synthetic Bambu artifacts: G-code with the X1C start routine,
project 3MFs, and a fake Bambu Studio profile tree. Shared by the pytest
suite and tools/dry_run.py so every command can be exercised on a machine
without Bambu Studio or a printer."""
import json
import os
import zipfile

# Keep the fake start routine in the same shape as Bambu's: the executed
# lines check_gcode looks for, padded past the 10,000 char floor that
# bambu_presets.check_machine enforces.
START_LINES = [
    ";===== machine: X1-{nozzle} =========================",
    "M1002 gcode_claim_action : 14",
    "M620 S0A",
    "M621 S0A",
    "M976 S3 P2",
    "M412 S1",
    "M190 S{bed}",
    "M109 S{temp}",
]


def start_gcode(nozzle=0.4, bed=55, temp=220, pad=True):
    s = "\n".join(START_LINES).format(nozzle=f"{nozzle:g}", bed=bed, temp=temp) + "\n"
    if pad:
        s += ";" + "=" * 78 + "\n"
        s += "".join(f"; pad line {i:05d} keeps this above the 10000 char floor\n" for i in range(230))
    return s


def body_gcode(layers=3, lh=0.2, square=(60.0, 60.0, 180.0, 180.0), tools=(0,), extra_lines=()):
    """A few layers of a square outline, alternating tools per layer."""
    x0, y0, x1, y1 = square
    out = ["; settings dump: M976 and M620 quoted here must be ignored", "; M620 S9A"]
    for n in range(1, layers + 1):
        out.append("; CHANGE_LAYER")
        out.append(f"; Z_HEIGHT: {n * lh:.2f}")
        out.append(f"G1 Z{n * lh:.2f} F600")
        out.append(f"T{tools[(n - 1) % len(tools)]}")
        out.append(f"G0 X{x0} Y{y0}")
        for x, y in ((x1, y0), (x1, y1), (x0, y1), (x0, y0)):
            out.append(f"G1 X{x} Y{y} E0.5 F3000")
        out.extend(extra_lines if n == 1 else ())
    return "\n".join(out) + "\n"


def gcode(nozzle=0.4, bed=55, temp=220, drop=(), **body):
    """Full plate G-code: start routine (minus any `drop` keywords) plus body."""
    head = "\n".join(ln for ln in start_gcode(nozzle, bed, temp).split("\n")
                     if not any(d in ln for d in drop))
    return head + "\n" + body_gcode(**body)


def project_settings(nozzle=0.4, plate="Textured PEI Plate", filaments=None, **over):
    """A project_settings.config in the shape Bambu Studio's CLI writes.
    filaments: list of (type, preset name, first-layer nozzle C, other-layers
    nozzle C, bed C on PEI plates, bed C on the Cool Plate)."""
    filaments = filaments or [("PLA", "Bambu PLA Basic @BBL X1C", 220, 220, 55, 35)]
    n = len(filaments)
    ps = {
        "printer_settings_id": f"Bambu Lab X1 Carbon {nozzle:g} nozzle",
        "print_settings_id": "0.20mm Standard @BBL X1C",
        "nozzle_diameter": [f"{nozzle:g}"],
        "curr_bed_type": plate,
        "filament_type": [f[0] for f in filaments],
        "filament_settings_id": [f[1] for f in filaments],
        "nozzle_temperature_initial_layer": [str(f[2]) for f in filaments],
        "nozzle_temperature": [str(f[3]) for f in filaments],
        "hot_plate_temp_initial_layer": [str(f[4]) for f in filaments],
        "hot_plate_temp": [str(f[4]) for f in filaments],
        "textured_plate_temp_initial_layer": [str(f[4]) for f in filaments],
        "textured_plate_temp": [str(f[4]) for f in filaments],
        "cool_plate_temp_initial_layer": [str(f[5]) for f in filaments],
        "cool_plate_temp": [str(f[5]) for f in filaments],
        "eng_plate_temp_initial_layer": ["0"] * n,
        "supertack_plate_temp_initial_layer": [str(f[5]) for f in filaments],
        "filament_colour": ["#000000"] * n,
        "enable_support": "0",
        "support_type": "normal(auto)",
        "brim_type": "no_brim",
        "initial_layer_print_height": "0.2",
        "initial_layer_line_width": "0.5",
        "layer_height": "0.2",
        "enable_prime_tower": "1",
        "different_settings_to_system": ["wall_loops;top_shell_layers", "", ""],
        "machine_start_gcode": start_gcode(nozzle),
        "wipe_tower_x": ["165"],
        "wipe_tower_y": ["220"],
    }
    ps.update(over)
    return ps


def model_settings(objects=None, plates=None):
    """model_settings.config XML. objects: {id: {key: value}}; plates: [{key: value}]."""
    objects = objects or {"2": {"name": "part_BLACK.stl", "extruder": "1"}}
    plates = plates or [{"plater_id": "1", "plater_name": "Plate 1"}]
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    for oid, meta in objects.items():
        out.append(f'  <object id="{oid}">')
        for k, v in meta.items():
            out.append(f'    <metadata key="{k}" value="{v}"/>')
        out.append("  </object>")
    for p in plates:
        out.append("  <plate>")
        for k, v in p.items():
            out.append(f'    <metadata key="{k}" value="{v}"/>')
        out.append("  </plate>")
    out.append("</config>")
    return "\n".join(out) + "\n"


def slice_info(plates):
    """slice_info.config for [(seconds, {filament id: grams}), ...]."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    for secs, grams in plates:
        out.append("  <plate>")
        out.append(f'    <metadata key="prediction" value="{secs}"/>')
        for fid, g in grams.items():
            out.append(f'    <filament id="{fid}" type="PLA" color="#000000" used_m="1.0" used_g="{g}"/>')
        out.append("  </plate>")
    out.append("</config>")
    return "\n".join(out) + "\n"


def write_3mf(path, ps=None, ms=None, gcodes=None, info=None, extra=None):
    """Write a minimal project 3MF. gcodes: {plate number: gcode text}."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("3D/3dmodel.model", '<?xml version="1.0"?><model/>')
        if ps is not None:
            z.writestr("Metadata/project_settings.config", json.dumps(ps, indent=4))
        if ms is not None:
            z.writestr("Metadata/model_settings.config", ms)
        for n, g in (gcodes or {}).items():
            z.writestr(f"Metadata/plate_{n}.gcode", g)
        if info is not None:
            z.writestr("Metadata/slice_info.config", info)
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return path


def fake_profiles(root, start_len_ok=True):
    """A Bambu-Studio-shaped profile tree: machine, process and filament
    presets chained with `inherits`, and the sibling `template` files that
    hold the machine G-code (which no inherits chain points to)."""
    m = os.path.join(root, "machine")
    p = os.path.join(root, "process")
    f = os.path.join(root, "filament")
    for d in (m, p, f):
        os.makedirs(d, exist_ok=True)
    dump = lambda d, name, obj: json.dump(obj, open(os.path.join(d, name + ".json"), "w"))  # noqa: E731
    dump(m, "fdm_machine_common", {"name": "fdm_machine_common", "machine_start_gcode": "G28\nM109 S205\n",
                                   "bed_exclude_area": ["0x0", "18x0", "18x28", "0x28"]})
    dump(m, "Bambu Lab X1 Carbon 0.4 nozzle", {"name": "Bambu Lab X1 Carbon 0.4 nozzle", "inherits": "fdm_machine_common",
                                               "nozzle_diameter": ["0.4"], "printer_model": "Bambu Lab X1 Carbon"})
    dump(m, "Bambu Lab X1 Carbon 0.4 nozzle template machine_start_gcode",
         {"machine_start_gcode": start_gcode(0.4, pad=start_len_ok), "printer_notes": "ignored"})
    dump(m, "Bambu Lab X1 Carbon 0.4 nozzle template change_filament_gcode",
         {"change_filament_gcode": "M620 S[next_extruder]A\nM621 S[next_extruder]A\n"})
    dump(m, "Bambu Lab X1 Carbon 0.2 nozzle", {"name": "Bambu Lab X1 Carbon 0.2 nozzle", "inherits": "fdm_machine_common",
                                               "nozzle_diameter": ["0.2"]})
    dump(p, "fdm_process_common", {"name": "fdm_process_common", "wall_loops": "2", "sparse_infill_density": "15%"})
    dump(p, "0.20mm Standard @BBL X1C", {"name": "0.20mm Standard @BBL X1C", "inherits": "fdm_process_common",
                                         "layer_height": "0.2", "compatible_printers": ["Bambu Lab X1 Carbon 0.4 nozzle"]})
    dump(f, "fdm_filament_common", {"name": "fdm_filament_common", "filament_colour": ["#808080"], "fan_min_speed": ["100"]})
    dump(f, "fdm_filament_pla", {"name": "fdm_filament_pla", "inherits": "fdm_filament_common", "filament_type": ["PLA"],
                                 "nozzle_temperature": ["220"]})
    dump(f, "Bambu PLA Basic @base", {"name": "Bambu PLA Basic @base", "inherits": "fdm_filament_pla", "filament_vendor": ["Bambu Lab"]})
    dump(f, "Bambu PLA Basic @BBL X1C", {"name": "Bambu PLA Basic @BBL X1C", "inherits": "Bambu PLA Basic @base",
                                         "compatible_printers": ["Bambu Lab X1 Carbon 0.4 nozzle"]})
    dump(f, "Bambu PLA Silk+ @BBL X1C", {"name": "Bambu PLA Silk+ @BBL X1C", "inherits": "fdm_filament_pla",
                                         "nozzle_temperature": ["230"], "filament_max_volumetric_speed": ["12"]})
    dump(f, "broken", "not a preset at all")
    return root
