"""
Hayabusa2 ANIMATION harness — Episode-01 COLD OPEN (BEAT 0).

Renders image sequences for the four cold-open beats. It MIRRORS render_finals.py
conventions and REUSES its lighting/visibility helpers, but keyframes the camera rig +
craft and renders an animation. It is NON-DESTRUCTIVE: everything (keyframes, lights,
visibility, quality) is set at render time in the loaded scene and the .blend is NEVER
saved. Safe to run headless against the master file repeatedly.

Shots (all = lone craft + starfield only; Earth/Ryugu/Torifune hidden; ion engines OFF
for a quiet, drifting mood; one hard raking key + faint cool rim for a lonely look):
  shotA "drift"     — craft a tiny point of light, very slow push-in + drift + slow tumble
  shotB "turn"      — closer; craft slowly yaws to face an empty patch of space (no asteroid)
  shotC "cone"      — clean 3/4 base PLATE (craft to one side, open space for a Premiere
                      camera-cone + 'predicted position' label overlay)
  shotD "pullback"  — camera dollies away; craft shrinks to a lonely silhouette (room for title)

Headless usage:
  B=/Applications/Blender.app/Contents/MacOS/Blender
  M=/Users/kienpham/Documents/youtube-channel/hayabusa2/hayabusa2.blend
  $B --background $M --python render_anim.py -- shotA                 # 4K/128 final sequence
  $B --background $M --python render_anim.py -- shotA --preview       # 1280x720/48 full preview seq
  $B --background $M --python render_anim.py -- shotA --still=120     # one 4K frame (or --preview for 720p)
  $B --background $M --python render_anim.py -- all [--preview]       # all four shots
Optional: --mblur (enable motion blur), --out=/abs/dir (override output dir for a sequence).
"""
import bpy, sys, math, os
import mathutils

# Reuse the tested helpers + prefix lists from the stills harness (same folder).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_finals as rf

RENDER_DIR = "/Users/kienpham/Documents/youtube-channel/hayabusa2/renders/anim"
FPS = 24

# Everything that must be HIDDEN for the lone-probe cold open (asteroids + Earth shells).
HIDE_PREFIXES = rf.EARTH_P + rf.RYUGU_SURF_P + rf.RYUGU_BODY_P + rf.TORIFUNE_BODY_P

# ---------------------------------------------------------------------------
# SHOT DEFINITIONS
# Keyframes are (frame, value). Frames are absolute (sequence starts at 1).
#   cam  : (frame, (x,y,z) location, lens_mm)
#   aim  : (frame, (x,y,z) location of HB2_AimRyugu — camera TRACK_TO's this)
#   root : (frame, (rx,ry,rz) deg rotation, (x,y,z) location of HB2_Root = whole craft)
# Craft sits at origin: solar wings span world-X (~7.8 m tip-to-tip), bus ~1.0x1.6x1.25 m,
# ion engines face world -Y. Cameras look from the -Y/engine side. Reference framings from
# render_finals.CAM_RIG: studio loc(13.5,-15.5,6)/lens38 (wide whole-craft); flyby
# loc(7.5,-7.5,2.4)/lens28. Distance from origin ~ sqrt(x^2+y^2+z^2).
#
# NOTE: cameras do NOT auto-fit. These are STARTING values tuned to intent; verify each
# shot's first/mid/last frame in --preview and nudge loc/lens so framing matches the brief
# (tiny point / quarter-frame / craft-to-one-side / shrinking).
# ---------------------------------------------------------------------------
SHOTS = {
    # A — reveal: craft a tiny glint far away, near-imperceptible push-in; slow tumble brings
    # a gold/cell face into the key for a growing "point of light". ~9 s.
    "shotA": dict(
        dur_frames=216,
        cam=[(1, (54.0, -61.0, 23.0), 52), (216, (43.0, -49.0, 18.5), 56)],
        aim=[(1, (0.0, 2.0, 0.0)), (216, (-1.5, 4.0, 0.6))],
        root=[(1, (0.0, 0.0, -24.0), (0.0, 0.0, 0.0)),
              (216, (5.0, 0.0, 8.0), (1.2, 2.6, 0.4))],
        fill=0.05,
    ),
    # B — turn: closer, craft ~1/4 frame; slow yaw to "face" the empty patch ahead (+Y);
    # hard raking key reveals scarred MLI / greebles. ~9 s.
    "shotB": dict(
        dur_frames=216,
        cam=[(1, (9.4, -10.8, 4.0), 42), (216, (8.3, -9.5, 3.6), 45)],
        aim=[(1, (0.0, 1.2, 0.3)), (216, (0.5, 2.3, 0.5))],
        root=[(1, (0.0, 0.0, -20.0), (0.0, 0.0, 0.0)),
              (216, (1.0, 0.0, 10.0), (0.2, 0.6, 0.1))],
        fill=0.07,
    ),
    # C — diagram base PLATE: craft to one side, open starfield on the other for the Premiere
    # camera-cone + 'predicted position' arrow/label. Cleaner/brighter fill so the plate reads.
    # Near-static slow drift (a hint of life). ~7 s.
    "shotC": dict(
        dur_frames=168,
        cam=[(1, (7.2, -8.6, 3.0), 38), (168, (6.7, -8.1, 2.9), 38)],
        aim=[(1, (2.8, 5.2, 0.6)), (168, (3.0, 5.6, 0.7))],
        root=[(1, (0.0, 0.0, -6.0), (0.0, 0.0, 0.0)),
              (168, (0.0, 0.0, -2.0), (0.0, 0.2, 0.0))],
        fill=0.22,
    ),
    # D — pull-back: dolly away, craft shrinks to a lonely silhouette with negative space for
    # the title sting; ends quiet/small. Reverse bookend of A. ~9 s.
    "shotD": dict(
        dur_frames=216,
        cam=[(1, (12.0, -14.0, 5.5), 40), (216, (41.0, -47.0, 18.0), 48)],
        aim=[(1, (0.0, 1.0, 0.0)), (216, (0.0, 3.0, 1.4))],
        root=[(1, (0.0, 0.0, 5.0), (0.0, 0.0, 0.0)),
              (216, (2.0, 0.0, 16.0), (0.4, 1.0, 0.2))],
        fill=0.04,
    ),
}


