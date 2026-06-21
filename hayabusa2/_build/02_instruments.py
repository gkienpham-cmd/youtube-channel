"""
02_instruments.py  --  RETIRED (deprecated no-op).  Blender 5.1 / Eevee Next.

================================  STATUS  ================================
This module is DEPRECATED.  build() does NOTHING.

All of the instrument / greeble / MLI-patchwork / radiator / NIRS3 / TIR /
bolt-ring / flat-octagon-HGA detail this pass used to add has been FOLDED INTO
02_craft.py, which owns the spacecraft body and authors that detail on the
CORRECT faces for the live bus convention (HX=0.50, HY=0.80, HZ=0.625).
=========================================================================

WHY IT WAS RETIRED (it was mutually destructive with 02_craft.py):
  * Shared owned object prefixes with 02_craft.py (HB2_MLIplate_, HB2_Seam_,
    HB2_NIRS3_, HB2_TIR_, HB2_GreebleB_, HB2_Boltring_, HB2_Radiator*) -> the two
    scripts fought over the same names.
  * _purge_owned() also deleted EVERY 0-user mesh in the whole file -- a
    dangerous global side effect.
  * It used a BACKWARDS axis convention (BX=0.80, BY=0.50 -- the 1.6 axis
    swapped) -> detail painted on the WRONG faces of the live 1.0x1.6x1.25 bus.
  * _ensure_radiator_material() re-authored the HB2_Radiator material owned by
    the materials agent (06_materials.py).

The integrator runs 02_craft.build() then 02_instruments.build().  Making this a
no-op guarantees that sequence is safe (no double-purge, no wrong-face detail,
no material re-authoring).  The old worker functions below are kept for
reference only; build() never calls them, and the two genuinely-destructive
helpers (_purge_owned, _ensure_radiator_material) have been neutered to hard
no-ops / by-name lookups so even a stray direct call cannot corrupt the scene.

Run headless (does nothing but print a deprecation note):
  Blender --background work.blend --python 02_instruments.py
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# Constants -- scene facts (verified from the work .blend)
# ---------------------------------------------------------------------------
ROOT_NAME = "HB2_Root"

# Bus core extents (centred at origin)
BX = 0.80   # +/-X face plane
BY = 0.50   # +/-Y face plane
BZ = 0.625  # +/-Z face plane

OWNED_PREFIXES = (
    "HB2_MLIplate_",
    "HB2_Radiator_",
    "HB2_NIRS3_",
    "HB2_TIR_",
    "HB2_GreebleB_",
    "HB2_Seam_",
    "HB2_Boltring_",
)

# Shared materials we only REFERENCE (must already exist in the file)
SHARED_MATS = (
    "HB2_Gold_MLI", "HB2_Black_MLI", "HB2_Silver_MLI",
    "HB2_Metal", "HB2_AntMetal", "HB2_AntWhite", "HB2_BlackMatte",
)

RNG_SEED = 20260621


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _scene_collection_map():
    return {c.name: c for c in bpy.data.collections}


def _get_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        # link under master scene collection so it is visible/renderable
        bpy.context.scene.collection.children.link(c)
    return c


def _unlink_from_all_collections(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)


def _link_only(obj, coll):
    _unlink_from_all_collections(obj)
    coll.objects.link(obj)


def _mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        raise RuntimeError(f"Expected shared material '{name}' is missing.")
    return m


def _assign_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def _new_mesh_obj(name, mesh, coll, parent):
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def _bm_to_obj(name, bm, coll, parent, mat=None, shade_smooth=False):
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = _new_mesh_obj(name, me, coll, parent)
    if mat is not None:
        _assign_mat(obj, mat)
    if shade_smooth:
        for p in me.polygons:
            p.use_smooth = True
    return obj


def _box(name, center, size, coll, parent, mat=None, bevel=0.0, shade_smooth=False):
    """Axis-aligned box centred at `center` with full extents `size`."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    if bevel > 0.0:
        bmesh.ops.bevel(
            bm, geom=list(bm.edges) + list(bm.verts),
            offset=bevel, segments=1, affect='EDGES', clamp_overlap=True,
        )
    return _bm_to_obj(name, bm, coll, parent, mat, shade_smooth)


