"""tools/preflight.py: offline pre-print check of a project 3MF."""
import json

import preflight
import synthetic as syn


def _3mf(tmp_path, ps=None, ms=None, gcodes=None, **kw):
    ps = ps if ps is not None else syn.project_settings(**kw)
    ms = ms if ms is not None else syn.model_settings()
    gcodes = {1: syn.gcode()} if gcodes is None else gcodes
    return str(syn.write_3mf(tmp_path / "p.3mf", ps=ps, ms=ms, gcodes=gcodes))


def _status(rep, check_substring):
    rows = [r for r in rep.rows if check_substring in r["check"]]
    assert rows, f"no row matching {check_substring!r} in {[r['check'] for r in rep.rows]}"
    return rows[0]["status"], rows[0]["note"]


def test_stock_pla_file_is_go(tmp_path):
    rep = preflight.check(_3mf(tmp_path), plate_installed="Textured PEI Plate", nozzle=0.4)
    assert not rep.failed
    assert _status(rep, "Start G-code")[0] == "pass"
    assert _status(rep, "check_gcode Metadata/plate_1.gcode")[0] == "pass"
    assert _status(rep, "PLA bed temp on Textured PEI Plate")[0] == "pass"
    assert "GO" in rep.text() and "NO-GO" not in rep.text()


def test_unknown_plate_and_nozzle_only_warn(tmp_path):
    rep = preflight.check(_3mf(tmp_path))
    assert not rep.failed
    assert _status(rep, "equals installed plate")[0] == "warn"
    assert _status(rep, "equals installed nozzle")[0] == "warn"


def test_wrong_nozzle_and_plate_fail(tmp_path):
    rep = preflight.check(_3mf(tmp_path), plate_installed="High Temp Plate", nozzle=0.2)
    assert _status(rep, "equals installed plate") == ("fail", "file Textured PEI Plate, printer High Temp Plate")
    assert _status(rep, "equals installed nozzle")[0] == "fail"


def test_per_plate_bed_type_overrides_project_default(tmp_path):
    ms = syn.model_settings(plates=[{"plater_id": "1", "bed_type": "High Temp Plate"}])
    rep = preflight.check(_3mf(tmp_path, ms=ms, plate="Textured PEI Plate"), plate_installed="High Temp Plate")
    assert _status(rep, "Plate 1 type equals installed plate")[0] == "pass"


def test_petg_on_cool_plate_fails_and_abs_warns_about_fumes(tmp_path):
    fil = [("PETG", "Bambu PETG Basic @BBL X1C", 245, 255, 70, 0), ("ABS", "Bambu ABS @BBL X1C", 260, 270, 90, 0)]
    ms = syn.model_settings(objects={"2": {"extruder": "1"}, "3": {"extruder": "2"}})
    rep = preflight.check(_3mf(tmp_path, ms=ms, plate="Cool Plate", filaments=fil, gcodes={}))
    assert _status(rep, "PETG on Cool Plate")[0] == "fail"
    assert _status(rep, "ABS on Cool Plate")[0] == "fail"
    assert _status(rep, "ABS fumes")[0] == "warn"
    assert _status(rep, "Slot 2 ABS nozzle first layer") == ("pass", "260 C in 240 to 280")


def test_pla_next_to_abs_on_one_plate_fails(tmp_path):
    fil = [("PLA", "Bambu PLA Basic @BBL X1C", 220, 220, 55, 35), ("ABS", "Bambu ABS @BBL X1C", 260, 270, 90, 0)]
    ms = syn.model_settings(objects={"2": {"extruder": "1"}, "3": {"extruder": "2"}})
    rep = preflight.check(_3mf(tmp_path, ms=ms, filaments=fil, gcodes={}))
    assert _status(rep, "One bed temperature fits") == ("fail", "ABS, PLA")


