# Maker space 3D printing setup (Bambu X1C + AMS)

Load this before asking for printable models. A snapshot of the maker space
setup, confirmed 2026-09-23, updated 2026-10-07. The `3d-print-design` skill
that sits next to this file points here first.

## Hardware

- Printer: Bambu Lab X1 Carbon (X1C) at the maker space.
- Multi-color: AMS, so up to 4 filaments per print. Design multi-color parts
  so color changes happen in as few layers as possible (flat faces up,
  raised or first-layer-inlay lettering). Never design vertical multi-color
  text: that is one filament swap per layer.
- Nozzles at the maker space: 0.2, 0.4, 0.6, 0.8 (hotend swaps; no mid-print
  swap). Default to 0.4: minimum stroke about 0.8 mm, lettering at least 5 mm
  cap height. Nozzle choice belongs to the person printing: state the
  time and risk trade-off once, then build for the nozzle they pick.
- Bed: 256 x 256 x 256 mm.
- Build plates: 2x Bambu Smooth PEI (one worn/scuffed), Bambu Cool Plate, gold
  textured PEI, black textured PEI. The textured plate is usually the one
  installed. With the 0.2 nozzle use Smooth PEI (see the 0.2 rules below).
- The printer's microSD card (mounts as `/Volumes/NO NAME` on a Mac with an SD
  slot via adapter) has continuous chamber video (`ipcam/`) and per-job
  timelapses; network-sent jobs are not stored there.

## Slicer

- Bambu Studio (`brew install --cask bambu-studio`).
  **Deliver 3MF, not STL.** STLs carry no color, so multi-color parts import
  as separate all-black objects and someone has to reassemble them. Give one
  3MF per printed piece: a single object whose parts are pre-assigned to AMS
  slots. Let Bambu Studio's own CLI write it (never hand-write the 3MF; the
  CLI crashes on hand-written ones): `tools/bambu_presets.py`
  flattens the bundled X1C presets (including the "template" G-code files),
  and a project script built on `tools/slicer.py` runs
  `BambuStudio --assemble --load-filament-ids ... --export-3mf` and
  test-slices every plate through `slicer.check_gcode`. Presets must keep `from: system`
  and their original `compatible_printers`, and parts must be centered on the
  256 mm bed, or the CLI refuses.
- **Safety gate, never skip it.** Nothing goes to the printer unless every
  plate re-slices clean through `slicer.check_gcode`: Bambu's own start routine
  (AMS load, nozzle wipe, M976 void detection, M412 runout, bed wait, 210+ C
  first layer), no extrusion off the bed or on the front-left lidar marker,
  first layer at Y 14 or more (the start routine draws purge lines at Y 0 to
  12), nozzle 190 to 250 C, bed 35 to 65 C, Z under 250. Your packaging step should
  run this itself and refuse to zip a failing file. For a new printer, filament
  or project, extend the gate before shipping, and diff the machine settings
  against a 3MF the Bambu Studio GUI saved (they matched 115 of 115 keys on
  2026-09-26).
- Bundle for the maker space Mac: one `~/Desktop/<name> Print Files.zip` (3MFs +
  a 2-page PDF: spools, then steps) for AirDrop.

## Hard-won slicing rules (2026-09-24, from real Bambu CLI slices)

- **CHECK THE START G-CODE (found 2026-09-26).** Bambu Studio keeps
  the X1C machine G-code in sibling files `<preset> template <key>.json` that no
  `inherits` chain points to. A flattener that only follows `inherits` silently
  gets fdm_machine_common's generic 20-line start: no AMS load before layer 1
  (prints whatever is in the toolhead), no nozzle wipe before Z probing, no
  first-layer scan, no void-printing detection (M976 S3 P2), nozzle at 205 C.
  Every 3MF built before the fix had it. (It was NOT what blobbed the hotend
  on 9/24: the printer's SD card camera shows that job ran Bambu's routine,
  lidar scan at 17:25, same sequence as a known-good Benchy. The blob grew
  from about 18:15 on a 0.2 hotend that later clogged a stock Benchy too.)
