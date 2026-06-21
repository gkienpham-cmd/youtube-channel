"""
03_stars.py  -- Hayabusa2 deep-space WORLD shader (Blender 5.1 / Eevee Next)

Rebuilds ONLY scene.world.node_tree into a realistic deep-space starfield:
  - dark void background
  - sparse, sharp pinpoint stars
  - wide brightness distribution (a few bright, many faint)
  - per-star color variation (faint red -> warm -> white -> blue-white)
  - subtle faint Milky-Way band

build() is idempotent: it clears and rebuilds the world node tree from scratch.
It does NOT open/save files, render, or touch any object/material/compositor.

Run headless to self-test:
  Blender --background work_stars.blend --python 03_stars.py -- --shot out.png
"""

import bpy
import sys


# ----------------------------------------------------------------------------
# Tunable parameters (single source of truth)
# ----------------------------------------------------------------------------
VORONOI_SCALE      = 120.0   # density of star cells (higher = more, smaller stars)
PINPOINT_BOUND     = 0.090   # Voronoi-distance upper bound for the dot mask
                             #   smaller -> sparser & tinier pinpoints
PINPOINT_KNEE_LO   = 0.04    # ColorRamp lower knee (black below this -> kills haze)
PINPOINT_KNEE_HI   = 0.85    # ColorRamp upper knee (full white above this)
                             #   gentle knee: trims the dim falloff to a small core
POWER_EXPONENT     = 4.0     # brightness spread; higher -> most stars dim, few bright
BRIGHT_FLOOR       = 0.18    # min brightness so faint stars still register through AgX
EMISSION_STRENGTH  = 9.0     # overall star brightness (AgX compresses highlights hard)

MILKYWAY_SCALE     = 2.5     # low-frequency band noise
MILKYWAY_STRENGTH  = 0.005   # keep subtle (one faint patch, not overall haze)

VOID_COLOR = (0.0008, 0.0010, 0.0018, 1.0)  # near-black, faintest cool tint

# Stellar color sequence (faint red -> warm yellow -> white -> blue-white)
STAR_COLORS = [
    (0.00, (1.000, 0.353, 0.235, 1.0)),  # #ff5a3c  faint red (rare, low end)
    (0.35, (1.000, 0.851, 0.627, 1.0)),  # #ffd9a0  warm yellow
    (0.70, (1.000, 1.000, 1.000, 1.0)),  # #ffffff  white (most common)
    (1.00, (0.737, 0.824, 1.000, 1.0)),  # #bcd2ff  blue-white (bright/hot)
]