def _cyl(name, center, radius, depth, coll, parent, mat=None, axis='Z',
         verts=24, shade_smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=verts,
        radius1=radius, radius2=radius, depth=depth,
    )
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Euler((0, math.radians(90), 0)).to_matrix())
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Euler((math.radians(90), 0, 0)).to_matrix())
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    return _bm_to_obj(name, bm, coll, parent, mat, shade_smooth)


def _torus(name, center, major_r, minor_r, coll, parent, mat=None,
           normal='Z', major_seg=24, minor_seg=8):
    bm = bmesh.new()
    # Build a torus in XY plane manually (no torus bmesh op available cross-version)
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        cx, cy = math.cos(a), math.sin(a)
        for j in range(minor_seg):
            b = 2 * math.pi * j / minor_seg
            r = major_r + minor_r * math.cos(b)
            x = r * cx
            y = r * cy
            z = minor_r * math.sin(b)
            bm.verts.new((x, y, z))
    bm.verts.ensure_lookup_table()
    for i in range(major_seg):
        for j in range(minor_seg):
            a0 = i * minor_seg
            a1 = ((i + 1) % major_seg) * minor_seg
            v0 = bm.verts[a0 + j]
            v1 = bm.verts[a0 + (j + 1) % minor_seg]
            v2 = bm.verts[a1 + (j + 1) % minor_seg]
            v3 = bm.verts[a1 + j]
            bm.faces.new((v0, v1, v2, v3))
    if normal == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Euler((0, math.radians(90), 0)).to_matrix())
    elif normal == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Euler((math.radians(90), 0, 0)).to_matrix())
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    return _bm_to_obj(name, bm, coll, parent, mat, shade_smooth=True)


# ---------------------------------------------------------------------------
# Idempotency: nuke owned objects + orphan meshes
# ---------------------------------------------------------------------------
def _purge_owned():
    # DEPRECATED + NEUTERED.  This used to delete every object matching the
    # OWNED_PREFIXES *and then sweep EVERY 0-user mesh in the whole file* -- a
    # dangerous global side effect that collided with 02_craft.py (which now owns
    # all of these prefixes).  build() is a retired no-op and never calls this.
    # Kept as a hard no-op so that even a direct call cannot wipe scene data.
    return


# ---------------------------------------------------------------------------
# Radiator material (the ONLY new material this script creates)
# ---------------------------------------------------------------------------
def _ensure_radiator_material():
    # DEPRECATED + NEUTERED.  HB2_Radiator is authored exclusively by the
    # materials agent (06_materials.py).  This used to re-author its node tree,
    # which clobbered the materials agent's work.  It now ONLY references the
    # material by name (never creates/edits it) -- honouring the assign-by-name
    # rule.  Returns the existing material, or None if absent (callers, if any,
    # must tolerate None; build() is a no-op and never calls this).
    return bpy.data.materials.get("HB2_Radiator")