def coldopen_visibility():
    """Lone craft + starfield only: hide every asteroid/Earth shell + the ion glow."""
    bpy.context.scene.world = bpy.data.worlds.get("World")   # starfield
    rf._hide_coll("Environment", False)                      # collection on; control objects
    rf._hide_coll("HB2_FX", False)
    rf._set_prefix_hide(HIDE_PREFIXES, True)                 # asteroids + Earth OUT
    for o in rf.ION_GLOW:
        rf._hide_obj(o, True)                                # engines OFF (quiet drift)
    for l in rf.STUDIO_LIGHTS:
        rf._hide_obj(l, True)                                # studio area lights off
    rf._hide_obj("HB2_FlybyFill", True)
    rf._hide_obj("HB2_EarthFill", True)


def coldopen_lights(fill=0.08):
    """Moody, lonely deep space. A strong RAKING key carves a hard terminator across the
    scarred craft; the shadow side falls toward near-black, held off the starfield only by a
    thin cool rim. `fill` is a whisper of cool bounce so the shadow side isn't pure black
    (lifted a little for the diagram plate C so it stays legible under the overlay)."""
    rf._ensure_sun("HB2_Sun", 6.5, (1.0, 0.95, 0.88), angle_deg=0.4,
                   rot=rf._aim((-9.0, 2.0, -7.0)))           # hard key, raking hard from +X/upper
    rf._ensure_sun("HB2_FillSun", fill, (0.55, 0.68, 1.0), angle_deg=10.0,
                   rot=rf._aim((9.0, -5.0, 3.0)))            # whisper cool fill from camera side
    rf._ensure_sun("HB2_RimSun", 1.4, (0.50, 0.70, 1.0), angle_deg=3.0,
                   rot=rf._aim((4.0, -6.0, -4.0)))           # thin cool back-rim, separates from starfield
    # Dedicated BODY fill: a local area light from the camera (-Y) side, centred on the bus.
    # Inverse-square falloff + the craft's geometry mean it lifts the fuselage's camera-facing
    # gold/black MLI (which the raking key leaves dark) while barely touching the solar wings
    # (their broad faces point +/-Z, nearly edge-on to this -Y light), so the panel look holds.
    rf._ensure_area("HB2_BodyFill", energy=600.0, size=2.5,
                    loc=(0.5, -6.0, 1.5), aim_at=(0.0, 0.0, 0.3),
                    color=(1.0, 0.97, 0.92))


