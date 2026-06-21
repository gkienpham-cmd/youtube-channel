# -*- coding: utf-8 -*-
"""
02_craft.py  --  HERO rebuild of the JAXA Hayabusa2 spacecraft body + instruments.

Blender 5.1 / Eevee Next.  Photorealistic 1:1 match to JAXA references (image 7 primary).

WHAT THIS DOES
  build()  (idempotent) :
    (a) deletes every legacy MESH parented to HB2_Root whose name does NOT start
        with "HB2_Solar" (purging orphan mesh data), keeping HB2_Root itself.
    (b) rebuilds the bus at CORRECT proportions:
            X = 1.0  (span / solar-attach axis)
            Y = 1.6  (depth, front-to-back)
            Z = 1.25 (height)
        faces at x=+/-0.50, y=+/-0.80, z=+/-0.625.  Taller-than-wide across the
        wings, deeper front-to-back.  (Old model had X/Y swapped -> the LEGO look.)
    (c) DE-LEGOs everything: bevel + smooth-by-angle on every structural object,
        recessed/raised alternating gold/black MLI relief on the bus faces,
        solidified blanket plates, struts / lattice at the solar-yoke roots and
        bracketing the antennas + sampler horn.
    (d) full instrument suite placed per image 7 (two flat-octagon phased-array
        HGAs along the depth axis, MGA, LGA, star trackers, sampler horn cluster,
        ONC-T/W1/W2, LIDAR, LRF-S1/S2, NIRS3, TIR, reentry capsule, 4 ion engines
        + glow disks, 12 RCS, deployables, greebles).
    (e) parents all new objects to HB2_Root and links them into the existing
        collections.  Re-running build() yields an identical scene.

CONVENTION (per orchestrator spec):
    +Z = top deck (antennas)      -Z = underside (asteroid-facing instruments)
    +/-X = solar wing span axis    -Y = ion-engine depth face

HARD RULES honoured:
  * No Blender MCP used.  Headless only.
  * Materials are assigned BY NAME only; none are created/edited/deleted.
  * HB2_Solar*, HB2_Earth*, Ryugu, HB2_Root, cameras and lights are untouched.
  * HB2_IonGlow0..3 are recreated with those exact names (render harness toggles
    them) in collection HB2_FX, material HB2_IonGlow.

USAGE
  Build only:
    blender --background work_craft.blend --python 02_craft.py
  Build + cheap test renders (front / top / three-quarter) written next to the
  path(s) given after --shot:
    blender --background work_craft.blend --python 02_craft.py -- --shot /tmp/t.png
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ----------------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------------
ROOT_NAME = "HB2_Root"
TAU = math.tau

# bus half-extents (faces). X span, Y depth, Z height.
HX = 0.50      # x face at +/-0.50  (span = 1.0)
HY = 0.80      # y face at +/-0.80  (depth = 1.6)
HZ = 0.625     # z face at +/-0.625 (height = 1.25)

# collections we are allowed to use (must already exist)
COLL = {
    "bus": "HB2_Bus",
    "ant": "HB2_Antennas",
    "inst": "HB2_Instruments",
    "prop": "HB2_Propulsion",
    "dep": "HB2_Deployables",
    "det": "HB2_Details",
    "fx": "HB2_FX",
}

# material names (assign-by-name only)
M_GOLD = "HB2_Gold_MLI"
M_BLACK = "HB2_Black_MLI"
M_SILVER = "HB2_Silver_MLI"
M_METAL = "HB2_Metal"
M_ANTMETAL = "HB2_AntMetal"
M_ANTWHITE = "HB2_AntWhite"
M_BLACKMATTE = "HB2_BlackMatte"
M_RAD = "HB2_Radiator"
M_IONGLOW = "HB2_IonGlow"
M_MARKER = "HB2_Marker"

# bookkeeping: names we create this run (so we can be idempotent & report count)
_CREATED = []


# ----------------------------------------------------------------------------
# low-level helpers
# ----------------------------------------------------------------------------
def _root():
    return bpy.data.objects.get(ROOT_NAME)


def _get_coll(key):
    c = bpy.data.collections.get(COLL[key])
    if c is None:
        # should already exist; create as a safety net and link to scene
        c = bpy.data.collections.new(COLL[key])
        bpy.context.scene.collection.children.link(c)
    return c


def _unlink_from_all_colls(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)


def _link(obj, coll_key):
    _unlink_from_all_colls(obj)
    _get_coll(coll_key).objects.link(obj)


def _assign_mat(obj, *mat_names):
    """Assign existing materials BY NAME. Never create/edit a material."""
    obj.data.materials.clear()
    for mn in mat_names:
        m = bpy.data.materials.get(mn)
        if m is None:
            # do NOT create materials; just skip silently (rule 5)
            continue
        obj.data.materials.append(m)


def _set_mat_index(obj, face_indices, slot):
    for fi in face_indices:
        obj.data.polygons[fi].material_index = slot


def _finalize(obj, coll_key, mats, parent=True, smooth_angle_deg=35.0,
              shade_smooth=True):
    """Common post-creation: name bookkeeping, parent, collection, material,
    smooth-by-angle (de-LEGO)."""
    if parent:
        r = _root()
        obj.parent = r
        obj.matrix_parent_inverse = r.matrix_world.inverted()
    _link(obj, coll_key)
    if isinstance(mats, str):
        mats = (mats,)
    _assign_mat(obj, *mats)
    if shade_smooth and obj.type == "MESH" and len(obj.data.polygons):
        for p in obj.data.polygons:
            p.use_smooth = True
        # auto-smooth via custom split normals (5.1 uses modifier/op)
        try:
            _shade_smooth_by_angle(obj, math.radians(smooth_angle_deg))
        except Exception:
            pass
    _CREATED.append(obj.name)
    return obj


def _shade_smooth_by_angle(obj, angle_rad):
    """Apply smooth-by-angle to one object headlessly (selection-safe)."""
    vl = bpy.context.view_layer
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    vl.objects.active = obj
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=angle_rad)
    except Exception:
        # fallback: just flat->smooth flag already set
        pass


def _bevel(obj, width=0.012, segments=2, angle_deg=30.0, harden=True,
           clamp=True, profile=0.7):
    """Add (idempotent) a Bevel modifier so nothing is a razor-edged box."""
    mod = obj.modifiers.get("HB2_Bevel")
    if mod is None:
        mod = obj.modifiers.new("HB2_Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle_deg)
    mod.harden_normals = harden
    mod.use_clamp_overlap = clamp
    mod.profile = profile
    mod.miter_outer = "MITER_ARC"
    return mod


def _solidify(obj, thickness=0.012, offset=-1.0):
    mod = obj.modifiers.get("HB2_Solid")
    if mod is None:
        mod = obj.modifiers.new("HB2_Solid", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = offset
    return mod


# ---- primitive builders (return object, NOT yet finalized) ----------------
def _mesh_obj_from_bm(name, bm):
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)  # temp; _finalize relinks
    return obj


def _box(name, size, loc=(0, 0, 0), rot=(0, 0, 0)):
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(sx, sy, sz))
    obj = _mesh_obj_from_bm(name, bm)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def _cyl(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), verts=24, cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts,
                          radius1=radius, radius2=radius, depth=depth)
    obj = _mesh_obj_from_bm(name, bm)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def _cone(name, r1, r2, depth, loc=(0, 0, 0), rot=(0, 0, 0), verts=24, cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts,
                          radius1=r1, radius2=r2, depth=depth)
    obj = _mesh_obj_from_bm(name, bm)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def _ngon_plate(name, radius, depth, sides=8, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Flat n-gon prism (octagon HGA face / base)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides,
                          radius1=radius, radius2=radius, depth=depth)
    obj = _mesh_obj_from_bm(name, bm)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def _uvsphere(name, radius, loc=(0, 0, 0), seg=24, ring=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=radius)
    obj = _mesh_obj_from_bm(name, bm)
    obj.location = loc
    return obj


# ----------------------------------------------------------------------------
# STEP (a) -- delete legacy craft
# ----------------------------------------------------------------------------
def _purge_legacy():
    r = _root()
    if r is None:
        raise RuntimeError("HB2_Root not found -- aborting (will not create it).")
    doomed = []
    for o in list(bpy.data.objects):
        if o.parent is r and o.type == "MESH" and not o.name.startswith("HB2_Solar"):
            doomed.append(o)
    dead_meshes = set()
    for o in doomed:
        if o.data and o.data.users <= 1:
            dead_meshes.add(o.data)
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
    # purge orphan mesh datablocks we just freed
    for me in list(dead_meshes):
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except Exception:
            pass
    # second sweep: any orphan meshes with 0 users left behind
    for me in list(bpy.data.meshes):
        if me.users == 0 and me.name.startswith(("HB2_", )):
            try:
                bpy.data.meshes.remove(me)
            except Exception:
                pass


# ----------------------------------------------------------------------------
# STEP (b)+(c) -- the bus body with surface relief
# ----------------------------------------------------------------------------
def _build_bus_core():
    """Central bus prism at correct proportions, with per-face MLI relief built
    directly into the mesh (inset + extrude alternating panels) so no face is a
    flat razor plane.  Beveled + smoothed."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(2 * HX, 2 * HY, 2 * HZ))
    bm.normal_update()
    bm.faces.ensure_lookup_table()

    # We'll process each of the 6 faces: subdivide into a grid, then inset each
    # sub-face and push it in/out to read as discrete MLI blanket panels.
    # Tag faces by their dominant normal axis.
    def axis_of(f):
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        return ax, (1 if n[ax] > 0 else -1)

    src_faces = list(bm.faces)
    for f in src_faces:
        ax, sgn = axis_of(f)
        # grid subdivisions: more along the long axes
        if ax == 0:      # +/-X face spans (Y,Z) = (1.6,1.25)
            cuts_u, cuts_v = 2, 2
        elif ax == 1:    # +/-Y face spans (X,Z) = (1.0,1.25)
            cuts_u, cuts_v = 1, 2
        else:            # +/-Z face spans (X,Y) = (1.0,1.6)
            cuts_u, cuts_v = 1, 2
        res = bmesh.ops.subdivide_edges(
            bm, edges=f.edges, cuts=max(cuts_u, cuts_v), use_grid_fill=True)
        bm.faces.ensure_lookup_table()

    bm.normal_update()
    # Now inset+extrude every face to make recessed/raised MLI panels with a
    # double inset (frame + quilted pad) so the body never reads as a flat box.
    panel_faces = [f for f in bm.faces]
    for i, f in enumerate(panel_faces):
        # outer frame inset (recessed channel showing structure)
        r1 = bmesh.ops.inset_individual(
            bm, faces=[f], thickness=0.025, depth=-0.008, use_even_offset=True)
        # inner quilted pad raised proud of the frame
        push = 0.022 if (i % 2 == 0) else 0.012
        bmesh.ops.inset_individual(
            bm, faces=[f], thickness=0.02, depth=0.0, use_even_offset=True)
        bmesh.ops.translate(bm, verts=f.verts, vec=f.normal * push)
    bm.normal_update()

    obj = _mesh_obj_from_bm("HB2_BusCore", bm)
    obj.location = (0, 0, 0)
    _finalize(obj, "bus", M_GOLD, smooth_angle_deg=26.0)
    # generous bevel so corners are clearly rounded (kills the razor-box look)
    _bevel(obj, width=0.022, segments=3, angle_deg=32.0, harden=True)
    return obj