# ---------------------------------------------------------------------------
# 1. Balanced gold + black MLI patchwork (LOCKED look per image 6)
# ---------------------------------------------------------------------------
def _build_mli_patchwork(coll, root):
    """Tile thin MLI 'panel plates' a few mm proud across the bus faces and
    assign Gold / Black / Silver in a believable balanced patchwork."""
    gold = _mat("HB2_Gold_MLI")
    black = _mat("HB2_Black_MLI")
    silver = _mat("HB2_Silver_MLI")

    rng = random.Random(RNG_SEED)
    proud = 0.006     # 6 mm proud
    plate_t = 0.010   # plate thickness
    gap = 0.006       # seam gap between plates (tight -> little BusCore shows through)
    count = 0

    # A balanced ~50/50 gold/black weighting with occasional silver strip.
    def pick_mat(ix, iy, face_key):
        # deterministic checker base, jittered so it's a believable quilt
        base = (ix + iy + hash(face_key) % 3) % 2
        r = rng.random()
        if r < 0.10:
            return silver
        if base == 0:
            return gold if r < 0.78 else black
        else:
            return black if r < 0.78 else gold

    # Each face described by: outward axis, sign, plane coord, the two in-plane
    # axes with their half-extents, and a grid resolution.
    faces = [
        # +X / -X faces : plane 1.0(Y) x 1.25(Z)
        ("PX", 'X', +1, BX, ('Y', BY), ('Z', BZ), 3, 4),
        ("NX", 'X', -1, BX, ('Y', BY), ('Z', BZ), 3, 4),
        # +Y / -Y faces : plane 1.6(X) x 1.25(Z)  (-Y has ion engines, keep sparser)
        ("PY", 'Y', +1, BY, ('X', BX), ('Z', BZ), 4, 4),
        ("NY", 'Y', -1, BY, ('X', BX), ('Z', BZ), 4, 3),
        # +Z top deck : plane 1.6(X) x 1.0(Y) -- sits just above TopDeck (z~0.685)
        ("PZ", 'Z', +1, 0.690, ('X', BX), ('Y', BY), 4, 3),
    ]

    for face_key, out_axis, sign, plane, (a_ax, a_half), (b_ax, b_half), na, nb in faces:
        # cell sizes
        ca = (2 * a_half) / na
        cb = (2 * b_half) / nb
        pa = ca - gap
        pb = cb - gap
        for ia in range(na):
            for ib in range(nb):
                a0 = -a_half + ca * (ia + 0.5)
                b0 = -b_half + cb * (ib + 0.5)
                # assemble center + size dict by axis
                center = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
                size = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
                center[out_axis] = plane + sign * (proud * 0.5)
                size[out_axis] = plate_t
                center[a_ax] = a0
                size[a_ax] = pa
                center[b_ax] = b0
                size[b_ax] = pb
                m = pick_mat(ia, ib, face_key)
                nm = f"HB2_MLIplate_{face_key}_{ia}_{ib}"
                _box(nm,
                     (center['X'], center['Y'], center['Z']),
                     (size['X'], size['Y'], size['Z']),
                     coll, root, mat=m, bevel=0.0015)
                count += 1
    return count


def _build_quilt_seams(coll, root):
    """Thin recessed quilting seam lines criss-crossing the big faces, to read
    as stitched MLI blanket seams up close."""
    metal = _mat("HB2_BlackMatte")
    seam_w = 0.004
    proud = 0.008
    count = 0

    # +Y and -Y faces : vertical + horizontal seam grid
    for sign, tag in ((+1, "PY"), (-1, "NY")):
        y = BY + sign * proud
        # vertical seams (along Z) at a few X positions
        for i, x in enumerate((-0.40, 0.0, 0.40)):
            _box(f"HB2_Seam_{tag}_v{i}", (x, y, 0.0),
                 (seam_w, 0.004, 2 * BZ * 0.92), coll, root, metal)
            count += 1
        # horizontal seams (along X) at a few Z positions
        for i, z in enumerate((-0.30, 0.10, 0.45)):
            _box(f"HB2_Seam_{tag}_h{i}", (0.0, y, z),
                 (2 * BX * 0.92, 0.004, seam_w), coll, root, metal)
            count += 1

    # +X and -X faces
    for sign, tag in ((+1, "PX"), (-1, "NX")):
        x = BX + sign * proud
        for i, z in enumerate((-0.30, 0.15)):
            _box(f"HB2_Seam_{tag}_h{i}", (x, 0.0, z),
                 (0.004, 2 * BY * 0.92, seam_w), coll, root, metal)
            count += 1
        for i, y in enumerate((-0.25, 0.25)):
            _box(f"HB2_Seam_{tag}_v{i}", (x, y, 0.0),
                 (0.004, seam_w, 2 * BZ * 0.92), coll, root, metal)
            count += 1
    return count