# ----------------------------------------------------------------------------
# build(): all world-shader edits, idempotent
# ----------------------------------------------------------------------------
def build():
    scene = bpy.context.scene
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True

    nt = world.node_tree
    nodes = nt.nodes
    links = nt.links

    # --- idempotent: wipe the whole world node tree and rebuild from scratch ---
    nodes.clear()

    def new(node_type, name, x, y):
        n = nodes.new(node_type)
        n.name = name
        n.label = name
        n.location = (x, y)
        return n

    # === Coordinates ========================================================
    texco = new("ShaderNodeTexCoord", "TexCoord", -1500, 0)
    mapping = new("ShaderNodeMapping", "Mapping", -1300, 0)
    links.new(texco.outputs["Generated"], mapping.inputs["Vector"])

    # === Voronoi star cells =================================================
    # F1 / Euclidean / 3D. Distance -> dot mask; Color -> per-cell randoms.
    vor = new("ShaderNodeTexVoronoi", "Voronoi_Stars", -1080, 120)
    vor.voronoi_dimensions = "3D"
    vor.feature = "F1"
    vor.distance = "EUCLIDEAN"
    vor.inputs["Scale"].default_value = VORONOI_SCALE
    if "Randomness" in vor.inputs:
        vor.inputs["Randomness"].default_value = 1.0
    links.new(mapping.outputs["Vector"], vor.inputs["Vector"])

    # === Pinpoint mask ======================================================
    # Distance ~0 at a cell centre. Map [0..bound] -> [1..0] so centres = 1.
    maprange = new("ShaderNodeMapRange", "Pinpoint_MapRange", -840, 260)
    maprange.inputs["From Min"].default_value = 0.0
    maprange.inputs["From Max"].default_value = PINPOINT_BOUND
    maprange.inputs["To Min"].default_value = 1.0
    maprange.inputs["To Max"].default_value = 0.0
    maprange.clamp = True
    links.new(vor.outputs["Distance"], maprange.inputs["Value"])

    # Hard knee near the top -> mostly black, tiny sharp dots.
    dot_ramp = new("ShaderNodeValToRGB", "Pinpoint_Ramp", -620, 260)
    dot_ramp.color_ramp.interpolation = "LINEAR"
    e0 = dot_ramp.color_ramp.elements[0]
    e0.position = PINPOINT_KNEE_LO
    e0.color = (0.0, 0.0, 0.0, 1.0)
    e1 = dot_ramp.color_ramp.elements[1]
    e1.position = PINPOINT_KNEE_HI
    e1.color = (1.0, 1.0, 1.0, 1.0)
    links.new(maprange.outputs["Result"], dot_ramp.inputs["Factor"])

    # === Per-cell random value (brightness + color driver) ==================
    # Voronoi Color is a constant random RGB per cell; take one channel.
    sep = new("ShaderNodeSeparateXYZ", "Cell_Random", -840, -120)
    links.new(vor.outputs["Color"], sep.inputs["Vector"])

    # === Brightness spread: power(random, exponent) =========================
    power = new("ShaderNodeMath", "Brightness_Power", -620, -120)
    power.operation = "POWER"
    links.new(sep.outputs["X"], power.inputs[0])
    power.inputs[1].default_value = POWER_EXPONENT

    # lift the power curve into [floor..1] so even faint stars survive AgX,
    # while the few near-1 randoms still read as distinctly bright.
    bfloor = new("ShaderNodeMapRange", "Bright_Floor", -480, -120)
    bfloor.inputs["From Min"].default_value = 0.0
    bfloor.inputs["From Max"].default_value = 1.0
    bfloor.inputs["To Min"].default_value = BRIGHT_FLOOR
    bfloor.inputs["To Max"].default_value = 1.0
    bfloor.clamp = True
    links.new(power.outputs["Value"], bfloor.inputs["Value"])

    # mask * brightness
    bright = new("ShaderNodeMath", "Pinpoint_x_Bright", -300, 80)
    bright.operation = "MULTIPLY"
    links.new(dot_ramp.outputs["Color"], bright.inputs[0])
    links.new(bfloor.outputs["Result"], bright.inputs[1])

    # === Per-star color (constant within a cell) ============================
    # Use a different Voronoi Color channel so colour is decorrelated from
    # brightness -> bright stars are not all the same hue.
    color_ramp = new("ShaderNodeValToRGB", "Star_Color", -400, -160)
    color_ramp.color_ramp.interpolation = "LINEAR"
    cr = color_ramp.color_ramp
    # set up the stellar-colour sequence
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = STAR_COLORS[0][0]
    cr.elements[0].color = STAR_COLORS[0][1]
    for pos, col in STAR_COLORS[1:]:
        el = cr.elements.new(pos)
        el.color = col
    links.new(sep.outputs["Y"], color_ramp.inputs["Factor"])

    # === Combine colour x brightness ========================================
    star_rgb = new("ShaderNodeMixRGB", "Star_RGB", -180, -40)
    star_rgb.blend_type = "MULTIPLY"
    star_rgb.inputs["Factor"].default_value = 1.0
    links.new(color_ramp.outputs["Color"], star_rgb.inputs["Color1"])
    # brightness (scalar) drives Color2; MixRGB broadcasts the float to RGB
    links.new(bright.outputs["Value"], star_rgb.inputs["Color2"])

    # === Optional faint Milky-Way band ======================================
    mw_noise = new("ShaderNodeTexNoise", "MilkyWay_Noise", -1080, -360)
    mw_noise.noise_dimensions = "3D"
    mw_noise.inputs["Scale"].default_value = MILKYWAY_SCALE
    mw_noise.inputs["Detail"].default_value = 8.0
    if "Roughness" in mw_noise.inputs:
        mw_noise.inputs["Roughness"].default_value = 0.65
    links.new(mapping.outputs["Vector"], mw_noise.inputs["Vector"])

    mw_ramp = new("ShaderNodeValToRGB", "MilkyWay_Ramp", -840, -360)
    mw_ramp.color_ramp.interpolation = "LINEAR"
    mw0 = mw_ramp.color_ramp.elements[0]
    mw0.position = 0.55
    mw0.color = (0.0, 0.0, 0.0, 1.0)        # pure black across most of sky
    mw1 = mw_ramp.color_ramp.elements[1]
    mw1.position = 0.80
    mw1.color = (0.32, 0.36, 0.50, 1.0)     # faint cool grey only at peaks
    links.new(mw_noise.outputs["Fac"], mw_ramp.inputs["Factor"])

    mw_scale = new("ShaderNodeMixRGB", "MilkyWay_Scale", -620, -360)
    mw_scale.blend_type = "MULTIPLY"
    mw_scale.inputs["Factor"].default_value = 1.0
    links.new(mw_ramp.outputs["Color"], mw_scale.inputs["Color1"])
    mw_scale.inputs["Color2"].default_value = (
        MILKYWAY_STRENGTH, MILKYWAY_STRENGTH, MILKYWAY_STRENGTH, 1.0)

    # === Final composite: stars + faint band over void ======================
    # stars (additive) on top of the milky-way band
    add_stars = new("ShaderNodeMixRGB", "Add_Stars", 60, -120)
    add_stars.blend_type = "ADD"
    add_stars.inputs["Factor"].default_value = 1.0
    links.new(mw_scale.outputs["Color"], add_stars.inputs["Color1"])
    links.new(star_rgb.outputs["Color"], add_stars.inputs["Color2"])

    # add the near-black void floor
    add_void = new("ShaderNodeMixRGB", "Add_Void", 260, -120)
    add_void.blend_type = "ADD"
    add_void.inputs["Factor"].default_value = 1.0
    add_void.inputs["Color1"].default_value = VOID_COLOR
    links.new(add_stars.outputs["Color"], add_void.inputs["Color2"])

    # === Emission -> World Output ===========================================
    emission = new("ShaderNodeEmission", "Star_Emission", 460, -120)
    emission.inputs["Strength"].default_value = EMISSION_STRENGTH
    links.new(add_void.outputs["Color"], emission.inputs["Color"])

    out = new("ShaderNodeOutputWorld", "World Output", 680, -120)
    links.new(emission.outputs["Emission"], out.inputs["Surface"])

    return world


