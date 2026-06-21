"""
05_ryugu.py  —  Asteroid Ryugu ("Torifune") for the Hayabusa2 / Eevee Next scene.

Builds THREE things, idempotently, into the `Environment` collection:
  (a) HB2_RyuguBody     — whole spinning-top / oblate body for approach & hero shots
                          (centered at its own origin, ~160 BU diameter; the
                          orchestrator positions/scales it for framing).
  (b) HB2_RyuguSurface  — upgraded dense close rubble surface for descent
                          (keeps its existing footprint: dome top at z=-18, ~28 BU).
  (c) HB2_Ryugu         — very dark bluish-grey rubble-pile material shared by all.

Plus the scattered angular boulders:
  HB2_Boulder*          — close-surface rubble field (300-600 angular rocks).
  HB2_BodyBoulder*      — boulders studding the whole-body limb.
  HB2_Otohime           — the big discrete boulder near the south pole.

Design notes
------------
* OWNS the Environment asteroid only. Never touches the spacecraft (HB2_* craft/
  solar/instruments), HB2_Earth*, cameras, lights, or world.
* Idempotent: every object/mesh/material it owns is removed by name (prefix) and
  rebuilt from scratch on each call to build().
* Cheap: all scattered boulders share a tiny pool of mesh datablocks (linked
  duplicates), so 300-900 rocks cost only a handful of unique meshes. Boulders are
  faceted/angular (flat-shaded decimated icospheres), not round.
* No file IO, no MCP, no rendering inside build().

Validate (headless):
  Blender --background work_ryugu.blend --python 05_ryugu.py -- --shot out.png
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
MAT_NAME = "HB2_Ryugu"

# Owned-object name prefixes (everything matching is wiped on rebuild).
OWNED_PREFIXES = (
    "HB2_RyuguSurface",
    "HB2_RyuguBody",
    "HB2_Boulder",       # close-surface rubble
    "HB2_BodyBoulder",   # whole-body studding rocks
    "HB2_Otohime",       # the big south-pole boulder
)
# Owned mesh-datablock / texture prefixes (cleaned so reruns don't pile up data).
OWNED_MESH_PREFIXES = ("HB2_RyuguSurfaceMesh", "HB2_RyuguBodyMesh",
                       "HB2_RockPool", "HB2_OtohimeMesh")
OWNED_TEX_PREFIX = "HB2_RyuguDisp"

# Whole-body geometry: a workable scale (NOT literal ~900 m, which would dwarf the
# 6 m craft). ~160 BU mean diameter; orchestrator rescales for any given shot.
BODY_RADIUS = 80.0          # mean equatorial radius (BU)  -> ~160 BU diameter
BODY_OBLATE = 0.87          # polar / equatorial  (Ryugu ~876/1004)
BODY_RIDGE_GAIN = 0.09      # extra equatorial bulge for the sharp ridge line

# Close-surface dome footprint (keep what the orchestrator's ryugu cam expects).
SURF_RADIUS = 14.0          # sphere radius (dome dims ~28 BU) ...
SURF_Z = -18.0              # ... with center at z=-18 so the top crowns near z=-4


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
#  Material — very dark bluish-grey rubble pile                                  #
# ----------------------------------------------------------------------------- #
def _build_material():
    """(Re)build HB2_Ryugu: dark bluish-grey, rough, strong bump relief.

    Albedo ~0.045 (linear base ~0.035-0.042 — dark but NOT pure black, or it loses
    form under a hard sun). Subtle two-tone grey variation (one warmer, one bluer)
    via large-scale noise + Color Ramp. Relief = two stacked bump layers (medium
    rubble + fine grit) driven by object-coordinate noise so the dark surface still
    reads as rock under directional light.
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

    # --- Base color: two-tone dark grey -----------------------------------
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    geo.location = (-1100, 260)
    tcoord = nt.nodes.new("ShaderNodeTexCoord")
    tcoord.location = (-1100, -260)

    col_noise = nt.nodes.new("ShaderNodeTexNoise")
    col_noise.location = (-820, 260)
    col_noise.noise_dimensions = '3D'
    col_noise.inputs["Scale"].default_value = 1.4     # large patches
    col_noise.inputs["Detail"].default_value = 4.0
    col_noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(geo.outputs["Position"], col_noise.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-540, 260)
    # Very dark; warmer grey -> bluer grey. (linear values, albedo ~0.045)
    e = ramp.color_ramp.elements
    e[0].position = 0.0
    e[0].color = (0.0360, 0.0345, 0.0310, 1.0)   # slightly warm dark grey
    e[1].position = 1.0
    e[1].color = (0.0305, 0.0335, 0.0420, 1.0)   # slightly bluer dark grey
    # add a faint mid stop so it doesn't read as a flat two-band split
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = (0.0335, 0.0350, 0.0370, 1.0)
    nt.links.new(col_noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # --- Relief: medium rubble bump + fine grit bump (stacked) -------------
    med_noise = nt.nodes.new("ShaderNodeTexNoise")
    med_noise.location = (-820, -60)
    med_noise.noise_dimensions = '3D'
    med_noise.inputs["Scale"].default_value = 6.0
    med_noise.inputs["Detail"].default_value = 10.0
    med_noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(tcoord.outputs["Object"], med_noise.inputs["Vector"])

    bump_med = nt.nodes.new("ShaderNodeBump")
    bump_med.location = (-360, -60)
    bump_med.inputs["Strength"].default_value = 0.55
    bump_med.inputs["Distance"].default_value = 0.02
    nt.links.new(med_noise.outputs["Fac"], bump_med.inputs["Height"])

    fine_noise = nt.nodes.new("ShaderNodeTexNoise")
    fine_noise.location = (-820, -380)
    fine_noise.noise_dimensions = '3D'
    fine_noise.inputs["Scale"].default_value = 26.0
    fine_noise.inputs["Detail"].default_value = 12.0
    fine_noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(tcoord.outputs["Object"], fine_noise.inputs["Vector"])

    bump_fine = nt.nodes.new("ShaderNodeBump")
    bump_fine.location = (120, -120)
    bump_fine.inputs["Strength"].default_value = 0.35
    bump_fine.inputs["Distance"].default_value = 0.006
    nt.links.new(fine_noise.outputs["Fac"], bump_fine.inputs["Height"])
    nt.links.new(bump_med.outputs["Normal"], bump_fine.inputs["Normal"])
    nt.links.new(bump_fine.outputs["Normal"], bsdf.inputs["Normal"])

    # --- BSDF scalar values ------------------------------------------------
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.97       # 0.92-1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.2   # low specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.2

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
#  (b) Close rubble surface  HB2_RyuguSurface  + HB2_Boulder*                    #
# ----------------------------------------------------------------------------- #
def _build_surface(coll, mat):
    """Dense angular-boulder surface patch with fine regolith between rocks.

    Keeps the existing footprint (sphere center z=-18, radius 14 -> dome top ~z=-4,
    dims ~28 BU) so the orchestrator's ryugu camera frames it unchanged.
    """
    # --- base dome ---------------------------------------------------------
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=SURF_RADIUS)
    me = bpy.data.meshes.new("HB2_RyuguSurfaceMesh")
    bm.to_mesh(me)
    bm.free()
    surf = bpy.data.objects.new("HB2_RyuguSurface", me)
    surf.location = (0.0, 0.0, SURF_Z)
    me.materials.append(mat)
    _shade_smooth(surf)
    _link_only(surf, coll)

    # fine regolith displacement between the boulders
    disp_tex = _new_clouds_tex("HB2_RyuguDisp_Surf", size=1.6, depth=5)
    dmod = surf.modifiers.new("Disp", 'DISPLACE')
    dmod.texture = disp_tex
    dmod.strength = 0.5
    dmod.mid_level = 0.5
    dmod.direction = 'NORMAL'

    # --- scatter angular boulders over the dome top ------------------------
    pool = _build_rock_pool("HB2_RockPool_Surf", count=14, seed0=4001)
    rng = random.Random(20240621)

    # The orchestrator's ryugu cam sits at (7.5,-8.5,3.3) aiming (0,0,-1): it looks
    # down onto the crown of the dome around the origin. Carpet a generous cap so
    # the frame is wall-to-wall rock (~50-70% coverage like torifune 1).
    n_boulders = 460
    placed = 0
    idx = 0
    # cap half-angle from the top pole (how far down the dome we cover)
    cap = math.radians(58.0)
    while placed < n_boulders:
        idx += 1
        # bias polar angle toward the crown but allow spread to the limb
        u = rng.random()
        theta = cap * (u ** 0.62)            # 0 at pole -> cap at edge
        phi = rng.uniform(0.0, 2.0 * math.pi)
        st, ct = math.sin(theta), math.cos(theta)
        nx, ny, nz = st * math.cos(phi), st * math.sin(phi), ct
        # surface point on the sphere (world space)
        px = SURF_RADIUS * nx
        py = SURF_RADIUS * ny
        pz = SURF_Z + SURF_RADIUS * nz

        # mixed scale: many small/medium, few large; sizes in BU
        r = rng.random()
        if r < 0.62:
            s = rng.uniform(0.35, 0.9)       # small/medium
        elif r < 0.9:
            s = rng.uniform(0.9, 1.8)        # medium-large
        else:
            s = rng.uniform(1.8, 3.2)        # the occasional big block

        me_rock = pool[rng.randrange(len(pool))]
        b = bpy.data.objects.new(f"HB2_Boulder{placed}", me_rock)  # linked dup
        # half-bury: sink each rock partly into the surface along the local normal
        bury = rng.uniform(0.28, 0.62) * s
        b.location = (px - nx * bury, py - ny * bury, pz - nz * bury)
        b.rotation_euler = Euler((rng.uniform(0, math.tau),
                                  rng.uniform(0, math.tau),
                                  rng.uniform(0, math.tau)))
        b.scale = (s * rng.uniform(0.85, 1.15),
                   s * rng.uniform(0.85, 1.15),
                   s * rng.uniform(0.7, 1.0))
        if not b.data.materials:
            b.data.materials.append(mat)
        _shade_flat(b)
        _link_only(b, coll)
        placed += 1

    return surf


