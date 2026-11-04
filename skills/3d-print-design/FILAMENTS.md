# Filament and print settings quick reference (maker space stock, Bambu X1C)

One row per material the maker space stocks (see the stock list in
[PRINTER_SETUP.md](PRINTER_SETUP.md)). Every number below comes from Bambu
Lab's public pages, fetched 2026-11-03; the bracketed numbers point to the
source list at the bottom. Where a Bambu Studio preset value and a wiki range
differ, both are given: the preset is what the printer actually runs when
you pick the stock profile, the range is what Bambu says is safe to tune
within. Re-check the sources before relying on this after a Bambu Studio
update; the profile files change.

How to use this file:

- Pick the material row, then the plate column that matches the plate that
  is physically installed. The X1C start routine lowers the nozzle 0.04 mm on
  a Textured PEI plate, so a wrong plate type in the file costs first-layer
  adhesion [8].
- The `check_gcode` safety gate in `tools/slicer.py` is written for PLA
  Basic and Silk: first-layer nozzle 210 to 239 C, body nozzle 190 to 250 C,
  bed 35 to 65 C. PLA Tough+, ABS and PETG trip it on purpose. Extend the
  windows in `slicer.py` for those materials before packaging, as
  `PRINTER_SETUP.md` already requires for any new filament.
- Preset names are the ones `tools/bambu_presets.py` can flatten from the
  installed Bambu Studio: `Bambu <material> @BBL X1C` and
  `Bambu <material> @BBL X1C 0.2 nozzle`.

## Summary table

Temperatures in C. "Preset" columns are the Bambu Studio X1C filament
profiles [6]; first layer / other layers where they differ. "Wiki range" is
Bambu's nozzle temperature range for the material family [1].

| Material (stock) | Bambu Studio preset | Preset nozzle (first / other) | Wiki nozzle range | Preset bed: Cool / Smooth PEI / Textured PEI | Wiki bed range on PEI plates | Max flow 0.4 / 0.2 nozzle (mm3/s) | Part fan min to max |
|---|---|---|---|---|---|---|---|
| PLA Basic | `Bambu PLA Basic @BBL X1C` | 220 / 220 | 190 to 240 | 35 / 55 / 55 | 45 to 65 (Cool Plate 35 to 45) | 21 to 29 / 2 | 100 to 100 |
| PLA Silk+ (Gold) | `Bambu PLA Silk+ @BBL X1C` | 230 / 230 | 190 to 240 (guide says 210 to 240, try 235) | 35 / 55 / 55 | 45 to 65 (Cool Plate 35 to 45) | 12 / 2 | 100 to 100 |
| PLA Silk (Rose Gold) | `Bambu PLA Silk @BBL X1C` | 230 / 230 | 190 to 240 | 35 / 55 / 55 | 45 to 65 (Cool Plate 35 to 45) | 12 / not shipped | 100 to 100 |
| PLA Tough+ (Black) | `Bambu PLA Tough+ @BBL X1C` | 245 / 245 | 220 to 250 (preset range) | 35 / 55 / 55 | 45 to 65 (Cool Plate 35 to 45) | 18 to 25 / 2 | 100 to 100 |
| ABS | `Bambu ABS @BBL X1C` | 260 / 270 | 240 to 280 | not allowed / 90 / 90 | 90 to 100; Cool Plate not recommended | 16 to 25 / 2 | 10 to 60 |
| PETG Basic | `Bambu PETG Basic @BBL X1C` | 245 / 255 | 240 to 270 | not allowed / 70 / 70 | 60 to 80; Cool Plate not recommended | 15 / 1 | 20 to 40 |
| PETG Translucent | `Bambu PETG Translucent @BBL X1C` | 250 / 245 | 230 to 260 | not allowed / 70 / 70 | 60 to 80; Cool Plate not recommended | 6 / not shipped | 10 to 30 |

"Max flow" is `filament_max_volumetric_speed` in the preset; two values mean
the profile lists one per nozzle variant. A 0.2 nozzle caps every material at
1 to 2 mm3/s, which is why color changes take minutes on it [6]. "Not
allowed" means the preset sets that plate to 0 C, and Bambu Studio then
reports the filament as incompatible with that plate [1].

