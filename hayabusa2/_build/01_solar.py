"""
01_solar.py  --  Hayabusa2 solar-array rebuild (Blender 5.1 / Eevee Next)

Rebuilds the solar wings of the photorealistic JAXA Hayabusa2 model so they read
as the real spacecraft (see reference "image 7" / "image 1" / "image 6"): each
wing is a LONG, NARROW, LANDSCAPE blade -- a thin ladder/H yoke off the side of
the bus, a clear gap, then THREE solar panels in a row along the span (X). Each
panel is WIDER along the span (X) than it is deep (Y), so three of them in a row
make one long thin blade. This is the "rotate the old panels 90 degrees" fix:
the previous panels were 0.62 (span) x 1.40 (depth) = tall/portrait/stubby; the
new panels are 0.64 (span) x 1.00 (depth) = landscape.

Authoring conventions (world / meters; HB2_Root sits at origin, identity xform):
    span        = X   (wings extend along +X / -X)
    panel depth = Y   (panels are ~1.0 m deep in Y)
    face normal = +Z  (cell side faces +Z)

Body spec (agreed): the bus is 1.0 (X span) x 1.6 (Y depth) x 1.25 (Z).
The solar paddles ATTACH on the x = +/-0.50 faces and extend along +/-X.

Ownership:
    * We OWN every object whose name starts with "HB2_Solar" and the material
      "HB2_SolarCells" (rebuilt from scratch here).
    * We only REFERENCE the shared materials HB2_Gold_MLI, HB2_Metal and
      HB2_Silver_MLI by name -- we never edit them.

This module is import/exec-safe. build() is fully idempotent: it deletes every
object whose name starts with "HB2_Solar" (old slabs + anything we previously
made), purges the freed meshes, then recreates everything cleanly and (re)builds
the HB2_SolarCells node tree from scratch. It performs NO file open/save, NO
render and NO MCP calls.

Run headless for self-validation (the --shot block lives ONLY in __main__):
    blender --background work_solar.blend --python 01_solar.py -- --shot out.png
"""

import bpy
import bmesh
from mathutils import Vector

# ---------------------------------------------------------------------------
# Configuration (all in world/meters; HB2_Root is at origin with identity xform)
# ---------------------------------------------------------------------------

PREFIX          = "HB2_Solar"          # every owned object name starts with this
COLLECTION_NAME = "HB2_SolarArrays"
ROOT_NAME       = "HB2_Root"
CELL_MAT_NAME   = "HB2_SolarCells"     # we OWN this one -> rebuild node tree

# Shared materials we only REFERENCE (never destructively rebuild)
MAT_YOKE  = "HB2_Gold_MLI"             # gold-foil yoke / ladder, like the refs
MAT_FRAME = "HB2_Silver_MLI"           # silver backing plate behind the cells
MAT_RIB   = "HB2_Metal"                # bare-metal seam ribs / back stiffeners

# --- Bus geometry (the bus is being rebuilt to these dims by another agent) ---
BUS_FACE_X = 0.50                      # +X / -X side faces of the bus (attach here)

# --- Wing plane height (Z of the blade mid-plane) ---
WING_Z = 0.15

# --- Yoke: a long thin ladder/H between the bus face and the inner panel ------
# Lengthened to roughly DOUBLE the body-to-panel gap so the craft reads like the
# real JAXA references (long thin striped boom with a clear gap to the wing).
YOKE_LEN     = 0.95                    # outboard reach of the yoke (X)  (was 0.45)
YOKE_X0      = BUS_FACE_X              # inboard end, on the bus face (x = 0.50)
YOKE_X1      = BUS_FACE_X + YOKE_LEN   # outboard end (x = 1.45)         (was 0.95)
YOKE_Y       = 0.45                    # longerons sit at y = +/- this
YOKE_BAR     = 0.045                   # longeron square cross-section (Y & Z)
YOKE_CROSS_T = 0.04                    # cross-member thickness (X & Z)
YOKE_CROSS_Y = 2.0 * YOKE_Y + YOKE_BAR # cross-member length in Y (spans longerons)
N_CROSS      = 5                       # cross-members along the longer yoke (was 3)

