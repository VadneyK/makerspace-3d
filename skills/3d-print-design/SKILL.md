---
name: 3d-print-design
description: 3D printing pipeline for the maker space Bambu X1C with AMS. Use before designing, changing, slicing or packaging anything printable, and when a print result is reported (blob, clog, failed first layer, Benchy).
---

# 3D print design (maker space Bambu X1C + AMS)

## Read first
1. [PRINTER_SETUP.md](PRINTER_SETUP.md): hardware, plates, nozzles, filament in stock, slicing rules, the safety gate.
2. [TOOLING_RESEARCH.md](TOOLING_RESEARCH.md): which MCP servers and skills were evaluated, and why.
3. The project's own `HANDOFF.md` if one exists.

## Hard rules
- **Nozzle choice belongs to whoever is printing.** State the time and risk trade-off once, then build for the nozzle
  they picked. Before calling hardware bad, ask for a stock print (Bambu's Benchy) on it.
- **Never ship a file that skipped `check_gcode`** (in `${CLAUDE_PLUGIN_ROOT}/tools/slicer.py`). Packaging re-slices every plate and refuses failures.
- **One zip, every time**: 3MFs plus a short PDF guide (spools, then steps).
- **Do not claim causes the evidence does not show.** The printer's microSD (`ipcam/`, `timelapse/`) is the evidence.
- Deliver 3MF built by Bambu Studio's CLI, never hand-written 3MF, never bare STLs.
- Gold or any second color goes on faces that print flat (face up, or a first-layer inlay on the bed face).
  Multi-color text on a vertical face costs one filament swap per layer and comes out stringy.

## Pipeline
Python env: `python3 -m venv venv && venv/bin/pip install numpy scipy pillow manifold3d trimesh fonttools reportlab`.

1. Geometry: a script with manifold3d, trimesh and fontTools writes one STL per color body, named `<part>_<COLOR>.stl`.
2. Presets: `python ~/makerspace-3d/tools/bambu_presets.py` (copied there by `/makerspace-3d:setup`) flattens Bambu
   Studio's bundled X1C presets (including the "template" G-code files) into `~/makerspace-3d/tools/presets/`. Needs
   Bambu Studio installed.
3. Projects: build an assemble list with `~/makerspace-3d/tools/slicer.py` (`piece`, `run`), then add height ranges, per-object
   settings and `different_settings_to_system` as described in `PRINTER_SETUP.md`.
4. Package: re-slice each file with `slicer.slice_3mf`, which runs `check_gcode` on every plate, then zip.
5. Verify the 3MF settings: unzip `Metadata/project_settings.config` and check `printer_settings_id`,
   `nozzle_diameter`, `curr_bed_type`, filament presets, and that `machine_start_gcode` starts with
   `;===== machine: X1-<nozzle>`.

## Look at it before sending
- Bambu's own render (`Metadata/top_1.png`) hides inlays on the bed face and can paint a whole plate one color when a
  thin film of another color covers it. Draw the real layers from the G-code with `${CLAUDE_PLUGIN_ROOT}/tools/gview.py` instead.
- **build123d MCP** (started by this plugin's `.mcp.json`; its tools appear as `mcp__plugin_makerspace-3d_build123d__*`, or `mcp__build123d__*` if it was added by hand): `render_view` for previews while
  designing, `measure`, `analyze_printability`, `cross_sections` for wall thickness, overhangs and fit. It exports STL
  and STEP only; 3MF still comes from the Bambu Studio CLI.

## Tools evaluated
See `TOOLING_RESEARCH.md`. Meshy is for organic shapes, not plaques with lettering. Bambu LAN MCPs need network
access to the printer.