The maker space's clear PETG swatch is unlabelled; PETG Basic and PETG
Translucent have different presets (Translucent runs at a quarter of the
flow), so read the spool before slicing.

## Drying, storage, enclosure, AMS

| Material | Dry before use | Oven | X1C heatbed (spool covered, flip midway) | AMS 2 Pro | AMS / AMS lite | Enclosure and door |
|---|---|---|---|---|---|---|
| PLA Basic, Tough+ | Recommended | 50 to 55 C, 8 h | 60 to 70 C, 12 h | 45 C, 12 h | Compatible | Either; open the door or lift the glass if the bed is above 45 C [1] |
| PLA Silk, Silk+ | Recommended; store under 20 % RH | 55 C, 8 h | 65 to 75 C, 12 h | 45 C, 12 h | Compatible | As PLA [1] [3] |
| ABS | Recommended | 75 to 85 C, 8 h | 90 to 100 C, 12 h | Not compatible (AMS HT: 80 C, 8 h) | AMS compatible, AMS lite not recommended | Enclosed printer recommended, keep the door closed [1] |
| PETG Basic | Recommended (required after 72 h above 50 % RH) | 60 to 65 C, 8 h | 75 to 85 C, 12 h | 65 C, 12 h | Compatible | Enclosed recommended for layer strength; open the door if the bed is above 60 C [1] [11] |
| PETG Translucent | Required, with desiccant during the print | 65 C, 8 h | 75 to 85 C, 12 h | 65 C, 12 h | Compatible | As PETG [1] [12] |

Sources for the table: drying appendix [2], material table [1], product
pages [9] [10] [11] [12]. The X1C can dry filament itself from Toolbox >
Dry Filament on the screen [4]; unload the toolhead first and cover the
spool with its box or a printed PC cover [2].

Softening temperatures from the presets (`temperature_vitrification`):
PLA family 45 C, PETG 55 C, ABS 75 C [6]. Bambu's rule: when the bed runs
hotter than the filament's softening point, open the front door or remove
the glass lid so the chamber does not soften filament in the extruder [1].

## Per material notes

### PLA Basic (most of the swatch board)

- Nozzle 190 to 240 C, preset 220 C; any nozzle size; no hardened nozzle
  needed; AMS compatible; prints on open or enclosed printers [1].
- Bed: Cool Plate 35 to 45 C; Smooth PEI, Textured PEI 45 to 65 C; preset
  uses 35 / 55 / 55 [1] [6]. Glue stick or liquid glue is optional for PLA
  and mainly protects the plate [1].
- Fan 100 % from layer 2 (`close_fan_the_first_x_layers` 1), minimum layer
  time 4 s [6].
- Not for parts that live at about 50 C or hotter; it slowly softens [1].
- Dry 50 to 55 C for 8 h in an oven, or 60 to 70 C for 12 h under a cover on
  the heatbed [2].

### PLA Silk+ (Gold) and PLA Silk (Rose Gold)

- Silk+ is Bambu's current silk line, Silk the older one; both share the
  same PLA family limits [1] [3]. The maker space has one spool of each.
- Nozzle: only 0.2 and 0.4 are recommended by Bambu; 0.6 and 0.8 are not [3].
  The 0.2 preset caps flow at 2 mm3/s [6].
- Gloss recipe from Bambu's silk guide [3]: outer wall 40 to 60 mm/s (start
  at 50), keep the outer wall speed constant ("Don't slow down outer walls"
  in developer mode, cooling slowdown logic "Consistent Surface"), 0.16 mm
  layers, top surface pattern Archimedean Chords or Concentric, nozzle 235 C
  first layer and other layers. Silk+ keeps its layer adhesion at the slow
  outer wall speed, unlike generic silk PLA [10].
- Print the display face upright (Lay on Face) when it is curved; flat
  faces show layer lines and lose gloss [3]. For the maker space's flat
  inlay lettering this does not apply: the inlay sits on the plate.