def _build_bus_blankets():
    """Separate alternating gold/black/silver MLI blanket plates laid over each
    bus face with real thickness (solidify), small gaps showing structure.
    These are the 'busy surface' layer on top of the core relief."""
    faces = [
        # (axis, sign, label)
        (0, +1, "PX"), (0, -1, "NX"),
        (1, +1, "PY"), (1, -1, "NY"),
        (2, +1, "PZ"), (2, -1, "NZ"),
    ]
    mats_cycle = [M_GOLD, M_BLACK, M_GOLD, M_SILVER, M_BLACK, M_GOLD]
    gap = 0.022
    for ax, sgn, lbl in faces:
        if ax == 0:
            uext, vext = HY, HZ        # plate spans Y,Z
            nu, nv = 2, 2
            base = lambda u, v: (sgn * (HX + 0.006), u, v)
            usz = lambda du: (0.006, du, None)
        elif ax == 1:
            uext, vext = HX, HZ
            nu, nv = 2, 2
            base = lambda u, v: (u, sgn * (HY + 0.006), v)
        else:
            uext, vext = HX, HY
            nu, nv = 2, 2
            base = lambda u, v: (u, v, sgn * (HZ + 0.006))
        # grid of plates
        k = 0
        for iu in range(nu):
            for iv in range(nv):
                du = (2 * uext) / nu - gap
                dv = (2 * vext) / nv - gap
                cu = -uext + (iu + 0.5) * (2 * uext / nu)
                cv = -vext + (iv + 0.5) * (2 * vext / nv)
                if ax == 0:
                    loc = (sgn * (HX + 0.007), cu, cv)
                    size = (0.012, du, dv)
                elif ax == 1:
                    loc = (cu, sgn * (HY + 0.007), cv)
                    size = (du, 0.012, dv)
                else:
                    loc = (cu, cv, sgn * (HZ + 0.007))
                    size = (du, dv, 0.012)
                nm = "HB2_MLIplate_%s_%d_%d" % (lbl, iu, iv)
                mat = mats_cycle[(iu * nv + iv + (0 if sgn > 0 else 3)) % len(mats_cycle)]
                ob = _box(nm, size, loc)
                _finalize(ob, "bus", mat, smooth_angle_deg=40.0)
                _bevel(ob, width=0.005, segments=2, angle_deg=35.0)
                _solidify(ob, thickness=0.01)
                k += 1


