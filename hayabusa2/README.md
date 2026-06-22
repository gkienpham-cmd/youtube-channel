# Hayabusa2 — Procedural Blender Asset (Episode 01)

A photoreal 3D model of JAXA's **Hayabusa2** asteroid sample-return spacecraft, built
**procedurally** in Blender and rendered in three hero scenes for the channel's Episode 01.
This doc is the durable reference for the build — read it before editing the scene or scripts.

## Overview
- **Engine:** Blender **5.1** / **Eevee Next** (`scene.render.engine = "BLENDER_EEVEE"`), **AgX** view
  transform, raytraced reflections on. Units **metric** (1 unit = 1 m).
- **Master scene:** one `.blend` (`hayabusa2.blend`) holds the craft + Earth + Ryugu + starfield;
  the render harness reuses it for all three shots by toggling lights / world / object visibility.
- **Everything is scripted.** The geometry/materials are (re)built by idempotent `_build/*.py`
  scripts so the scene can be regenerated deterministically. Edit the scripts, not (only) the .blend.

## Files & layout
```
hayabusa2/
├── hayabusa2.blend        # master scene (binary; the saved source of truth)
├── render_finals.py       # render harness: 3 scenes, headless, per-scene toggles
├── _build/                # idempotent procedural build scripts (the "source")
│   ├── 01_solar.py        #   solar arrays + cell material
│   ├── 02_craft.py        #   bus/fuselage, instruments, antennas, ion engines, greebles
│   ├── 02_instruments.py  #   RETIRED no-op shim (superseded by 02_craft.py)
│   ├── 03_stars.py        #   starfield world (Voronoi pinpoints + faint Milky Way)
│   ├── 04_earth.py        #   Earth (Blue Marble) + cloud + atmosphere shells
│   ├── 05_ryugu.py        #   asteroid Ryugu body + close surface + boulders
│   └── 06_materials.py    #   shared MLI/radiator/ion-glow materials
├── renders/               # 4K finals: studio_beauty.png, cruise.png, ryugu.png
└── textures/              # bluemarble.jpg (packed into the .blend)
```