- Cool Plate SuperTack is not recommended for silk [3]. The maker space
  does not own one.
- Dry at 55 C for 8 h before a visible print; damp silk strings and prints
  unevenly glossy; store under 20 % RH [3].

### PLA Tough+ (Black)

- Bambu's impact-resistant PLA; the product page lists it as compatible
  with every AMS and recommends Bambu Support for PLA or Support for
  PLA/PETG as the interface material because its layer bond is strong
  enough to fuse with same-material supports [9]. The maker space has no
  support filament in stock (confirm on the swatch board).
- Preset runs hotter than PLA Basic: 245 C with a 220 to 250 C range, flow
  18 to 25 mm3/s on 0.4, 2 mm3/s on 0.2, minimum layer time 8 s [6]. Bambu
  notes a slightly stronger, non-pungent smell at that temperature [9].
- Bed, plates, drying, AMS and enclosure: same as PLA (the material table
  counts PLA Tough as standard PLA) [1].
- `check_gcode` refuses the stock Tough+ preset: its first-layer check
  only accepts `M109 S210` to `S239`, and 245 C is outside that. Its body
  window (190 to 250 C) passes 245 C but not a 250 C tune. Widen both for a
  Tough+ project.

### ABS (black, white, gray, red, orange, yellow, blue, teal, green)

- Enclosed printer recommended, door closed; bed 90 to 100 C on Smooth,
  Textured or Engineering plate; Cool Plate not recommended; preset 90 C [1]
  [6]. Glue stick or liquid glue on the plate [1] [11].
- Nozzle 240 to 280 C; preset 260 C first layer, 270 C after; part fan 10
  to 60 %, off for the first 3 layers; air filtration on in the preset [6].
- Warping: avoid very large footprints and high infill; lower the speed
  and raise the bed if it lifts; gyroid infill and 15 % density shrink
  less than straight-line patterns at 50 %+ [11] [7].
- Fumes: Bambu's own page says ABS releases styrene at print temperature
  and recommends an enclosed printer, ventilation, and a vapor mask for
  long jobs; pause or ventilate more if children, pregnant people or people
  with respiratory conditions are present [11]. Flag this to whoever prints.
- AMS: compatible; AMS lite not recommended. AMS 2 Pro cannot dry it
  (65 C ceiling); oven 75 to 85 C for 8 h or heatbed 90 to 100 C for 12 h [1]
  [2].
- The safety gate refuses ABS (nozzle and bed above its PLA window) until
  `NOZZLE_C` and `BED_C` in `slicer.py` are widened, and the
  `M109 S2[1-3]\d` first-layer check must also accept 260 C.

### PETG Basic and PETG Translucent (one clear swatch)

- Bed 60 to 80 C on PEI plates, Cool Plate not recommended, preset 70 C on
  every plate including SuperTack [1] [6]. Open the door or lift the lid
  when the bed is above 60 C so the chamber stays under PETG's 55 C
  softening point [1] [6].
- Nozzle: PETG 240 to 270 C in the wiki, preset Basic 245 C first layer
  then 255 C; Translucent 230 to 260 C, preset 250 C then 245 C [1] [6].
- Flow: Basic 15 mm3/s, Translucent 6 mm3/s on the 0.4 nozzle; Translucent
  has no 0.2 preset [6]. Fan is low (Basic 20 to 40 %, Translucent 10 to
  30 %), off for 3 layers [6].
- Moisture: Basic must be dried after 72 h above 50 % RH; Translucent must
  be dried before every use and kept in desiccant while printing or it
  bubbles and clouds [11] [12]. Oven 60 to 65 C for 8 h, AMS 2 Pro 65 C
  for 12 h [2].
- Transparency depends on speed, nozzle temperature and infill, so test a
  small piece before a visible part [12].
- The safety gate refuses PETG (bed 70 C, nozzle above 250 C) until the
  windows in `slicer.py` are widened.

## Plates the maker space owns, by material

From the material table [1] and the preset plate temperatures [6]:

