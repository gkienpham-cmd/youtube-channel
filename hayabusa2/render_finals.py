"""
Hayabusa2 render harness — one scene per invocation (headless) for 4K finals,
or import the functions and call setup_scene()/render_one() from the live instance.

Headless usage:
  Blender --background hayabusa2.blend --python render_finals.py -- studio
  Blender --background hayabusa2.blend --python render_finals.py -- cruise
  Blender --background hayabusa2.blend --python render_finals.py -- ryugu
Optional flags after the scene name:
  --preview         1280x720 @ 64 samples (fast check) instead of 3840x2160 @ 256
  --out=/abs/path.png   override output path

Scene = ONE master scene reused via toggles (lights / world / collection+object
visibility). Camera rig is shared and left untouched.
"""
import bpy, sys, math

RENDER_DIR = "/Users/kienpham/Documents/youtube-channel/hayabusa2/renders"
STUDIO_LIGHTS = ["HB2_Studio_Key", "HB2_Studio_Fill", "HB2_Studio_Rim"]
SUNS          = ["HB2_Sun", "HB2_FillSun", "HB2_RimSun"]
ION_GLOW      = ["HB2_IonGlow0", "HB2_IonGlow1", "HB2_IonGlow2", "HB2_IonGlow3"]
EARTH_P       = ("HB2_Earth",)                                       # surface + cloud + atmo shells
RYUGU_SURF_P  = ("HB2_RyuguSurface", "HB2_Boulder")                  # close descent surface (anim use)
RYUGU_BODY_P  = ("HB2_RyuguBody", "HB2_BodyBoulder", "HB2_Otohime")  # whole spinning-top body
OUT_NAME      = {"studio": "studio_beauty", "cruise": "cruise", "ryugu": "ryugu"}

# Whole-Ryugu placement for the ryugu hero shot. The body is modelled ~170 BU at origin (engulfing
# the craft), so for this shot it is scaled down + pushed back to read as a big body BESIDE the 6 m
# craft (artistic scale, like reference image 3/6). Boulders are parented to the body so they follow.
RYUGU_BODY_LOC   = (6.0, 34.0, -7.0)
RYUGU_BODY_SCALE = 0.125

# Per-scene camera rig (HB2_PreviewCam TRACK_TO HB2_AimRyugu).
# The craft sits at its natural build orientation: HB2_Root rotation Z = 0, so the solar
# wings spread along world-X and the ion engines face world -Y. These views look across the
# -Y/engine side so the X-spread wings read broadside (not foreshortened) and the blue
# ion glow is toward camera. (Do NOT re-introduce the old +90deg Z root rotation.)
CAM_RIG = {
    "studio": dict(loc=(13.5, -15.5, 6.0), aim=(0.0, 0.0, -1.0), lens=38),  # pulled back further: bigger wings
    "cruise": dict(loc=(8.0, -9.0, 2.8), aim=(-0.6, 1.8, 0.2), lens=22),  # wider for the bigger wings, Earth behind
    "ryugu":  dict(loc=(10.5, -12.0, 4.6), aim=(1.5, 12.0, -1.0), lens=26),  # wider for the bigger wings
}


def _hide_obj(name, hide):
    o = bpy.data.objects.get(name)
    if o:
        o.hide_render = hide
        o.hide_viewport = hide


def _hide_coll(name, hide):
    c = bpy.data.collections.get(name)
    if c:
        c.hide_render = hide
        c.hide_viewport = hide


