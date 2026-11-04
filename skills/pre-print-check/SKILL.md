---
name: pre-print-check
description: Pre-print checklist for the maker space Bambu X1C with AMS. Use before any 3MF goes to the printer, when someone says they are about to print or asks whether a file is ready, and after a failed first layer. Covers plate and bed, nozzle, AMS and filament, supports, first layer, and the file itself. Run it with a path to a 3MF to get a scripted report first.
---

# Pre-print check (maker space Bambu X1C + AMS)

Work through every section, report one line per item (pass, warn, fail,
or "ask"), and end with go or no-go. Do not skip the file section: nothing
goes to the printer unless `check_gcode` passed on every plate (hard rule
in `3d-print-design`). Facts below cite Bambu Lab's public pages, listed at
the end; the maker space rules come from
[PRINTER_SETUP.md](../3d-print-design/PRINTER_SETUP.md) and the material
numbers from [FILAMENTS.md](../3d-print-design/FILAMENTS.md).

## 0. Scripted part first

If a 3MF path was given (or one is obvious from the conversation), run

```
python3 ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py <file.3mf> --plate-installed "<plate>" --nozzle <0.2|0.4|0.6|0.8>
```

It reads the project settings inside the 3MF, compares them with the
material table, runs the `check_gcode` safety gate on every sliced plate,
and prints a pass / warn / fail table. Paste that table, then do the
hands-on items below that a script cannot see. Without a 3MF, do the
checklist by asking the person; do not guess the answers.

## 1. Plate and bed

- [ ] **The plate in the file matches the plate on the printer.** The X1C
      reads the plate markings and stops the job when they do not match the
      slice file (Build Plate Detection) [4]. On a Textured PEI plate the
      printer also lowers the nozzle 0.04 mm after leveling, so a file that
      says Cool Plate or High Temp Plate while a textured plate is installed
      prints its first layer too high [7]. The textured plate is usually the
      one installed; with the 0.2 nozzle use Smooth PEI and set the plate
      type per plate (PRINTER_SETUP).
- [ ] **Plate washed.** Dish soap, warm water, sponge or brush, rinse, dry
      with a paper towel; never acetone; hold the plate by its edges. A clean
      PEI plate holds a thin water film; beading means it is greasy [5] [1].
- [ ] **Bed temperature matches the material and the plate** (FILAMENTS
      summary table). PLA 45 to 65 C on PEI plates, 35 to 45 C on the Cool
      Plate; PETG 60 to 80 C and ABS 90 to 100 C on PEI, neither on the Cool
      Plate [1]. The file's first-layer bed temperature must appear as
      `M190 S<temp>` in the G-code (the gate checks for M190).
- [ ] **Glue for ABS and PETG** (glue stick or Bambu liquid glue); optional
      for PLA, where it mainly protects the plate [1].
- [ ] **Door and lid.** PLA and PETG with a bed above 45 C (PLA) or 60 C
      (PETG): open the front door or lift the glass so the chamber does not
      soften filament in the extruder. ABS: door closed, lid on [1].
- [ ] **Auto Bed Leveling is on** for the job (the printer's Print
      Calibration options) unless the person is deliberately skipping it
      for a repeat print on an untouched plate [4].

## 2. Nozzle

- [ ] **Nozzle size on the printer equals the file's.** The file's
      `printer_settings_id` ends with the nozzle size, and its start G-code
      first line is `;===== machine: X1-<size>` (PRINTER_SETUP). The maker
      space has 0.2, 0.4, 0.6 and 0.8 hotends, no mid-print swaps.
- [ ] **Material allowed on that nozzle.** Silk and Silk+: 0.2 or 0.4 only
      [3]. Standard PLA, PETG and ABS: any size [1]. A 0.2 nozzle caps flow at
      1 to 2 mm3/s, so expect long times and slow color changes (FILAMENTS).
- [ ] **Hotend is clean.** No blob on the nozzle, no filament stuck in the
      extruder. The 2026-09-24 blob started on a 0.2 hotend that later
      clogged a stock Benchy (PRINTER_SETUP). If in doubt, ask for a stock
      Benchy on that hotend before blaming the file (hard rule).
