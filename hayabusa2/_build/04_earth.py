"""
04_earth.py  --  Rebuild the background Earth of the Hayabusa2 deep-space scene
                  into a realistic Earth with real continents (NASA Blue Marble).

Target engine: Blender 5.1 / Eevee Next (BLENDER_EEVEE), AgX view transform.

build() is fully idempotent (rebuild-by-name). It ONLY touches:
    - HB2_Earth          (mesh + transform/collection preserved; mesh replaced)
    - HB2_EarthClouds    (new shell, parented to HB2_Earth)
    - HB2_EarthAtmo      (new shell, parented to HB2_Earth)
    - material "HB2_Earth" (node tree cleared + rebuilt)
It does NOT modify the World/stars, Sun/lights, solar arrays, bus, or instruments,
and it does NOT change HB2_Earth's visibility flags (the render harness owns those).
The cloud/atmo shells copy HB2_Earth's hide_render/hide_viewport so they toggle with it.

Run headless to build only:
    blender --background work_earth.blend --python 04_earth.py

Run + render a cheap test (camera/render scaffolding lives in __main__ ONLY):
    blender --background work_earth.blend --python 04_earth.py -- --shot /path/out.png
"""

import bpy
import os
import math
import mathutils

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EARTH_NAME   = "HB2_Earth"
CLOUDS_NAME  = "HB2_EarthClouds"
ATMO_NAME    = "HB2_EarthAtmo"
MAT_NAME     = "HB2_Earth"
CLOUDS_MAT   = "HB2_EarthClouds"
ATMO_MAT     = "HB2_EarthAtmo"

# Shared real path so the packed image's source still resolves in the live master.
TEXTURE_PATH = "/Users/kienpham/Documents/youtube-channel/hayabusa2/textures/bluemarble.jpg"

EARTH_LOC    = (-4.0, 27.0, 4.0)   # world location of the Earth (verified)
EARTH_RADIUS = 8.0                 # dims ~16 -> radius ~8 (verified)
SEGMENTS     = 128
RINGS        = 64

CLOUD_SCALE  = 1.015               # ~1.5% larger
ATMO_SCALE   = 1.025               # ~2.5% larger
ATMO_COLOR   = (0.357, 0.561, 1.0) # #5b8fff soft blue


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _purge_mesh(mesh):
    """Remove a mesh datablock if it has no other users."""
    if mesh is None:
        return
    try:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    except (ReferenceError, RuntimeError):
        pass


def _remove_object(name):
    """Fully remove an object and purge its orphaned mesh."""
    ob = bpy.data.objects.get(name)
    if ob is None:
        return
    mesh = ob.data if ob.type == 'MESH' else None
    for coll in list(ob.users_collection):
        coll.objects.unlink(ob)
    bpy.data.objects.remove(ob, do_unlink=True)
    _purge_mesh(mesh)


def _uv_sphere_mesh(name, radius, segments, rings):
    """Create a UV-sphere mesh datablock with an explicit equirectangular UV map.

    bmesh.ops.create_uvsphere(calc_uvs=True) does not reliably produce a UV layer
    that survives to_mesh() in headless mode, so we build the UV layer ourselves
    from each vertex's spherical coordinates: U = longitude (0..1 wrapping), V =
    latitude (0..1). This is exactly the projection a Blue Marble equirectangular
    image expects. The longitude seam is handled per-loop so it doesn't smear.
    """
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=segments,
        v_segments=rings,
        radius=radius,
        calc_uvs=False,
    )
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    uv_layer = bm.loops.layers.uv.new("UVMap")
    inv_r = 1.0 / radius if radius else 1.0
    two_pi = 2.0 * math.pi

    for face in bm.faces:
        face.smooth = True
        # Per-face longitudes, fixed for the wrap seam.
        us = []
        for loop in face.loops:
            co = loop.vert.co
            lon = math.atan2(co.y, co.x)          # -pi..pi
            u = (lon / two_pi) + 0.5              # 0..1
            us.append(u)
        # If this face straddles the +/-pi seam, push the small-U corners +1.
        if (max(us) - min(us)) > 0.5:
            us = [u + 1.0 if u < 0.5 else u for u in us]
        for loop, u in zip(face.loops, us):
            co = loop.vert.co
            lat = math.asin(max(-1.0, min(1.0, co.z * inv_r)))  # -pi/2..pi/2
            v = (lat / math.pi) + 0.5             # 0..1 (south->north)
            loop[uv_layer].uv = (u, v)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _set_alpha_blend(mat):
    """Configure a material for alpha blending across Eevee Next API variants."""
    if hasattr(mat, "surface_render_method"):
        # Blender 5.x Eevee Next: BLENDED disables depth write -> proper transparency.
        mat.surface_render_method = 'BLENDED'
    if hasattr(mat, "blend_method"):
        mat.blend_method = 'BLEND'
    mat.use_transparent_shadow = True
    if hasattr(mat, "show_transparent_back"):
        mat.show_transparent_back = False