# ---------------------------------------------------------------------------
# 2. Silver thermal-radiator louver panels (NEW material HB2_Radiator)
# ---------------------------------------------------------------------------
def _build_radiators(coll, root, rad_mat):
    """Slatted radiator panels on 1-2 side faces (horizontal slats)."""
    count = 0
    proud = 0.012
    # Place one radiator block on -X face and one on +X face (upper region),
    # away from the dense -Z underside instruments.
    specs = [
        # (tag, out_axis, sign, plane, panel center in-plane, panel half-size)
        ("NX", 'X', -1, BX, (-0.10, 0.18), (0.30, 0.34)),   # (Y0,Z0),(Yhalf,Zhalf)
        ("PX", 'X', +1, BX, (0.05, -0.05), (0.28, 0.30)),
    ]
    for tag, out_axis, sign, plane, (b0, c0), (bh, ch) in specs:
        # backing frame plate
        center = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        size = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        center[out_axis] = plane + sign * (proud * 0.5)
        size[out_axis] = 0.012
        center['Y'] = b0
        size['Y'] = 2 * bh
        center['Z'] = c0
        size['Z'] = 2 * ch
        _box(f"HB2_Radiator_{tag}_frame",
             (center['X'], center['Y'], center['Z']),
             (size['X'], size['Y'], size['Z']),
             coll, root, mat=rad_mat, bevel=0.004)
        count += 1
        # horizontal slats (proud ridges along Y) stacked in Z
        nslat = 9
        for s in range(nslat):
            z = c0 - ch + (2 * ch) * (s + 0.5) / nslat
            sc = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
            ss = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
            sc[out_axis] = plane + sign * (proud + 0.004)
            ss[out_axis] = 0.012
            sc['Y'] = b0
            ss['Y'] = 2 * bh * 0.96
            sc['Z'] = z
            ss['Z'] = (2 * ch / nslat) * 0.55
            _box(f"HB2_Radiator_{tag}_slat{s}",
                 (sc['X'], sc['Y'], sc['Z']),
                 (ss['X'], ss['Y'], ss['Z']),
                 coll, root, mat=rad_mat)
            count += 1
    return count


# ---------------------------------------------------------------------------
# 3. Missing instruments on -Z underside cluster : NIRS3 + TIR
# ---------------------------------------------------------------------------
def _build_nirs3_tir(coll, root):
    """NIRS3 (near-IR spectrometer, dark aperture) and TIR (thermal-IR imager,
    lens), per image 5, on the -Z underside near the other optical heads."""
    metal = _mat("HB2_Metal")
    black = _mat("HB2_BlackMatte")
    gold = _mat("HB2_Gold_MLI")
    new = 0

    underside = -BZ  # -0.625 (bottom of bus core; instruments hang below)

    # ---- NIRS3 : compact box with a small dark circular aperture ----
    nb_center = (-0.33, 0.18, underside - 0.085)
    _box("HB2_NIRS3_body", nb_center, (0.150, 0.140, 0.170),
         coll, root, mat=gold, bevel=0.006)
    new += 1
    # gold-foil wrapped collar
    _box("HB2_NIRS3_collar",
         (nb_center[0], nb_center[1], underside - 0.012),
         (0.165, 0.155, 0.040), coll, root, mat=gold)
    new += 1
    # dark recessed aperture on the -Z facing side
    _cyl("HB2_NIRS3_aperture",
         (nb_center[0], nb_center[1], underside - 0.172),
         radius=0.045, depth=0.020, coll=coll, parent=root,
         mat=black, axis='Z', verts=28)
    new += 1
    # tiny baffle lip
    _torus("HB2_NIRS3_lip",
           (nb_center[0], nb_center[1], underside - 0.168),
           major_r=0.050, minor_r=0.008, coll=coll, parent=root,
           mat=metal, normal='Z')
    new += 1

    # ---- TIR : small box with a protruding lens ----
    tb_center = (0.10, 0.30, underside - 0.075)
    _box("HB2_TIR_body", tb_center, (0.130, 0.130, 0.150),
         coll, root, mat=metal, bevel=0.005)
    new += 1
    _box("HB2_TIR_hood",
         (tb_center[0], tb_center[1], underside - 0.010),
         (0.140, 0.140, 0.030), coll, root, mat=black)
    new += 1
    # protruding lens barrel
    _cyl("HB2_TIR_lens_barrel",
         (tb_center[0], tb_center[1], underside - 0.165),
         radius=0.040, depth=0.060, coll=coll, parent=root,
         mat=metal, axis='Z', verts=28)
    new += 1
    # dark glass element
    _cyl("HB2_TIR_lens_glass",
         (tb_center[0], tb_center[1], underside - 0.196),
         radius=0.034, depth=0.006, coll=coll, parent=root,
         mat=black, axis='Z', verts=28)
    new += 1
    return new