- **Evidence lives on the printer's microSD card:** `ipcam/` has continuous
  chamber video in ~4.5 min chunks named by printer local time, `timelapse/`
  one video per job. Network-sent jobs are not kept on the card. A Mac with an SD slot needs a microSD adapter. `bambu_presets.py` overlays the templates and refuses a
  machine preset without M620/M976; `slicer.check_gcode` refuses any slice
  whose start lacks the AMS load, M976, M412, nozzle wipe, M190 or M109 S2xx.
  The machine_start_gcode must equal what the GUI writes (about 20,600 chars,
  first line `;===== machine: X1-0.2`). Opening a 3MF in the GUI and re-picking
  the printer preset also restores it.

- **ROOT CAUSE (2026-09-30): fill `different_settings_to_system`.** Bambu
  Studio's GUI keeps a project value only if its key is listed in
  project_settings `different_settings_to_system` ([print; each filament;
  printer], `;`-joined keys). The CLI writes it empty, so the GUI silently
  reloaded stock presets on every open. a `mark_changed_settings()` step in your project script fills it; open the 3MF in the GUI and check the
  process name shows "*" (modified) before shipping.
- **Put anything that must print on the OBJECT, not in project settings
  (2026-09-30).** The maker space's Bambu Studio opened our CLI-built 3MF and
  dropped its project-level settings (first layer 0.12 became 0.1, the brim
  vanished, the plate became Textured PEI) but kept the per-object ones
  (concentric, walls, layer zones). Brim and first-layer speeds go in
  `model_settings.config` per object; leave global first-layer settings at
  Bambu's stock values so the GUI and our slice agree. Ship a 1-layer
  footprint test before any long print.
- **0.2 nozzle: Smooth PEI, set per plate (2026-09-30).** On "Textured PEI
  Plate" Bambu's start code lowers the nozzle 0.04 mm; a 0.2 nozzle's 0.1 mm
  first layer then drags in the texture (thin, blotchy). Write the plate type
  per plate (`<metadata key="bed_type" value="High Temp Plate"/>` in the
  plate block of model_settings.config); the maker space's Bambu Studio keeps that one.
- **Plates on hand:** 2x Bambu Smooth PEI (one worn), Bambu Cool Plate,
  gold textured PEI, black textured PEI. For PLA with a 0.2 nozzle or a
  visible underside, use Smooth PEI (`curr_bed_type: High Temp Plate`,
  `hot_plate_temp_initial_layer` 60). The file's plate must match the plate
  installed or the X1C may flag a mismatch.
- **Plate type: set it explicitly.** Flattened machine presets
  default to `curr_bed_type: Cool Plate` (35 C first layer) and that failed a
  print on layer 1 on 2026-09-24. Set `curr_bed_type: Textured PEI Plate`,
  first layer 60 C, slow first layer, and check `M190 S60` in the G-code.
  Wash the plate with dish soap before big prints.
- **Nozzles at the maker space: 0.2, 0.4, 0.6, 0.8.** Default to 0.4. The 0.2
  purges at about 2 mm3/s, so every color change costs minutes; a multi-color
  disc went 4.9 h (0.4, zoned) vs 13.2 h (0.2 at 0.14) vs 24.5 h (0.2 at 0.06).
  No mid-print nozzle swaps on the X1C.
- **The maker space mentor's preferred surfaces:** concentric top and bottom, 4 walls, 7 top /
  5 bottom shells. Bake these onto each object, because a preset switch in the
  GUI resets global settings (it reset flush-into-infill once).
- **Prime tower rule:** every object on a multi-color plate must share the same
  layer heights. So vary layer height by Z (height range modifiers), never per
  object, and never put a tall single-color object next to a different-colored
  one: a black block taller than a white part forced a swap on every layer
  (1.7 h test became 7.4 h). Separate plates per color-mix.
- **Height ranges via the CLI:** `--load-assemble-list` ignores
  `height_ranges`. Instead export the project, then write
  `Metadata/layer_config_ranges.xml` (`<objects><object id="N"><range min_z
  max_z><option opt_key="layer_height">`) and set per-plate `wipe_tower_x/y`
  in project_settings, then slice with `BambuStudio --slice 0 file.3mf`. Proven
  by the layer-height counts in the G-code. Object settings go as
  `<metadata key=... value=...>` on each `<object>` in model_settings.config
  (proven: 60% infill there tripled the time).