def _build_bus_panel_seams():
    """Thin dark seam lines between blanket panels (structure showing through)."""
    seams = []
    # vertical seams on the 4 side faces (split the face mid-height path)
    for ax, sgn, lbl in [(0, +1, "PX"), (0, -1, "NX"), (1, +1, "PY"), (1, -1, "NY")]:
        if ax == 0:
            off = sgn * (HX + 0.012)
            # horizontal mid seam (along Y) and vertical mid seam (along Z)
            seams.append(("HB2_Seam_%s_h0" % lbl, (0.004, 2 * HY * 0.98, 0.005),
                          (off, 0, 0.0)))
            seams.append(("HB2_Seam_%s_v0" % lbl, (0.004, 0.005, 2 * HZ * 0.98),
                          (off, 0.0, 0)))
        else:
            off = sgn * (HY + 0.012)
            seams.append(("HB2_Seam_%s_h0" % lbl, (2 * HX * 0.98, 0.004, 0.005),
                          (0, off, 0.0)))
            seams.append(("HB2_Seam_%s_v0" % lbl, (0.005, 0.004, 2 * HZ * 0.98),
                          (0.0, off, 0)))
    for nm, size, loc in seams:
        ob = _box(nm, size, loc)
        _finalize(ob, "bus", M_BLACKMATTE, smooth_angle_deg=50.0, shade_smooth=False)


def _build_top_bottom_panels():
    """Top deck plate (instrument mounting) and bottom panel (asteroid-facing
    deck), slightly oversized with beveled rims."""
    # top deck
    top = _box("HB2_TopDeck", (2 * HX * 1.02, 2 * HY * 1.02, 0.05),
               (0, 0, HZ + 0.012))
    _finalize(top, "bus", M_GOLD, smooth_angle_deg=40.0)
    _bevel(top, width=0.012, segments=2, angle_deg=40.0)
    # bottom panel
    bot = _box("HB2_BottomPanel", (2 * HX * 1.02, 2 * HY * 1.02, 0.06),
               (0, 0, -HZ - 0.015))
    _finalize(bot, "bus", M_SILVER, smooth_angle_deg=40.0)
    _bevel(bot, width=0.012, segments=2, angle_deg=40.0)


def _build_radiators():
    """Slatted radiator panels on the +/-X side faces (real louvers)."""
    for sgn, lbl in [(+1, "PX"), (-1, "NX")]:
        off = sgn * (HX + 0.02)
        frame = _box("HB2_Radiator_%s_frame" % lbl, (0.014, 0.62, 0.7),
                     (off, 0.0, 0.0))
        _finalize(frame, "bus", M_RAD, smooth_angle_deg=45.0, shade_smooth=False)
        _bevel(frame, width=0.005, segments=1)
        n = 9
        for i in range(n):
            z = -0.30 + i * (0.60 / (n - 1))
            sl = _box("HB2_Radiator_%s_slat%d" % (lbl, i),
                      (0.016, 0.58, 0.04), (off + sgn * 0.004, 0.0, z))
            _finalize(sl, "bus", M_RAD, smooth_angle_deg=45.0, shade_smooth=False)
            _bevel(sl, width=0.004, segments=1)


# ----------------------------------------------------------------------------
# struts / lattice  (image 7: visible trusses)
# ----------------------------------------------------------------------------
def _strut(name, p0, p1, r=0.018, verts=8, coll="det", mat=M_METAL):
    p0 = Vector(p0)
    p1 = Vector(p1)
    mid = (p0 + p1) * 0.5
    d = (p1 - p0)
    length = d.length
    if length < 1e-5:
        return None
    ob = _cyl(name, r, length, verts=verts)
    # orient +Z along d
    z = Vector((0, 0, 1))
    dn = d.normalized()
    axis = z.cross(dn)
    if axis.length < 1e-6:
        rotm = Matrix.Identity(4) if dn.z > 0 else Matrix.Rotation(math.pi, 4, "X")
    else:
        ang = math.acos(max(-1, min(1, z.dot(dn))))
        rotm = Matrix.Rotation(ang, 4, axis.normalized())
    ob.location = mid
    ob.rotation_euler = rotm.to_euler()
    _finalize(ob, coll, mat, smooth_angle_deg=50.0)
    _bevel(ob, width=0.004, segments=1)
    return ob


def _build_solar_yoke_struts():
    """Lattice / box members at the solar-yoke roots on the +/-X faces.
    The wings attach on X; build a small truss bracket where they meet the bus."""
    for sgn in (+1, -1):
        x0 = sgn * HX
        side = "R" if sgn > 0 else "L"
        # two longeron roots top & bottom (matching solar longeron Z=0.15)
        for yy in (+0.5, -0.5):
            base = _box("HB2_YokeRoot_%s_%s" % (side, "P" if yy > 0 else "N"),
                        (0.10, 0.10, 0.12), (sgn * (HX + 0.05), yy, 0.15))
            _finalize(base, "bus", M_GOLD, smooth_angle_deg=40.0)
            _bevel(base, width=0.006, segments=2)
        # diagonal truss members from bus face out to a yoke node
        node = Vector((sgn * (HX + 0.16), 0.0, 0.15))
        for yy in (+0.5, -0.5):
            _strut("HB2_YokeStrut_%s_%s0" % (side, "P" if yy > 0 else "N"),
                   (x0 + sgn * 0.01, yy, 0.15), node, r=0.02, coll="bus")
            _strut("HB2_YokeStrut_%s_%s1" % (side, "P" if yy > 0 else "N"),
                   (x0 + sgn * 0.01, yy, 0.15 + 0.0),
                   (sgn * (HX + 0.05), yy, 0.45), r=0.016, coll="bus")
        # the yoke hub the panels pivot on
        hub = _cyl("HB2_YokeHub_%s" % side, 0.05, 1.05,
                   loc=(sgn * (HX + 0.13), 0.0, 0.15), rot=(math.pi / 2, 0, 0),
                   verts=12)
        _finalize(hub, "bus", M_METAL, smooth_angle_deg=50.0)
        _bevel(hub, width=0.006, segments=2)