# ---------------------------------------------------------------------------
# 4. Equipment-box clutter + harnesses  (HB2_GreebleB_*)
# ---------------------------------------------------------------------------
def _build_greebles(coll, root, rad_mat):
    """~10-20 varied equipment boxes + brackets + cable/connector runs across
    the side faces to match the dense real look (image 4)."""
    gold = _mat("HB2_Gold_MLI")
    black = _mat("HB2_Black_MLI")
    silver = _mat("HB2_Silver_MLI")
    metal = _mat("HB2_Metal")
    matte = _mat("HB2_BlackMatte")
    rng = random.Random(RNG_SEED + 7)
    n = 0

    # --- equipment boxes on the side faces (proud of the MLI plates) ---
    # (axis, sign, plane, b0, c0, sb, sc, depth, mat)
    box_specs = [
        ('Y', +1, BY, -0.45, -0.30, 0.18, 0.14, 0.10, silver),
        ('Y', +1, BY, 0.50, 0.30, 0.16, 0.20, 0.12, gold),
        ('Y', +1, BY, 0.30, -0.35, 0.12, 0.12, 0.08, black),
        ('Y', -1, BY, -0.30, 0.32, 0.20, 0.12, 0.09, gold),
        ('Y', -1, BY, 0.40, -0.10, 0.14, 0.22, 0.11, silver),
        ('X', +1, BX, 0.30, 0.40, 0.16, 0.10, 0.08, black),
        ('X', +1, BX, -0.32, 0.42, 0.12, 0.10, 0.07, metal),
        ('X', -1, BX, 0.28, -0.38, 0.14, 0.12, 0.10, gold),
        ('X', -1, BX, -0.30, -0.40, 0.10, 0.16, 0.08, black),
        ('X', +1, BX, -0.10, -0.42, 0.18, 0.10, 0.06, silver),
    ]
    for i, (ax, sign, plane, b0, c0, sb, sc, depth, m) in enumerate(box_specs):
        # which two in-plane axes?
        if ax == 'X':
            bax, cax = 'Y', 'Z'
        elif ax == 'Y':
            bax, cax = 'X', 'Z'
        else:
            bax, cax = 'X', 'Y'
        center = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        size = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        center[ax] = plane + sign * (0.012 + depth * 0.5)
        size[ax] = depth
        center[bax] = b0
        size[bax] = sb
        center[cax] = c0
        size[cax] = sc
        _box(f"HB2_GreebleB_box{i}",
             (center['X'], center['Y'], center['Z']),
             (size['X'], size['Y'], size['Z']),
             coll, root, mat=m, bevel=0.004)
        n += 1
        # small fastener/connector nub on each box
        nub_c = dict(center)
        nub_c[ax] = plane + sign * (0.012 + depth + 0.012)
        _cyl(f"HB2_GreebleB_box{i}_nub",
             (nub_c['X'], nub_c['Y'], nub_c['Z']),
             radius=0.015, depth=0.024, coll=coll, parent=root,
             mat=metal, axis=ax, verts=16)
        n += 1

    # --- a small radiator-faced electronics box (uses new radiator mat) ---
    _box("HB2_GreebleB_radbox",
         (0.0, BY + 0.07, 0.15), (0.22, 0.10, 0.18),
         coll, root, mat=rad_mat, bevel=0.004)
    n += 1

    # --- cable / harness runs : thin gold conduit cylinders along faces ---
    # Each run is a short straight conduit between two points on a face.
    cable_runs = [
        # +Y face vertical/horizontal harnesses
        ('Y', +1, BY, (-0.45, -0.22), (-0.45, 0.20), 0.012),
        ('Y', +1, BY, (-0.45, 0.20), (0.45, 0.22), 0.010),
        ('Y', +1, BY, (0.50, 0.10), (0.50, -0.30), 0.010),
        # -Y face
        ('Y', -1, BY, (-0.30, 0.24), (0.40, 0.0), 0.012),
        ('Y', -1, BY, (0.40, 0.0), (0.40, -0.30), 0.010),
        # +X face
        ('X', +1, BX, (0.30, 0.30), (-0.32, 0.32), 0.010),
        # -X face
        ('X', -1, BX, (0.28, -0.28), (-0.30, -0.30), 0.010),
        ('X', -1, BX, (0.28, -0.28), (0.10, 0.20), 0.010),
    ]
    for i, (ax, sign, plane, p0, p1, rad) in enumerate(cable_runs):
        if ax == 'X':
            bax, cax = 'Y', 'Z'
        else:
            bax, cax = 'X', 'Z'
        # world endpoints
        e0 = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        e1 = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        off = plane + sign * 0.022
        e0[ax] = off
        e1[ax] = off
        e0[bax], e0[cax] = p0
        e1[bax], e1[cax] = p1
        v0 = Vector((e0['X'], e0['Y'], e0['Z']))
        v1 = Vector((e1['X'], e1['Y'], e1['Z']))
        mid = (v0 + v1) * 0.5
        length = (v1 - v0).length
        # build a Z cylinder then orient along (v1-v0)
        obj = _cyl(f"HB2_GreebleB_cable{i}", (0, 0, 0),
                   radius=rad, depth=length, coll=coll, parent=root,
                   mat=gold, axis='Z', verts=12)
        direction = (v1 - v0)
        if direction.length > 1e-6:
            quat = direction.to_track_quat('Z', 'Y')
            obj.rotation_euler = quat.to_euler()
        obj.location = mid
        n += 1
        # connector end-caps
        for j, vv in enumerate((v0, v1)):
            _box(f"HB2_GreebleB_cable{i}_c{j}",
                 (vv.x, vv.y, vv.z), (0.024, 0.024, 0.024),
                 coll, root, mat=matte)
            n += 1

    # --- a few L-brackets straddling face edges ---
    bracket_specs = [
        (0.0, BY + 0.02, 0.50, (0.30, 0.04, 0.05)),
        (0.40, BY + 0.02, -0.40, (0.20, 0.04, 0.05)),
        (BX + 0.02, -0.30, 0.40, (0.04, 0.20, 0.05)),
    ]
    for i, (x, y, z, s) in enumerate(bracket_specs):
        _box(f"HB2_GreebleB_bracket{i}", (x, y, z), s,
             coll, root, mat=metal, bevel=0.003)
        n += 1
    return n


