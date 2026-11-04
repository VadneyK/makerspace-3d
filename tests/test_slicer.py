"""tools/slicer.py: the check_gcode safety gate, check_motion, slice_report,
add_height_ranges, build_list and slot_of, all without Bambu Studio."""
import json
import zipfile

import pytest

import slicer
import synthetic as syn


# ---- check_motion ---------------------------------------------------------

def test_clean_body_passes():
    assert slicer.check_motion(syn.body_gcode()) == []


def test_extrusion_off_the_bed_is_refused():
    body = syn.body_gcode(extra_lines=["G1 X300 Y100 E0.5"])
    problems = slicer.check_motion(body)
    assert any("off the bed" in p for p in problems)


def test_travel_moves_off_the_bed_are_not_extrusion():
    body = syn.body_gcode(extra_lines=["G0 X300 Y100", "G1 X-5 Y100 F3000"])
    assert slicer.check_motion(body) == []


def test_lidar_marker_is_refused():
    body = syn.body_gcode(extra_lines=["G1 X10 Y10 E0.5"])
    assert any("lidar marker" in p for p in slicer.check_motion(body))


def test_first_layer_over_purge_lines_is_refused():
    body = syn.body_gcode(square=(60.0, 5.0, 180.0, 180.0))
    problems = slicer.check_motion(body)
    assert any("purge lines" in p and "Y5.0" in p for p in problems)


def test_second_layer_may_go_below_y14():
    body = "\n".join(["; CHANGE_LAYER", "G1 Z0.2", "G0 X60 Y60", "G1 X180 Y60 E0.5",
                      "; CHANGE_LAYER", "G1 Z0.4", "G0 X60 Y60", "G1 X60 Y5 E0.5"])
    assert slicer.check_motion(body) == []


@pytest.mark.parametrize("line,expect", [
    ("M104 S150", "nozzle 150 C"),
    ("M109 S260", "nozzle 260 C"),
    ("M140 S80", "bed 80 C"),
    ("M190 S20", "bed 20 C"),
    ("G1 Z251 F600", "Z 251"),
])
def test_temperature_and_height_windows(line, expect):
    body = syn.body_gcode(extra_lines=[line])
    assert expect in slicer.check_motion(body)


def test_color_change_flush_may_go_outside_the_bed():
    # Bambu purges into the chute at X-less positions between M620 and M621
    body = syn.body_gcode(extra_lines=["M620 S1A", "G1 X-20 Y250 E5", "M621 S1A"])
    assert slicer.check_motion(body) == []


def test_temperature_zero_is_ignored():
    body = syn.body_gcode(extra_lines=["M104 S0", "M140 S0"])
    assert slicer.check_motion(body) == []


# ---- check_gcode ----------------------------------------------------------

def test_good_gcode_passes():
    slicer.check_gcode(syn.gcode(), "plate_1")


@pytest.mark.parametrize("drop,name", [
    ("M620 S0A", "AMS filament load"),
    ("M976", "void printing detection"),
    ("M412", "runout detection"),
    ("M1002", "nozzle wipe"),
    ("M190", "bed wait"),
    ("M109", "first-layer nozzle temp"),
])
def test_missing_start_routine_step_is_refused(drop, name):
    with pytest.raises(RuntimeError) as e:
        slicer.check_gcode(syn.gcode(drop=(drop,)), "plate_1")
    assert name in str(e.value) and "plate_1" in str(e.value)


def test_quoted_settings_dump_does_not_count_as_executed():
    g = syn.gcode(drop=("M976",))
    g = g.replace("; CHANGE_LAYER", "; M976 S3 P2 (quoted in the settings dump)\n; CHANGE_LAYER", 1)
    with pytest.raises(RuntimeError, match="void printing detection"):
        slicer.check_gcode(g, "p")


def test_first_layer_temperature_outside_pla_window_is_refused():
    with pytest.raises(RuntimeError, match="first-layer nozzle temp"):
        slicer.check_gcode(syn.gcode(temp=245), "tough+")   # PLA Tough+ preset: see FILAMENTS.md


def test_unsafe_body_is_refused_with_the_reason():
    g = syn.gcode(extra_lines=["G1 X300 Y100 E0.5"])
    with pytest.raises(RuntimeError, match="unsafe print body.*off the bed"):
        slicer.check_gcode(g, "p")


# ---- slice_report ---------------------------------------------------------