def _iter_fcurves(obj):
    """Yield an object's f-curves across both the legacy and the Blender 4.4+ slotted-action
    APIs (in 5.1 `action.fcurves` is gone; f-curves live in channelbags under layers/strips)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    legacy = getattr(act, "fcurves", None)
    if legacy is not None:
        for fc in legacy:
            yield fc
        return
    slot = getattr(ad, "action_slot", None)
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            bags = []
            try:
                if slot is not None:
                    cb = strip.channelbag(slot)
                    if cb is not None:
                        bags.append(cb)
            except Exception:
                pass
            if not bags:
                bags = list(getattr(strip, "channelbags", []) or [])
            for bag in bags:
                for fc in getattr(bag, "fcurves", []):
                    yield fc


def _ease(obj):
    """Smooth all of an object's f-curves: Bezier + auto-clamped handles => gentle
    ease-in/ease-out at the endpoints (cinematic slow start / slow stop)."""
    for fc in _iter_fcurves(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()


def keyframe_shot(name):
    """Clear any prior animation and insert this shot's camera/aim/craft keyframes."""
    cam = bpy.data.objects["HB2_PreviewCam"]
    aim = bpy.data.objects["HB2_AimRyugu"]
    root = bpy.data.objects["HB2_Root"]

    # New keyframes default to smooth Bezier + auto-clamped handles (ease-in/out).
    try:
        ed = bpy.context.preferences.edit
        ed.keyframe_new_interpolation_type = 'BEZIER'
        ed.keyframe_new_handle_type = 'AUTO_CLAMPED'
    except Exception:
        pass

    # Idempotent: wipe old keys (object + camera-data lens) so reruns are deterministic.
    for o in (cam, aim, root):
        o.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()

    S = SHOTS[name]
    for (f, loc, lens) in S["cam"]:
        cam.location = mathutils.Vector(loc)
        cam.keyframe_insert("location", frame=f)
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
    for (f, aloc) in S["aim"]:
        aim.location = mathutils.Vector(aloc)
        aim.keyframe_insert("location", frame=f)
    for (f, rot, rloc) in S["root"]:
        root.rotation_euler = mathutils.Euler([math.radians(a) for a in rot], 'XYZ')
        root.keyframe_insert("rotation_euler", frame=f)
        root.location = mathutils.Vector(rloc)
        root.keyframe_insert("location", frame=f)

    _ease(cam); _ease(cam.data); _ease(aim); _ease(root)


def apply_quality_anim(preview=False, mblur=False):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "AgX"
    sc.render.resolution_percentage = 100
    if hasattr(sc.eevee, "use_raytracing"):
        sc.eevee.use_raytracing = True
        try:
            sc.eevee.ray_tracing_options.resolution_scale = "1"
        except Exception:
            pass
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    # Slow, meditative moves => motion blur is optional. Default OFF keeps stars crisp + is
    # faster; --mblur turns it on (modest shutter, a couple of steps).
    sc.render.use_motion_blur = mblur
    if mblur:
        sc.render.motion_blur_shutter = 0.5
        if hasattr(sc.eevee, "motion_blur_steps"):
            sc.eevee.motion_blur_steps = 2
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    if preview:
        sc.render.resolution_x, sc.render.resolution_y = 1280, 720
        sc.eevee.taa_render_samples = 48
    else:
        sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
        sc.eevee.taa_render_samples = 128


def _prep(name, preview, mblur):
    apply_quality_anim(preview=preview, mblur=mblur)
    coldopen_visibility()
    coldopen_lights(fill=SHOTS[name].get("fill", 0.3))
    bpy.context.scene.camera = bpy.data.objects["HB2_PreviewCam"]
    keyframe_shot(name)


def render_still(name, frame, preview=False, mblur=False, out=None):
    """Render a single frame (fast framing/lighting check)."""
    frame = int(frame)
    _prep(name, preview, mblur)
    sc = bpy.context.scene
    sc.frame_set(frame)
    if out is None:
        tag = "preview" if preview else "4k"
        out = "%s/_check/%s_%s_f%04d.png" % (RENDER_DIR, name, tag, int(frame))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("[render_anim] still %s f%d -> %s" % (name, frame, out))
    return out


def render_shot(name, preview=False, mblur=False, out=None, resume=False):
    """Render the full image sequence for one shot into a folder (####.png).
    resume=True sets use_overwrite=False so already-rendered frames are skipped (fast),
    letting an interrupted sequence pick up where it stopped."""
    _prep(name, preview, mblur)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = SHOTS[name]["dur_frames"]
    sc.frame_step = 1
    sc.render.use_overwrite = not resume
    sc.render.use_placeholder = False
    if out is None:
        out = "%s/%s%s" % (RENDER_DIR, ("preview_" if preview else ""), name)
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = out.rstrip("/") + "/"      # Blender appends 0001.png, 0002.png, ...
    print("[render_anim] sequence %s -> %s  (%d frames @ %dfps, %s)" % (
        name, sc.render.filepath, SHOTS[name]["dur_frames"], FPS,
        "1280x720/48" if preview else "3840x2160/128"))
    bpy.ops.render.render(animation=True)
    return out


def _argv():
    a = sys.argv
    return a[a.index("--") + 1:] if "--" in a else []


if __name__ == "__main__":
    args = _argv()
    targets = [args[0]] if args and not args[0].startswith("--") else []
    if not targets or targets == ["all"]:
        targets = ["shotA", "shotB", "shotC", "shotD"]
    preview = "--preview" in args
    mblur = "--mblur" in args
    resume = "--resume" in args
    out = next((a.split("=", 1)[1] for a in args if a.startswith("--out=")), None)
    still = next((a.split("=", 1)[1] for a in args if a.startswith("--still=")), None)
    for name in targets:
        if name not in SHOTS:
            raise ValueError("unknown shot %r (have %s)" % (name, list(SHOTS)))
        if still is not None:
            render_still(name, still, preview=preview, mblur=mblur, out=out)
        else:
            render_shot(name, preview=preview, mblur=mblur, out=out, resume=resume)
