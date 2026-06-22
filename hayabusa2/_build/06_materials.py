"""
06_materials.py  --  Spacecraft MLI / radiator / ion-engine-glow material
authoring for the photorealistic Hayabusa2 model (Blender 5.1 / Eevee Next).

GOAL
----
Make the gold MLI read as bright, lacquered, reflective gold *foil* (like the
real craft and the JAXA concept art) rather than a dull matte metal, bring the
other spacecraft-skin materials (black MLI, silver MLI, radiator) up to a
physically believable specular look, and give the ion-engine glow a soft,
contained cyan-blue emission (like the JAXA refs) instead of a white blowout.

DESIGN / SAFETY
---------------
* `build()` is idempotent. For the four MLI/radiator materials it edits the
  EXISTING node trees IN PLACE (never creating/deleting/renaming those mats or
  their nodes). For `HB2_IonGlow` it is get-or-create: it makes the material and
  its Emission->Output graph (plus a soft radial-falloff sub-graph) if missing,
  so a from-scratch rebuild still works; on re-run it finds the existing nodes by
  name and only re-sets their values. It never touches geometry/objects, and
  performs no file IO / render / MCP calls.
* The four MLI/radiator materials drive some Principled inputs through helper
  nodes (Base Color and Roughness come from ColorRamps; Normal from a Bump
  chain). Where an input is *linked* we set the value at its driver (the
  ColorRamp stops) instead of writing the ignored socket default. Where an input
  is *not* linked we set the socket default directly. Either way the result is
  deterministic, so re-running produces the identical node tree.
* The Bump (quilted-seam) chains and all texture/ColorRamp topology are
  preserved; only ColorRamp stop colors and free BSDF inputs are adjusted.

OWNED MATERIALS (only these are touched):
    HB2_Gold_MLI, HB2_Black_MLI, HB2_Silver_MLI, HB2_Radiator, HB2_IonGlow

The ion-glow geometry (HB2_IonGlow0-3 disks) is built/assigned BY NAME by a
separate script; this module only authors the HB2_IonGlow *material*.
"""

import bpy


# ---------------------------------------------------------------------------
# small helpers (no node creation / deletion -- only edits existing data)
# ---------------------------------------------------------------------------

def _principled(mat):
    """Return the Principled BSDF node of a material, or None."""
    nt = mat.node_tree
    if nt is None:
        return None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def _set_input(node, name, value):
    """Set a Principled input's default_value IF the input exists and is NOT
    linked. Linked inputs are driven by helper nodes and must be tuned at their
    source, so we deliberately skip them here to stay idempotent and avoid
    fighting the existing graph."""
    inp = node.inputs.get(name)
    if inp is None:
        return False
    if inp.is_linked:
        return False
    try:
        if hasattr(value, '__len__'):
            inp.default_value = value
        else:
            inp.default_value = float(value)
        return True
    except Exception:
        return False


def _ramp(mat, node_name):
    """Return the color_ramp of a named ColorRamp node, or None."""
    nt = mat.node_tree
    if nt is None:
        return None
    node = nt.nodes.get(node_name)
    if node is None or node.type != 'VALTORGB':
        return None
    return node.color_ramp


def _set_ramp_stops(cr, stops):
    """Set existing ColorRamp element positions + colors deterministically.

    `stops` is a list of (position, (r,g,b,a)) for the elements that already
    exist. We only write to existing elements (no add/remove), so topology is
    preserved and re-running is idempotent. Extra existing elements beyond the
    provided list are left untouched."""
    if cr is None:
        return
    for i, (pos, col) in enumerate(stops):
        if i < len(cr.elements):
            cr.elements[i].position = pos
            cr.elements[i].color = col


def _get_or_make_node(nt, name, bl_idname):
    """Return the node called `name`, creating it (of type `bl_idname`) if it
    does not already exist. Used only by the get-or-create HB2_IonGlow authoring
    so a from-scratch rebuild works while re-runs stay idempotent (we find the
    same node by name and only re-set its values)."""
    node = nt.nodes.get(name)
    if node is None or node.bl_idname != bl_idname:
        # If a stale node with the same name but wrong type somehow exists,
        # remove it so we author a clean, deterministic graph.
        if node is not None:
            nt.nodes.remove(node)
        node = nt.nodes.new(bl_idname)
        node.name = name
    return node


def _ensure_link(nt, from_socket, to_socket):
    """Idempotently ensure a link from `from_socket` to `to_socket`. If the
    destination is already driven by exactly this source, do nothing."""
    for ln in to_socket.links:
        if ln.from_socket == from_socket:
            return
    nt.links.new(from_socket, to_socket)