# --- Panels: THREE per wing, in a row along the span (X) ----------------------
# WIDER in span (X) than deep (Y) so three of them make a LONG NARROW blade.
PANEL_X     = 0.64                     # panel size along span (X)  <-- landscape
PANEL_Y     = 1.00                     # panel depth (Y)
PANEL_Z     = 0.02                     # panel thickness (Z)
PANEL_GAP   = 0.03                     # gap between adjacent panels (X)
PANEL_PITCH = PANEL_X + PANEL_GAP      # center-to-center spacing = 0.67
N_PANELS    = 3
# Inner-panel center pushed outboard of the longer yoke so the inner panel edge
# (PANEL_FIRST - PANEL_X/2 = 1.77 - 0.32 = 1.45) sits right at the boom tip
# (YOKE_X1 = 1.45), giving a clear ~0.95 m bus-face-to-panel-edge gap (roughly
# double the old ~0.45 m). The thin boom spans that whole gap, like the refs.
PANEL_FIRST = 1.77                             # inner-panel center X (edge at 1.45)

# --- Thin frame / border around each panel -----------------------------------
FRAME_W = 0.02                         # frame bar width
FRAME_Z = PANEL_Z + 0.006              # frame slightly proud of the cells

# --- Silver backing plate (just below the cell panel) -------------------------
BACK_MARGIN = 0.03                     # extra size around panel in X & Y
BACK_Z      = 0.012                    # backing thickness
BACK_DROP   = 0.018                    # how far below the cell panel center it sits

# --- Back struts / stiffeners running in Y at the panel seams -----------------
STRUT_X = 0.035                        # strut width along span (X)
STRUT_Y = PANEL_Y + 2.0 * BACK_MARGIN  # strut length in Y (full blade depth)
STRUT_Z = 0.05                         # strut height (Z), sits under the blade

# --- Seam ribs across the two gaps between the 3 panels (top side) ------------
RIB_X = 0.045                          # rib width along span
RIB_Y = PANEL_Y + 0.01                 # rib length in Y
RIB_Z = 0.045                          # rib height (Z)

# --- Cell-grid material look --------------------------------------------------
# Dark base so the cells stay near-black in shadow / deep-space shots, with the
# blue arriving as a sunlit specular/coat sheen (see _build_solar_cell_material).
COL_CELL  = (0.0080, 0.0140, 0.0520, 1.0)  # #0a1227 dark indigo cell (slightly deeper)
COL_GRID  = (0.0300, 0.0460, 0.0880, 1.0)  # #1f2c46 gridline (a touch darker too)
COL_SHEEN = (0.050, 0.230, 0.950, 1.0)     # vivid sapphire AR-coat sheen (lit-angle blue)
CELLS_X   = 4                              # cell COLUMNS across one panel (span/X)
CELLS_Y   = 3                              # cell ROWS along panel depth (Y)
# -> 4 x 3 per panel  =>  12 x 3 cells per wing (3 panels in a row).

# --- Edge-softening bevel on panels / frames ---------------------------------
BEVEL_WIDTH = 0.005


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _get_root():
    return bpy.data.objects.get(ROOT_NAME)


def _get_collection():
    """Return the HB2_SolarArrays collection, creating + linking it if absent."""
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _delete_owned_objects():
    """Delete every object whose name starts with PREFIX and purge its mesh."""
    doomed = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
    meshes = set()
    for o in doomed:
        if o.type == 'MESH' and o.data is not None:
            meshes.add(o.data)
        bpy.data.objects.remove(o, do_unlink=True)
    # Purge orphaned meshes we just freed (no remaining users).
    for me in meshes:
        if me.users == 0:
            try:
                bpy.data.meshes.remove(me)
            except (RuntimeError, ReferenceError):
                pass
    # Also sweep any stale leftover meshes named like our objects.
    for me in list(bpy.data.meshes):
        if me.name.startswith(PREFIX) and me.users == 0:
            try:
                bpy.data.meshes.remove(me)
            except (RuntimeError, ReferenceError):
                pass


