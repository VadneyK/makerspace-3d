"""Dry run of everything the makerspace-3d plugin exposes, on any machine,
without Bambu Studio, a printer, or network access:

  manifests   .claude-plugin/plugin.json, marketplace.json, .mcp.json parse and agree
  skills      every skills/*/SKILL.md has frontmatter, its links resolve
  dashes      no em or en dash in any tracked text file (house rule)
  imports     tools/slicer.py, bambu_presets.py, gview.py, preflight.py import
  presets     bambu_presets flattens a fake Bambu Studio profile tree and refuses a bad machine preset
  gate        slicer.check_gcode passes a good plate and refuses each broken start routine
  gview       gview.render draws a synthetic plate to PNG
  preflight   preflight.check says GO on a stock PLA file and NO-GO on a wrong plate
  setup       what /makerspace-3d:setup would find here (uv, Bambu Studio, Python, deps); nothing is installed
  bambu       if Bambu Studio is installed, the real CLI prints its help

    python3 tools/dry_run.py [--quiet]

Exit 1 if any check other than the two environment reports fails.
"""
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

RESULTS = []
BAD_DASHES = (chr(0x2014), chr(0x2013))   # em dash, en dash: never in this repo


def report(name, ok, note="", info=False):
    RESULTS.append((name, ok, note, info))


def step(name, fn, info=False):
    try:
        note = fn() or ""
        report(name, True, note, info)
    except Exception as e:   # noqa: BLE001 - a dry run reports, it does not crash
        report(name, False, f"{type(e).__name__}: {e}", info)


def manifests():
    p = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    m = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
    s = json.load(open(os.path.join(ROOT, ".mcp.json")))
    assert [x["name"] for x in m["plugins"]] == [p["name"]], "marketplace and plugin names differ"
    srv = s["mcpServers"]["build123d"]
    assert srv["command"] == "uv" and any(a.startswith("build123d-mcp==") for a in srv["args"])
    return f"plugin {p['name']}; MCP build123d via {srv['command']} {' '.join(srv['args'])}"


def skills():
    found = []
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        path = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        assert m, f"{d}: no frontmatter"
        fm = dict(line.partition(":")[::2] for line in m.group(1).splitlines())
        fm = {k.strip(): v.strip() for k, v in fm.items()}
        assert fm.get("name") == d, f"{d}: frontmatter name {fm.get('name')!r}"
        assert fm.get("description"), f"{d}: no description"
        for dp, _, files in os.walk(os.path.join(ROOT, "skills", d)):
            for f in files:
                if not f.endswith(".md"):
                    continue
                t = open(os.path.join(dp, f), encoding="utf-8").read()
                for target in re.findall(r"\]\(([^)]+)\)", t):
                    if target.startswith(("http", "#", "mailto:")):
                        continue
                    assert os.path.exists(os.path.join(dp, target.split("#")[0])), f"{f}: broken link {target}"
        kind = "command" if fm.get("disable-model-invocation") == "true" else "auto skill"
        found.append(f"{d} ({kind})")
    return ", ".join(found)


def dashes():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    hits = []
    for f in files:
        p = os.path.join(ROOT, f)
        try:
            text = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        hits += [f"{f}:{n}" for n, line in enumerate(text.splitlines(), 1) if any(ch in line for ch in BAD_DASHES)]
    assert not hits, "em or en dash in " + ", ".join(hits)
    return f"{len(files)} tracked files clean"


def imports():
    names = ["slicer", "bambu_presets", "preflight"]
    try:
        import PIL  # noqa: F401
        names.append("gview")
    except ImportError:
        pass
    for n in names:
        importlib.import_module(n)
    return ", ".join(names) + ("" if "gview" in names else " (gview skipped: no pillow)")