# ---------------------------------------------------------------------------
# per-material tuning
# ---------------------------------------------------------------------------

def _build_gold(mat):
    """HB2_Gold_MLI -- bright lacquered reflective gold foil.

    Base Color and Roughness are driven by ColorRamps; we tune those stops.
    Coat (currently 0) is the biggest 'shinier' lever -> add a thin glossy
    clear-coat for the lacquered-foil sheen.
    """
    bsdf = _principled(mat)
    if bsdf is None:
        return

    # --- free inputs (not linked) ---
    _set_input(bsdf, "Metallic", 1.0)
    # Crisp lacquered clear-coat sheen on top of the foil.
    _set_input(bsdf, "Coat Weight", 0.4)
    _set_input(bsdf, "Coat Roughness", 0.10)
    _set_input(bsdf, "Coat IOR", 1.5)
    # Subtle anisotropy -> slightly streaky foil highlight.
    _set_input(bsdf, "Anisotropic", 0.2)
    # Keep specular neutral/strong.
    _set_input(bsdf, "Specular IOR Level", 0.5)

    # --- Base Color driven by 'Color Ramp' (warm gold, with seam variation) ---
    # Target warm gold ~ linear (0.85, 0.55, 0.16) (#E6B23A-ish). Keep two
    # stops so the seam noise still produces tonal variation: a bright primary
    # gold and a slightly deeper gold for the quilted valleys.
    _set_ramp_stops(_ramp(mat, "Color Ramp"), [
        (0.0, (0.85, 0.55, 0.16, 1.0)),   # primary bright gold
        (1.0, (0.55, 0.35, 0.10, 1.0)),   # deeper gold in the seams
    ])

    # --- Roughness driven by 'Color Ramp.001' (fed by Noise Texture) ---
    # Drive a crisp range ~0.10 (floor) .. 0.30 so highlights stay tight and
    # the foil reads reflective. ColorRamp colors are read as scalar roughness.
    _set_ramp_stops(_ramp(mat, "Color Ramp.001"), [
        (0.0, (0.10, 0.10, 0.10, 1.0)),   # roughness floor -> crisp highlight
        (1.0, (0.30, 0.30, 0.30, 1.0)),   # rougher seam/quilt areas
    ])


def _build_black(mat):
    """HB2_Black_MLI -- dark charcoal quilted blanket, semi-glossy (not matte)."""
    bsdf = _principled(mat)
    if bsdf is None:
        return

    _set_input(bsdf, "Metallic", 0.5)
    _set_input(bsdf, "Coat Weight", 0.2)
    _set_input(bsdf, "Coat Roughness", 0.15)
    _set_input(bsdf, "Specular IOR Level", 0.5)

    # Base Color (driven by 'Color Ramp'): dark charcoal with subtle seam shift.
    _set_ramp_stops(_ramp(mat, "Color Ramp"), [
        (0.0, (0.022, 0.022, 0.024, 1.0)),  # charcoal
        (1.0, (0.010, 0.010, 0.011, 1.0)),  # near-black seams
    ])

    # Roughness (driven by 'Color Ramp.001'): semi-gloss ~0.30..0.42 so it
    # catches a soft specular like real black MLI.
    _set_ramp_stops(_ramp(mat, "Color Ramp.001"), [
        (0.0, (0.30, 0.30, 0.30, 1.0)),
        (1.0, (0.42, 0.42, 0.42, 1.0)),
    ])


def _build_silver(mat):
    """HB2_Silver_MLI -- bright reflective aluminized foil."""
    bsdf = _principled(mat)
    if bsdf is None:
        return

    _set_input(bsdf, "Metallic", 1.0)
    _set_input(bsdf, "Specular IOR Level", 0.5)
    # A whisper of coat keeps it consistent with the foil family but stays bright.
    _set_input(bsdf, "Coat Weight", 0.1)
    _set_input(bsdf, "Coat Roughness", 0.10)

    # Base Color (driven by 'Color Ramp'): bright neutral aluminium.
    _set_ramp_stops(_ramp(mat, "Color Ramp"), [
        (0.0, (0.88, 0.89, 0.90, 1.0)),
        (1.0, (0.70, 0.71, 0.73, 1.0)),
    ])

    # Roughness (driven by 'Color Ramp.001'): tight ~0.15..0.22, centred ~0.18.
    _set_ramp_stops(_ramp(mat, "Color Ramp.001"), [
        (0.0, (0.15, 0.15, 0.15, 1.0)),
        (1.0, (0.22, 0.22, 0.22, 1.0)),
    ])


