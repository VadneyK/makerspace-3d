# makerspace-3d

A Claude Code plugin that gives Claude the working context for a maker space with a Bambu Lab X1 Carbon and AMS,
so you can open a session and ask for printable models, slicing, or help with a failed print.

## What is in it

| Piece | Where | What it does |
|---|---|---|
| Skill `3d-print-design` | `skills/3d-print-design/SKILL.md` | Loads automatically when you ask about designing, slicing or packaging a print. Hard rules and the build pipeline. |
| Printer setup | `skills/3d-print-design/PRINTER_SETUP.md` | Hardware, build plates, nozzles, filament in stock, hard-won slicing rules (Bambu Studio quirks, first layer, plate type, multi-color cost). |
| Tooling survey | `skills/3d-print-design/TOOLING_RESEARCH.md` | Which MCP servers and skills were evaluated, and which were skipped and why. |
| build123d MCP | `.mcp.json` | Starts the `build123d-mcp` CAD server (render, measure, printability checks). |
| Slicing toolkit | `tools/` | `slicer.py` (assemble a multi-color project through Bambu Studio's CLI, plus `check_gcode`, a safety gate that refuses unsafe G-code), `bambu_presets.py` (flatten Bambu's bundled presets), `gview.py` (draw a sliced plate from its G-code). |

Not included on purpose: personal notes, memory, and individual projects. This is only the shared setup.

## Install

You need Claude Code, plus `uv` (for the CAD server): `brew install uv`.
For the slicing tools: Bambu Studio (`brew install --cask bambu-studio`) and Python 3.

The repo is private, so you must have access to it and be signed in to GitHub (`gh auth login`).

```
/plugin marketplace add VadneyK/makerspace-3d
/plugin install makerspace-3d@makerspace-3d
```

Restart the session, then just ask, for example: "Design a 100 x 60 mm name plate in two colors for the X1C."
Claude will read the setup first and follow the rules in it.

## Use the tools directly

```
python3 -m venv venv && venv/bin/pip install numpy scipy pillow manifold3d trimesh fonttools reportlab
venv/bin/python tools/bambu_presets.py      # writes tools/presets/ from the installed Bambu Studio
```

`tools/slicer.py` expects the preset file names that `bambu_presets.py` writes. Open it and read the top of the file
before building on it; it was written for one project and is a starting point, not a framework.

## Without the plugin system

Copy `skills/3d-print-design/` into `~/.claude/skills/` and add the CAD server yourself:

```
claude mcp add build123d -- uv tool run --python 3.12 build123d-mcp==0.3.90
```

## Notes

- The filament list and plates are a snapshot of one maker space (September to October 2026). Confirm before relying on them.
- `build123d-mcp` is a third-party Apache-2.0 project (https://github.com/pzfreo/build123d-mcp); it runs locally and
  executes the code Claude gives it. Installing the plugin starts it.