# ---------------------------------------------------------------------------
# 5. Panel seams + fastener rings on bus panels
# ---------------------------------------------------------------------------
def _build_boltrings(coll, root):
    """Small bolt-ring circles around panel corners / box mounts."""
    metal = _mat("HB2_Metal")
    n = 0
    proud = 0.006

    def ring(tag, ax, sign, plane, b, c, r=0.018):
        nonlocal n
        center = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        if ax == 'X':
            bax, cax = 'Y', 'Z'
        elif ax == 'Y':
            bax, cax = 'X', 'Z'
        else:
            bax, cax = 'X', 'Y'
        center[ax] = plane + sign * proud
        center[bax] = b
        center[cax] = c
        _torus(f"HB2_Boltring_{tag}",
               (center['X'], center['Y'], center['Z']),
               major_r=r, minor_r=0.004, coll=coll, parent=root,
               mat=metal, normal=ax)
        n += 1

    # corner bolt rings on +/-Y faces
    for sign, tag in ((+1, "PY"), (-1, "NY")):
        for bx in (-0.62, 0.0, 0.62):
            for cz in (-0.50, 0.50):
                ring(f"{tag}_{bx:+.2f}_{cz:+.2f}".replace('.', ''),
                     'Y', sign, BY, bx, cz)
    # corner bolt rings on +/-X faces
    for sign, tag in ((+1, "PX"), (-1, "NX")):
        for by in (-0.32, 0.32):
            for cz in (-0.50, 0.50):
                ring(f"{tag}_{by:+.2f}_{cz:+.2f}".replace('.', ''),
                     'X', sign, BX, by, cz)
    return n