def _build_antenna_struts(hga_specs):
    """Box/tube members bracketing the two top antennas (image 7 trusses)."""
    for spec in hga_specs:
        cx, cy = spec["x"], spec["y"]
        z_top = HZ + 0.05 + spec["leg_h"]
        # cross brace between the 4 legs
        br = _box("HB2_%s_brace" % spec["tag"],
                  (spec["r"] * 1.2, 0.03, 0.03),
                  (cx, cy, HZ + 0.05 + spec["leg_h"] * 0.55))
        _finalize(br, "ant", M_METAL, smooth_angle_deg=50.0)
        _bevel(br, width=0.004, segments=1)


# ----------------------------------------------------------------------------
# STEP (d) -- instruments
# ----------------------------------------------------------------------------
def _build_hgas():
    """Two flat octagonal phased-array HGAs on the +Z top deck, arranged along
    the Y (depth) axis so their long span fits side-by-side.  Flat octagon
    plates with concentric ring pattern + rim + feed -- NOT parabolic dishes."""
    z_deck = HZ + 0.05
    specs = [
        dict(tag="HGA_X", x=0.0, y=+0.40, r=0.46, leg_h=0.33,
             base_mat=M_ANTMETAL, face_mat=M_ANTWHITE),
        dict(tag="HGA_Ka", x=0.0, y=-0.34, r=0.46, leg_h=0.30,
             base_mat=M_ANTMETAL, face_mat=M_ANTWHITE),
    ]
    for s in specs:
        cx, cy, r, lh = s["x"], s["y"], s["r"], s["leg_h"]
        z0 = z_deck + lh
        # 4 short legs raising the dish
        leg_r = r * 0.62
        for i, (dx, dy) in enumerate([(leg_r, leg_r), (-leg_r, leg_r),
                                      (-leg_r, -leg_r), (leg_r, -leg_r)]):
            lg = _cyl("HB2_%s_leg%d" % (s["tag"], i), 0.018, lh,
                      loc=(cx + dx * 0.7, cy + dy * 0.7, z_deck + lh * 0.5),
                      verts=8)
            _finalize(lg, "ant", M_METAL, smooth_angle_deg=50.0)
            _bevel(lg, width=0.004, segments=1)
        # base octagon (metal frame) -- thicker
        base = _ngon_plate("HB2_%s_base" % s["tag"], r, 0.05, sides=8,
                           loc=(cx, cy, z0), rot=(0, 0, math.radians(22.5)))
        _finalize(base, "ant", s["base_mat"], smooth_angle_deg=20.0)
        _bevel(base, width=0.01, segments=2, angle_deg=20.0)
        # face octagon (white phased-array) sitting just above the base
        face = _ngon_plate("HB2_%s_face" % s["tag"], r * 0.86, 0.03, sides=8,
                           loc=(cx, cy, z0 + 0.035),
                           rot=(0, 0, math.radians(22.5)))
        _finalize(face, "ant", s["face_mat"], smooth_angle_deg=20.0)
        _bevel(face, width=0.006, segments=1, angle_deg=20.0)
        # concentric ring pattern: 2 raised rings + center
        for j, rr in enumerate([r * 0.62, r * 0.34]):
            ring = _cyl("HB2_%s_ring%d" % (s["tag"], j), rr, 0.012,
                        loc=(cx, cy, z0 + 0.05), verts=8)
            ring.rotation_euler = (0, 0, math.radians(22.5))
            _finalize(ring, "ant", s["base_mat"], smooth_angle_deg=20.0)
            _bevel(ring, width=0.004, segments=1, angle_deg=20.0)
        # center feed
        feed = _cyl("HB2_%s_feed" % s["tag"], 0.05, 0.06,
                    loc=(cx, cy, z0 + 0.07), verts=12)
        _finalize(feed, "ant", s["base_mat"], smooth_angle_deg=30.0)
        _bevel(feed, width=0.005, segments=1)
    _build_antenna_struts(specs)
    return specs


def _build_mga_lga():
    """X-band MGA (mid-gain horn/dome) + LGA (low-gain stub) on the top deck,
    set off to one side of the two HGAs."""
    z_deck = HZ + 0.05
    # MGA: stalk + dome + horn, near +Y edge between/beside HGAs
    mx, my = 0.34, 0.05
    stalk = _cyl("HB2_MGA_stalk", 0.03, 0.12, loc=(mx, my, z_deck + 0.06),
                 verts=10)
    _finalize(stalk, "ant", M_GOLD, smooth_angle_deg=40.0)
    _bevel(stalk, width=0.004, segments=1)
    dome = _uvsphere("HB2_MGA_ball", 0.09, loc=(mx, my, z_deck + 0.17))
    _finalize(dome, "ant", M_GOLD, smooth_angle_deg=60.0)
    horn = _cone("HB2_MGA_horn", 0.04, 0.09, 0.16,
                 loc=(mx, my, z_deck + 0.30), verts=16)
    _finalize(horn, "ant", M_BLACKMATTE, smooth_angle_deg=50.0)
    _bevel(horn, width=0.004, segments=1)
    # LGA: small stalk + cap, other side
    lx, ly = -0.34, 0.05
    lstalk = _cyl("HB2_LGA_stalk", 0.022, 0.12, loc=(lx, ly, z_deck + 0.06),
                  verts=10)
    _finalize(lstalk, "ant", M_ANTMETAL, smooth_angle_deg=40.0)
    _bevel(lstalk, width=0.004, segments=1)
    ldome = _uvsphere("HB2_LGA_dome", 0.052, loc=(lx, ly, z_deck + 0.14))
    _finalize(ldome, "ant", M_GOLD, smooth_angle_deg=60.0)
    lcap = _ngon_plate("HB2_LGA_cap", 0.07, 0.025, sides=12,
                       loc=(lx, ly, z_deck + 0.185))
    _finalize(lcap, "ant", M_ANTMETAL, smooth_angle_deg=40.0)
    _bevel(lcap, width=0.004, segments=1)


def _build_star_trackers():
    """Two hooded star trackers on the upper -Y side (image 5/7)."""
    for sgn, side in [(+1, "R"), (-1, "L")]:
        cx = sgn * 0.32
        body = _box("HB2_StarTracker_%s" % side, (0.12, 0.12, 0.14),
                    (cx, -HY + 0.02, 0.42))
        _finalize(body, "ant", M_METAL, smooth_angle_deg=40.0)
        _bevel(body, width=0.006, segments=2)
        hood = _cone("HB2_StarTrackerBaffle_%s" % side, 0.055, 0.07, 0.10,
                     loc=(cx, -HY - 0.06, 0.45), rot=(math.pi / 2, 0, 0),
                     verts=16)
        _finalize(hood, "ant", M_BLACKMATTE, smooth_angle_deg=50.0)
        _bevel(hood, width=0.004, segments=1)


