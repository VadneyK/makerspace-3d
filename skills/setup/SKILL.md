---
name: setup
description: Check and set up what the makerspace-3d plugin needs (uv, Bambu Studio, Python env, slicer presets). Run by hand once after installing.
disable-model-invocation: true
---

Set up this machine for the maker space 3D printing tools. Work through the checks in order, report one line per
check, and ask before installing anything.

1. `uv --version`. Needed for the build123d CAD server. If missing, offer `brew install uv`.
2. `test -d /Applications/BambuStudio.app`. Needed for slicing. If missing, offer `brew install --cask bambu-studio`.
3. `python3 --version` (3.10 or newer).
4. Work folder: create `~/makerspace-3d/` and copy `${CLAUDE_PLUGIN_ROOT}/tools/` into it as `~/makerspace-3d/tools/`
   (the presets are written next to the scripts, and the plugin folder is replaced on every update).
5. Python env: `python3 -m venv ~/makerspace-3d/venv && ~/makerspace-3d/venv/bin/pip install numpy scipy pillow manifold3d trimesh fonttools reportlab`.
6. Presets (needs step 2): `cd ~/makerspace-3d/tools && ~/makerspace-3d/venv/bin/python bambu_presets.py`. It must print
   one line per preset and write `presets/*.json`. If it stops on "start G-code is not Bambu's X1C routine", Bambu
   Studio is too old or too new for the script: say so and stop.
7. Tell the person to restart the session so the build123d CAD server (started by this plugin) is available, and to
   check it with `/mcp`.

Finish with a short table: check, status, what is left to do. Then suggest a first request, for example
"Design a 100 x 60 mm name plate in two colors for the X1C."
