"""
07_torifune.py  —  Asteroid "Torifune" for the Hayabusa2 / Eevee Next scene.

Builds an elongated, irregular, heavily-cratered, boulder-strewn S-type (stony
silicate) asteroid, brighter & warmer than the existing dark Ryugu. Built
idempotently into the `Environment` collection:
  (a) HB2_TorifuneBody     — single elongated lumpy mass (~180 x 68.6 x 72.9 BU
                             pre-displace; axis ratio ~0.41 => roughly 2.4:1
                             long:short), with a SUBTLE off-center waist hint so
                             it reads as ONE lumpy body (a possible-but-unconfirmed
                             contact binary, NOT a split peanut). Centered at its
                             own origin; the orchestrator positions/scales it.
  (b) HB2_TorifuneBoulder* — 380 boulders scattered over the ELONGATED surface,
                             raycast-anchored onto the true displaced body.
  (c) HB2_Torifune         — bright, warm light-grey stony material (clearly
                             brighter + warmer than HB2_Ryugu's near-black bluish).

Honors the research: highly elongated, possible contact binary, ~450-476 m,
S/Sq-type, ~60% olivine / 40% pyroxene, moderate space weathering, broadly
uniform surface; and the reference photo (a single irregular light-grey cratered
body). Long axis = world X (deliberate).

Design notes
------------
* OWNS the Torifune asteroid only. Never touches the spacecraft (HB2_* craft/
  solar/instruments), HB2_Earth*, HB2_Ryugu*, cameras, lights, or world.
* Idempotent: every object/mesh/texture it owns is removed by name (prefix) and
  rebuilt from scratch on each call to build().
* Cheap: all scattered boulders share a tiny pool of mesh datablocks (linked
  duplicates), so 380 rocks cost only a handful of unique meshes. Boulders are
  faceted/angular (flat-shaded decimated icospheres), not round.
* No file IO, no MCP, no rendering inside build().
* This is a FLYBY at distance (not a descent): body + boulders only. NO close
  rubble dome, and NO discrete mega-boulder (surface is homogeneous per research).

Validate (headless):
  Blender --background --factory-startup --python 07_torifune.py -- --shot out.png
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler


# ----------------------------------------------------------------------------- #
#  Constants                                                                     #
# ----------------------------------------------------------------------------- #
ENV_COLL = "Environment"
MAT_NAME = "HB2_Torifune"

# Owned-object name prefixes (everything matching is wiped on rebuild).
OWNED_PREFIXES = ("HB2_TorifuneBody", "HB2_TorifuneBoulder")
# Owned mesh-datablock / texture prefixes (cleaned so reruns don't pile up data).
OWNED_MESH_PREFIXES = ("HB2_TorifuneBodyMesh", "HB2_TorRockPool")
OWNED_TEX_PREFIX = "HB2_TorifuneDisp"

# Whole-body geometry: a workable scale (large BU; render-time scaling happens
# elsewhere). Long axis = world X (deliberate).
BODY_LONG   = 90.0     # +/-X half-length (long axis)
# FAT prolate spheroid: two EQUAL minor axes (circular cross-section), long axis = X.
# 0.70 -> dims ~180 x 126 x 126 BU => ~1.43:1 (clearly elongated but FAT / sphere-like,
# matching the rounded reference). Was 0.46 = 2.17:1 which read too thin/egg-y.
AXIS_MID    = 0.70     # Y factor  (== AXIS_SHORT for a true prolate spheroid)
AXIS_SHORT  = 0.70     # Z factor
WAIST_DEPTH = 0.0      # NO waist: a prolate spheroid is fattest in the middle
WAIST_POS   = 0.12     # (unused while WAIST_DEPTH = 0)
WAIST_WIDTH = 0.42     # (unused while WAIST_DEPTH = 0)
LUMP_GAIN   = 0.08     # low-freq irregularity -> a lumpy / rougher silhouette
# One small distinct protrusion (the nub on the real Torifune's limb in the reference):
# a tight localized radial bulge so the body isn't a perfectly smooth ellipsoid.
NUB_DIR     = (0.10, 0.32, 0.86)   # nub direction (upper, slightly +Y)
NUB_HEIGHT  = 0.15     # bulge height as a fraction of local radius
NUB_TIGHT   = 8.0      # exponent: higher = tighter / more localized bump


# ----------------------------------------------------------------------------- #
#  Small helpers                                                                 #
# ----------------------------------------------------------------------------- #
def _env_collection():
    """Return (create if needed) the Environment collection, linked to the scene."""
    coll = bpy.data.collections.get(ENV_COLL)
    if coll is None:
        coll = bpy.data.collections.new(ENV_COLL)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _purge_owned():
    """Remove every object / mesh / texture this script owns (idempotency)."""
    # Objects first (so meshes become unused).
    for obj in [o for o in bpy.data.objects
                if any(o.name.startswith(p) for p in OWNED_PREFIXES)]:
        bpy.data.objects.remove(obj, do_unlink=True)
    # Meshes.
    for me in [m for m in bpy.data.meshes
               if any(m.name.startswith(p) for p in OWNED_MESH_PREFIXES)]:
        if me.users == 0:
            bpy.data.meshes.remove(me)
    # Displacement textures.
    for tx in [t for t in bpy.data.textures if t.name.startswith(OWNED_TEX_PREFIX)]:
        if tx.users == 0:
            bpy.data.textures.remove(tx)


def _link_only(obj, coll):
    """Ensure obj lives in exactly `coll` (unlink from any other collection)."""
    for c in list(obj.users_collection):
        if c is not coll:
            c.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def _shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def _shade_flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False


# ----------------------------------------------------------------------------- #
#  Material — bright, warm light-grey stony silicate (S-type)                    #
# ----------------------------------------------------------------------------- #
def _build_material():
    """(Re)build HB2_Torifune: bright warm light-grey, rough, strong bump relief.

    Clearly BRIGHTER + WARMER than HB2_Ryugu (which is near-black ~0.03 bluish).
    Base albedo ~0.15-0.21 linear, R>G>B throughout (warm tan -> weathered grey),
    ~5x brighter than Ryugu. Subtle warm-grey variation via large-scale noise +
    Color Ramp. Relief = two stacked bump layers (medium rubble + fine grit)
    driven by object-coordinate noise so the surface reads as rock under
    directional light.
    """
    mat = bpy.data.materials.get(MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(MAT_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (820, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (480, 0)

    # --- Base color: warm tan -> weathered grey ----------------------------
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    geo.location = (-1100, 260)
    tcoord = nt.nodes.new("ShaderNodeTexCoord")
    tcoord.location = (-1100, -260)

    col_noise = nt.nodes.new("ShaderNodeTexNoise")
    col_noise.location = (-820, 260)
    col_noise.noise_dimensions = '3D'
    col_noise.inputs["Scale"].default_value = 1.3       # large patches
    col_noise.inputs["Detail"].default_value = 4.0
    col_noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(geo.outputs["Position"], col_noise.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-540, 260)
    # Bright + warm (linear values; R>G>B = warm; ~5x brighter than Ryugu).
    e = ramp.color_ramp.elements
    e[0].position = 0.0
    e[0].color = (0.205, 0.170, 0.140, 1.0)   # warm tan
    e[1].position = 1.0
    e[1].color = (0.150, 0.140, 0.130, 1.0)   # weathered grey
    # mid warm grey stop so it doesn't read as a flat two-band split
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = (0.180, 0.158, 0.135, 1.0)    # mid warm grey
    nt.links.new(col_noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # --- Relief: medium rubble bump + fine grit bump (stacked) -------------
    med_noise = nt.nodes.new("ShaderNodeTexNoise")
    med_noise.location = (-820, -60)
    med_noise.noise_dimensions = '3D'
    med_noise.inputs["Scale"].default_value = 5.5
    med_noise.inputs["Detail"].default_value = 10.0
    med_noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(tcoord.outputs["Object"], med_noise.inputs["Vector"])

    bump_med = nt.nodes.new("ShaderNodeBump")
    bump_med.location = (-360, -60)
    bump_med.inputs["Strength"].default_value = 0.54    # rough rocky micro-relief
    bump_med.inputs["Distance"].default_value = 0.02
    nt.links.new(med_noise.outputs["Fac"], bump_med.inputs["Height"])

    fine_noise = nt.nodes.new("ShaderNodeTexNoise")
    fine_noise.location = (-820, -380)
    fine_noise.noise_dimensions = '3D'
    fine_noise.inputs["Scale"].default_value = 24.0
    fine_noise.inputs["Detail"].default_value = 12.0
    fine_noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(tcoord.outputs["Object"], fine_noise.inputs["Vector"])

    bump_fine = nt.nodes.new("ShaderNodeBump")
    bump_fine.location = (120, -120)
    bump_fine.inputs["Strength"].default_value = 0.34    # rough rocky micro-relief
    bump_fine.inputs["Distance"].default_value = 0.006
    nt.links.new(fine_noise.outputs["Fac"], bump_fine.inputs["Height"])
    nt.links.new(bump_med.outputs["Normal"], bump_fine.inputs["Normal"])
    nt.links.new(bump_fine.outputs["Normal"], bsdf.inputs["Normal"])

    # --- BSDF scalar values ------------------------------------------------
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.90       # 0.85-0.95
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.10   # low specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.10

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ----------------------------------------------------------------------------- #
#  Displacement textures                                                         #
# ----------------------------------------------------------------------------- #
def _new_clouds_tex(name, size, depth):
    tx = bpy.data.textures.new(name, type='CLOUDS')
    tx.noise_scale = size
    tx.noise_depth = depth
    tx.noise_basis = 'BLENDER_ORIGINAL'
    return tx


def _new_musgrave_voronoi_tex(name, size):
    """Voronoi-distance texture -> blocky / faceted rubble undulation."""
    tx = bpy.data.textures.new(name, type='VORONOI')
    tx.noise_scale = size
    tx.distance_metric = 'DISTANCE'
    return tx


# ----------------------------------------------------------------------------- #
#  Angular-boulder mesh pool (shared datablocks; faceted, not round)             #
# ----------------------------------------------------------------------------- #
def _make_rock_mesh(name, seed, subdiv=2, jitter=0.30, squash=0.7):
    """Create one angular boulder mesh (a chunky, faceted rock — not a spike).

    Built from a subdiv-2 icosphere (80 faces) whose verts get a few octaves of
    smooth low-frequency lumpiness (so the silhouette is blocky/irregular, not
    needle-sharp), an anisotropic squash, and a hard planar 'cleave' on one or two
    sides to read as a fractured face. Flat-shaded so facets catch the hard sun
    (matches torifune's angular rubble).
    """
    rng = random.Random(seed)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)

    # A few coherent "lobe" directions: displace each vert by sum of cosine lobes.
    lobes = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(),
              rng.uniform(0.12, jitter)) for _ in range(5)]
    for v in bm.verts:
        n = v.co.normalized()
        disp = 0.0
        for d, amp in lobes:
            disp += amp * max(0.0, n.dot(d)) ** 1.5
        # a little fine per-vertex grit too, but small -> avoids spikes
        disp += rng.uniform(-0.06, 0.06)
        v.co = n * (1.0 + disp)

    # anisotropic squash (rocks are rarely spherical)
    sx = rng.uniform(0.85, 1.2)
    sy = rng.uniform(0.85, 1.2)
    sz = squash * rng.uniform(0.85, 1.05)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz

    # Cleave one or two flat fracture faces: clamp verts beyond a random plane.
    for _ in range(rng.randint(1, 2)):
        pn = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                     rng.uniform(-1, 1))).normalized()
        d = rng.uniform(0.55, 0.8)            # plane offset from center
        for v in bm.verts:
            proj = v.co.dot(pn)
            if proj > d:
                v.co -= pn * (proj - d)       # flatten onto the plane

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    # flat shading -> angular facets
    for p in me.polygons:
        p.use_smooth = False
    return me


def _build_rock_pool(prefix, count, seed0):
    """Return a list of `count` distinct angular rock meshes for instancing."""
    pool = []
    for i in range(count):
        # mostly chunky subdiv-2; a few subdiv-3 for the biggest blocks
        sub = 3 if (i % 6 == 0) else 2
        me = _make_rock_mesh(f"{prefix}_{i:02d}", seed0 + i * 17,
                             subdiv=sub,
                             jitter=0.30 if sub == 2 else 0.24,
                             squash=0.6 + (i % 3) * 0.12)
        pool.append(me)
    return pool


# ----------------------------------------------------------------------------- #
#  (a) Whole elongated irregular body  HB2_TorifuneBody                          #
# ----------------------------------------------------------------------------- #
def _build_body(coll, mat):
    """FAT prolate spheroid (clearly elongated but sphere-like), solid + ROUGH-surfaced.

    Icosphere -> fat prolate ellipsoid (long axis = X, two EQUAL minor axes) -> low-
    frequency lumpy irregularity -> one small localized nub on the limb -> layered
    NORMAL displacement (broad undulation + crater bowls + angular crags + medium
    lumps + fine grit) so the surface reads as a heavily cratered, rough silicate
    rubble body. Centered at its own origin for the orchestrator.
    """
    # Icosphere (NO poles) so the surface + displacement are EVEN. A UV sphere
    # leaves a pinwheel/starburst where its verts converge at the poles (visible
    # end-on) and stretches geometry toward them; an icosphere is uniform.
    # subdiv 7 ~= 40k verts: enough density for crisp ROUGH displacement detail.
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=7, radius=1.0)

    # 3 FIXED deterministic low-frequency lobes (so rebuilds are identical).
    lobes = [(Vector(( 0.8, 0.4, 0.45)).normalized(), 0.55),
             (Vector((-0.5, 0.7, -0.30)).normalized(), 0.30),
             (Vector(( 0.2, -0.6, 0.75)).normalized(), 0.45)]
    nub_dir = Vector(NUB_DIR).normalized()

    for v in bm.verts:
        n = v.co.normalized()
        # 1) prolate ellipsoid (long axis = X, equal minor axes -> circular section)
        ex = BODY_LONG * n.x
        ey = BODY_LONG * AXIS_MID * n.y
        ez = BODY_LONG * AXIS_SHORT * n.z
        # 2) (optional) waist pinch — disabled for a true prolate spheroid (WAIST_DEPTH=0)
        xa = ex / BODY_LONG
        d = (xa - WAIST_POS) / WAIST_WIDTH
        pinch = 1.0 - WAIST_DEPTH * math.exp(-(d * d))
        ey *= pinch
        ez *= pinch
        # 3) very gentle low-frequency irregularity (stays convex; no big dents)
        wob = 1.0
        for ldir, amp in lobes:
            wob += LUMP_GAIN * amp * (max(0.0, n.dot(ldir)) ** 1.5 - 0.30)
        ex *= wob
        ey *= wob
        ez *= wob
        # 4) one small localized nub on the limb (tight radial bulge)
        nub = 1.0 + NUB_HEIGHT * (max(0.0, n.dot(nub_dir)) ** NUB_TIGHT)
        ex *= nub
        ey *= nub
        ez *= nub
        v.co = Vector((ex, ey, ez))
    bm.normal_update()

    me = bpy.data.meshes.new("HB2_TorifuneBodyMesh")
    bm.to_mesh(me)
    bm.free()
    body = bpy.data.objects.new("HB2_TorifuneBody", me)
    body.location = (0.0, 0.0, 0.0)
    me.materials.append(mat)
    _shade_smooth(body)
    _link_only(body, coll)

    # --- LOW-relief displacement (4 stacked Displace mods, NORMAL) ----------
    # Tuned to match the uploaded reference: a SMOOTH, SOLID body with broad
    # shallow features (gentle facets + degraded crater bowls), NOT a boulder-
    # popcorn coat. Total strengths are ~1/3 of the previous pass so the prolate
    # silhouette stays clean and the surface reads as bedrock under directional
    # light. The crater mechanic (Voronoi DISTANCE, high mid_level) is preserved
    # but gentle: shallow bowls with soft raised rims.
    #
    # --- ROUGH layered displacement (6 stacked Displace mods, NORMAL) -------
    # Heavily-cratered, craggy rubble look with DEEPER craters in TWO sizes (a few
    # big degraded basins + a denser medium crater field) for a natural, varied
    # surface. Tuned up from the previous pass but kept believable, not exaggerated.
    # Icosphere subdiv 7 keeps the detail crisp without UV-sphere pole streaks.
    #
    # 1) big broad undulation (clouds) -> large-scale lumps, the base form
    t_und = _new_clouds_tex("HB2_TorifuneDisp_Und", size=0.70, depth=4)
    m1 = body.modifiers.new("DispUnd", 'DISPLACE')
    m1.texture = t_und
    m1.strength = BODY_LONG * 0.038
    m1.mid_level = 0.5
    m1.direction = 'NORMAL'
    # 2) big deep crater basins (Voronoi DISTANCE, LARGE cells -> few/big, high
    #    mid_level -> deep) -> a few large degraded basins (crater-size variety).
    t_bigcr = _new_musgrave_voronoi_tex("HB2_TorifuneDisp_BigCrater", size=1.0)
    m2 = body.modifiers.new("DispBigCrater", 'DISPLACE')
    m2.texture = t_bigcr
    m2.strength = BODY_LONG * 0.027
    m2.mid_level = 0.80
    m2.direction = 'NORMAL'
    # 3) main crater field, DEEPER (Voronoi DISTANCE, mid cells; higher strength +
    #    higher mid_level -> deeper bowls with sharper rims).
    t_crater = _new_musgrave_voronoi_tex("HB2_TorifuneDisp_Crater", size=0.55)
    m3 = body.modifiers.new("DispCrater", 'DISPLACE')
    m3.texture = t_crater
    m3.strength = BODY_LONG * 0.031     # deeper craters (was 0.026)
    m3.mid_level = 0.85                 # more inward -> deeper bowls (was 0.82)
    m3.direction = 'NORMAL'
    # 4) angular crags / faceted roughness (Voronoi DISTANCE, higher freq) -> the
    #    blocky rubble character.
    t_crag = _new_musgrave_voronoi_tex("HB2_TorifuneDisp_Crag", size=1.25)
    m4 = body.modifiers.new("DispCrag", 'DISPLACE')
    m4.texture = t_crag
    m4.strength = BODY_LONG * 0.018
    m4.mid_level = 0.6
    m4.direction = 'NORMAL'
    # 5) medium lumps (clouds)
    t_med = _new_clouds_tex("HB2_TorifuneDisp_Med", size=0.20, depth=5)
    m5 = body.modifiers.new("DispMed", 'DISPLACE')
    m5.texture = t_med
    m5.strength = BODY_LONG * 0.015
    m5.mid_level = 0.5
    m5.direction = 'NORMAL'
    # 6) fine regolith grit (high-freq clouds)
    t_fine = _new_clouds_tex("HB2_TorifuneDisp_Fine", size=0.075, depth=5)
    m6 = body.modifiers.new("DispFine", 'DISPLACE')
    m6.texture = t_fine
    m6.strength = BODY_LONG * 0.007
    m6.mid_level = 0.5
    m6.direction = 'NORMAL'

    return body


# ----------------------------------------------------------------------------- #
#  (b) Boulders scattered over the elongated surface  HB2_TorifuneBoulder*       #
# ----------------------------------------------------------------------------- #
def _build_boulders(coll, mat):
    """Scatter a dense field of angular boulders over the fat prolate body surface.

    Creator wants the rougher, rubble-strewn look back, so this is a full boulder
    field (not a sprinkle). For each boulder pick a uniform unit direction, map it
    through the SAME prolate envelope as the body before raycasting (so boulders
    hug the silhouette, not a sphere), then RE-ANCHOR onto the true displaced
    surface and parent to HB2_TorifuneBody so they follow its runtime scale/move.
    """
    pool = _build_rock_pool("HB2_TorRockPool_Body", count=20, seed0=8101)
    rng = random.Random(20260705)
    n_target = 400             # more boulders (creator request)
    SHELL = 1.05               # raycast START shell, just outside the surface
    # Blue-noise spacing: reject a candidate that lands within MIN_SEP (angular) of
    # an already-placed boulder. This DECLUMPS the field so the rocks read as
    # naturally spaced across the whole surface (nature-made), not piled or gridded.
    MIN_SEP = math.radians(3.0)
    min_dot = math.cos(MIN_SEP)
    max_attempts = n_target * 80

    boulders = []      # (obj, unit-direction, size) for the re-anchor pass
    accepted = []      # accepted unit radial directions (for the spacing test)
    attempts = 0
    i = 0
    while len(boulders) < n_target and attempts < max_attempts:
        attempts += 1
        # uniform unit direction on the sphere
        z = rng.uniform(-1.0, 1.0)
        ph = rng.uniform(0.0, math.tau)
        rxy = math.sqrt(max(0.0, 1.0 - z * z))
        nx, ny, nz = rxy * math.cos(ph), rxy * math.sin(ph), z
        # map through the SAME prolate envelope as the body
        ex = BODY_LONG * nx
        ey = BODY_LONG * AXIS_MID * ny
        ez = BODY_LONG * AXIS_SHORT * nz
        xa = ex / BODY_LONG
        d = (xa - WAIST_POS) / WAIST_WIDTH
        pinch = 1.0 - WAIST_DEPTH * math.exp(-(d * d))
        ey *= pinch
        ez *= pinch
        start = Vector((ex, ey, ez)) * SHELL
        ndir = start.normalized()

        # spacing test: skip if too close to an already-placed boulder
        if any(ndir.dot(a) > min_dot for a in accepted):
            continue
        accepted.append(ndir)

        # boulder sizes (rubble field: many small + some big blocks)
        r = rng.random()
        if r < 0.60:
            s = rng.uniform(0.25, 0.9)       # small/medium
        elif r < 0.88:
            s = rng.uniform(0.9, 2.2)        # medium-large
        else:
            s = rng.uniform(2.2, 4.3)        # the occasional big block

        me_rock = pool[rng.randrange(len(pool))]
        b = bpy.data.objects.new(f"HB2_TorifuneBoulder{i}", me_rock)  # linked dup
        i += 1
        b.location = start                    # provisional (re-anchored below)
        b.rotation_euler = Euler((rng.uniform(0, math.tau),
                                  rng.uniform(0, math.tau),
                                  rng.uniform(0, math.tau)))
        b.scale = (s * rng.uniform(0.85, 1.2),
                   s * rng.uniform(0.85, 1.2),
                   s * rng.uniform(0.7, 1.0))
        if not b.data.materials:
            b.data.materials.append(mat)
        _shade_flat(b)
        _link_only(b, coll)
        boulders.append((b, ndir, s))

    # --- RE-ANCHOR every boulder onto the displaced surface ----------------
    body = bpy.data.objects.get("HB2_TorifuneBody")
    _anchor_boulders_to_body(body, boulders)
    return boulders


def _anchor_boulders_to_body(body, boulders):
    """Raycast each boulder onto the evaluated (displaced) body surface.

    `boulders` is a list of (obj, unit_dir, size) where `unit_dir` is the unit
    radial direction (object space, body-centered) the boulder lives along and
    `size` is its representative scale. Each boulder origin is moved to the true
    surface hit point minus a small embed along the radial direction so its base
    sinks in (no floating). Boulders are then parented (keep-transform) to the
    body so they follow the body's runtime scale/translation.
    """
    # ensure the body's Displace modifiers are evaluated before we raycast it
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body_eval = body.evaluated_get(dg)
    # the body sits at its own origin (loc 0, scale 1) during build, so object
    # space == the body-centered frame we placed boulders in.
    far = BODY_LONG * 2.5            # start well outside any displaced peak
    body_mat = body.matrix_world.copy()
    for obj, ndir, size in boulders:
        ndir = ndir.normalized()
        origin = ndir * far                       # outside the surface
        direction = -ndir                          # straight toward center
        hit, loc, nrm, _idx = body_eval.ray_cast(origin, direction)
        if not hit:
            # extremely unlikely; leave provisional placement but pull it in to
            # the local envelope radius so it can't float far off the silhouette.
            obj.location = ndir * (BODY_LONG * 0.96)
        else:
            # embed the boulder base: sink it inward by a fraction of its size so
            # the rock's lower half is buried in the regolith (like the refs).
            embed = min(size * 0.45, BODY_LONG * 0.05)
            obj.location = loc - ndir * embed
        # Parent to the body, preserving the world placement we just set so the
        # boulder tracks the body's later scale/move (harness flyby shot).
        obj.parent = body
        obj.matrix_parent_inverse = body_mat.inverted()


# ----------------------------------------------------------------------------- #
#  Public entry point                                                            #
# ----------------------------------------------------------------------------- #
def build():
    """Idempotently (re)build Torifune: material, elongated body, boulders.

    No file IO / no rendering / no MCP here.
    """
    coll = _env_collection()
    _purge_owned()
    mat = _build_material()
    _build_body(coll, mat)
    _build_boulders(coll, mat)

    # make sure the dependency graph reflects the new modifiers
    bpy.context.view_layer.update()


# ----------------------------------------------------------------------------- #
#  Headless self-test (only when run directly with --shot)                       #
# ----------------------------------------------------------------------------- #
def _argv_after_ddash():
    a = bpy.context.window_manager  # noqa: F841  (kept for clarity)
    import sys
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _cheap_render(out_path, mode):
    """A cheap Eevee test render. mode: 'topdown' (silhouette) or '3q' (relief)."""
    import mathutils
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 960
    sc.render.resolution_y = 540
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    if hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 48

    # black sky for the test
    w = bpy.data.worlds.get("HB2_TestBlack")
    if w is None:
        w = bpy.data.worlds.new("HB2_TestBlack")
    w.use_nodes = True
    w.node_tree.nodes.clear()
    bg = w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0, 0, 0, 1)
    bg.inputs["Strength"].default_value = 0.0
    wout = w.node_tree.nodes.new("ShaderNodeOutputWorld")
    w.node_tree.links.new(bg.outputs["Background"], wout.inputs["Surface"])
    sc.world = w

    # a hard key sun (test-only light, named so it can be cleaned)
    sun = bpy.data.objects.get("HB2_TorifuneTestSun")
    if sun is None:
        sd = bpy.data.lights.new("HB2_TorifuneTestSunData", 'SUN')
        sun = bpy.data.objects.new("HB2_TorifuneTestSun", sd)
        bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 4.0          # honest preview (real rig uses a softer key)
    sun.data.color = (1.0, 0.96, 0.9)
    sun.data.angle = math.radians(0.53)
    sun.rotation_euler = Euler((math.radians(52), 0.0, math.radians(48)))
    # a soft cool fill so the relief reads as form, not high-contrast speckle
    fill = bpy.data.objects.get("HB2_TorifuneTestFill")
    if fill is None:
        fd = bpy.data.lights.new("HB2_TorifuneTestFillData", 'SUN')
        fill = bpy.data.objects.new("HB2_TorifuneTestFill", fd)
        bpy.context.scene.collection.objects.link(fill)
    fill.data.energy = 1.1
    fill.data.color = (0.8, 0.85, 1.0)
    fill.rotation_euler = Euler((math.radians(115), 0.0, math.radians(-120)))

    # test camera
    cam = bpy.data.objects.get("HB2_TorifuneTestCam")
    if cam is None:
        cd = bpy.data.cameras.new("HB2_TorifuneTestCamData")
        cam = bpy.data.objects.new("HB2_TorifuneTestCam", cd)
        bpy.context.scene.collection.objects.link(cam)
    sc.camera = cam

    body = bpy.data.objects.get("HB2_TorifuneBody")
    if mode == "topdown":
        # look straight down -Z from +Z to confirm the 2.4:1 elongated
        # silhouette with a faint waist.
        cam.location = mathutils.Vector((0.0, 0.0, BODY_LONG * 3.4))
        cam.data.lens = 70
        look = mathutils.Vector((0, 0, 0)) - cam.location
        cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    else:  # 3q : a 3/4 view to confirm cratered / boulder relief
        cam.location = mathutils.Vector((BODY_LONG * 2.6,
                                         -BODY_LONG * 2.2,
                                         BODY_LONG * 1.1))
        cam.data.lens = 80
        look = mathutils.Vector((0, 0, 0)) - cam.location
        cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()

    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"[07_torifune] rendered {mode} -> {out_path}")


if __name__ == "__main__":
    build()
    import sys
    args = _argv_after_ddash()
    if "--shot" in args:
        i = args.index("--shot")
        base = args[i + 1] if i + 1 < len(args) else "/tmp/_t_torifune.png"
        if base.lower().endswith(".png"):
            top_out = base[:-4] + "_topdown.png"
            q_out = base[:-4] + "_3q.png"
        else:
            top_out = base + "_topdown.png"
            q_out = base + "_3q.png"
        _cheap_render(top_out, "topdown")
        _cheap_render(q_out, "3q")
        print(f"[07_torifune] self-test renders: {top_out} , {q_out}")