- **Vertical multi-color text is expensive:** one swap per layer. A base with
  raised gold letters on its standing front face took 7.5 h alone; put
  several such pieces on one plate so the swaps are shared (3 bases: 12.4 h).
  Better: lay the face on the bed and make the lettering a flat inlay in the
  first two layers (or the last two layers on a top face): 3.4 h per base.
- Tools (the plugin's `tools/` folder, copied to `~/makerspace-3d/tools/` by `/makerspace-3d:setup`): `tools/slicer.py` (assemble list, range injection, slice report,
  `check_gcode` safety gate), `tools/bambu_presets.py` (flatten presets),
  `tools/gview.py` (draw a sliced plate from its own G-code),
  `tools/preflight.py` (offline pre-print report of a 3MF: plate, nozzle,
  material limits from `FILAMENTS.md`, and the gate on every sliced plate),
  `tools/dry_run.py` (exercise every tool on a machine without Bambu Studio).
- Material limits (nozzle and bed temperatures per plate, drying, AMS,
  enclosure) for everything in stock: `FILAMENTS.md`, with Bambu's sources.

## Filament in stock at the maker space (swatch board photo 2026-09-23, updated 2026-10-06)

PLA (Bambu PLA Basic unless noted; names are read off the swatches, so
confirm Bambu's official color name before ordering):

| Color | Code |
|---|---|
| Jade White | 10100 |
| Black | 10101 |
| Silver | 10102 |
| Gray (labelled "PLA GRAY") | n/a |
| Magenta | 10202 |
| Red | 10200 |
| Yellow | 10400 |
| Purple | 10700 |
| Deep royal blue | 10601 |
| Sky blue | 10603 |
| Deep green | 10502 |
| Orange | 10300 |
| PLA Silk+ Gold | n/a |
| PLA Silk Rose Gold | n/a |

ABS: Black 40101, White 40100, gray/silver (unlabelled), Red 40200,
Orange 40300, Yellow 40400, Blue 40600, Teal 40601, Green 40500.

PLA Tough+ (added 2026-10-06: "we also have tough + black and stuff"): **Black** confirmed; other Tough+ colors may be in stock, ask.
Bambu PLA Tough+ is a high-impact PLA for functional parts (clips, brackets,
snap fits, anything dropped or flexed); prints like PLA. Bambu Studio presets
exist for it: `Bambu PLA Tough+ @BBL X1C` (0.4) and `... X1C 0.2 nozzle`.
Plain "Bambu PLA Tough @BBL X1C" is a different, older product.

PETG and MISC: one translucent/clear swatch only.

No navy, no matte line, no dark neutral other than Black and Gray.

## Tooling on the Mac used for design

- No OpenSCAD; Bambu Studio is installed (2026-09-23). Models are generated in
  Python with manifold3d (booleans, hulls, revolves), trimesh (STL export),
  fontTools (real font outlines) and numpy/scipy.
- A three.js viewer served with `python3 -m http.server` works for previews.
- build123d MCP server (`build123d-mcp==0.3.90`, added 2026-09-30, tools
  `mcp__plugin_makerspace-3d_build123d__*` when installed through this plugin's `.mcp.json`): render_view, measure, analyze_printability while
  designing. Exports STL/STEP only; 3MF still comes from the Bambu Studio CLI.
- Verify in the real GUI before shipping: open the 3MF in Bambu Studio, check the process name shows "*" (modified), Global and Objects
  values, Plate Settings > Plate type, then Slice and look at layer 1 with
  Color Scheme = Line Type. Bambu's own sliced render is in the 3MF as
  `Metadata/top_1.png` / `plate_1.png` after `slicer.slice_3mf(path, keep=...)`.
- Tooling survey: `TOOLING_RESEARCH.md` (Meshy and Bambu LAN MCPs not useful here).
- Lesson from a card-box project: cardboard flexes, plastic does not, so size a
  cavity with 3 to 5 mm of slack per side over the nominal item.
