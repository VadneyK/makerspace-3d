# 3D printing tooling research (2026-09-30)

Read-only survey: nothing was installed. Every third-party MCP server runs code on
a machine and is persistent config, so installing one is the owner's call.

## Worth installing (ranked)

1. **build123d-mcp** (https://github.com/pzfreo/build123d-mcp). Apache-2.0, 96
   stars, last commit 2026-09-25. Local CAD session with PNG/SVG previews,
   measurement, printability checks, STEP/STL export. Gives Claude eyes on the
   geometry while designing. Runs locally via uv; use stdio mode (HTTP mode has
   no auth). No 3MF export, so the Bambu Studio CLI stays in the pipeline.
2. **3d-print-modeling skill** (https://github.com/m-esm/3d-print-modeling).
   MIT, 1 star. Same stack as this plugin's tools (trimesh, manifold3d, build123d) plus a
   headless multi-view and section-cut screenshot loop. Needs a Playwright
   Chromium download. Best value: borrow the render loop into the 3d-print-design skill.
3. **bambu-printer-mcp** (https://github.com/DMontgomery40/bambu-printer-mcp).
   GPL-2.0, 167 stars. Offline 3MF inspection and Bambu CLI slicing are the
   only parts we can use (printer control needs LAN access to the X1C). Mostly
   duplicates `tools/slicer.py`; marginal.

## Skip

- **3dp-mcp-server** (mcpmarket "3dp", https://github.com/brs077/3dp-mcp-server):
  build123d wrapper, 13 stars, all commits 2026-03-14 to 03-18, license
  CC BY-NC-ND (no modifications allowed). Abandoned; build123d-mcp covers it.
- **Meshy MCP** (https://github.com/meshy-dev/meshy-mcp-server): AI
  text/image-to-3D in Meshy's cloud, needs the Pro plan (about $20/mo, credits
  per call). Meshy's own blog says it is not built for exact measurements or
  clean flat lettering. Good for figurines, wrong for plaques.
- Bambu LAN MCPs, OctoPrint/Moonraker MCPs: need network access to the printer.
- Blender MCP: organic/scene work, runs arbitrary Python in Blender.
- OpenSCAD MCPs: a second CAD language next to our Python stack.

## Fact checked

Bambu ships a "Bambu PLA Silk+ @BBL X1C 0.2 nozzle" system preset (230 C, max
2 mm3/s); the `n02 slot3 PLA Silk+ Gold` preset that `tools/bambu_presets.py` writes is flattened from it.
Bambu's store lists 0.2 and 0.4 stainless nozzles as recommended for Silk+.
