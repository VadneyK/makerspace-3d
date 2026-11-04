"""tools/bambu_presets.py against a fake Bambu Studio profile tree."""
import json
import os

import pytest

import bambu_presets as bp
import synthetic as syn


@pytest.fixture
def tree(tmp_path, monkeypatch):
    root = syn.fake_profiles(str(tmp_path / "BBL"))
    monkeypatch.setattr(bp, "PROFILES", root)
    monkeypatch.setattr(bp, "OUT", str(tmp_path / "presets"))
    return root


def test_index_maps_names_to_paths_and_skips_junk(tree):
    idx = bp.index("filament")
    assert set(idx) == {"fdm_filament_common", "fdm_filament_pla", "Bambu PLA Basic @base",
                        "Bambu PLA Basic @BBL X1C", "Bambu PLA Silk+ @BBL X1C"}
    assert idx["Bambu PLA Basic @BBL X1C"].endswith("Bambu PLA Basic @BBL X1C.json")


def test_flatten_follows_the_inherits_chain_child_wins(tree):
    idx = bp.index("filament")
    d = bp.flatten("filament", "Bambu PLA Silk+ @BBL X1C", idx)
    assert d["fan_min_speed"] == ["100"]                 # from fdm_filament_common
    assert d["filament_type"] == ["PLA"]                 # from fdm_filament_pla
    assert d["nozzle_temperature"] == ["230"]            # child overrides parent's 220


def test_templates_overlay_only_gcode_keys(tree):
    idx = bp.index("machine")
    t = bp.templates(idx["Bambu Lab X1 Carbon 0.4 nozzle"], "Bambu Lab X1 Carbon 0.4 nozzle")
    assert set(t) == {"machine_start_gcode", "change_filament_gcode"}
    assert t["machine_start_gcode"].startswith(";===== machine: X1-0.4")
    assert bp.templates(idx["Bambu Lab X1 Carbon 0.2 nozzle"], "Bambu Lab X1 Carbon 0.2 nozzle") == {}


def test_machine_without_templates_keeps_generic_start_and_is_refused(tree):
    with pytest.raises(SystemExit, match="start G-code is not Bambu's X1C routine"):
        bp.make("machine", "Bambu Lab X1 Carbon 0.2 nozzle")


def test_make_writes_a_standalone_system_preset(tree):
    p = bp.make("machine", "Bambu Lab X1 Carbon 0.4 nozzle")
    d = json.load(open(p))
    assert os.path.basename(p) == "Bambu Lab X1 Carbon 0.4 nozzle.json"
    assert "inherits" not in d
    assert d["from"] == "system" and d["is_custom_defined"] == "1"
    assert d["machine_start_gcode"].startswith(";===== machine: X1-0.4") and "M976" in d["machine_start_gcode"]
    assert d["change_filament_gcode"].startswith("M620")
    assert d["bed_exclude_area"] == ["0x0", "18x0", "18x28", "0x28"]


def test_make_applies_overrides_and_custom_file_name(tree):
    p = bp.make("process", "0.20mm Standard @BBL X1C", bp.PROCESS, "p04 0.20")
    d = json.load(open(p))
    assert os.path.basename(p) == "p04 0.20.json"
    assert d["wall_loops"] == "4" and d["top_shell_layers"] == "7" and d["flush_into_infill"] == "1"
    assert d["compatible_printers"] == ["Bambu Lab X1 Carbon 0.4 nozzle"]   # kept, or the CLI refuses the file
    assert d["layer_height"] == "0.2"


def test_fil_sets_only_the_display_colour(tree):
    p = bp.fil("Bambu PLA Basic @BBL X1C", "#D4A637", "slot3 PLA Silk+ Gold")
    d = json.load(open(p))
    assert d["filament_colour"] == ["#D4A637"]
    assert d["filament_vendor"] == ["Bambu Lab"] and d["nozzle_temperature"] == ["220"]


def test_check_machine_rejects_short_or_generic_start_gcode():
    with pytest.raises(SystemExit):
        bp.check_machine({"name": "x", "machine_start_gcode": "G28\nM620 S0A\nM976 S3 P2\n"})   # too short
    with pytest.raises(SystemExit):
        bp.check_machine({"name": "x", "machine_start_gcode": "M620 S0A\n" + "; pad\n" * 3000})   # no M976
    bp.check_machine({"name": "x", "machine_start_gcode": syn.start_gcode()})


def test_main_writes_the_preset_set_slicer_expects(monkeypatch, capsys):
    import slicer
    calls = []

    def fake_make(kind, name, overrides=None, fname=None):
        calls.append((kind, name, fname or name))
        return os.path.join("presets", (fname or name) + ".json")
    monkeypatch.setattr(bp, "make", fake_make)
    bp.main()
    written = {f + ".json" for _, _, f in calls}
    for nozzle, (machine, fils) in slicer.NOZZLE.items():
        assert machine in written, nozzle
        assert set(fils) <= written, nozzle
    assert [n for k, n, _ in calls if k == "machine"] == ["Bambu Lab X1 Carbon 0.4 nozzle", "Bambu Lab X1 Carbon 0.2 nozzle"]
    assert all(o == bp.PROCESS for k, n, o in [(c[0], c[1], bp.PROCESS) for c in calls if c[0] == "process"])
    assert len(capsys.readouterr().out.splitlines()) == len(calls)