- [ ] **Nozzle temperature inside Bambu's range for the material**
      (FILAMENTS: PLA 190 to 240 C, Tough+ 220 to 250 C, PETG 240 to 270 C,
      ABS 240 to 280 C) [1] [6].

## 3. AMS and filament

- [ ] **Every slot the file uses holds the right spool.** Check the send
      dialog's slot mapping: the color index in Bambu Studio is not the AMS
      slot number [9]. A slot whose filament type does not match the sliced
      type cannot be selected at all (PLA file, ABS slot) [9].
- [ ] **RFID read or filament info set by hand.** Bambu spools are read by
      RFID; a third-party spool shows "?" until its type and color are
      entered on the screen, and must still match the sliced material [9]
      [10].
- [ ] **Filament is dry.** PETG Translucent must be dried before every use;
      PETG Basic after 72 h above 50 % RH; PLA, Silk and ABS are
      "recommended" (FILAMENTS drying table) [2] [11] [12]. Damp filament
      strings, bubbles and loses strength [2]. The X1C can dry a spool
      itself (Toolbox > Dry Filament, spool covered, flip it midway) [4] [2].
- [ ] **AMS desiccant and humidity.** Check the humidity reading on the AMS
      page of the screen; replace or regenerate desiccant when it is high
      [4] [2].
- [ ] **Enough filament.** Compare the slice report grams per slot
      (`slicer.slice_report`, or Bambu Studio's sliced plate info) with the
      remaining estimate on each spool; enable AMS Auto-Refill only when a
      second spool with the same brand, type, color and nozzle temperature
      is loaded [4].
- [ ] **Do not pause and unload mid-print**; that breaks the auto-refill
      backup and switches to the external spool [10].
- [ ] **Multi-color plate rules** (PRINTER_SETUP): same layer heights for
      every object on the plate, prime tower on, flush into infill on, no
      tall single-color object next to a multi-color one.

## 4. Supports

- [ ] **Does the part need supports at all?** Check overhangs with
      `analyze_printability` in the build123d MCP, or in Bambu Studio's
      overhang preview. Prefer re-orienting (flat face down, lettering as an
      inlay) to adding supports (3d-print-design hard rules).
- [ ] **If supports are on**: type (normal or tree), interface layers, and
      whether removal will mark a visible face. More interface layers and a
      faster interface speed make removal easier [8].
- [ ] **Material-specific**: PLA Tough+ bonds so well that Bambu
      recommends a dedicated support filament (Support for PLA, or Support
      for PLA/PETG) as the interface [13]; the maker space stocks none, so
      plan removal or re-orient. ABS with Support for ABS: variable layer
      height is unsupported, raise the flushing volume to 800, and turn off
      flush into infill/support [8].
- [ ] **Brim for small footprints or tall thin parts.** Adhesion scales with
      contact area; a brim, or supports for tall thin items, prevents
      lift-off and nozzle strikes [5]. Put the brim on the object, not in
      project settings (PRINTER_SETUP).

## 5. First layer

- [ ] **First layer height and width.** Bambu's own recommendation when a
      first layer is marginal: 0.25 mm layer height and 0.5 mm line width
      [5]. Keep global first-layer settings at Bambu's stock values and put
      changes on the object (PRINTER_SETUP). With the 0.2 nozzle on a
      textured plate the 0.1 mm first layer drags in the texture; use Smooth
      PEI (PRINTER_SETUP).
- [ ] **No extrusion below Y 14 on layer 1**: the start routine draws its
      purge and flow-calibration lines at Y 0 to 12; the gate refuses files
      that print over them (PRINTER_SETUP).
- [ ] **First Layer Inspection is on** in the printer's Print Options; the
      lidar scans the finished first layer and warns on defects [4]. It only
      works for files sliced by Bambu Studio [14].
- [ ] **Watch the first layer** in person or on the camera. First-layer
      failures are the ones that waste the most time; the 2026-09-24 fail
      was a Cool Plate temperature on a textured plate (PRINTER_SETUP).
- [ ] **Footprint test before a long print**: a 1-layer footprint of the
      part on the same plate and material (PRINTER_SETUP).
- [ ] **If the first layer did not stick last time**: wrong plate type in
      the file, dirty plate, bed too cold, no brim, no glue, or a bed that
      needs re-leveling after cleaning the nozzle and plate [7].

## 6. The file

- [ ] **`check_gcode` passed on every plate** (`preflight.py` runs it, or
      `slicer.slice_3mf`): Bambu's own start routine (AMS load, nozzle wipe,
      M976 void detection, M412 runout, bed wait, first-layer nozzle temp),
      no extrusion off the bed or on the lidar marker, Z under 250
      (PRINTER_SETUP).