# ----------------------------------------------------------------------------
# __main__: self-test scaffolding only (camera + render). NOT part of build().
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    build()

    if "--shot" in sys.argv:
        out_path = sys.argv[sys.argv.index("--shot") + 1]
        scene = bpy.context.scene

        import math
        from mathutils import Euler

        # --- temp camera pointing at EMPTY sky (toward +Y, away from model) ---
        cam_data = bpy.data.cameras.new("TMP_StarCam")
        cam_data.lens = 35.0
        cam_obj = bpy.data.objects.new("TMP_StarCam", cam_data)
        scene.collection.objects.link(cam_obj)
        # Sit near origin but look out at +Y where there is no geometry.
        cam_obj.location = (0.0, 0.0, 2.0)
        # default cam looks down -Z; rotate +90deg about X to look toward +Y
        cam_obj.rotation_euler = Euler((math.radians(90.0), 0.0, 0.0), "XYZ")

        prev_cam = scene.camera
        scene.camera = cam_obj

        # --- cheap render settings (keep AgX) ---
        prev = {
            "engine": scene.render.engine,
            "rx": scene.render.resolution_x,
            "ry": scene.render.resolution_y,
            "pct": scene.render.resolution_percentage,
            "vt": scene.view_settings.view_transform,
            "path": scene.render.filepath,
            "ff": scene.render.image_settings.file_format,
        }
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        scene.view_settings.view_transform = "AgX"  # keep AgX
        try:
            scene.eevee.taa_render_samples = 16
        except Exception:
            pass
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = out_path

        bpy.ops.render.render(write_still=True)
        print("STAR TEST RENDER WRITTEN:", out_path)

        # --- restore (so the .blend is untouched if ever saved) ---
        scene.camera = prev_cam
        scene.render.engine = prev["engine"]
        scene.render.resolution_x = prev["rx"]
        scene.render.resolution_y = prev["ry"]
        scene.render.resolution_percentage = prev["pct"]
        scene.view_settings.view_transform = prev["vt"]
        scene.render.filepath = prev["path"]
        scene.render.image_settings.file_format = prev["ff"]
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.cameras.remove(cam_data)