def ensure_black_world():
    """Plain pure-black world for the studio beauty shot."""
    w = bpy.data.worlds.get("HB2_BlackWorld")
    if w is None:
        w = bpy.data.worlds.new("HB2_BlackWorld")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs["Strength"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def _set_cam(name):
    import mathutils
    rig = CAM_RIG[name]
    cam = bpy.data.objects.get("HB2_PreviewCam")
    aim = bpy.data.objects.get("HB2_AimRyugu")
    if cam:
        cam.location = mathutils.Vector(rig["loc"])
        cam.data.lens = rig["lens"]
    if aim:
        aim.location = mathutils.Vector(rig["aim"])


def _set_prefix_hide(prefixes, hide):
    """Hide/show all objects whose name starts with any of the given prefixes."""
    for o in bpy.data.objects:
        if any(o.name.startswith(p) for p in prefixes):
            o.hide_render = hide
            o.hide_viewport = hide


def _place_ryugu_body():
    """Scale + position the whole Ryugu body for the ryugu hero shot (boulders parented to it follow)."""
    import mathutils
    b = bpy.data.objects.get("HB2_RyuguBody")
    if b:
        b.location = mathutils.Vector(RYUGU_BODY_LOC)
        b.scale = (RYUGU_BODY_SCALE, RYUGU_BODY_SCALE, RYUGU_BODY_SCALE)


def _aim(vec):
    """Euler so a SUN's local -Z points along world `vec` (the direction light travels)."""
    import mathutils
    return mathutils.Vector(vec).to_track_quat('-Z', 'Y').to_euler()


def _ensure_sun(name, energy, color, rot=None, angle_deg=None):
    """Get-or-create a SUN and set energy/color (+ optional rotation / soft-shadow angle).
    Rotation, when given, is set explicitly so the flyby key/fill/rim are aimed
    deterministically per scene."""
    o = bpy.data.objects.get(name)
    if o is None:
        d = bpy.data.lights.new(name + "Data", "SUN")
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
    o.data.energy = energy
    o.data.color = color
    if angle_deg is not None:
        o.data.angle = math.radians(angle_deg)
    if rot is not None:
        o.rotation_euler = rot
    o.hide_render = False
    o.hide_viewport = False
    return o


def _ensure_area(name, energy, size, loc, aim_at, color=(1.0, 1.0, 1.0)):
    """Get-or-create a LOCAL area light. Unlike a sun, its inverse-square falloff lets it
    light the nearby craft while barely touching the distant Earth — used as the cruise
    craft fill so Earth can stay backlit."""
    import mathutils
    o = bpy.data.objects.get(name)
    if o is None:
        d = bpy.data.lights.new(name + "Data", "AREA")
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
    o.data.energy = energy
    o.data.size = size
    o.data.color = color
    o.location = mathutils.Vector(loc)
    direction = mathutils.Vector(aim_at) - mathutils.Vector(loc)
    o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    o.hide_render = False
    o.hide_viewport = False
    return o


def _setup_flyby_lights(name):
    """Per-scene deep-space lighting (cruise / ryugu).

    cruise -- "sun behind Earth": the key is aimed so its light travels FROM the Earth
      (~(-4,27,4)) toward the craft, backlighting it and rim-lighting Earth's atmosphere
      (offset slightly off the camera-Earth axis so Earth keeps a lit crescent, not a
      black disk). A strong cool FILL from the camera side then lifts the craft's
      engine-side detail so it still reads (the chosen "backlit Earth + legible craft"
      look), plus a cool-blue rim for separation against space.

    ryugu -- "lights on": a bright key over the camera's shoulder so BOTH the craft and
      the asteroid read clearly (the old shared setup left this shot too dark), opened up
      by a cool fill + cool-blue rim.

    Sun directions are set explicitly per scene (overriding any prior angle)."""
    if name == "cruise":
        # Key BEHIND Earth: light travels from Earth(~-4,27,4) toward the craft so the camera
        # sees Earth's far limb glowing (backlit) and the craft is rim-lit from the Earth side.
        _ensure_sun("HB2_Sun",     7.5, (1.0, 0.96, 0.88), angle_deg=0.6,
                    rot=_aim((5.0, -21.0, -3.0)))
        # BOTH directional fill AND rim are OFF for cruise — any camera-side global sun would
        # front-light Earth and kill the backlit look. The craft is lit by a LOCAL area light.
        _ensure_sun("HB2_FillSun", 0.0, (0.55, 0.68, 1.0), angle_deg=8.0,
                    rot=_aim((-10.5, 18.5, -3.0)))
        _ensure_sun("HB2_RimSun",  0.0, (0.50, 0.70, 1.0), angle_deg=3.0,
                    rot=_aim((2.0, 4.0, 4.0)))
        # LOCAL fill beside the craft (camera side) — lifts the engine-side detail so it reads,
        # with inverse-square falloff that barely reaches the distant Earth (keeps Earth backlit).
        _ensure_area("HB2_FlybyFill", energy=1400.0, size=6.0,
                     loc=(5.0, -6.0, 3.0), aim_at=(0.0, 0.0, 0.0),
                     color=(0.92, 0.94, 1.0))
        # Dim dedicated Earth-fill: lights Earth's camera side as a readable lit gibbous
        # (terminator down the disc) while only grazing the craft front, so Earth reads
        # brighter without killing the backlit look or washing the craft.
        _ensure_sun("HB2_EarthFill", 1.6, (0.95, 0.97, 1.0), angle_deg=1.0,
                    rot=_aim((9.0, 14.0, 7.0)))
    elif name == "ryugu":
        _ensure_sun("HB2_Sun",     6.5, (1.0, 0.97, 0.93), angle_deg=0.6,
                    rot=_aim((-2.0, 20.0, -11.0)))     # key over the camera's shoulder (dimmed from 8.0)
        _ensure_sun("HB2_FillSun", 3.0, (0.55, 0.68, 1.0), angle_deg=10.0,
                    rot=_aim((9.0, 14.0, 4.0)))        # cool fill opening the shadow side
        _ensure_sun("HB2_RimSun",  3.2, (0.50, 0.70, 1.0), angle_deg=3.0,
                    rot=_aim((-6.0, 5.0, 6.0)))        # cool-blue rim


def setup_scene(name):
    """Toggle camera / lights / world / visibility for one of: studio | cruise | ryugu.

    NOTE: HB2_Earth + shells AND the Ryugu surface/boulders all live in the
    'Environment' collection, so visibility must be controlled at the OBJECT level
    (by name prefix), never by hiding the whole collection."""
    sc = bpy.context.scene
    starfield = bpy.data.worlds.get("World")
    black = ensure_black_world()
    _hide_coll("Environment", False)   # collection always on; control its objects directly
    _hide_coll("HB2_FX", False)
    _set_cam(name)
    if name == "studio":
        sc.world = black
        for l in STUDIO_LIGHTS: _hide_obj(l, False)
        for l in SUNS:          _hide_obj(l, True)
        _hide_obj("HB2_FlybyFill", True)               # cruise-only local fill
        _hide_obj("HB2_EarthFill", True)               # cruise-only Earth fill
        for o in ION_GLOW:      _hide_obj(o, True)     # engines off, clean beauty
        _set_prefix_hide(EARTH_P, True)
        _set_prefix_hide(RYUGU_SURF_P, True)
        _set_prefix_hide(RYUGU_BODY_P, True)           # asteroid out of the studio shot
    elif name == "cruise":
        sc.world = starfield
        _setup_flyby_lights(name)
        for l in STUDIO_LIGHTS: _hide_obj(l, True)
        for l in SUNS:          _hide_obj(l, False)
        for o in ION_GLOW:      _hide_obj(o, False)    # ion engines firing
        _set_prefix_hide(EARTH_P, False)              # Earth + atmosphere visible
        _set_prefix_hide(RYUGU_SURF_P, True)
        _set_prefix_hide(RYUGU_BODY_P, True)           # no asteroid in deep-space cruise
    elif name == "ryugu":
        sc.world = starfield
        _setup_flyby_lights(name)
        for l in STUDIO_LIGHTS: _hide_obj(l, True)
        for l in SUNS:          _hide_obj(l, False)
        _hide_obj("HB2_FlybyFill", True)               # cruise-only local fill
        _hide_obj("HB2_EarthFill", True)               # cruise-only Earth fill
        for o in ION_GLOW:      _hide_obj(o, True)     # ion off during descent
        _set_prefix_hide(EARTH_P, True)
        _set_prefix_hide(RYUGU_SURF_P, True)           # close surface reserved for animation
        _set_prefix_hide(RYUGU_BODY_P, False)          # show the whole spinning-top body
        _place_ryugu_body()
    else:
        raise ValueError("unknown scene: %r" % name)


def apply_quality(preview=False):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    # Raytraced reflections so the shiny gold MLI reflects Earth/sun/sky
    if hasattr(sc.eevee, "use_raytracing"):
        sc.eevee.use_raytracing = True
        try:
            sc.eevee.ray_tracing_options.resolution_scale = "1"
        except Exception:
            pass
    if preview:
        sc.render.resolution_x, sc.render.resolution_y = 1280, 720
        sc.eevee.taa_render_samples = 64
    else:
        sc.render.resolution_x, sc.render.resolution_y = 3840, 2160   # 4K UHD
        sc.eevee.taa_render_samples = 256                              # balanced
    # Eevee Next gather/shadow quality nudges (guarded — attrs vary by build)
    for attr, val in (("taa_samples", 16),):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, val)


def render_one(name, out=None, preview=False):
    apply_quality(preview=preview)
    setup_scene(name)
    if out is None:
        out = "%s/%s.png" % (RENDER_DIR, OUT_NAME.get(name, name))
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    return out


def _argv():
    a = sys.argv
    return a[a.index("--") + 1:] if "--" in a else []


if __name__ == "__main__":
    args = _argv()
    scene = args[0] if args else "cruise"
    preview = "--preview" in args
    out = next((a.split("=", 1)[1] for a in args if a.startswith("--out=")), None)
    path = render_one(scene, out=out, preview=preview)
    print("[render_finals] %s -> %s" % (scene, path))