- [ ] **`different_settings_to_system` is filled** and the GUI shows the
      process name with "*"; otherwise Bambu Studio silently reloads stock
      presets on open (PRINTER_SETUP).
- [ ] **Plate type, nozzle, filament presets and start G-code verified** in
      `Metadata/project_settings.config` (3d-print-design pipeline step 5).
- [ ] **The real layers looked at**, with `tools/gview.py`, not only
      Bambu's `top_1.png` render, which hides bed-face inlays
      (3d-print-design).

## 7. Printer options worth a glance

AI Print Monitoring (spaghetti, purge chute pile-up, nozzle clumping, with a
pause sensitivity), Build Plate Detection, First Layer Inspection,
Auto-Recovery from Step Loss and Open Door Detection live under Settings >
Print Options on the X1C screen [4]. Keep plate detection and first layer
inspection on for every job someone will not be watching.

## Report format

```
| Area        | Check                                  | Status | Note |
| Plate       | File plate = installed plate           | pass   | Textured PEI |
| ...
Verdict: GO / NO-GO (reason)
```

## Sources (fetched 2026-11-03)

1. Bambu Lab Wiki, Filament Guide and Material Table:
   https://wiki.bambulab.com/en/general/filament-guide-material-table
2. Bambu Lab Wiki, Filament Drying Recommendations:
   https://wiki.bambulab.com/en/filament-acc/filament/dry-filament
3. Bambu Lab Wiki, Printing with PLA Silk / Silk+ filaments:
   https://wiki.bambulab.com/en/x1/manual/printing-with-silk-filaments
4. Bambu Lab Wiki, X1 series screen operation (Print Calibration, Toolbox,
   Print Options, AMS options):
   https://wiki.bambulab.com/en/x1/manual/screen-operation
5. Bambu Lab Wiki, Textured PEI Plate cleaning guide (cleaning steps, water
   film test, brim and first-layer advice):
   https://wiki.bambulab.com/en/filament-acc/acc/pei-plate-clean-guide
6. Bambu Studio filament profiles for the X1C,
   `resources/profiles/BBL/filament/` in https://github.com/bambulab/BambuStudio
7. Bambu Lab Wiki, Common print quality problems and solutions (warping and
   first-layer causes, 0.04 mm textured plate offset):
   https://wiki.bambulab.com/en/knowledge-sharing/common-print-quality-problem
8. Bambu Lab Wiki, Support for ABS printing guide (support parameters,
   interface layers, flushing):
   https://wiki.bambulab.com/en/filament-acc/filament/support-for-abs
9. Bambu Lab Wiki, X1 multi-color printing (slot mapping, type matching):
   https://wiki.bambulab.com/en/x1/manual/multi-color-printing
10. Bambu Lab Wiki, AMS main functions and workflow (RFID, loading,
    auto-refill, pause warning):
    https://wiki.bambulab.com/en/ams/manual/ams-function-introduction
11. Bambu Lab store, PETG Basic: https://us.store.bambulab.com/products/petg-basic
12. Bambu Lab store, PETG Translucent:
    https://us.store.bambulab.com/products/petg-translucent
13. Bambu Lab store, PLA Tough+:
    https://us.store.bambulab.com/products/pla-tough-upgrade
14. Bambu Lab Wiki, X1 FAQ (third-party slicers and First Layer Inspection):
    https://wiki.bambulab.com/en/x1/manual/faq