def test_slice_report_reads_hours_grams_layers_and_heights(tmp_path):
    g = syn.gcode(layers=4, lh=0.2)
    g = g.replace("; Z_HEIGHT: 0.80", "; Z_HEIGHT: 0.90")   # one 0.1 step on top
    path = syn.write_3mf(tmp_path / "p.3mf", gcodes={1: g}, info=syn.slice_info([(7200, {1: 12.5, 3: 0.4})]))
    rep = slicer.slice_report(str(path))
    assert rep == [dict(hours=2.0, grams={1: 12.5, 3: 0.4}, layers=4, heights={0.2: 3, 0.3: 1})]


def test_slice_report_runs_the_gate_on_every_plate(tmp_path):
    bad = syn.gcode(drop=("M976",))
    path = syn.write_3mf(tmp_path / "p.3mf", gcodes={1: syn.gcode(), 2: bad},
                         info=syn.slice_info([(60, {1: 1.0}), (60, {1: 1.0})]))
    with pytest.raises(RuntimeError, match="plate_2.gcode: start G-code missing"):
        slicer.slice_report(str(path))


def test_slice_report_without_gcode_reports_time_only(tmp_path):
    path = syn.write_3mf(tmp_path / "p.3mf", info=syn.slice_info([(3600, {2: 3.0})]))
    assert slicer.slice_report(str(path)) == [dict(hours=1.0, grams={2: 3.0}, layers=None, heights=None)]


# ---- add_height_ranges ----------------------------------------------------

def test_add_height_ranges_writes_xml_and_merges_settings(tmp_path):
    src = syn.write_3mf(tmp_path / "in.3mf", ps=syn.project_settings(), ms=syn.model_settings(),
                        extra={"Metadata/layer_config_ranges.xml": "<objects>stale</objects>"})
    out = slicer.add_height_ranges(str(src), {2: [(0, 0.4, {"layer_height": "0.08"}), (0.4, 30, {"layer_height": "0.2"})]},
                                   str(tmp_path / "out.3mf"), settings={"wipe_tower_x": ["150"]})
    with zipfile.ZipFile(out) as z:
        xml = z.read("Metadata/layer_config_ranges.xml").decode()
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        assert z.namelist().count("Metadata/layer_config_ranges.xml") == 1
    assert '<object id="2">' in xml
    assert '<range min_z="0" max_z="0.4">' in xml and '<option opt_key="layer_height">0.08</option>' in xml
    assert "stale" not in xml
    assert cfg["wipe_tower_x"] == ["150"] and cfg["curr_bed_type"] == "Textured PEI Plate"


# ---- build_list and slot_of -----------------------------------------------

def test_slot_of_reads_the_color_suffix():
    assert slicer.slot_of("/x/01_plate_BLACK.stl") == 1
    assert slicer.slot_of("base_JADE-WHITE.stl") == 2
    assert slicer.slot_of("letters_SILK-GOLD.stl") == 3
    with pytest.raises(KeyError):
        slicer.slot_of("letters_PURPLE.stl")


def test_build_list_centers_pieces_and_names_slots(tmp_path):
    trimesh = pytest.importorskip("trimesh")
    box = trimesh.creation.box((20, 10, 4))
    box.apply_translation((100, 100, 50))        # floating, off center
    cap = trimesh.creation.box((20, 10, 1))
    cap.apply_translation((100, 100, 52.5))
    piece = slicer.piece([(box, "base_BLACK"), (cap, "top_SILK-GOLD")], (128, 128),
                         print_params={"wall_loops": "4"}, height_ranges=[{"min_z": 0, "max_z": 1}])
    path = slicer.build_list([("Plate 1", [piece], (165, 220))], str(tmp_path))
    data = json.load(open(path))
    plate = data["plates"][0]
    assert plate["plate_name"] == "Plate 1" and plate["plate_params"] == {"wipe_tower_x": "165", "wipe_tower_y": "220"}
    objs = plate["objects"]
    assert [o["filaments"] for o in objs] == [[1], [3]]
    assert all(o["assemble_index"] == [1] and o["print_params"] == {"wall_loops": "4"} for o in objs)
    assert objs[0]["height_ranges"] == [{"min_z": 0, "max_z": 1}]
    base = trimesh.load(objs[0]["path"])
    top = trimesh.load(objs[1]["path"])
    assert base.bounds[0][2] == pytest.approx(0.0)            # dropped to the bed
    assert top.bounds[1][2] == pytest.approx(5.0)             # shared frame kept
    assert (base.bounds[0][:2] + base.bounds[1][:2]) / 2 == pytest.approx((128, 128))