def _new_box(name, size, location, collection, root, material=None, bevel=False):
    """
    Create an axis-aligned box mesh object centered at `location`.
    size = (sx, sy, sz) full dimensions. Returns the object.
    Optionally adds a small Bevel modifier so edges aren't razor sharp.
    """
    sx, sy, sz = size
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)          # unit cube, -0.5..0.5
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bm.to_mesh(me)
    bm.free()
    me.update()

    obj = bpy.data.objects.new(name, me)
    obj.location = Vector(location)
    collection.objects.link(obj)
    if root is not None:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    if material is not None:
        obj.data.materials.append(material)

    if bevel:
        m = obj.modifiers.new("Bevel", 'BEVEL')
        m.width = BEVEL_WIDTH
        m.segments = 2
        m.limit_method = 'ANGLE'
        m.angle_limit = 0.6981  # 40 deg -> only real corners

    return obj


def _ensure_material(name):
    """Return an existing material by name (shared mats must already exist)."""
    return bpy.data.materials.get(name)


# ---------------------------------------------------------------------------
# HB2_SolarCells material  --  2-axis cell grid (rows AND columns)
# ---------------------------------------------------------------------------

def _build_solar_cell_material():
    """
    (Re)build HB2_SolarCells: a crisp 2-D cell matrix that reads DARK / near-black
    in shadow but FLASHES vivid sapphire-blue where direct light grazes it -- the
    "sunlit blue sheen" of the real arrays (lit panel in image 6; near-black panels
    in the deep-space shot image 10).

    Layout: a Brick texture driven by Object coordinates lays out CELLS_X columns
    across the panel span (X) and CELLS_Y rows in depth (Y); the brick "mortar" is
    the thin gridline between near-square indigo cells. We keep that visible grid.

    Look: the base color stays a deep, dark indigo so the cells sit near-black in
    shadow. The blue is delivered as an anti-reflective COVER-GLASS sheen, not as a
    bright albedo:
      * a strong clear COAT (weight ~0.9) with very low coat roughness (~0.02) and
        a saturated sapphire Coat Tint -> a crisp blue specular highlight wherever
        a light actually hits, so lit cells flash sapphire while shadowed cells stay
        dark;
      * a saturated blue Specular Tint reinforces the same coloured highlight;
      * a Layer Weight (Facing) Fresnel term mixes a touch of the sapphire sheen
        into the base color at grazing angles, so the blue blooms toward the edges /
        glancing-lit regions (the AR-coating look) without lifting the head-on,
        in-shadow cells off black.

    We reuse the datablock if it exists but always clear+rebuild the node tree so
    repeated runs are identical.
    """
    mat = bpy.data.materials.get(CELL_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(CELL_MAT_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    nt.links.clear()

    n_out   = nt.nodes.new("ShaderNodeOutputMaterial")
    n_bsdf  = nt.nodes.new("ShaderNodeBsdfPrincipled")
    n_coord = nt.nodes.new("ShaderNodeTexCoord")
    n_map   = nt.nodes.new("ShaderNodeMapping")
    n_brick = nt.nodes.new("ShaderNodeTexBrick")
    n_bump  = nt.nodes.new("ShaderNodeBump")
    n_rough = nt.nodes.new("ShaderNodeMath")   # gridlines slightly rougher
    # Grazing-angle sapphire sheen: Fresnel (Layer Weight Facing) -> Mix into base.
    n_lw    = nt.nodes.new("ShaderNodeLayerWeight")
    n_sheen = nt.nodes.new("ShaderNodeMixRGB")  # base color <- sapphire at grazing

    n_out.location   = (820, 0)
    n_bsdf.location  = (520, 0)
    n_sheen.location = (300, 180)
    n_lw.location    = (60, 320)
    n_brick.location = (40, 60)
    n_map.location   = (-180, 60)
    n_coord.location = (-380, 60)
    n_bump.location  = (40, -260)
    n_rough.location = (40, -120)

    # --- coordinates: Object space so the grid is independent of UVs/scale ---
    # Each panel object is a unit cube scaled to (PANEL_X, PANEL_Y, PANEL_Z), so
    # Object coords run -0.5..0.5 across each local axis (before object scale).
    # Scale X and Y so the brick lays out CELLS_X x CELLS_Y divisions across the
    # panel's span (X) and depth (Y). Brick repeats once per unit of input, so we
    # divide the requested counts by the local extent to get divisions/meter.
    sx = CELLS_X / PANEL_X          # divisions per local meter in X (span)
    sy = CELLS_Y / PANEL_Y          # divisions per local meter in Y (depth)
    n_map.inputs['Scale'].default_value = (sx, sy, 1.0)

    nt.links.new(n_coord.outputs['Object'], n_map.inputs['Vector'])
    nt.links.new(n_map.outputs['Vector'], n_brick.inputs['Vector'])

    # --- brick tuned to near-square cells with a thin mortar = gridline gap ---
    b = n_brick
    b.offset = 0.0                  # no running-bond offset -> a true grid
    b.offset_frequency = 1
    b.squash = 1.0
    b.squash_frequency = 1
    b.inputs['Color1'].default_value = COL_CELL
    b.inputs['Color2'].default_value = (
        COL_CELL[0] * 1.18, COL_CELL[1] * 1.18, COL_CELL[2] * 1.18, 1.0
    )  # subtle cell-to-cell tonal variation
    b.inputs['Mortar'].default_value = COL_GRID
    b.inputs['Scale'].default_value = 1.0          # already scaled via Mapping
    b.inputs['Mortar Size'].default_value = 0.045  # thin but visible gridline
    b.inputs['Mortar Smooth'].default_value = 0.1
    b.inputs['Bias'].default_value = 0.0
    b.inputs['Brick Width'].default_value = 1.0
    b.inputs['Row Height'].default_value = 1.0

    # --- grazing-angle sapphire sheen mixed into the base color ---------------
    # Layer Weight 'Facing' = 0 head-on, -> 1 at grazing angles. Blend a little of
    # the saturated sapphire sheen over the dark cell base at glancing angles so
    # the array picks up an AR-coating blue toward its edges / glancing-lit areas,
    # while head-on (and in-shadow) cells stay near-black. Blend = 0.30 keeps the
    # base black at facing and reaches ~0.30 sapphire at full grazing -> tinted,
    # not flooded. (The big blue *highlight* comes from the coat/specular below;
    # this term just colours the diffuse roll-off blue instead of grey.)
    n_lw.inputs['Blend'].default_value = 0.22   # sharper grazing-only falloff
    n_sheen.blend_type = 'MIX'
    n_sheen.inputs['Color2'].default_value = COL_SHEEN
    nt.links.new(b.outputs['Color'], n_sheen.inputs['Color1'])      # dark cell base
    nt.links.new(n_lw.outputs['Facing'], n_sheen.inputs['Fac'])     # grazing -> more blue

    # --- glassy cover-glass BSDF (dark base, vivid blue specular/coat) ---------
    n_bsdf.inputs['Base Color'].default_value = COL_CELL
    nt.links.new(n_sheen.outputs['Color'], n_bsdf.inputs['Base Color'])
    n_bsdf.inputs['Metallic'].default_value = 0.42    # semiconductor sheen; lowered
    #   slightly so the dark base stays near-black under diffuse ambient (the blue
    #   now comes from the coat/specular, which fire on DIRECT light, not ambient).
    n_bsdf.inputs['IOR'].default_value = 1.5
    # Strong clear-coat -> a CRISP blue specular highlight wherever light hits.
    # High weight + very low coat roughness = a tight, bright sapphire flash on
    # lit cells; a saturated sapphire Coat Tint colours that highlight blue.
    if 'Coat Weight' in n_bsdf.inputs:
        n_bsdf.inputs['Coat Weight'].default_value = 0.9        # was 0.4
        n_bsdf.inputs['Coat Roughness'].default_value = 0.02    # was 0.04 (crisper)
    if 'Coat Tint' in n_bsdf.inputs:
        n_bsdf.inputs['Coat Tint'].default_value = COL_SHEEN    # sapphire coat sheen
    # Saturated blue specular tint reinforces the coloured highlight.
    if 'Specular Tint' in n_bsdf.inputs:
        n_bsdf.inputs['Specular Tint'].default_value = (0.10, 0.42, 1.0, 1.0)
    if 'Specular IOR Level' in n_bsdf.inputs:
        n_bsdf.inputs['Specular IOR Level'].default_value = 0.6  # a touch hotter spec

    # Roughness: cells glassy (~0.10), gridlines a touch rougher (~0.38). Slightly
    # glassier than before so the sunlit highlight stays tight and bright-blue.
    # Map brick factor (0 = mortar, 1 = cell) -> roughness via Multiply-Add.
    n_rough.operation = 'MULTIPLY_ADD'
    n_rough.inputs[1].default_value = -0.28   # value * (-0.28) ...
    n_rough.inputs[2].default_value = 0.38    # ... + 0.38 => cell~0.10, mortar~0.38
    nt.links.new(b.outputs['Fac'], n_rough.inputs[0])
    nt.links.new(n_rough.outputs['Value'], n_bsdf.inputs['Roughness'])

    # Subtle raised-cell bump so gridlines catch light (cheap, value-driven).
    n_bump.inputs['Strength'].default_value = 0.12
    n_bump.inputs['Distance'].default_value = 0.003
    nt.links.new(b.outputs['Fac'], n_bump.inputs['Height'])
    nt.links.new(n_bump.outputs['Normal'], n_bsdf.inputs['Normal'])

    nt.links.new(n_bsdf.outputs['BSDF'], n_out.inputs['Surface'])
    return mat


# ---------------------------------------------------------------------------
# Geometry builders
# ---------------------------------------------------------------------------

def _build_yoke(side, sgn, coll, root, mat, rib_mat):
    """
    Build one wing's long thin ladder/H yoke between the bus face (x = +/-0.50)
    and the inner panel. Two longerons along X at y = +/- YOKE_Y joined by
    N_CROSS cross-members -> reads as an H / ladder, with a clear visible gap
    before the first panel. Gold-foil longerons, bare-metal rungs.
    """
    objs = []
    cx = sgn * (YOKE_X0 + YOKE_X1) / 2.0     # center X of longerons
    length_x = (YOKE_X1 - YOKE_X0)
    for j, ys in enumerate((+YOKE_Y, -YOKE_Y)):
        objs.append(_new_box(
            f"{PREFIX}Longeron_{side}{j}",
            (length_x, YOKE_BAR, YOKE_BAR),
            (cx, ys, WING_Z),
            coll, root, mat,
        ))
    # Cross-members spaced evenly between the inboard (bus) and outboard ends.
    if N_CROSS == 1:
        fracs = [0.5]
    else:
        fracs = [k / (N_CROSS - 1) for k in range(N_CROSS)]
    for k, f in enumerate(fracs):
        xx = sgn * (YOKE_X0 + f * (YOKE_X1 - YOKE_X0))
        # nudge the end rungs just inside the ends so they read as a closed ladder
        if f == 0.0:
            xx = sgn * (YOKE_X0 + YOKE_CROSS_T * 0.5)
        elif f == 1.0:
            xx = sgn * (YOKE_X1 - YOKE_CROSS_T * 0.5)
        objs.append(_new_box(
            f"{PREFIX}Cross_{side}{k}",
            (YOKE_CROSS_T, YOKE_CROSS_Y, YOKE_CROSS_T),
            (xx, 0.0, WING_Z),
            coll, root, rib_mat,
        ))
    return objs


def _build_panels(side, sgn, coll, root, cell_mat, frame_mat, rib_mat):
    """
    Build one wing's THREE landscape panels in a row along X. Each panel gets:
      * the visible solar-cell blade (HB2_SolarCells, 4x3 grid),
      * a thin frame/border (silver) around it,
      * a silver backing plate just below it,
    plus bare-metal seam ribs on top across the two inter-panel gaps and back
    struts/stiffeners running in Y under the blade at those same seams.
    """
    objs = []
    centers = [sgn * (PANEL_FIRST + i * PANEL_PITCH) for i in range(N_PANELS)]

    for i, xx in enumerate(centers):
        # --- Solar-cell blade (the visible cell grid) -----------------------
        objs.append(_new_box(
            f"{PREFIX}Panel_{side}{i}",
            (PANEL_X, PANEL_Y, PANEL_Z),
            (xx, 0.0, WING_Z),
            coll, root, cell_mat, bevel=True,
        ))

        # --- Thin frame/border around the panel (4 bars) --------------------
        hx = PANEL_X / 2.0
        hy = PANEL_Y / 2.0
        # left/right bars (run in Y, full depth incl. corners)
        for sx_sign, tag in ((+1, "xp"), (-1, "xn")):
            objs.append(_new_box(
                f"{PREFIX}Frame_{side}{i}_{tag}",
                (FRAME_W, PANEL_Y + FRAME_W, FRAME_Z),
                (xx + sx_sign * (hx + FRAME_W * 0.5), 0.0, WING_Z),
                coll, root, frame_mat, bevel=True,
            ))
        # front/back bars (run in X, panel width only)
        for sy_sign, tag in ((+1, "yp"), (-1, "yn")):
            objs.append(_new_box(
                f"{PREFIX}Frame_{side}{i}_{tag}",
                (PANEL_X, FRAME_W, FRAME_Z),
                (xx, sy_sign * (hy + FRAME_W * 0.5), WING_Z),
                coll, root, frame_mat, bevel=True,
            ))

        # --- Silver backing plate, slightly larger, set just below ----------
        objs.append(_new_box(
            f"{PREFIX}Back_{side}{i}",
            (PANEL_X + BACK_MARGIN, PANEL_Y + BACK_MARGIN, BACK_Z),
            (xx, 0.0, WING_Z - BACK_DROP),
            coll, root, frame_mat, bevel=True,
        ))

    # --- Seam ribs (top) across the two gaps between the 3 panels -----------
    seams = [(centers[i] + centers[i + 1]) / 2.0 for i in range(N_PANELS - 1)]
    for s, xx in enumerate(seams):
        objs.append(_new_box(
            f"{PREFIX}Rib_{side}{s}",
            (RIB_X, RIB_Y, RIB_Z),
            (xx, 0.0, WING_Z),
            coll, root, rib_mat,
        ))

    # --- Back struts/stiffeners (run in Y) under the blade at the seams ------
    # One at each panel-to-panel seam and one at the inboard root of the blade.
    strut_x = list(seams)
    strut_x.append(sgn * (PANEL_FIRST - PANEL_X / 2.0 - PANEL_GAP / 2.0))  # inboard root
    for s, xx in enumerate(strut_x):
        objs.append(_new_box(
            f"{PREFIX}Strut_{side}{s}",
            (STRUT_X, STRUT_Y, STRUT_Z),
            (xx, 0.0, WING_Z - BACK_DROP - STRUT_Z * 0.3),
            coll, root, rib_mat,
        ))

    return objs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build():
    """
    Idempotent rebuild of the solar arrays. Safe to run repeatedly: deletes all
    HB2_Solar* objects first, then recreates, per wing, a long thin ladder yoke +
    3 landscape panels (frame + cells + backing) + seam ribs + back struts, and
    (re)builds the HB2_SolarCells material. No file IO, no render, no MCP.
    """
    root = _get_root()
    coll = _get_collection()

    # (a) wipe everything we own
    _delete_owned_objects()

    # (b) rebuild the cell-grid material (reuse datablock, clear+rebuild tree)
    cell_mat  = _build_solar_cell_material()
    frame_mat = _ensure_material(MAT_FRAME) or cell_mat
    rib_mat   = _ensure_material(MAT_RIB) or cell_mat
    yoke_mat  = _ensure_material(MAT_YOKE) or rib_mat

    # (c) recreate geometry for both wings (L at -X, R at +X, mirrored)
    created = []
    for side, sgn in (("L", -1.0), ("R", +1.0)):
        created += _build_yoke(side, sgn, coll, root, yoke_mat, rib_mat)
        created += _build_panels(side, sgn, coll, root, cell_mat, frame_mat, rib_mat)

    # Make sure nothing we made lingers in another collection.
    for o in created:
        for c in list(o.users_collection):
            if c is not coll:
                c.objects.unlink(o)
        if o.name not in coll.objects:
            coll.objects.link(o)

    # Refresh dependency graph so downstream reads see final transforms.
    bpy.context.view_layer.update()

    n_panels = sum(1 for o in created if o.name.startswith(PREFIX + "Panel_"))
    tip = PANEL_FIRST + (N_PANELS - 1) * PANEL_PITCH + PANEL_X / 2.0
    print(f"[01_solar] build(): created {len(created)} objects, "
          f"{n_panels} cell panels ({n_panels // 2}/wing). "
          f"Panel = {PANEL_X} x {PANEL_Y} x {PANEL_Z} (span x depth x thick). "
          f"Cells = {CELLS_X}x{CELLS_Y}/panel ({CELLS_X * N_PANELS}x{CELLS_Y}/wing). "
          f"Attach x=+/-{BUS_FACE_X}. Tip-to-tip span ~= {2 * tip:.2f} m.")
    return created


# ---------------------------------------------------------------------------
# Test-only scaffolding (NOT part of build()).  Runs only when executed directly
# AND only renders when "--shot <path>" is present on the command line.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    build()

    if "--shot" in sys.argv:
        png_path = sys.argv[sys.argv.index("--shot") + 1]

        scene = bpy.context.scene

        # Cheap Eevee preview just for geometry/material checks.
        try:
            scene.render.engine = 'BLENDER_EEVEE_NEXT'
        except Exception:
            try:
                scene.render.engine = 'BLENDER_EEVEE'
            except Exception:
                pass
        try:
            scene.eevee.taa_render_samples = 16
        except Exception:
            pass
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = False

        import os
        base, ext = os.path.splitext(png_path)

        def _make_cam(name, loc, look_at, lens=40):
            cam_data = bpy.data.cameras.new(name)
            cam_data.lens = lens
            cam = bpy.data.objects.new(name, cam_data)
            bpy.context.scene.collection.objects.link(cam)
            cam.location = Vector(loc)
            direction = Vector(look_at) - Vector(loc)
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            return cam

        target = (0.0, 0.0, WING_Z)
        shots = [
            ("_TMP_Cam_top",   (0.0, 0.0, 12.0), target, base + "_top" + ext),     # top-down (best for span)
            ("_TMP_Cam_34",    (7.0, -8.0, 5.0), target, base + ext),              # 3/4 hero
            ("_TMP_Cam_front", (0.0, -11.0, 0.6), target, base + "_front" + ext),  # broadside
        ]
        for name, loc, look, out in shots:
            cam = _make_cam(name, loc, look)
            scene.camera = cam
            scene.render.filepath = out
            bpy.ops.render.render(write_still=True)
            print(f"[01_solar] wrote test render: {out}")
