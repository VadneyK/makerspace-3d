"""The plugin itself: manifests, skills, links, and the house rule on dashes."""
import json
import os
import re
import subprocess

import pytest

from conftest import ROOT

BAD_DASHES = (chr(0x2014), chr(0x2013))   # em dash, en dash: never in this repo
SKILLS = sorted(d for d in os.listdir(os.path.join(ROOT, "skills")) if os.path.isdir(os.path.join(ROOT, "skills", d)))


def _frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: no frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def test_plugin_manifest():
    d = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert d["name"] == "makerspace-3d"
    assert d["description"] and d["author"]["name"]


def test_marketplace_points_at_this_plugin():
    m = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
    p = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert m["name"] == "makerspace-3d"
    assert [x["name"] for x in m["plugins"]] == [p["name"]]
    assert m["plugins"][0]["source"] == "./"


def test_mcp_server_definition():
    d = json.load(open(os.path.join(ROOT, ".mcp.json")))
    srv = d["mcpServers"]["build123d"]
    assert srv["command"] == "uv"
    assert srv["args"][:3] == ["tool", "run", "--python"]
    assert any(a.startswith("build123d-mcp==") for a in srv["args"]), "pin the server version"


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_frontmatter(skill):
    fm, body = _frontmatter(os.path.join(ROOT, "skills", skill, "SKILL.md"))
    assert fm["name"] == skill
    assert len(fm["description"]) > 40
    assert body.strip()


def test_setup_is_a_command_not_an_auto_skill():
    fm, _ = _frontmatter(os.path.join(ROOT, "skills", "setup", "SKILL.md"))
    assert fm.get("disable-model-invocation") == "true"


def test_pre_print_check_loads_on_its_own_and_runs_preflight():
    fm, body = _frontmatter(os.path.join(ROOT, "skills", "pre-print-check", "SKILL.md"))
    assert fm.get("disable-model-invocation") != "true"
    assert "tools/preflight.py" in body
    for section in ("Plate and bed", "Nozzle", "AMS and filament", "Supports", "First layer", "The file"):
        assert section in body


def _md_files():
    out = []
    for dp, _, files in os.walk(ROOT):
        if ".git" in dp or "venv" in dp:
            continue
        out += [os.path.join(dp, f) for f in files if f.endswith(".md")]
    return out


@pytest.mark.parametrize("path", _md_files(), ids=lambda p: os.path.relpath(p, ROOT))
def test_relative_links_resolve(path):
    text = open(path, encoding="utf-8").read()
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#")[0]
        assert os.path.exists(os.path.join(os.path.dirname(path), target)), f"{path}: broken link {target}"


def test_filament_reference_cites_every_bracketed_source():
    text = open(os.path.join(ROOT, "skills", "3d-print-design", "FILAMENTS.md"), encoding="utf-8").read()
    body, sources = text.split("## Sources")
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", body)}
    listed = {int(n) for n in re.findall(r"^\s*(\d+)\. ", sources, re.M)}
    assert cited <= listed, cited - listed
    assert listed <= cited, f"unused sources {listed - cited}"
    assert "https://" in sources


def test_no_em_or_en_dashes_in_tracked_files():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    files += [os.path.relpath(p, ROOT) for p in _md_files()]
    hits = []
    for f in set(files):
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if any(ch in line for ch in BAD_DASHES):
                hits.append(f"{f}:{n}")
    assert hits == []