def presets():
    import bambu_presets as bp
    import synthetic as syn
    tmp = tempfile.mkdtemp(prefix="dry_")
    try:
        bp.PROFILES = syn.fake_profiles(os.path.join(tmp, "BBL"))
        bp.OUT = os.path.join(tmp, "presets")
        p = bp.make("machine", "Bambu Lab X1 Carbon 0.4 nozzle")
        d = json.load(open(p))
        assert d["machine_start_gcode"].startswith(";===== machine: X1-0.4") and "inherits" not in d
        bp.make("process", "0.20mm Standard @BBL X1C", bp.PROCESS, "p04 0.20")
        bp.fil("Bambu PLA Basic @BBL X1C", "#000000", "slot1 PLA Basic Black")
        try:
            bp.make("machine", "Bambu Lab X1 Carbon 0.2 nozzle")   # no template files: generic start
        except SystemExit as e:
            assert "not Bambu's X1C routine" in str(e)
        else:
            raise AssertionError("a machine preset without Bambu's start routine was accepted")
        return f"3 presets written, generic machine refused ({os.listdir(bp.OUT)})"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gate():
    import slicer
    import synthetic as syn
    slicer.check_gcode(syn.gcode(), "good")
    refused = []
    for drop in ("M620 S0A", "M976", "M412", "M1002", "M190", "M109"):
        try:
            slicer.check_gcode(syn.gcode(drop=(drop,)), drop)
        except RuntimeError:
            refused.append(drop)
    assert len(refused) == 6, f"only refused {refused}"
    for extra, word in ((["G1 X300 Y100 E0.5"], "off the bed"), (["G1 X10 Y10 E0.5"], "lidar"), (["M140 S100"], "bed 100")):
        try:
            slicer.check_gcode(syn.gcode(extra_lines=extra), word)
        except RuntimeError as e:
            assert word in str(e)
        else:
            raise AssertionError(f"body with {extra} was accepted")
    return "good plate passes; 6 start-routine omissions and 3 unsafe bodies refused"


def gview_check():
    import gview
    import synthetic as syn
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix="dry_")
    try:
        path = syn.write_3mf(os.path.join(tmp, "p.3mf"), gcodes={1: syn.gcode(layers=2, tools=(0, 1))})
        out = os.path.join(tmp, "plate.png")
        gview.render(path, out, {0: (255, 0, 0), 1: (0, 0, 255)}, (0, 0, 256, 256), scale=2)
        im = Image.open(out).convert("RGB")
        assert im.size == (512, 512) and im.getpixel((240, 392)) == (0, 0, 255)
        return "512 x 512 PNG, top layer color on top"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def preflight_check():
    import preflight
    import synthetic as syn
    tmp = tempfile.mkdtemp(prefix="dry_")
    try:
        path = syn.write_3mf(os.path.join(tmp, "p.3mf"), ps=syn.project_settings(), ms=syn.model_settings(),
                             gcodes={1: syn.gcode()})
        good = preflight.check(path, "Textured PEI Plate", 0.4)
        bad = preflight.check(path, "Cool Plate", 0.2)
        assert not good.failed and bad.failed
        return f"GO on the stock file ({len(good.rows)} checks); NO-GO on the wrong plate and nozzle"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def setup_env():
    lines = []
    uv = shutil.which("uv")
    lines.append(f"uv: {uv or 'missing (CAD server needs it)'}")
    lines.append("Bambu Studio: " + ("found" if os.path.isdir("/Applications/BambuStudio.app") else "not at /Applications/BambuStudio.app"))
    lines.append(f"python: {sys.version.split()[0]}" + ("" if sys.version_info >= (3, 10) else " (need 3.10+)"))
    missing = []
    for mod in ("numpy", "scipy", "PIL", "manifold3d", "trimesh", "fontTools", "reportlab"):
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    lines.append("python deps: " + ("all present" if not missing else "missing " + ", ".join(missing)))
    work = os.path.expanduser("~/makerspace-3d")
    lines.append(f"work folder {work}: " + ("present" if os.path.isdir(work) else "absent (setup creates it)"))
    pres = os.path.join(work, "tools", "presets")
    n = len([f for f in os.listdir(pres) if f.endswith(".json")]) if os.path.isdir(pres) else 0
    lines.append(f"flattened presets: {n}")
    return "; ".join(lines)


def bambu_cli():
    exe = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
    if not os.path.exists(exe):
        return "skipped: Bambu Studio not installed"
    r = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-300:]
    return "CLI answers --help"


def main(argv=None):
    quiet = "--quiet" in (argv or sys.argv[1:])
    step("manifests", manifests)
    step("skills", skills)
    step("dashes", dashes)
    step("imports", imports)
    step("presets", presets)
    step("gate", gate)
    try:
        import PIL  # noqa: F401
        step("gview", gview_check)
    except ImportError:
        report("gview", True, "skipped: pillow not installed", info=True)
    step("preflight", preflight_check)
    step("setup", setup_env, info=True)
    step("bambu", bambu_cli, info=True)
    failed = [r for r in RESULTS if not r[1] and not r[3]]
    for name, ok, note, info in RESULTS:
        tag = "INFO" if info else ("OK  " if ok else "FAIL")
        if not quiet or not ok:
            print(f"{tag} {name:10s} {note}")
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed" + (", FAILED: " + ", ".join(r[0] for r in failed) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