# ---------------------------------------------------------------------------
# 6. Refine HGAs to flat octagonal phased-array dishes
# ---------------------------------------------------------------------------
def _octagon_face_mesh(me, radius, thickness, ring_inset):
    """(Re)build mesh data `me` as a flat octagon plate (two stacked octagon
    rings -> a subtle concentric step) of given outer `radius` and `thickness`,
    centred on local origin, facing +Z."""
    bm = bmesh.new()
    half = thickness * 0.5
    rings = [radius, radius - ring_inset, radius * 0.45]
    z_top = [half, half + thickness * 0.25, half + thickness * 0.55]

    def oct_ring(r, z):
        vs = []
        for k in range(8):
            ang = math.pi / 8 + (2 * math.pi * k / 8)  # flat-topped octagon
            vs.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
        return vs

    # top concentric rings (front face, slightly raised center)
    top_rings = [oct_ring(r, z) for r, z in zip(rings, z_top)]
    center_top = bm.verts.new((0, 0, z_top[-1] + thickness * 0.15))
    # bottom ring (back face)
    bot = oct_ring(radius, -half)

    bm.verts.ensure_lookup_table()

    # bridge concentric top rings (annular faces)
    for ri in range(len(top_rings) - 1):
        a = top_rings[ri]
        b = top_rings[ri + 1]
        for k in range(8):
            bm.faces.new((a[k], a[(k + 1) % 8], b[(k + 1) % 8], b[k]))
    # cap the innermost top ring to center
    inner = top_rings[-1]
    for k in range(8):
        bm.faces.new((inner[k], inner[(k + 1) % 8], center_top))
    # side wall between outer top ring and bottom ring
    outer_top = top_rings[0]
    for k in range(8):
        bm.faces.new((outer_top[k], bot[k], bot[(k + 1) % 8], outer_top[(k + 1) % 8]))
    # bottom cap (single n-gon)
    bm.faces.new(list(reversed(bot)))

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()


def _refine_hgas():
    """Replace HB2_HGA_X_face / HB2_HGA_Ka_face meshes with flat octagons,
    add a gold rim torus (owned prefix) around each.  Idempotent."""
    ant_white = _mat("HB2_AntWhite")
    gold = _mat("HB2_Gold_MLI")
    notes = []
    details = _get_collection("HB2_Details")
    root = bpy.data.objects.get(ROOT_NAME)

    for name, radius in (("HB2_HGA_X_face", 0.41), ("HB2_HGA_Ka_face", 0.40)):
        obj = bpy.data.objects.get(name)
        if obj is None:
            notes.append(f"{name} MISSING (skipped)")
            continue
        # Rebuild its mesh in place (deterministic) -> flat octagon plate.
        _octagon_face_mesh(obj.data, radius=radius, thickness=0.020,
                           ring_inset=0.05)
        # keep it flat-facing +Z at the same world position (faces already flat)
        _assign_mat(obj, ant_white)
        for p in obj.data.polygons:
            p.use_smooth = False
        # gold rim torus around the octagon, at the face's world centre
        wc = obj.matrix_world.translation
        rim = _torus(f"HB2_Boltring_HGArim_{name[-7:]}",
                     (wc.x, wc.y, wc.z + 0.002),
                     major_r=radius * 1.005, minor_r=0.014,
                     coll=details, parent=root, mat=gold, normal='Z',
                     major_seg=8)  # octagonal rim to match plate
        notes.append(f"{name} -> flat octagon (r={radius}) + gold rim")
    return notes