def _build_radiator(mat):
    """HB2_Radiator -- clean white/silver radiator panel.

    This material uses direct (unlinked) Base Color / Roughness (the Wave
    Texture -> Color Ramp -> Bump chain only drives the grooved Normal, not the
    color), so we set the BSDF colour/rough inputs straight. References (JAXA
    art) show the radiator reading bright white-silver, so we lift the base
    colour toward white and back off the metallic a touch (a real white thermal
    radiator is a bright dielectric coating, not a polished mirror).
    """
    bsdf = _principled(mat)
    if bsdf is None:
        return

    _set_input(bsdf, "Base Color", (0.90, 0.91, 0.93, 1.0))  # clean white-silver
    _set_input(bsdf, "Metallic", 0.6)
    _set_input(bsdf, "Roughness", 0.22)
    _set_input(bsdf, "Specular IOR Level", 0.5)


def _build_ionglow(mat):
    """HB2_IonGlow -- soft, contained CYAN-BLUE ion-engine-face glow.

    GET-OR-CREATE: this material may already exist in the .blend (an Emission ->
    Output graph, color ~[0.2,0.45,1.0] strength 14 -- too hot, clips to white
    through AgX). It is NOT authored by any geometry script, so we author it here
    for reproducibility. If the Emission/Output graph is missing (from-scratch
    rebuild) we create it; otherwise we reuse the existing nodes by name.

    Look (matched to JAXA refs `hayabusa2 image 9/10.jpg`, `hayabusa image
    11.jpg`): saturated cyan-blue, soft -- a bright core that falls off to a
    dim edge so each disk reads as a *glow*, not a flat hot disc. We drive the
    Emission Strength with a radial falloff built from the Generated texture
    coordinate (bounding-box normalized 0..1 per object, so it centres correctly
    on all four identical HB2_IonGlow0-3 disks without needing UVs).
    """
    # --- core tunable values ---
    GLOW_COLOR   = (0.15, 0.45, 1.0, 1.0)  # saturated cyan-blue
    CORE_STRENGTH = 11.0                   # vivid bright core, matched to ref image 9 (14 = white blowout)
    EDGE_STRENGTH = 3.0                    # soft dim edge, raised so the whole disk glows brighter

    mat.use_nodes = True
    nt = mat.node_tree

    # If this is a from-scratch material, bpy.data.materials.new(use_nodes=True)
    # seeds a default Principled BSDF we don't want. Drop any stray Principled so
    # the authored graph is clean and identical whether created or reused.
    for stray in [n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"]:
        nt.nodes.remove(stray)

    # Output + Emission (get-or-create so a from-scratch rebuild works).
    out = _get_or_make_node(nt, "Material Output", "ShaderNodeOutputMaterial")
    emis = _get_or_make_node(nt, "Emission", "ShaderNodeEmission")
    emis.inputs["Color"].default_value = GLOW_COLOR

    # --- soft radial falloff sub-graph driving Emission Strength ---
    # Generated coords -> recentre to [-0.5,0.5] in XY -> radial distance ->
    # Color Ramp shaping core->edge -> map to [EDGE..CORE] strength.
    texco = _get_or_make_node(nt, "IonGlow TexCoord", "ShaderNodeTexCoord")

    # Subtract 0.5 from the Generated vector so the disk centre sits at origin.
    sub = _get_or_make_node(nt, "IonGlow Center", "ShaderNodeVectorMath")
    sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)

    # Vector length -> radial distance from centre (0 at core, ~0.5 at rim).
    length = _get_or_make_node(nt, "IonGlow Radius", "ShaderNodeVectorMath")
    length.operation = 'LENGTH'

    # Shape the radius into a soft 1->0 core->edge mask via a ColorRamp.
    ramp = _get_or_make_node(nt, "IonGlow Falloff", "ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = 'EASE'  # smooth, soft shoulder
    # Two-stop soft falloff: wider bright core (out to ~0.24 radius) fading to dark by ~0.5
    # so the disks read as bigger, brighter blue glows (ref image 9).
    _set_ramp_stops(cr, [
        (0.24, (1.0, 1.0, 1.0, 1.0)),
        (0.50, (0.0, 0.0, 0.0, 1.0)),
    ])

    # Map mask [0..1] -> Emission Strength [EDGE..CORE].
    strength = _get_or_make_node(nt, "IonGlow Strength", "ShaderNodeMapRange")
    strength.inputs["From Min"].default_value = 0.0
    strength.inputs["From Max"].default_value = 1.0
    strength.inputs["To Min"].default_value = EDGE_STRENGTH
    strength.inputs["To Max"].default_value = CORE_STRENGTH

    # Wire it up (idempotent).
    _ensure_link(nt, texco.outputs["Generated"], sub.inputs[0])
    _ensure_link(nt, sub.outputs["Vector"], length.inputs[0])
    _ensure_link(nt, length.outputs["Value"], ramp.inputs["Fac"])
    _ensure_link(nt, ramp.outputs["Color"], strength.inputs["Value"])
    _ensure_link(nt, strength.outputs["Result"], emis.inputs["Strength"])
    _ensure_link(nt, emis.outputs["Emission"], out.inputs["Surface"])


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

# Materials we author. The bool flag = "create the material if it is missing"
# (only HB2_IonGlow is get-or-create; the MLI/radiator mats must already exist
# and are tuned in place).
_BUILDERS = (
    ("HB2_Gold_MLI",   _build_gold,     False),
    ("HB2_Black_MLI",  _build_black,    False),
    ("HB2_Silver_MLI", _build_silver,   False),
    ("HB2_Radiator",   _build_radiator, False),
    ("HB2_IonGlow",    _build_ionglow,  True),
)


def build():
    """Idempotently author the owned spacecraft-skin + ion-glow materials.

    The MLI/radiator materials are tuned in place (skipped with a warning if
    absent). HB2_IonGlow is get-or-create: created if missing so a from-scratch
    rebuild still works. No file IO, no render, no MCP.
    """
    touched = []
    for name, fn, create_if_missing in _BUILDERS:
        mat = bpy.data.materials.get(name)
        if mat is None:
            if create_if_missing:
                mat = bpy.data.materials.new(name)
                mat.use_nodes = True
                print(f"[06_materials] created missing material '{name}'")
            else:
                print(f"[06_materials] WARNING: material '{name}' not found -- skipped")
                continue
        if mat.node_tree is None:
            # get-or-create builders author their own graph; only skip the
            # in-place tuners that genuinely have nothing to edit.
            if create_if_missing:
                mat.use_nodes = True
            else:
                print(f"[06_materials] WARNING: material '{name}' has no node tree -- skipped")
                continue
        fn(mat)
        touched.append(name)
    print(f"[06_materials] build() done. Authored: {', '.join(touched)}")
    return touched


# ---------------------------------------------------------------------------
# stand-alone test (only runs when executed directly, never on import)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    build()

    # --- verify the ion-glow emission programmatically (the test render may not
    # show the glow if the engines are hidden, so confirm the values here) ---
    _ion = bpy.data.materials.get("HB2_IonGlow")
    if _ion and _ion.node_tree:
        _emis = _ion.node_tree.nodes.get("Emission")
        if _emis:
            _col = tuple(round(float(x), 4) for x in _emis.inputs["Color"].default_value)
            _str_in = _emis.inputs["Strength"]
            if _str_in.is_linked:
                # Strength is driven by the radial falloff (Map Range To Min..Max).
                _mr = _ion.node_tree.nodes.get("IonGlow Strength")
                _edge = round(float(_mr.inputs["To Min"].default_value), 4) if _mr else "?"
                _core = round(float(_mr.inputs["To Max"].default_value), 4) if _mr else "?"
                print(f"[06_materials] IonGlow emission color={_col} "
                      f"strength=radial[edge={_edge}..core={_core}]")
            else:
                print(f"[06_materials] IonGlow emission color={_col} "
                      f"strength={round(float(_str_in.default_value), 4)}")

    # Parse args after the `--` separator.
    argv = sys.argv
    shot_path = None
    if "--" in argv:
        extra = argv[argv.index("--") + 1:]
        if "--shot" in extra:
            i = extra.index("--shot")
            if i + 1 < len(extra):
                shot_path = extra[i + 1]

    if shot_path:
        scene = bpy.context.scene

        # Ensure Eevee + raytracing so the gold's reflections/highlights show.
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except Exception:
            pass
        ee = scene.eevee
        for attr, val in (("use_raytracing", True), ("use_shadows", True)):
            if hasattr(ee, attr):
                try:
                    setattr(ee, attr, val)
                except Exception:
                    pass

        # Cheap test render: smaller frame + fewer samples (does NOT alter build()).
        scene.render.resolution_percentage = 35
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = 64
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = shot_path

        print(f"[06_materials] test render -> {shot_path}")
        bpy.ops.render.render(write_still=True)
        print("[06_materials] test render complete")
