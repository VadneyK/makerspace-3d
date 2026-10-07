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
| Command `/makerspace-3d:setup` | `skills/setup/SKILL.md` | One-shot environment check and setup. |
| Slicing toolkit | `tools/` | `slicer.py` (assemble a multi-color project through Bambu Studio's CLI, plus `check_gcode`, a safety gate that refuses unsafe G-code), `bambu_presets.py` (flatten Bambu's bundled presets), `gview.py` (draw a sliced plate from its G-code). |

Not included on purpose: personal notes, memory, and individual projects. This is only the shared setup.

## Install

1. Accept the GitHub invitation (github.com/VadneyK/makerspace-3d/invitations). The repo is private, so until you do,
   every command below fails with "Repository not found".
2. Let Claude Code use your GitHub login. In Terminal, answer yes when it asks about git credentials:

   ```
   gh auth login
   gh auth setup-git
   ```

   (Install the GitHub CLI first with `brew install gh` if you do not have it.)
3. Install the plugin from Terminal. Doing it there avoids the interactive plugin screen:

   ```
   claude plugin marketplace add VadneyK/makerspace-3d
   claude plugin install makerspace-3d@makerspace-3d
   ```

4. Start `claude` and run `/makerspace-3d:setup`. It checks for `uv` (the CAD server), Bambu Studio and Python, asks
   before installing anything, builds a Python env in `~/makerspace-3d/`, and writes the slicer presets. Restart the
   session afterwards and check `/mcp`: `plugin:makerspace-3d:build123d` should show as connected (the first start
   downloads Python 3.12 and can take a minute).
5. Ask for something: "Design a 100 x 60 mm name plate in two colors for the X1C." Claude reads the setup first and
   follows the rules in it.

The Claude desktop app's Code tab reads the same plugin settings, so a plugin installed from Terminal shows up there
under + > Plugins. Adding a custom GitHub marketplace from the desktop prompt box is not documented, so use Terminal
for steps 3 and 4's first half.

### Updates

Updates do not arrive on their own. Auto-update is off by default for third-party marketplaces. To get the latest:

```
claude plugin marketplace update makerspace-3d
claude plugin update makerspace-3d@makerspace-3d
```

Then run `/makerspace-3d:setup` again, because it copies `tools/` into `~/makerspace-3d/` and those copies do not
update by themselves.

### Before you install

The plugin starts a local program (the CAD server, run by `uv`) and `/makerspace-3d:setup` can install software with
Homebrew and pip, after asking. Read `.mcp.json` and `skills/setup/SKILL.md` first if you want to see exactly what.

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
