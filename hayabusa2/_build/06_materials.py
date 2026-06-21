"""
06_materials.py  --  Spacecraft MLI / radiator material polish for the
photorealistic Hayabusa2 model (Blender 5.1 / Eevee Next).

GOAL
----
Make the gold MLI read as bright, lacquered, reflective gold *foil* (like the
real craft and the JAXA concept art) rather than a dull matte metal, and bring
the other spacecraft-skin materials (black MLI, silver MLI, radiator) up to a
physically believable specular look.

DESIGN / SAFETY
---------------
* `build()` is idempotent. It edits the EXISTING node trees of four named
  materials IN PLACE. It never creates, deletes, or renames materials or nodes,
  never touches geometry/objects, and performs no file IO / render / MCP calls.
* The four MLI/radiator materials drive some Principled inputs through helper
  nodes (Base Color and Roughness come from ColorRamps; Normal from a Bump
  chain). Where an input is *linked* we set the value at its driver (the
  ColorRamp stops) instead of writing the ignored socket default. Where an input
  is *not* linked we set the socket default directly. Either way the result is
  deterministic, so re-running produces the identical node tree.
* The Bump (quilted-seam) chains and all texture/ColorRamp topology are
  preserved; only ColorRamp stop colors and free BSDF inputs are adjusted.

OWNED MATERIALS (only these are touched):
    HB2_Gold_MLI, HB2_Black_MLI, HB2_Silver_MLI, HB2_Radiator
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
    """HB2_Radiator -- light-grey radiator, minor polish only.

    This material uses direct (unlinked) Base Color / Roughness, so we set the
    BSDF inputs straight.
    """
    bsdf = _principled(mat)
    if bsdf is None:
        return

    _set_input(bsdf, "Base Color", (0.78, 0.80, 0.82, 1.0))
    _set_input(bsdf, "Metallic", 0.85)
    _set_input(bsdf, "Roughness", 0.18)
    _set_input(bsdf, "Specular IOR Level", 0.5)


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

_BUILDERS = {
    "HB2_Gold_MLI":   _build_gold,
    "HB2_Black_MLI":  _build_black,
    "HB2_Silver_MLI": _build_silver,
    "HB2_Radiator":   _build_radiator,
}


def build():
    """Idempotently retune the four owned spacecraft-skin materials in place.

    No file IO, no render, no MCP. Edits existing node trees only.
    """
    touched = []
    for name, fn in _BUILDERS.items():
        mat = bpy.data.materials.get(name)
        if mat is None:
            print(f"[06_materials] WARNING: material '{name}' not found -- skipped")
            continue
        if mat.node_tree is None:
            print(f"[06_materials] WARNING: material '{name}' has no node tree -- skipped")
            continue
        fn(mat)
        touched.append(name)
    print(f"[06_materials] build() done. Tuned: {', '.join(touched)}")
    return touched


# ---------------------------------------------------------------------------
# stand-alone test (only runs when executed directly, never on import)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    build()

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