# ---------------------------------------------------------------------------
# Master build  --  RETIRED (deprecated no-op)
# ---------------------------------------------------------------------------
#
# !!  THIS MODULE IS DEPRECATED AND INTENTIONALLY DOES NOTHING.  !!
#
# All of the instrument / greeble / MLI-patchwork / radiator / NIRS3 / TIR /
# bolt-ring / flat-octagon-HGA detail that this pass used to add has been FOLDED
# INTO 02_craft.py (which owns the spacecraft body and authors that detail on the
# CORRECT faces for the live bus convention HX=0.50, HY=0.80, HZ=0.625).
#
# Why it was retired (it was mutually destructive with 02_craft.py):
#   * It shared owned object prefixes with 02_craft.py (HB2_MLIplate_, HB2_Seam_,
#     HB2_NIRS3_, HB2_TIR_, HB2_GreebleB_, HB2_Boltring_, HB2_Radiator*), so the
#     two scripts overwrote / fought over the same names.
#   * Its _purge_owned() additionally deleted EVERY 0-user mesh in the whole
#     file -- a dangerous global side effect that could wipe unrelated data.
#   * It used a BACKWARDS axis convention (BX=0.80, BY=0.50 -- the 1.6 axis
#     swapped), so it painted detail on the WRONG faces of the live 1.0x1.6x1.25
#     bus.
#   * It re-authored the HB2_Radiator material (_ensure_radiator_material()),
#     which is owned by the materials agent (06_materials.py).
#
# The integrator runs 02_craft.build() then 02_instruments.build() in that order.
# Making this a no-op guarantees that sequence is safe: craft produces the
# complete, correct craft and instruments does NOT touch it (no double-purge, no
# wrong-face detail, no material re-authoring).
#
# The old implementation functions are kept below for reference only; build()
# never calls them.  If you ever revive this module, you MUST: (1) give it
# UNIQUE owned prefixes that 02_craft.py does not emit, (2) scope _purge_owned()
# to ONLY those unique prefixes (never a global 0-user mesh sweep), (3) use the
# CORRECT convention BX=0.50 / BY=0.80, and (4) DELETE _ensure_radiator_material()
# so HB2_Radiator is only ever referenced by name.
#
def build():
    print("=" * 60)
    print("02_instruments.build(): RETIRED no-op.")
    print("  All instrument/greeble/MLI/radiator detail now lives in 02_craft.py")
    print("  (authored on the correct faces).  This pass intentionally does")
    print("  nothing -- no objects created, no purge, no material edits.")
    print("=" * 60)
    return {}


# ---------------------------------------------------------------------------
# __main__ : build, then OPTIONAL cheap test render (scaffolding only here)
# ---------------------------------------------------------------------------
def _test_render(out_path):
    """Cheap Eevee test render from a temp 3/4 camera. Scaffolding ONLY -- never
    called by build(); only used for self-validation."""
    import os
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    try:
        scene.eevee.taa_render_samples = 96
        scene.eevee.use_raytracing = True
    except Exception:
        pass
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    # ensure a simple sun + fill so the bus reads even if studio lights are off
    def _ensure_sun(name, rot, energy):
        l = bpy.data.objects.get(name)
        if l is None:
            ld = bpy.data.lights.new(name, 'SUN')
            l = bpy.data.objects.new(name, ld)
            bpy.context.scene.collection.objects.link(l)
        l.data.energy = energy
        l.rotation_euler = Euler(rot)
        l.hide_render = False
        return l
    _ensure_sun("HB2_TMP_Sun", (math.radians(58), math.radians(12), math.radians(35)), 4.0)
    _ensure_sun("HB2_TMP_Fill", (math.radians(118), math.radians(-15), math.radians(200)), 2.2)
    _ensure_sun("HB2_TMP_Under", (math.radians(150), math.radians(8), math.radians(90)), 1.6)

    # temp camera framing the WHOLE bus from a couple of 3/4 angles
    cam_data = bpy.data.cameras.new("HB2_TMP_Cam")
    cam_data.lens = 55
    cam = bpy.data.objects.new("HB2_TMP_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam
    look_at = Vector((0.0, 0.0, 0.0))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    base, ext = os.path.splitext(out_path)
    # angle A : +Y / -X / top 3-4 (sees +Y face + top + HGAs)
    # angle B : -Y / +X / low 3-4 (sees -Y ion side + underside instruments)
    angles = [
        ("", Vector((2.6, -3.0, 1.7))),          # +Y/-X/top hero 3-4
        ("_b", Vector((-2.4, -2.8, -1.6))),      # low 3-4 from -Y looking UP at underside
    ]
    for suffix, loc in angles:
        cam.location = loc
        tgt = look_at if suffix == "" else Vector((0.0, -0.1, -0.55))  # aim at underside
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = out_path if suffix == "" else f"{base}{suffix}{ext}"
        bpy.ops.render.render(write_still=True)
        print(f"  test render written: {scene.render.filepath}")


if __name__ == "__main__":
    import sys
    build()
    argv = sys.argv
    if "--shot" in argv:
        idx = argv.index("--shot")
        if idx + 1 < len(argv):
            _test_render(argv[idx + 1])