def _build_sampler():
    """Sampler horn cluster on the -Z underside: collar + ~1m tapered tube with
    a slightly flared tip projecting down."""
    collar = _cyl("HB2_SamplerCollar", 0.13, 0.10, loc=(0, 0, -HZ - 0.06),
                  verts=20)
    _finalize(collar, "inst", M_METAL, smooth_angle_deg=40.0)
    _bevel(collar, width=0.006, segments=2)
    # main horn (tapered) hanging down ~1m
    horn = _cone("HB2_SamplerHorn", 0.075, 0.06, 0.90,
                 loc=(0, 0, -HZ - 0.55), verts=24)
    _finalize(horn, "inst", M_METAL, smooth_angle_deg=35.0)
    _bevel(horn, width=0.006, segments=2)
    # flared tip
    tip = _cone("HB2_SamplerTip", 0.06, 0.115, 0.13,
                loc=(0, 0, -HZ - 1.05), verts=24)
    _finalize(tip, "inst", M_METAL, smooth_angle_deg=35.0)
    _bevel(tip, width=0.005, segments=1)
    # a couple of struts bracketing the horn root (image 7 trusses)
    for ang in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5):
        x = 0.18 * math.cos(ang)
        y = 0.18 * math.sin(ang)
        _strut("HB2_SamplerStrut_%d" % int(math.degrees(ang)),
               (x * 0.4, y * 0.4, -HZ - 0.04),
               (x, y, -HZ - 0.30), r=0.012, coll="inst")