# ----------------------------------------------------------------------------- #
#  (a) Whole spinning-top body  HB2_RyuguBody  + HB2_BodyBoulder* + HB2_Otohime  #
# ----------------------------------------------------------------------------- #
def _build_body(coll, mat):
    """Spinning-top / oblate body with equatorial ridge + studded limb.

    UV-sphere -> flattened to BODY_OBLATE on Z -> equatorial loop scaled out to make
    the diamond silhouette + sharp ridge -> layered displacement (large rubble +
    medium craters + fine bump). Centered at its own origin for the orchestrator.
    """
    segs_u, segs_v = 128, 96
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs_u, v_segments=segs_v,
                              radius=BODY_RADIUS)

    # Shape it into a spinning top (Ryugu's diamond / 独楽 silhouette):
    #   For each vertex take its latitude phi (=asin(z/R)).  We RESHAPE the
    #   horizontal radius as a function of latitude so the cross-section is a
    #   rounded diamond: a sharp maximum at the equator (the ridge) tapering toward
    #   flattened poles.  We also squash Z (oblate) and add a small extra bump right
    #   at the equator for the discrete "Ryujin Dorsum" ridge line.
    for v in bm.verts:
        co = v.co
        r = co.length
        if r < 1e-6:
            continue
        # latitude in [-pi/2, pi/2]
        s = max(-1.0, min(1.0, co.z / r))
        phi = math.asin(s)
        lat = abs(phi) / (math.pi / 2.0)         # 0 equator -> 1 pole
        # Diamond horizontal-radius profile:
        #   near equator stay near full radius, then taper ~linearly to the poles
        #   (linear taper of horizontal radius = straight conical flanks = diamond).
        #   Mostly-linear taper for crisp angular flanks, a touch of cosine just to
        #   keep the poles from collapsing to a perfect point.
        taper = (1.0 - lat)
        horiz_profile = 0.94 * taper + 0.06 * math.cos(phi)
        # sharp equatorial ridge: narrow boost centred on the equator
        ridge = math.exp(-(lat * 7.5) ** 2)      # ~1 at equator, ->0 quickly
        horiz_profile *= (1.0 + BODY_RIDGE_GAIN * ridge)

        new_horiz = BODY_RADIUS * horiz_profile
        h = math.hypot(co.x, co.y)
        if h > 1e-6:
            f = new_horiz / h
            co.x *= f
            co.y *= f
        # polar height: oblate, with slightly flattened caps near the poles
        co.z = BODY_RADIUS * BODY_OBLATE * s
    bm.normal_update()

    me = bpy.data.meshes.new("HB2_RyuguBodyMesh")
    bm.to_mesh(me)
    bm.free()
    body = bpy.data.objects.new("HB2_RyuguBody", me)
    body.location = (0.0, 0.0, 0.0)
    me.materials.append(mat)
    _shade_smooth(body)
    _link_only(body, coll)

    # --- layered displacement on the body ----------------------------------
    # Kept gentle so it textures the surface (rubble + craters) WITHOUT drowning
    # the diamond silhouette / equatorial ridge that the mesh shaping created.
    # 1) large rubble undulation (blocky Voronoi)
    t_large = _new_musgrave_voronoi_tex("HB2_RyuguDisp_BodyL", size=0.6)
    m1 = body.modifiers.new("DispLarge", 'DISPLACE')
    m1.texture = t_large
    m1.strength = BODY_RADIUS * 0.045
    m1.mid_level = 0.55
    m1.direction = 'NORMAL'
    # 2) medium craters / lumps (clouds)
    t_med = _new_clouds_tex("HB2_RyuguDisp_BodyM", size=0.4, depth=4)
    m2 = body.modifiers.new("DispMed", 'DISPLACE')
    m2.texture = t_med
    m2.strength = BODY_RADIUS * 0.03
    m2.mid_level = 0.5
    m2.direction = 'NORMAL'
    # 3) fine surface bump (clouds, high freq)
    t_fine = _new_clouds_tex("HB2_RyuguDisp_BodyF", size=0.09, depth=5)
    m3 = body.modifiers.new("DispFine", 'DISPLACE')
    m3.texture = t_fine
    m3.strength = BODY_RADIUS * 0.012
    m3.mid_level = 0.5
    m3.direction = 'NORMAL'

    # --- studding boulders over the surface (so the limb looks rocky) ------
    # Boulders are created on a smooth envelope, then RE-ANCHORED onto the
    # TRUE displaced surface by raycasting against the evaluated body mesh (see
    # _anchor_to_body below). They are parented to HB2_RyuguBody so they follow
    # the body's runtime transform (the harness scales the body to 0.125 and
    # moves it for the hero shot).
    pool = _build_rock_pool("HB2_RockPool_Body", count=16, seed0=7001)
    rng = random.Random(987654)
    n_body_boulders = 280
    # smooth envelope radius used only as a raycast START shell (well outside the
    # displaced surface, whose peaks reach ~BODY_RADIUS*1.045).
    Rb = BODY_RADIUS * 1.04
    boulders = []      # (obj, unit-direction) pairs for the re-anchor pass
    for i in range(n_body_boulders):
        # even-ish sphere distribution (uniform on sphere, then oblate-squashed)
        z = rng.uniform(-1.0, 1.0)
        phi = rng.uniform(0.0, math.tau)
        rxy = math.sqrt(max(0.0, 1.0 - z * z))
        nx, ny, nz = rxy * math.cos(phi), rxy * math.sin(phi), z
        px = Rb * nx
        py = Rb * ny
        pz = Rb * nz * BODY_OBLATE
        # boulder sizes scaled to the body (a few % of radius)
        r = rng.random()
        if r < 0.7:
            s = BODY_RADIUS * rng.uniform(0.012, 0.03)
        elif r < 0.93:
            s = BODY_RADIUS * rng.uniform(0.03, 0.06)
        else:
            s = BODY_RADIUS * rng.uniform(0.06, 0.1)
        me_rock = pool[rng.randrange(len(pool))]
        b = bpy.data.objects.new(f"HB2_BodyBoulder{i}", me_rock)
        # provisional placement on the smooth envelope (re-anchored below)
        b.location = (px, py, pz)
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
        boulders.append((b, Vector((nx, ny, nz)), s))

    # --- Otohime: one big discrete angular boulder near the south pole -----
    oto_me = _make_rock_mesh("HB2_OtohimeMesh", seed=31337, subdiv=2,
                             jitter=0.42, squash=0.55)
    oto = bpy.data.objects.new("HB2_Otohime", oto_me)
    # near south pole (-Z); direction toward the flattened south cap
    oto_r = BODY_RADIUS * 0.16            # ~160x120x70 m scaled to the body
    oto_dir = Vector((0.1, -0.06, -BODY_OBLATE * 0.92)).normalized()
    oto.location = (Rb * oto_dir.x, Rb * oto_dir.y, Rb * oto_dir.z)
    oto.scale = (oto_r * 1.0, oto_r * 0.8, oto_r * 0.55)   # 160x120x70-ish ratio
    oto.rotation_euler = Euler((0.3, -0.2, 0.7))
    if not oto.data.materials:
        oto.data.materials.append(mat)
    _shade_flat(oto)
    _link_only(oto, coll)
    boulders.append((oto, oto_dir, oto_r))

    # --- RE-ANCHOR every boulder onto the displaced surface ----------------
    # Evaluate the body (with its 3 Displace modifiers applied) and raycast each
    # boulder from a point outside its radial direction toward the center; drop
    # the boulder origin onto the hit point, embedded slightly so its base sinks
    # into the surface instead of hovering. Then parent to the body so the whole
    # rubble field rides the body's transform.
    _anchor_boulders_to_body(body, boulders)

    return body


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
    far = BODY_RADIUS * 2.5            # start well outside any displaced peak
    body_mat = body.matrix_world.copy()
    for obj, ndir, size in boulders:
        ndir = ndir.normalized()
        origin = ndir * far                       # outside the surface
        direction = -ndir                          # straight toward center
        hit, loc, nrm, _idx = body_eval.ray_cast(origin, direction)
        if not hit:
            # extremely unlikely; leave provisional placement but pull it in to
            # the mean radius so it can't float far off the silhouette.
            obj.location = ndir * (BODY_RADIUS * 0.96)
        else:
            # embed the boulder base: sink it inward by a fraction of its size so
            # the rock's lower half is buried in the regolith (like the refs).
            embed = min(size * 0.45, BODY_RADIUS * 0.05)
            obj.location = loc - ndir * embed
        # Parent to the body, preserving the world placement we just set so the
        # boulder tracks the body's later scale/move (harness hero shot).
        obj.parent = body
        obj.matrix_parent_inverse = body_mat.inverted()