| Plate on hand | PLA family | ABS | PETG |
|---|---|---|---|
| Smooth PEI (two, one worn) | 45 to 65 C, preset 55; use for 0.2 nozzle and visible undersides (PRINTER_SETUP) | 90 to 100 C, preset 90, glue | 60 to 80 C, preset 70 |
| Textured PEI, gold or black | 45 to 65 C, preset 55; usually installed | 90 to 100 C, preset 90, glue | 60 to 80 C, preset 70 |
| Cool Plate | 35 to 45 C, preset 35 (failed a first layer on 2026-09-24, see PRINTER_SETUP) | not recommended | not recommended |

Wash any plate with dish soap and warm water, never acetone; a clean PEI
plate holds a thin water film instead of beading [1] [5].

## Sources

1. Bambu Lab Wiki, "Filament Guide and Material Table" (nozzle and AMS
   compatibility, nozzle temperature ranges, bed temperatures per plate,
   chamber and door guidance, drying summary, cleaning):
   https://wiki.bambulab.com/en/general/filament-guide-material-table
2. Bambu Lab Wiki, "Filament Drying Recommendations" (Appendix I drying
   parameters per filament, heatbed drying procedure, storage humidity):
   https://wiki.bambulab.com/en/filament-acc/filament/dry-filament
3. Bambu Lab Wiki, "Printing with PLA Silk / Silk+ filaments" (nozzle
   sizes, gloss settings, drying, SuperTack note):
   https://wiki.bambulab.com/en/x1/manual/printing-with-silk-filaments
4. Bambu Lab Wiki, "X1 series screen operation" (Toolbox > Dry Filament,
   print options):
   https://wiki.bambulab.com/en/x1/manual/screen-operation
5. Bambu Lab Wiki, "Textured PEI Plate cleaning guide":
   https://wiki.bambulab.com/en/filament-acc/acc/pei-plate-clean-guide
6. Bambu Studio filament profiles, `resources/profiles/BBL/filament/` on
   the master branch of https://github.com/bambulab/BambuStudio, files
   `Bambu PLA Basic @BBL X1C.json`, `Bambu PLA Silk+ @BBL X1C.json`,
   `Bambu PLA Silk @BBL X1C.json`, `Bambu PLA Tough+ @BBL X1C.json`,
   `Bambu ABS @BBL X1C.json`, `Bambu PETG Basic @BBL X1C.json`,
   `Bambu PETG Translucent @BBL X1C.json` and their `0.2 nozzle` variants,
   flattened through their `inherits` chain (`@base`, `fdm_filament_pla`,
   `fdm_filament_abs`, `fdm_filament_pet`, `fdm_filament_common`). These are
   the same files `tools/bambu_presets.py` flattens from the installed app.
7. Bambu Lab Wiki, "Common print quality problems and solutions" (warping
   causes, infill advice, plate type mismatch):
   https://wiki.bambulab.com/en/knowledge-sharing/common-print-quality-problem
8. Same page as 7, section "Model warping, falling off, or collapsing":
   the printer lowers the nozzle 0.04 mm on a Textured PEI plate after
   leveling, so a wrong plate type in the slicer leaves the nozzle too high.
9. Bambu Lab store, "PLA Tough+":
   https://us.store.bambulab.com/products/pla-tough-upgrade (AMS
   compatibility, support filament advice, odor note; the EU store page
   https://eu.store.bambulab.com/products/pla-tough-upgrade carries the same
   printing notes).
10. Bambu Lab store, "PLA Silk+":
    https://us.store.bambulab.com/products/pla-silk-upgrade (drying after
    opening, slow outer wall, layer bonding).
11. Bambu Lab store, "ABS": https://us.store.bambulab.com/products/abs-filament
    (enclosure, warping advice, styrene warning) and "PETG Basic":
    https://us.store.bambulab.com/products/petg-basic (72 h / 50 % RH drying
    rule).
12. Bambu Lab store, "PETG Translucent":
    https://us.store.bambulab.com/products/petg-translucent (must dry before
    use, desiccant during printing, transparency factors).