def _new_material(name):
    """Return a fresh material with a cleared node tree."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    # In Blender 5.1 a new material already owns a node_tree; 'use_nodes' is
    # deprecated (warns on read/write), so we use node_tree directly.
    nt = mat.node_tree
    nt.nodes.clear()
    return mat, nt


# ---------------------------------------------------------------------------
# Texture
# ---------------------------------------------------------------------------
def _load_earth_image():
    """Load (or reuse) the Blue Marble image, set sRGB, and pack it."""
    img = None
    # Reuse an already-loaded copy if its filepath matches.
    for im in bpy.data.images:
        if im.filepath and os.path.abspath(bpy.path.abspath(im.filepath)) == os.path.abspath(TEXTURE_PATH):
            img = im
            break
    if img is None:
        if not os.path.exists(TEXTURE_PATH):
            raise FileNotFoundError(
                "Blue Marble texture not found at %s -- download it first." % TEXTURE_PATH
            )
        img = bpy.data.images.load(TEXTURE_PATH, check_existing=True)

    # Color: the base color map must be sRGB.
    try:
        img.colorspace_settings.name = 'sRGB'
    except Exception:
        pass

    # Pack so it embeds on save (idempotent: only pack if not already packed).
    if img.packed_file is None:
        try:
            img.pack()
        except RuntimeError:
            pass
    return img


# ---------------------------------------------------------------------------
# Material: Earth surface (continents + ocean/land roughness)
# ---------------------------------------------------------------------------
def _build_earth_material(img):
    mat, nt = _new_material(MAT_NAME)
    mat.use_backface_culling = False
    nodes, links = nt.nodes, nt.links

    out  = nodes.new("ShaderNodeOutputMaterial");  out.location  = (700, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled");   bsdf.location = (380, 0)

    # Texture coordinates -> UV (Flat projection on the UV-unwrapped sphere)
    texco = nodes.new("ShaderNodeTexCoord"); texco.location = (-820, 0)

    tex = nodes.new("ShaderNodeTexImage"); tex.location = (-560, 120)
    tex.image = img
    tex.projection = 'FLAT'
    if hasattr(tex, "interpolation"):
        tex.interpolation = 'Cubic'
    links.new(texco.outputs["UV"], tex.inputs["Vector"])

    # Base color = the photo
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    # Wetness mask: oceans read as blue-dominant + dark. Use the blue channel,
    # contrasted by a ColorRamp, to drive Roughness (ocean glossy, land matte).
    sep = nodes.new("ShaderNodeSeparateColor"); sep.location = (-300, -220)
    links.new(tex.outputs["Color"], sep.inputs["Color"])

    # Blue minus red gives a clean "is it ocean" signal (oceans blue>>red,
    # land/desert red>=blue, ice ~neutral so stays land-ish/matte).
    diff = nodes.new("ShaderNodeMath"); diff.location = (-60, -220)
    diff.operation = 'SUBTRACT'
    links.new(sep.outputs["Blue"], diff.inputs[0])
    links.new(sep.outputs["Red"],  diff.inputs[1])

    ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (160, -260)
    cr = ramp.color_ramp
    cr.interpolation = 'LINEAR'
    cr.elements[0].position = 0.02   # land  (blue-red small/negative clamped)
    cr.elements[0].color = (0.9, 0.9, 0.9, 1.0)   # high roughness -> matte land
    cr.elements[1].position = 0.10   # ocean (blue clearly > red)
    cr.elements[1].color = (0.22, 0.22, 0.22, 1.0)  # low roughness -> glossy sea
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

    # Earth is dielectric, no metal.
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.45

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Material: Clouds (procedural, white, semi-transparent)
# ---------------------------------------------------------------------------
def _build_cloud_material():
    """Multi-scale procedural cloud shell.

    Goal (ref: 'earth photo.jpg'): a real full-disc Earth look -- big thick
    opaque cloud masses in some regions, thin wispy/swirling clouds in others,
    and large fully-clear ocean gaps. NOT a uniform haze.

    The shader builds a single 0..1 "cloud density" field from three octaves at
    very different scales, then uses that ONE field to drive two things at once:
        (a) the Transparent<->cloud Mix factor   -> where clouds exist at all
        (b) the cloud BSDF brightness (color)     -> how thick/opaque they read
    Because both are driven by density, thin wisps render dim & see-through while
    dense fronts render bright & opaque -- exactly the variation we want.

    Node graph (left -> right):
        TexCoord(Object) -> Mapping
          coverage: Voronoi(F1, scale~1.1) -> Ramp(coverage)   (big covered vs clear)
          swirl:    Noise(distort, scale~4.2) -> Ramp(swirl)    (cyclonic bands/fronts)
          detail:   Noise(scale~16) -> subtract-bias            (wispy edges)
        combine -> Clamp -> "density" (0..1), which drives BOTH:
            density -> Ramp(alpha) ......... Mix.Fac  (transparent vs cloud)
            density -> MixRGB(grey..white) . Diffuse.Color  (thin dim vs thick bright)
        Mix( Transparent , Diffuse , Fac=alpha ) -> Output
    """
    mat, nt = _new_material(CLOUDS_MAT)
    _set_alpha_blend(mat)
    mat.use_backface_culling = False
    nodes, links = nt.nodes, nt.links

    out    = nodes.new("ShaderNodeOutputMaterial");  out.location    = (1180, 0)
    mix    = nodes.new("ShaderNodeMixShader");       mix.location    = (980, 0)
    transp = nodes.new("ShaderNodeBsdfTransparent"); transp.location = (760, 150)
    diff   = nodes.new("ShaderNodeBsdfDiffuse");     diff.location   = (760, -160)

    # --- Coordinates ---------------------------------------------------------
    texco = nodes.new("ShaderNodeTexCoord"); texco.location = (-1180, 0)
    mapn  = nodes.new("ShaderNodeMapping");  mapn.location  = (-1000, 0)
    # A non-uniform stretch (clouds band zonally on a real Earth) + an arbitrary
    # offset so the pattern doesn't sit symmetrically on the object axes.
    mapn.inputs["Location"].default_value = (3.1, 1.7, 0.4)
    mapn.inputs["Scale"].default_value    = (1.0, 0.72, 1.0)
    links.new(texco.outputs["Object"], mapn.inputs["Vector"])

    # --- (1) COVERAGE: low-frequency mask -> big covered regions vs clear oceans
    # A single big organic Noise octave (low Detail) gives broad smooth highs and
    # lows -- large contiguous weather systems and large clear oceans -- without
    # the radial "cells" a Voronoi would stamp in. This is the master gate.
    cover = nodes.new("ShaderNodeTexNoise"); cover.location = (-760, 280)
    cover.inputs["Scale"].default_value      = 1.25
    cover.inputs["Detail"].default_value     = 2.0
    cover.inputs["Roughness"].default_value  = 0.5
    if "Distortion" in cover.inputs:
        cover.inputs["Distortion"].default_value = 0.45   # warps the big masses
    links.new(mapn.outputs["Vector"], cover.inputs["Vector"])

    # Ramp the coverage: a wide clear band at the low end (big oceans), then a
    # smooth rise into covered. Keep it gentle so coverage VARIES continuously
    # (full -> partial -> none) rather than hard on/off.
    cover_ramp = nodes.new("ShaderNodeValToRGB"); cover_ramp.location = (-540, 300)
    ccr = cover_ramp.color_ramp
    ccr.interpolation = 'EASE'
    ccr.elements[0].position = 0.36   # below -> clear ocean
    ccr.elements[0].color = (0, 0, 0, 1)
    ccr.elements[1].position = 0.74   # above -> fully covered region
    ccr.elements[1].color = (1, 1, 1, 1)
    links.new(cover.outputs["Fac"], cover_ramp.inputs["Fac"])

    # --- (2) SWIRL: mid-frequency distorted noise -> cyclonic banding/fronts ---
    swirl = nodes.new("ShaderNodeTexNoise"); swirl.location = (-760, 20)
    swirl.inputs["Scale"].default_value      = 4.2
    swirl.inputs["Detail"].default_value     = 6.0
    swirl.inputs["Roughness"].default_value  = 0.62
    if "Lacunarity" in swirl.inputs:
        swirl.inputs["Lacunarity"].default_value = 2.2
    if "Distortion" in swirl.inputs:
        swirl.inputs["Distortion"].default_value = 1.3   # high -> swirled fronts
    links.new(mapn.outputs["Vector"], swirl.inputs["Vector"])

    # Gentle contrast on the swirl so bands have structure (not a flat 0.5 haze).
    swirl_ramp = nodes.new("ShaderNodeValToRGB"); swirl_ramp.location = (-540, 40)
    scr = swirl_ramp.color_ramp
    scr.interpolation = 'EASE'
    scr.elements[0].position = 0.30
    scr.elements[0].color = (0, 0, 0, 1)
    scr.elements[1].position = 0.78
    scr.elements[1].color = (1, 1, 1, 1)
    links.new(swirl.outputs["Fac"], swirl_ramp.inputs["Fac"])

    # --- (3) DETAIL: high-frequency noise -> wispy edges / texture -------------
    detail = nodes.new("ShaderNodeTexNoise"); detail.location = (-760, -240)
    detail.inputs["Scale"].default_value     = 16.0
    detail.inputs["Detail"].default_value    = 8.0
    detail.inputs["Roughness"].default_value = 0.55
    if "Distortion" in detail.inputs:
        detail.inputs["Distortion"].default_value = 0.35
    links.new(mapn.outputs["Vector"], detail.inputs["Vector"])

    # Center the detail around 0 so it ADDS and SUBTRACTS (erodes wispy edges).
    detail_bias = nodes.new("ShaderNodeMath"); detail_bias.location = (-540, -240)
    detail_bias.operation = 'SUBTRACT'
    links.new(detail.outputs["Fac"], detail_bias.inputs[0])
    detail_bias.inputs[1].default_value = 0.5

    # --- COMBINE -------------------------------------------------------------
    # Strategy: COVERAGE is the master gate (keeps masses contiguous + preserves
    # big clear oceans). The swirl MODULATES intensity *within* covered regions
    # rather than punching holes, so fronts stay connected. Detail only nibbles
    # the edges. This avoids the "popcorn" look of multiplying everything.
    #
    #   modulator = 0.55 + 0.45 * swirl        (range 0.55..1.0, never zero)
    #   masses    = coverage * modulator
    #   density   = masses + 0.16*detail_bias + 0.12*swirl   (edge wisps + arms)

    modulator = nodes.new("ShaderNodeMath"); modulator.location = (-320, 60)
    modulator.operation = 'MULTIPLY_ADD'
    links.new(swirl_ramp.outputs["Color"], modulator.inputs[0])
    modulator.inputs[1].default_value = 0.45   # swirl contrast inside masses
    modulator.inputs[2].default_value = 0.55   # floor so masses never vanish
    modulator.use_clamp = True

    masses = nodes.new("ShaderNodeMath"); masses.location = (-120, 140)
    masses.operation = 'MULTIPLY'
    links.new(cover_ramp.outputs["Color"], masses.inputs[0])
    links.new(modulator.outputs["Value"],  masses.inputs[1])

    # Faint standalone swirl "arms" reaching slightly into clear gaps (fronts).
    arms = nodes.new("ShaderNodeMath"); arms.location = (-120, -40)
    arms.operation = 'MULTIPLY_ADD'
    links.new(swirl_ramp.outputs["Color"], arms.inputs[0])
    arms.inputs[1].default_value = 0.12
    links.new(masses.outputs["Value"],     arms.inputs[2])

    detailed = nodes.new("ShaderNodeMath"); detailed.location = (80, -40)
    detailed.operation = 'MULTIPLY_ADD'
    links.new(detail_bias.outputs["Value"], detailed.inputs[0])
    detailed.inputs[1].default_value = 0.16    # gentle edge texture (not shatter)
    links.new(arms.outputs["Value"],        detailed.inputs[2])

    clamp = nodes.new("ShaderNodeClamp"); clamp.location = (260, -40)
    clamp.inputs["Min"].default_value = 0.0
    clamp.inputs["Max"].default_value = 1.0
    links.new(detailed.outputs["Value"], clamp.inputs["Value"])

    # --- DENSITY -> ALPHA (drives the Transparent<->cloud Mix factor) ----------
    # A LINEAR ramp gives a long translucent transition: a low floor stays clear
    # (oceans), the mid band yields thin see-through wisps, and the high end
    # saturates to opaque thick masses. Linear (not Ease) keeps thin wisps from
    # snapping straight to opaque, preserving real density variation.
    alpha = nodes.new("ShaderNodeValToRGB"); alpha.location = (480, 120)
    acr = alpha.color_ramp
    acr.interpolation = 'LINEAR'
    acr.elements[0].position = 0.30   # below -> fully clear sky (alpha 0)
    acr.elements[0].color = (0, 0, 0, 1)
    acr.elements[1].position = 0.88   # above -> fully opaque cloud (alpha 1)
    acr.elements[1].color = (1, 1, 1, 1)
    links.new(clamp.outputs["Result"], alpha.inputs["Fac"])

    # --- DENSITY -> COLOR (thin clouds are dimmer/greyer, thick are bright) -----
    # Mix a soft grey (thin) up to near-white (thick) by the SAME density field,
    # so wisps don't read as bright as the dense fronts even where alpha > 0.
    cloud_col = nodes.new("ShaderNodeMixRGB"); cloud_col.location = (480, -200)
    cloud_col.blend_type = 'MIX'
    cloud_col.inputs["Color1"].default_value = (0.42, 0.44, 0.48, 1.0)  # thin grey
    cloud_col.inputs["Color2"].default_value = (0.96, 0.97, 1.0,  1.0)  # thick white
    links.new(clamp.outputs["Result"], cloud_col.inputs["Fac"])
    links.new(cloud_col.outputs["Color"], diff.inputs["Color"])

    # --- Assemble: Fac 0 = transparent (clear), Fac 1 = cloud -----------------
    links.new(alpha.outputs["Color"], mix.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix.inputs[1])
    links.new(diff.outputs["BSDF"],   mix.inputs[2])
    links.new(mix.outputs["Shader"],  out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Material: Atmosphere rim (Fresnel blue glow)
# ---------------------------------------------------------------------------
def _build_atmo_material():
    mat, nt = _new_material(ATMO_MAT)
    _set_alpha_blend(mat)
    # Render the rim from the BACK faces so the glow sits around the limb,
    # in front of the dark space, not over the planet disc.
    mat.use_backface_culling = False
    nodes, links = nt.nodes, nt.links

    out = nodes.new("ShaderNodeOutputMaterial"); out.location = (760, 0)
    mix = nodes.new("ShaderNodeMixShader");      mix.location = (520, 0)
    transp = nodes.new("ShaderNodeBsdfTransparent"); transp.location = (300, 150)
    emit = nodes.new("ShaderNodeEmission");      emit.location = (300, -120)
    emit.inputs["Color"].default_value = (ATMO_COLOR[0], ATMO_COLOR[1], ATMO_COLOR[2], 1.0)
    emit.inputs["Strength"].default_value = 0.60

    # Layer Weight (Facing) -> strong at the limb, ~0 at the center.
    lw = nodes.new("ShaderNodeLayerWeight"); lw.location = (-200, 0)
    lw.inputs["Blend"].default_value = 0.30

    ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (20, 0)
    cr = ramp.color_ramp
    cr.interpolation = 'EASE'
    cr.elements[0].position = 0.35   # center of disc -> transparent
    cr.elements[0].color = (0, 0, 0, 1)
    cr.elements[1].position = 0.92   # limb -> full glow (soft, wide band)
    cr.elements[1].color = (1, 1, 1, 1)
    links.new(lw.outputs["Facing"], ramp.inputs["Fac"])

    links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Shell objects (clouds + atmosphere)
# ---------------------------------------------------------------------------
def _make_shell(name, radius, material, parent, collection):
    me = _uv_sphere_mesh(name, radius, SEGMENTS, RINGS)
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    collection.objects.link(ob)
    # Parent to HB2_Earth, keeping transform (shell sits at origin of parent).
    ob.parent = parent
    ob.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    ob.location = (0.0, 0.0, 0.0)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)
    # Inherit visibility so it toggles together with the Earth.
    ob.hide_render = parent.hide_render
    ob.hide_viewport = parent.hide_viewport
    return ob


# ---------------------------------------------------------------------------
# MAIN BUILD  (idempotent; ALL edits live here; no file IO / no render / no MCP)
# ---------------------------------------------------------------------------
def build():
    # ---- Idempotency: remove the shells; we rebuild them fresh every run.
    _remove_object(CLOUDS_NAME)
    _remove_object(ATMO_NAME)

    earth = bpy.data.objects.get(EARTH_NAME)
    if earth is None:
        raise RuntimeError("HB2_Earth not found in scene.")

    target_coll = earth.users_collection[0] if earth.users_collection else bpy.context.scene.collection

    # ---- Rebuild HB2_Earth mesh as a UV sphere (same object/name/transform/collection).
    old_mesh = earth.data
    new_mesh = _uv_sphere_mesh(EARTH_NAME + "_tmp", EARTH_RADIUS, SEGMENTS, RINGS)
    earth.data = new_mesh
    if old_mesh is not None and old_mesh != new_mesh:
        _purge_mesh(old_mesh)
    # Reclaim the canonical mesh name now that the old datablock is gone.
    new_mesh.name = EARTH_NAME

    # Lock the verified transform (do NOT touch visibility flags).
    earth.location = EARTH_LOC
    earth.rotation_euler = (0.0, 0.0, 0.0)
    earth.scale = (1.0, 1.0, 1.0)

    # ---- Surface material.
    img = _load_earth_image()
    earth_mat = _build_earth_material(img)
    earth.data.materials.clear()
    earth.data.materials.append(earth_mat)

    # ---- Cloud + atmosphere shells, parented to HB2_Earth.
    cloud_mat = _build_cloud_material()
    atmo_mat = _build_atmo_material()
    _make_shell(CLOUDS_NAME, EARTH_RADIUS * CLOUD_SCALE, cloud_mat, earth, target_coll)
    _make_shell(ATMO_NAME,   EARTH_RADIUS * ATMO_SCALE,  atmo_mat,  earth, target_coll)

    # Refresh so downstream reads (and the render harness) see final state.
    bpy.context.view_layer.update()

    print("[04_earth] build() complete: HB2_Earth rebuilt + HB2_EarthClouds + HB2_EarthAtmo.")
    print("[04_earth] texture packed: %s" % (img.packed_file is not None))


# ---------------------------------------------------------------------------
# __main__  --  build, and optionally render a cheap test shot.
#               (Camera / render scaffolding lives ONLY here.)
# ---------------------------------------------------------------------------
def _render_test(out_path):
    import sys
    scene = bpy.context.scene

    # Force the Earth + shells visible for THIS test render only.
    for nm in (EARTH_NAME, CLOUDS_NAME, ATMO_NAME):
        ob = bpy.data.objects.get(nm)
        if ob:
            ob.hide_render = False
            ob.hide_viewport = False

    # Temp camera framing the whole Earth (radius ~8) at (-4, 27, 4). Place it on
    # the sunlit side and pull WAY back so the full disc sits in frame with space
    # around it (so we can judge continents, ocean gloss, clouds, and the limb).
    cam_data = bpy.data.cameras.new("HB2_TmpEarthCam")
    cam_data.lens = 50.0
    cam = bpy.data.objects.new("HB2_TmpEarthCam", cam_data)
    scene.collection.objects.link(cam)

    earth = bpy.data.objects.get(EARTH_NAME)
    target = mathutils.Vector(earth.location) if earth else mathutils.Vector(EARTH_LOC)
    # Sun comes from ~(+X,+Y,-Z); sit on the lit side (+X, toward -Y) and above.
    cam.location = target + mathutils.Vector((14.0, -34.0, 9.0))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    # Cheap render; KEEP AgX (do not change view transform).
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 48
    except Exception:
        pass
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = out_path

    bpy.ops.render.render(write_still=True)
    print("[04_earth] test render written to %s" % out_path)


if __name__ == "__main__":
    import sys
    build()

    argv = sys.argv
    if "--shot" in argv:
        idx = argv.index("--shot")
        if idx + 1 < len(argv):
            _render_test(argv[idx + 1])
        else:
            print("[04_earth] --shot given but no output path followed it.")