# ----------------------------------------------------------------------------- #
#  Public entry point                                                            #
# ----------------------------------------------------------------------------- #
def build():
    """Idempotently (re)build Ryugu: material, whole body, close surface, boulders.

    No file IO / no rendering / no MCP here.
    """
    coll = _env_collection()
    _purge_owned()
    mat = _build_material()
    _build_body(coll, mat)
    _build_surface(coll, mat)

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
    """A cheap Eevee test render. mode: 'body' (whole body) or 'surface' (close)."""
    import mathutils
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 900
    sc.render.resolution_y = 900
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

    # a hard sun (test-only light, named so it can be cleaned)
    sun = bpy.data.objects.get("HB2_RyuguTestSun")
    if sun is None:
        sd = bpy.data.lights.new("HB2_RyuguTestSunData", 'SUN')
        sun = bpy.data.objects.new("HB2_RyuguTestSun", sd)
        bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 5.5      # match the scene's HB2_Sun for an honest preview
    sun.data.angle = math.radians(0.53)
    sun.rotation_euler = Euler((math.radians(58), 0.0, math.radians(35)))

    # test camera
    cam = bpy.data.objects.get("HB2_RyuguTestCam")
    if cam is None:
        cd = bpy.data.cameras.new("HB2_RyuguTestCamData")
        cam = bpy.data.objects.new("HB2_RyuguTestCam", cd)
        bpy.context.scene.collection.objects.link(cam)
    sc.camera = cam

    if mode == "body":
        body = bpy.data.objects.get("HB2_RyuguBody")
        # frame the whole body from a near-equatorial 3/4 angle so the diamond
        # silhouette + equatorial ridge are clearly visible (low elevation).
        cam.location = mathutils.Vector((BODY_RADIUS * 3.0,
                                         -BODY_RADIUS * 2.7,
                                         BODY_RADIUS * 0.55))
        cam.data.lens = 65
        look = mathutils.Vector((0, 0, 0)) - cam.location
        cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        # hide the close surface + its boulders for the body shot
        for o in bpy.data.objects:
            if o.name.startswith("HB2_RyuguSurface") or o.name.startswith("HB2_Boulder"):
                o.hide_render = True
        for o in bpy.data.objects:
            if o.name.startswith("HB2_RyuguBody") or o.name.startswith("HB2_BodyBoulder") \
               or o.name.startswith("HB2_Otohime"):
                o.hide_render = False
    else:  # surface
        cam.location = mathutils.Vector((7.5, -8.5, 3.3))
        cam.data.lens = 44
        look = mathutils.Vector((0, 0, -4.5)) - cam.location
        cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        for o in bpy.data.objects:
            if o.name.startswith("HB2_RyuguBody") or o.name.startswith("HB2_BodyBoulder") \
               or o.name.startswith("HB2_Otohime"):
                o.hide_render = True
        for o in bpy.data.objects:
            if o.name.startswith("HB2_RyuguSurface") or o.name.startswith("HB2_Boulder"):
                o.hide_render = False

    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"[05_ryugu] rendered {mode} -> {out_path}")


if __name__ == "__main__":
    build()
    import sys
    args = _argv_after_ddash()
    if "--shot" in args:
        i = args.index("--shot")
        base = args[i + 1] if i + 1 < len(args) else "/tmp/_t_ryugu.png"
        # render both a body view and a surface view (suffix the path)
        if base.lower().endswith(".png"):
            body_out = base[:-4] + "_body.png"
            surf_out = base[:-4] + "_surface.png"
        else:
            body_out = base + "_body.png"
            surf_out = base + "_surface.png"
        _cheap_render(body_out, "body")
        _cheap_render(surf_out, "surface")
        print(f"[05_ryugu] self-test renders: {body_out} , {surf_out}")