def test_unused_slots_are_not_checked(tmp_path):
    fil = [("PLA", "Bambu PLA Basic @BBL X1C", 220, 220, 55, 35), ("ABS", "Bambu ABS @BBL X1C", 260, 270, 90, 0)]
    ms = syn.model_settings(objects={"2": {"extruder": "1"}})
    rep = preflight.check(_3mf(tmp_path, ms=ms, filaments=fil))
    assert not any("ABS" in r["check"] for r in rep.rows)


def test_tough_plus_uses_its_own_nozzle_range(tmp_path):
    fil = [("PLA", "Bambu PLA Tough+ @BBL X1C", 245, 245, 55, 35)]
    rep = preflight.check(_3mf(tmp_path, filaments=fil, gcodes={}))
    assert _status(rep, "Slot 1 PLA nozzle first layer") == ("pass", "245 C in 220 to 250")
    fil = [("PLA", "Bambu PLA Basic @BBL X1C", 260, 220, 55, 35)]
    rep = preflight.check(_3mf(tmp_path, filaments=fil, gcodes={}))
    assert _status(rep, "Slot 1 PLA nozzle first layer")[0] == "fail"


def test_silk_on_a_big_nozzle_fails(tmp_path):
    fil = [("PLA", "Bambu PLA Silk+ @BBL X1C", 230, 230, 55, 35)]
    rep = preflight.check(_3mf(tmp_path, nozzle=0.6, filaments=fil, gcodes={}))
    assert _status(rep, "silk on 0.6 nozzle")[0] == "fail"


def test_point_two_nozzle_on_textured_plate_warns(tmp_path):
    rep = preflight.check(_3mf(tmp_path, nozzle=0.2, gcodes={}))
    assert _status(rep, "0.2 nozzle on textured plate")[0] == "warn"


def test_generic_start_gcode_fails(tmp_path):
    ps = syn.project_settings(machine_start_gcode="G28\nM109 S205\n")
    rep = preflight.check(_3mf(tmp_path, ps=ps, gcodes={}))
    assert _status(rep, "Start G-code")[0] == "fail"


def test_empty_different_settings_warns(tmp_path):
    ps = syn.project_settings(different_settings_to_system=["", "", ""])
    rep = preflight.check(_3mf(tmp_path, ps=ps, gcodes={}))
    assert _status(rep, "different_settings_to_system")[0] == "warn"


def test_mixed_object_layer_heights_fail(tmp_path):
    ms = syn.model_settings(objects={"2": {"extruder": "1", "layer_height": "0.2"}, "3": {"extruder": "1", "layer_height": "0.12"}})
    rep = preflight.check(_3mf(tmp_path, ms=ms, gcodes={}))
    assert _status(rep, "share one layer height")[0] == "fail"


def test_unsliced_file_warns_and_bad_gcode_fails(tmp_path):
    rep = preflight.check(_3mf(tmp_path, gcodes={}))
    assert _status(rep, "check_gcode on every plate")[0] == "warn"
    rep = preflight.check(_3mf(tmp_path, gcodes={1: syn.gcode(drop=("M976",))}))
    status, note = _status(rep, "check_gcode Metadata/plate_1.gcode")
    assert status == "fail" and "void printing detection" in note


def test_not_a_project_3mf_fails(tmp_path):
    path = str(syn.write_3mf(tmp_path / "bare.3mf"))
    rep = preflight.check(path)
    assert rep.failed and rep.rows[0]["check"] == "project_settings.config present"


def test_main_exit_codes_and_json(tmp_path, capsys):
    path = _3mf(tmp_path)
    assert preflight.main([path, "--plate-installed", "Textured PEI Plate", "--nozzle", "0.4"]) == 0
    assert "Verdict: GO" in capsys.readouterr().out
    assert preflight.main([path, "--nozzle", "0.2", "--json"]) == 1
    rows = json.loads(capsys.readouterr().out)
    assert any(r["status"] == "fail" and "installed nozzle" in r["check"] for r in rows)