def _build_underside_cameras():
    """ONC-T / ONC-W1 / ONC-W2 cameras, LIDAR, LRF-S1/S2, NIRS3, TIR, reentry
    capsule -- all on the -Z underside cluster, looking down (-Z)."""
    zb = -HZ - 0.01     # mounting plane just below bottom deck
    def cam(name, body_r, body_h, lens_r, lens_h, loc, body_mat=M_METAL):
        bx, by = loc
        b = _cyl(name + "_body", body_r, body_h, loc=(bx, by, zb - body_h / 2),
                 verts=18)
        _finalize(b, "inst", body_mat, smooth_angle_deg=40.0)
        _bevel(b, width=0.005, segments=2)
        l = _cyl(name + "_lens", lens_r, lens_h,
                 loc=(bx, by, zb - body_h - lens_h / 2 + 0.005), verts=18)
        _finalize(l, "inst", M_BLACKMATTE, smooth_angle_deg=40.0)
        _bevel(l, width=0.004, segments=1)

    cam("HB2_ONC_T", 0.065, 0.18, 0.05, 0.08, (0.30, -0.22))
    cam("HB2_ONC_W1", 0.045, 0.10, 0.03, 0.05, (0.30, 0.12))
    cam("HB2_ONC_W2", 0.043, 0.10, 0.028, 0.05, (-0.12, 0.30))
    cam("HB2_LIDAR", 0.075, 0.16, 0.055, 0.07, (-0.33, -0.20))

    # LRF-S1/S2 small range finders
    for i, (lx, ly) in enumerate([(0.12, -0.36), (-0.05, -0.40)]):
        b = _box("HB2_LRF_%s" % ("a" if i == 0 else "b"), (0.05, 0.05, 0.06),
                 (lx, ly, zb - 0.03))
        _finalize(b, "inst", M_BLACKMATTE, smooth_angle_deg=45.0)
        _bevel(b, width=0.004, segments=1)

    # NIRS3 (near-IR spectrometer): collar + body + lip + aperture
    nx, ny = -0.30, 0.12
    col = _cyl("HB2_NIRS3_collar", 0.085, 0.04, loc=(nx, ny, zb - 0.02), verts=18)
    _finalize(col, "inst", M_GOLD, smooth_angle_deg=40.0)
    _bevel(col, width=0.004, segments=1)
    body = _box("HB2_NIRS3_body", (0.15, 0.14, 0.16), (nx, ny, zb - 0.10))
    _finalize(body, "inst", M_GOLD, smooth_angle_deg=40.0)
    _bevel(body, width=0.005, segments=2)
    lip = _cyl("HB2_NIRS3_lip", 0.058, 0.016, loc=(nx, ny, zb - 0.05), verts=18)
    _finalize(lip, "inst", M_METAL, smooth_angle_deg=40.0)
    _bevel(lip, width=0.003, segments=1)
    ap = _cyl("HB2_NIRS3_aperture", 0.045, 0.02, loc=(nx, ny, zb - 0.065),
              verts=16)
    _finalize(ap, "inst", M_BLACKMATTE, smooth_angle_deg=40.0)

    # TIR (thermal IR imager): body + barrel + hood
    tx, ty = 0.12, 0.30
    tbody = _box("HB2_TIR_body", (0.13, 0.13, 0.15), (tx, ty, zb - 0.09))
    _finalize(tbody, "inst", M_METAL, smooth_angle_deg=40.0)
    _bevel(tbody, width=0.005, segments=2)
    tbar = _cyl("HB2_TIR_lens_barrel", 0.04, 0.06, loc=(tx, ty, zb - 0.18),
                verts=16)
    _finalize(tbar, "inst", M_METAL, smooth_angle_deg=40.0)
    _bevel(tbar, width=0.003, segments=1)
    thood = _cyl("HB2_TIR_hood", 0.07, 0.03, loc=(tx, ty, zb - 0.215), verts=18)
    _finalize(thood, "inst", M_BLACKMATTE, smooth_angle_deg=45.0)

    # reentry capsule: truncated cone (~0.4m) on the +Y upper side area
    cx, cy, cz = 0.0, 0.58, 0.30
    drum = _cyl("HB2_Capsule_drum", 0.20, 0.18, loc=(cx, cy, cz),
                rot=(math.pi / 2, 0, 0), verts=24)
    _finalize(drum, "dep", M_GOLD, smooth_angle_deg=40.0)
    _bevel(drum, width=0.006, segments=2)
    ring = _cyl("HB2_Capsule_ring", 0.205, 0.03, loc=(cx, cy - 0.085, cz),
                rot=(math.pi / 2, 0, 0), verts=24)
    _finalize(ring, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(ring, width=0.004, segments=1)
    shield = _cone("HB2_Capsule_shield", 0.20, 0.13, 0.10,
                   loc=(cx, cy + 0.10, cz), rot=(-math.pi / 2, 0, 0), verts=24)
    _finalize(shield, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(shield, width=0.004, segments=1)


# ----------------------------------------------------------------------------
# propulsion: ion engines + glow + RCS
# ----------------------------------------------------------------------------
def _build_ion_engines():
    """4 mu10 ion engines on a gimbal plate on the -Y depth face, firing -Y.
    Recreate HB2_IonGlow0..3 (exact names) in HB2_FX with HB2_IonGlow."""
    yface = -HY
    # gimbal mounting plate flush to -Y face
    plate = _box("HB2_IES_plate", (0.72, 0.10, 0.52), (0, yface - 0.04, -0.05))
    _finalize(plate, "prop", M_METAL, smooth_angle_deg=40.0)
    _bevel(plate, width=0.006, segments=2)
    gim = _ngon_plate("HB2_IES_gimbal", 0.30, 0.06, sides=16,
                      loc=(0, yface - 0.02, -0.05), rot=(math.pi / 2, 0, 0))
    _finalize(gim, "prop", M_GOLD, smooth_angle_deg=40.0)
    _bevel(gim, width=0.005, segments=2)

    centers = [(-0.2, 0.10), (0.2, 0.10), (-0.2, -0.20), (0.2, -0.20)]
    for i, (cx, cz) in enumerate(centers):
        # thruster body (round)
        body = _cyl("HB2_IonThr%d_body" % i, 0.085, 0.12,
                    loc=(cx, yface - 0.10, cz), rot=(math.pi / 2, 0, 0),
                    verts=20)
        _finalize(body, "prop", M_METAL, smooth_angle_deg=35.0)
        _bevel(body, width=0.005, segments=2)
        # gridded exit (dark disk)
        grid = _cyl("HB2_IonThr%d_grid" % i, 0.082, 0.02,
                    loc=(cx, yface - 0.165, cz), rot=(math.pi / 2, 0, 0),
                    verts=24)
        _finalize(grid, "prop", M_BLACKMATTE, smooth_angle_deg=40.0)
        _bevel(grid, width=0.003, segments=1)
        # glow disk -- EXACT NAME, HB2_FX collection, HB2_IonGlow material
        glow = _cyl("HB2_IonGlow%d" % i, 0.072, 0.012,
                    loc=(cx, yface - 0.185, cz), rot=(math.pi / 2, 0, 0),
                    verts=24)
        _finalize(glow, "fx", M_IONGLOW, smooth_angle_deg=40.0,
                  shade_smooth=False)


def _build_rcs():
    """12 RCS thrusters at the corners/edges, pointing outward."""
    # 12 positions: 4 top corners, 4 bottom corners, plus 4 mid-edge
    pts = []
    for sx in (+1, -1):
        for sy in (+1, -1):
            pts.append((sx * (HX - 0.02), sy * (HY - 0.06), +HZ - 0.05, sx, 0, 0))
            pts.append((sx * (HX - 0.02), sy * (HY - 0.06), -HZ + 0.05, sx, 0, 0))
    # add 4 more on +/-Y edges to reach 12
    extra = [
        (HX - 0.02, HY - 0.02, 0.0, 0, 1, 0),
        (-HX + 0.02, HY - 0.02, 0.0, 0, 1, 0),
        (HX - 0.02, -HY + 0.02, 0.0, 0, -1, 0),
        (-HX + 0.02, -HY + 0.02, 0.0, 0, -1, 0),
    ]
    pts = pts[:8] + extra  # exactly 12
    for i, (px, py, pz, nx, ny, nz) in enumerate(pts):
        # small flared nozzle pointing along outward normal
        nrm = Vector((nx, ny, nz))
        if nrm.length < 1e-6:
            nrm = Vector((1, 0, 0))
        nrm.normalize()
        noz = _cone("HB2_RCS%02d" % i, 0.018, 0.03, 0.055, verts=12)
        # orient the cone's +Z along the outward normal
        zaxis = Vector((0, 0, 1))
        axis = zaxis.cross(nrm)
        if axis.length < 1e-6:
            rot = (0, 0, 0) if nrm.z > 0 else (math.pi, 0, 0)
        else:
            ang = math.acos(max(-1, min(1, zaxis.dot(nrm))))
            rot = Matrix.Rotation(ang, 4, axis.normalized()).to_euler()
        noz.location = (px + nrm.x * 0.03, py + nrm.y * 0.03, pz + nrm.z * 0.03)
        noz.rotation_euler = rot
        _finalize(noz, "prop", M_METAL, smooth_angle_deg=40.0)
        _bevel(noz, width=0.003, segments=1)


# ----------------------------------------------------------------------------
# deployables + markers + greebles
# ----------------------------------------------------------------------------
def _build_deployables():
    """MASCOT, MINERVA-II x2, SCI, DCAM3 around the lower body."""
    # MASCOT (boxy lander) on -X lower side
    m = _box("HB2_MASCOT", (0.12, 0.30, 0.26), (-HX - 0.06, 0.10, -0.30))
    _finalize(m, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(m, width=0.005, segments=2)
    lid = _box("HB2_MASCOT_lid", (0.02, 0.28, 0.24), (-HX - 0.12, 0.10, -0.30))
    _finalize(lid, "dep", M_GOLD, smooth_angle_deg=40.0)
    _bevel(lid, width=0.004, segments=1)
    # MINERVA-II 1 & 2 (drum landers) on +X lower side
    m1 = _cyl("HB2_MINERVA1", 0.13, 0.16, loc=(HX + 0.06, 0.12, -0.28),
              rot=(0, math.pi / 2, 0), verts=18)
    _finalize(m1, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(m1, width=0.005, segments=2)
    m2 = _cyl("HB2_MINERVA2", 0.10, 0.13, loc=(HX + 0.05, -0.24, -0.02),
              rot=(0, math.pi / 2, 0), verts=18)
    _finalize(m2, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(m2, width=0.005, segments=2)
    # SCI (small carry-on impactor) on +Y lower-ish / -Z
    sb = _cyl("HB2_SCI_body", 0.14, 0.16, loc=(-0.32, 0.28, -HZ - 0.10),
              verts=20)
    _finalize(sb, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(sb, width=0.005, segments=2)
    sd = _cone("HB2_SCI_dome", 0.13, 0.05, 0.13, loc=(-0.32, 0.28, -HZ - 0.22),
               verts=20)
    _finalize(sd, "dep", M_METAL, smooth_angle_deg=40.0)
    _bevel(sd, width=0.004, segments=1)
    # DCAM3 (deployable camera) small box near SCI / underside
    dc = _box("HB2_DCAM3", (0.10, 0.10, 0.10), (-0.05, 0.40, -HZ - 0.08))
    _finalize(dc, "dep", M_BLACKMATTE, smooth_angle_deg=45.0)
    _bevel(dc, width=0.004, segments=1)


def _build_target_markers():
    """5 spherical target markers (reflective) tucked around the lower body."""
    spots = [
        (0.30, 0.55, -0.45),
        (-0.30, 0.55, -0.40),
        (0.40, -0.55, -0.42),
        (-0.40, -0.55, -0.38),
        (0.0, 0.0, -HZ - 0.02),
    ]
    for i, (x, y, z) in enumerate(spots):
        tm = _uvsphere("HB2_TargetMarker%d" % i, 0.05, loc=(x, y, z),
                       seg=16, ring=8)
        _finalize(tm, "dep", M_MARKER, smooth_angle_deg=60.0)
        _bevel(tm, width=0.003, segments=1)


def _build_greebles():
    """Equipment boxes, brackets, cable harnesses, bolt rings -- break up every
    large flat face so nothing reads as a bare slab."""
    rng = []
    # --- equipment boxes on the +Y face (front bay, image 7) ---
    eq = [
        ("HB2_EquipBoxA", (0.42, 0.12, 0.40), (0.30, HY + 0.06, 0.05), M_SILVER),
        ("HB2_EquipBoxB", (0.30, 0.10, 0.46), (-0.32, HY + 0.05, -0.10), M_BLACK),
        ("HB2_EquipBoxC", (0.20, 0.14, 0.20), (0.0, HY + 0.06, -0.35), M_GOLD),
    ]
    for nm, sz, loc, mat in eq:
        ob = _box(nm, sz, loc)
        _finalize(ob, "bus", mat, smooth_angle_deg=40.0)
        _bevel(ob, width=0.006, segments=2)

    # --- deck boxes (avionics) on the top deck around the antennas ---
    deck = [
        ("HB2_DeckBoxA", (0.18, 0.16, 0.14), (0.0, 0.05, HZ + 0.13), M_GOLD),
        ("HB2_DeckBoxB", (0.12, 0.12, 0.12), (0.30, 0.55, HZ + 0.12), M_BLACK),
        ("HB2_DeckBoxC", (0.12, 0.14, 0.10), (-0.30, 0.55, HZ + 0.11), M_GOLD),
        ("HB2_DeckBoxD", (0.10, 0.12, 0.13), (0.30, -0.55, HZ + 0.12), M_SILVER),
        ("HB2_DeckBoxE", (0.12, 0.12, 0.14), (-0.30, -0.55, HZ + 0.13), M_GOLD),
        ("HB2_DeckBoxF", (0.08, 0.08, 0.10), (0.0, 0.62, HZ + 0.11), M_BLACK),
    ]
    for nm, sz, loc, mat in deck:
        ob = _box(nm, sz, loc)
        _finalize(ob, "ant", mat, smooth_angle_deg=40.0)
        _bevel(ob, width=0.005, segments=2)

    # --- a radiator-looking equipment box + assorted greeble boxes ---
    gb_specs = [
        (0.18, 0.10, 0.14, M_SILVER), (0.16, 0.12, 0.20, M_GOLD),
        (0.12, 0.08, 0.12, M_BLACK), (0.20, 0.09, 0.12, M_GOLD),
        (0.14, 0.11, 0.22, M_SILVER), (0.08, 0.16, 0.10, M_BLACK),
        (0.07, 0.12, 0.10, M_METAL), (0.10, 0.14, 0.12, M_GOLD),
        (0.08, 0.10, 0.16, M_BLACK), (0.06, 0.18, 0.10, M_SILVER),
    ]
    # distribute greeble boxes across the -Y, +X, -X faces (which are emptier)
    placements = [
        (-0.28, -HY - 0.05, 0.30), (0.28, -HY - 0.05, -0.25),
        (HX + 0.05, 0.30, 0.40), (HX + 0.05, -0.30, -0.30),
        (-HX - 0.05, 0.30, -0.35), (-HX - 0.05, -0.25, 0.40),
        (0.0, -HY - 0.05, 0.40), (0.15, HY + 0.05, 0.45),
        (-0.20, HY + 0.05, 0.40), (0.30, -HY - 0.05, 0.20),
    ]
    for i, ((sx, sy, sz, mat), (px, py, pz)) in enumerate(zip(gb_specs, placements)):
        ob = _box("HB2_GreebleB_box%d" % i, (sx, sy, sz), (px, py, pz))
        _finalize(ob, "det", mat, smooth_angle_deg=40.0)
        _bevel(ob, width=0.005, segments=2)
        # small nub on top of each greeble box
        nub = _box("HB2_GreebleB_box%d_nub" % i, (0.03, 0.03, 0.03),
                   (px, py, pz + sz / 2 + 0.015))
        _finalize(nub, "det", M_METAL, smooth_angle_deg=45.0)
        _bevel(nub, width=0.002, segments=1)

    radbox = _box("HB2_GreebleB_radbox", (0.22, 0.10, 0.18),
                  (0.0, -HY - 0.06, -0.10))
    _finalize(radbox, "det", M_RAD, smooth_angle_deg=45.0, shade_smooth=False)
    _bevel(radbox, width=0.005, segments=1)

    # --- brackets ---
    brk = [
        ("HB2_GreebleB_bracket0", (0.30, 0.04, 0.05), (0.0, HY + 0.02, 0.30)),
        ("HB2_GreebleB_bracket1", (0.20, 0.04, 0.05), (-0.30, HY + 0.02, 0.20)),
        ("HB2_GreebleB_bracket2", (0.04, 0.20, 0.05), (HX + 0.02, 0.0, 0.50)),
        ("HB2_Bracket0", (0.05, 0.12, 0.05), (HX + 0.03, 0.22, 0.30)),
        ("HB2_Bracket1", (0.05, 0.12, 0.05), (-HX - 0.03, -0.22, -0.18)),
    ]
    for nm, sz, loc in brk:
        ob = _box(nm, sz, loc)
        _finalize(ob, "det", M_METAL, smooth_angle_deg=45.0)
        _bevel(ob, width=0.004, segments=1)

    # --- cable harnesses: thin tubes running along faces ---
    cables = [
        ("HB2_Cable0", (0.81, HY + 0.03, -0.2), (0.81, HY + 0.03, 0.45), 0.013),
        ("HB2_Cable1", (-0.81, HY + 0.03, -0.2), (-0.81, HY + 0.03, 0.45), 0.013),
        ("HB2_GreebleB_cable1", (0.0, HY + 0.04, -0.30), (0.0, HY + 0.04, 0.45), 0.012),
        ("HB2_GreebleB_cable3", (0.18, HY + 0.04, -0.30), (0.18, HY + 0.04, 0.40), 0.012),
        ("HB2_GreebleB_cable5", (HX + 0.03, -0.30, -0.30), (HX + 0.03, -0.30, 0.40), 0.012),
        ("HB2_GreebleB_cable6", (-HX - 0.03, 0.30, -0.30), (-HX - 0.03, 0.30, 0.40), 0.012),
    ]
    for nm, p0, p1, r in cables:
        _strut(nm, p0, p1, r=r, verts=8, coll="det", mat=M_BLACKMATTE)

    # --- connector blocks ---
    conns = [
        ("HB2_Conn0", (0.10, 0.06, 0.08), (0.50, HY + 0.04, 0.18)),
        ("HB2_Conn1", (0.08, 0.06, 0.10), (-0.48, HY + 0.04, -0.12)),
        ("HB2_Conn2", (0.12, 0.08, 0.06), (0.30, HY + 0.04, 0.30)),
        ("HB2_Conn3", (0.07, 0.07, 0.09), (-0.20, HY + 0.04, -0.25)),
    ]
    for nm, sz, loc in conns:
        ob = _box(nm, sz, loc)
        _finalize(ob, "det", M_METAL, smooth_angle_deg=45.0)
        _bevel(ob, width=0.003, segments=1)

    # --- bolt rings around the antenna bases on the deck ---
    for tag, cx, cy, rr in [("HGAX", 0.0, 0.40, 0.50), ("HGAKa", 0.0, -0.34, 0.50)]:
        n = 8
        for j in range(n):
            a = j * TAU / n
            bx = cx + rr * math.cos(a)
            by = cy + rr * math.sin(a)
            bolt = _cyl("HB2_Boltring_%s_%d" % (tag, j), 0.012, 0.025,
                        loc=(bx, by, HZ + 0.06), verts=8)
            _finalize(bolt, "det", M_METAL, smooth_angle_deg=45.0)

    # --- bolt ring on the sampler collar (underside) ---
    for j in range(8):
        a = j * TAU / 8
        bx = 0.13 * math.cos(a)
        by = 0.13 * math.sin(a)
        bolt = _cyl("HB2_Bolt%d" % j, 0.011, 0.025, loc=(bx, by, -HZ - 0.05),
                    verts=8)
        _finalize(bolt, "det", M_METAL, smooth_angle_deg=45.0)


# ----------------------------------------------------------------------------
# build()  -- ALL edits, idempotent.  No file open/save, no render, no MCP.
# ----------------------------------------------------------------------------
def build():
    # make sure we operate in OBJECT mode
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass

    _CREATED.clear()

    # (a) delete legacy craft (all non-solar meshes under HB2_Root)
    _purge_legacy()

    # (b)+(c) bus body with relief + de-LEGO
    _build_bus_core()
    _build_bus_blankets()
    _build_bus_panel_seams()
    _build_top_bottom_panels()
    _build_radiators()
    _build_solar_yoke_struts()

    # (d) instruments
    _build_hgas()
    _build_mga_lga()
    _build_star_trackers()
    _build_sampler()
    _build_underside_cameras()
    _build_ion_engines()
    _build_rcs()
    _build_deployables()
    _build_target_markers()
    _build_greebles()

    # refresh
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass

    print("[02_craft] build() complete: created %d objects." % len(_CREATED))
    return len(_CREATED)


# ----------------------------------------------------------------------------
# self-test rendering (only when --shot is present).  Never raises if absent.
# ----------------------------------------------------------------------------
def _render_shots(out_paths):
    import os
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE"   # Eevee Next in 5.1
    except Exception:
        pass
    try:
        scene.eevee.taa_render_samples = 96
    except Exception:
        pass
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    # temp camera
    cam_data = bpy.data.cameras.new("HB2_TmpCam")
    cam_data.lens = 60
    cam = bpy.data.objects.new("HB2_TmpCam", cam_data)
    scene.collection.objects.link(cam)
    prev_cam = scene.camera
    scene.camera = cam

    # add temp key + fill + rim lights so test renders are legible from every
    # angle (these are removed afterwards; existing scene lights are untouched).
    tmp_lights = []
    for nm, energy, rot in [
        ("HB2_TmpKey", 4.5, (math.radians(52), 0, math.radians(35))),
        ("HB2_TmpFill", 2.0, (math.radians(60), 0, math.radians(215))),
        ("HB2_TmpRim", 2.5, (math.radians(115), 0, math.radians(120))),
    ]:
        ld = bpy.data.lights.new(nm, type="SUN")
        ld.energy = energy
        lo = bpy.data.objects.new(nm, ld)
        scene.collection.objects.link(lo)
        lo.rotation_euler = rot
        tmp_lights.append((lo, ld))

    target = Vector((0, 0, 0))
    R = 6.0

    def look_at(camobj, loc):
        camobj.location = loc
        d = (target - Vector(loc))
        camobj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    views = {
        # +Y instrument-bay side (image 7 hero side); shows depth + antennas
        "front": (0.0, R, 0.25),
        "top": (0.0001, 0.0, R),                       # straight down +Z
        # image-7 three-quarter: from +Y / +X above, antennas + bay visible
        "threeq": (R * 0.55, R * 0.62, R * 0.48),
    }

    base = out_paths[0] if out_paths else "/tmp/_t_craft.png"
    root, ext = os.path.splitext(base)
    if not ext:
        ext = ".png"
    written = []
    for name, loc in views.items():
        look_at(cam, loc)
        scene.render.filepath = "%s_%s%s" % (root, name, ext)
        try:
            bpy.ops.render.render(write_still=True)
            written.append(scene.render.filepath)
        except Exception as e:
            print("[02_craft] render %s failed: %s" % (name, e))

    # also write the exact requested path (three-quarter) for convenience
    look_at(cam, views["threeq"])
    scene.render.filepath = base
    try:
        bpy.ops.render.render(write_still=True)
        written.append(base)
    except Exception as e:
        print("[02_craft] render base failed: %s" % e)

    # cleanup temp cam/lights (keep scene pristine)
    scene.camera = prev_cam
    objs_to_remove = [cam] + [lo for lo, _ld in tmp_lights]
    data_to_remove = [cam_data] + [ld for _lo, ld in tmp_lights]
    for o in objs_to_remove:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
    for d in data_to_remove:
        try:
            if d.users == 0:
                if isinstance(d, bpy.types.Camera):
                    bpy.data.cameras.remove(d)
                else:
                    bpy.data.lights.remove(d)
        except Exception:
            pass
    print("[02_craft] wrote shots: %s" % ", ".join(written))


if __name__ == "__main__":
    import sys
    build()
    argv = sys.argv
    if "--shot" in argv:
        idx = argv.index("--shot")
        outs = [a for a in argv[idx + 1:] if not a.startswith("--")]
        if not outs:
            outs = ["/tmp/_t_craft.png"]
        _render_shots(outs)