## Conventions
- `HB2_Root` is an empty at the origin with **identity transform** (rotation z = 0); all craft
  parts are parented to it. Do **not** re-introduce a root rotation (an old phase span the whole
  craft 90° about Z — that's reverted).
- All owned objects/materials are prefixed **`HB2_`** (e.g. `HB2_SolarPanel_*`, `HB2_Gold_MLI`).
  Build scripts wipe-by-prefix then rebuild, so names matter.
- Bus axes: **+Z** top deck (antennas) / **−Z** sampler-horn underside / solar booms on **±X** /
  ion engines on **−Y**. Bus ≈ **1.0 (X) × 1.6 (Y) × 1.25 (Z)**.
- Collections: `Hayabusa2` (craft), `Environment` (Earth + Ryugu — toggle these per-OBJECT by
  name prefix, never by hiding the whole collection), `Cameras`, `Lights`, `HB2_FX` (ion glow).

## Build pipeline (`_build/`)
Each script defines a module-level **`build()`** that is **idempotent** (deletes everything it owns
by name prefix, then recreates it) and does **no file IO / no render / no MCP**. The `if __name__
== "__main__"` block only runs a standalone test render — it does **not** run on import.

**To run a build into the live/open scene** (the integration pattern), exec the file with
`__name__` set to something non-`"__main__"`, then call `build()`:
```python
ns = {"__name__": "hb2_build", "__file__": path}
exec(compile(open(path).read(), path, 'exec'), ns)
ns["build"]()            # rebuilds that subsystem in place
```
Then `bpy.context.view_layer.update()` and save. Per-script ownership is disjoint (no two scripts
fight over the same objects). `02_instruments.py` is a retired no-op (kept only so old references
don't break) — `02_craft.py` owns the bus/instruments now.

## Render harness (`render_finals.py`)
One master scene → three shots via `setup_scene(name)` toggling cameras / lights / world /
visibility. Headless:
```
Blender --background hayabusa2.blend --python render_finals.py -- <studio|cruise|ryugu> [--preview] [--out=/abs/path.png]
```
`--preview` = 1280×720 @ 64 samples (fast); default = **3840×2160 @ 256** (4K final → `renders/`).
- **`CAM_RIG`** — per-scene `loc/aim/lens` for the shared `HB2_PreviewCam` (TRACK_TO `HB2_AimRyugu`).
  ⚠️ **Cameras do NOT auto-fit** — if the craft/wings are resized you must re-frame `CAM_RIG`
  (pull back / change lens) and preview-check, or the wings clip.
- **`_setup_flyby_lights(name)`** — per-scene deep-space lighting (cruise vs ryugu), see below.
- **Render-time lights** (`HB2_Sun`, `HB2_FillSun`, `HB2_RimSun`, `HB2_FlybyFill`, `HB2_EarthFill`)
  are **created at render time by the harness, NOT saved in the .blend**. Studio uses the in-scene
  `HB2_Studio_Key/Fill/Rim` area lights instead.

## Scene anatomy
### Spacecraft (`02_craft.py`, `06_materials.py`)
Bus with wrinkled **gold/black/silver MLI** foil (Principled, grid-seam shader), flat-octagon
**HGA** antennas on +Z (NOT dishes), four **μ10 ion thrusters** on a white IES plate (−Y) with a
bright blue glow (`HB2_IonGlow`, emission), RCS thrusters, sampler horn (−Z), reentry capsule,
instruments (ONC/LIDAR/NIRS3/TIR/star trackers), and greebles. Ion glow material lives in
`06_materials.py` (`CORE_STRENGTH 11`, `EDGE 3`, color ≈ (0.15,0.45,1.0)) — global, so every shot
that shows the engines gets the brighter blue.

### Solar arrays (`01_solar.py`) — **stylized**
> ⚠️ **Deliberate stylized choice:** the panels run **parallel to the world Y axis** (a broad
> paddle crossing the end of a thin **X** boom — a "T"). The *real* Hayabusa2 runs the blade
> **along** the boom (X). The creator chose the Y orientation on purpose — do NOT "correct" it to
> match the real craft unless asked.

Per wing: a thin two-rail **yoke/boom** along X (`HB2_SolarLongeron_*`, length 1.9, tip at x=2.40)
with a **single cross-bar** (`HB2_SolarCross_*`) at the **3/4 point** (x = 1.925, closer to the
panel). At the boom tip, **3 segments stacked along Y** (`HB2_SolarPanel_{side}{0,1,2}`), each
**1.5 (X) × 2.4 (Y) × 0.02**, blade center x = ±3.15 → tip-to-tip **7.8 m**, paddle Y-length
**7.26 m**. Adjacent plates are joined by **two small evenly-spaced connector tabs per seam**
(`HB2_SolarRib_{side}{seam}_{tab}`, 8 total) — museum-model look (ref `hayabusa2 image 4.jpg`).
Cells: 5×10 per segment via a Brick-on-Object-coords material (`HB2_SolarCells`). The cell look is a
**dark blue base + a bright blue specular/coat glint** (the blue arrives on direct sun, cells stay
dark in shadow) — tuned for an intense sun reflection (cell roughness ≈ 0.045, Specular IOR Level
0.85, Metallic 0.25; AgX-safe, kept blue not white).

Key derived relationships (auto-scale from `PANEL_X`/`PANEL_Y`/`YOKE_LEN`):
`BLADE_CX = YOKE_X1 + PANEL_X/2`; panel inner edge always == boom tip; cross at
`YOKE_X0 + YOKE_CROSS_FRAC·(YOKE_X1−YOKE_X0)`. Change only the constants; the rest follows.

### Earth (`04_earth.py`) — **cruise shot only**
UV sphere at **(−4, 27, 4)**, radius 8, real **NASA Blue Marble** texture (packed), with procedural
**cloud** + **atmosphere** shells (Fresnel blue rim, emission **0.60**). It has no self-emission, so
its brightness comes from scene light. In cruise the key sun is **behind** Earth (backlit); a dim
dedicated `HB2_EarthFill` sun (in the harness) lifts the camera-facing side to a readable lit
gibbous while keeping the backlit/terminator look.

### Ryugu (`05_ryugu.py`) — **ryugu shot only**
A rounded oblate "spinning-top" body (`HB2_RyuguBody`, modelled ~170 BU at origin) with **4
displacement layers** (blocky + crisp Voronoi crags + craters + grit) and **~500 scattered angular
boulders** raycast-anchored to the displaced surface; dark bluish-grey albedo. The harness scales
it 0.125 and moves it to (6,34,−7) for the hero shot (boulders parented, so they follow). It
engulfs the craft at origin → the harness **hides `HB2_RyuguBody*` in studio + cruise**.

### Starfield (`03_stars.py`)
World shader: Voronoi pinpoint stars (power-curve brightness, per-star color ramp) + faint
Milky-Way band. High emission (~9) because AgX compresses it.

## Lighting (per scene)
- **studio** — black world + in-scene `HB2_Studio_Key/Fill/Rim` area lights; engines off (clean
  beauty); Earth + Ryugu hidden.
- **cruise** — starfield world; **key sun behind Earth** (backlit), directional fill/rim **off**, a
  **local area fill** (`HB2_FlybyFill`, inverse-square so it lifts the craft but not the distant
  Earth) + the `HB2_EarthFill` sun; ion engines **on**; Earth visible, Ryugu hidden.
- **ryugu** — starfield; bright-ish key over the camera shoulder (energy 6.5) + cool fill + rim;
  ion engines off (descent); Ryugu body visible, Earth hidden.
`HB2_FlybyFill` and `HB2_EarthFill` are **cruise-only** and explicitly hidden in studio/ryugu (they
are NOT in the `SUNS` list, which is shown in ryugu).

## Key decisions & gotchas
- **Stylized Y solar panels** (above) — intentional, not a bug.
- **Cameras are static** — re-frame `CAM_RIG` whenever the wings/craft are resized; nothing
  auto-fits.
- **Render-time lights** aren't in the .blend — they're created by `render_finals.py` each render.
- **`Environment` collection** holds BOTH Earth and Ryugu — toggle visibility per-object by name
  prefix, never by hiding the collection.
- **Idempotent builds** wipe-by-prefix; keep the `HB2_` naming intact.
- The cruise final is the slow one (~4–6 min at 4K — backlit scene + raytracing + area light).

## Current state (latest)
Solar paddle **1.5 × 2.4 × 0.02** per segment, tip-to-tip **7.8 m**, cross at **3/4** (1.925), 8
seam-connector tabs, bright blue cells. Earth atmosphere emission **0.60** + cruise `HB2_EarthFill`.
Three 4K finals in `renders/`. (The full phase-by-phase log lives in Claude's project memory at
`~/.claude/projects/<this project>/memory/hayabusa2-blender-build.md`.)

## Making changes (checklist)
1. Edit the relevant `_build/*.py` constant(s)/material(s) (and `render_finals.py` for lighting/cams).
2. Exec the script(s) into the live scene → `build()`; verify object dims/positions; **save** the
   `.blend`.
3. `--preview` render the affected shots; re-frame cameras if the craft size changed; tune.
4. Render the 4K finals to `renders/`; review.
