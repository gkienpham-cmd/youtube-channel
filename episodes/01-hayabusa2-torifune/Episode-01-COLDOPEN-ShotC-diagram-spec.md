# Episode 01 — COLD OPEN / BEAT 0 · "Fire Blind" diagram (Shot C overlay spec)

**Beat:** 📊 motion graphic, ~0:18–0:30 of the cold open.
**Method:** Blender 3D base plate ("Shot C") + Premiere/After-Effects overlay.
**Base plate:** `hayabusa2/renders/anim/_check/shotC_preview_f0084.png` (preview); 4K final 3840×2160, ~7 s @ 24 fps, slow drift.
**Narration this beat covers:**
> "Its cameras can't even turn to follow the rock. So it has to aim at an empty patch of space — where it *predicts* the asteroid will be — and fire blind. Get the timing wrong by a few minutes, and it photographs a shadow. Get the distance wrong by a few hundred meters… and it doesn't survive."

This file is the editor-facing build sheet for the camera-cone / reticle / "predicted position" overlay that composites on top of the Blender plate.

---

## 1. Purpose & concept

One idea, told cleanly: **the camera is bolted facing forward and cannot turn.** During the flyby the craft is moving too fast to track the asteroid, so it can't swing its cameras to follow the rock. Instead it points its fixed forward camera at an *empty* patch of space — the spot where the math says the asteroid *will be* when the craft gets there — and shoots on faith. The graphic makes that legible in one glance: a locked-forward camera cone projecting from the craft into open black space, and a marked target sitting in that emptiness with **nothing in it**. The tension is the gap between *aim* and *certainty* — we're pointing at a prediction, not at a thing we can see. Register is **awe-not-dread**: this is the elegant, nervy cleverness of the plan, not a horror beat. Minimal, precise, confident — the look of a good science documentary, not a HUD from an action movie.

---

## 2. Plate description (from the rendered frame)

**Craft position:** Hayabusa2 sits in the **lower-left quadrant**. The bus / instrument deck (the +Z top deck — the cylindrical/octagon antenna + ONC instrument cluster) reads at the **upper-left of the craft**, and one broad **blue solar paddle** sweeps diagonally down-and-right toward the **bottom-center**. The craft's long axis runs on a diagonal from upper-left (instrument deck) down to lower-right (panel tip).

**Open negative space:** the **entire upper-right ~two-thirds of the frame is empty starfield** — a large, clean, dark patch with nothing in it. This is the room we have to work in, and it's big.

**Screen-space forward (where the cone/arrow point):** the craft's travel direction is world **+Y**; the ONC science cameras look forward along travel from the **+Z instrument deck**. On this plate, the instrument deck faces **up and to the right**, away from the trailing panel — so **screen-forward = toward the upper-right**, pointing straight into the big empty patch. Cone origin ≈ the instrument cluster at the top of the bus (upper-left of the craft); cone and arrow aim **up-and-right** into open space. Direction of travel and the open patch agree — exactly what this beat needs.

**Composition verdict: GOOD AS-IS — no re-render required.** The forward direction points into the largest empty region of frame, which is the whole ballgame for this overlay. The negative space is generous enough to seat the cone, the reticle, and the label without crowding the craft.

*Optional insurance tweak (only if you're re-rendering Shot C anyway for other reasons — not worth a render on its own):* nudge the craft **~5–8% further toward the lower-left** (or drop the lens a hair) to add a touch more breathing room above the instrument deck. Target a clear forward cone-throw of **≥ 55–60% of frame width** of empty space from the deck to the upper-right corner, and keep the reticle's resting spot clear of the top and right edges by ≥ 8% (title-safe-ish). Current frame already roughly meets this; the tweak just buys margin so the label never kisses an edge. **Do not** flip or rotate the craft — the forward-points-into-open-space relationship is correct and must be preserved.

---

## 3. Element build (Premiere / After Effects)

All positions below are in **screen space on the 4K (3840×2160) plate**. Build at 4K; everything is vector/shape so it scales. Keep the craft itself untouched — overlay only.

### 3a. Camera cone ("locked forward")
The hero element: a **semi-transparent triangular beam** emanating from the forward camera and projecting **straight ahead** into the empty patch. It must read as *bolted in place* — it does **not** turn, sweep, or track.

- **Origin (apex):** at the **ONC instrument cluster** on the bus — the top of the craft's instrument deck (upper-left of the craft body). Tuck the apex just slightly *inside* the deck silhouette so the beam looks like it's coming *out of* the camera, not floating in front of it.
- **Direction:** along **screen-forward (+Y) = up-and-to-the-right**, into the open negative space. A single fixed heading — lock it; no rotation keyframes on the cone's angle ever.
- **Shape:** isosceles triangle / narrow wedge. Full **half-angle ≈ 8–12°** (total spread ~16–24°) — wide enough to read as a field-of-view, narrow enough to feel like a *fixed* lens, not a floodlight. Length: throw it **most of the way across the open patch** so the far edge sits near the reticle (≈ 55–70% of frame width).
- **Fill:** flat, **cool neutral** — a desaturated pale cyan / cold white. Suggested: `#9FB8C9` → fade to transparent along the length. **Opacity 8–14%** at the apex, feathering down to **0%** at the far end (a soft volumetric falloff). Keep it whisper-quiet; this is a *hint* of a beam, not a laser.
- **Edges:** two thin **rim lines** along the cone's long edges at **20–30% opacity**, same cool tint, **1.5–2 px @ 4K**, lightly feathered (0.5–1 px). The rim lines are what actually sell the cone; the fill is just atmosphere.
- **Feather:** soft outer feather (4–8 px) on the fill so it melts into the starfield. No hard geometric edge anywhere except the faint rim lines.
- **Locked-forward read:** optionally place a tiny **fixed bracket / lens icon** (2–3 short ticks) right at the apex on the deck, so the eye registers "this is anchored to the camera." Keep it tiny.

### 3b. "Predicted position" marker (the empty target)
A **reticle** sitting in the empty space at the **far end of the cone**, marking where the asteroid is predicted to be — with **nothing inside it**. The emptiness is the point; do not put a rock there.

- **Position:** centered on the cone's far axis, in clear sky, ≥ 8% from the top and right edges.
- **Form:** a **crosshair-in-a-dashed-box** or a **bracketed reticle** (four corner ticks framing a small empty square), ~**110–150 px** across @ 4K. Either reads as "designated target." A tiny center gap (no dot, or a hollow dot) keeps the middle conspicuously empty.
- **Style:** thin strokes **2 px @ 4K**, same cool neutral as the cone (slightly brighter, e.g. `#C8DAE6` at **70–85%** opacity) so it sits a half-step above the cone. Dashes short and even.
- **"It's empty" treatment (recommended, subtle):** one of —
  - a faint **dashed crosshair** through the box center (emphasizes there's nothing where the lines cross), **and/or**
  - a tiny lowercase tag near the reticle reading `no target yet` or `empty` at very low emphasis (40–55% opacity, small) — optional; the arrow label may be enough.
  Keep at most **one** emptiness cue plus the main label, or it gets busy.

### 3c. Arrow + label
An **arrow** from open sky into the reticle, labeled `predicted position` (lowercase, per script).

- **Arrow:** a clean thin line with a small triangular head, pointing **into** the reticle from slightly above/right of it (so the label can live in clear space and the arrow bridges label → target). Stroke **2 px @ 4K**, cool neutral, **75–85%** opacity, gentle 0–1 slight curve max (prefer straight). Head small and tasteful.
- **Label text:** `predicted position` — **lowercase**, exactly as scripted (the italics in the script signal emphasis in narration, not a styling instruction; set it roman/regular).
- **Font:** clean geometric/neutral **sans-serif**, matching the channel's science-doc lower-third (e.g. the same family as the *July 5, 2026* date card — Inter / Helvetica Now / Aktiv Grotesk class). **Regular or Medium** weight. **Letter-spacing +20–40** (tracking) for that calm instrument-readout feel. **Sentence/all-lowercase**, **NOT** all-caps.
- **Size:** ~**40–52 px** cap height @ 4K (reads cleanly on a phone without shouting). Smaller than any headline lower-third; this is an annotation, not a title.
- **Color:** off-white / cool neutral `#E6EEF3` at **90%**, optionally with a **hairline leader rule** under or beside the text (1 px, 40%) tying label to arrow — a tidy callout look.
- **Position:** in the **open sky to the upper-right of the reticle** (or directly right of it), inside title-safe, never overlapping the craft or the cone fill. Left-align the text block to wherever the leader/arrow begins.

### 3d. Optional flourishes (use ≤1, keep faint)
- A **faint dashed trajectory line** curving from the craft's nose forward through the reticle (the predicted intercept path), 1 px @ 40%, long dashes — reinforces "we're flying toward this point."
- A couple of **tick marks / range hash** along that trajectory line (distance gates) — only if it doesn't clutter.
- A subtle **"no signal / empty"** micro-treatment inside the reticle (a single faint flicker, see timing) to sell emptiness.
Pick one at most. Default to none if in doubt — minimal wins.

---

## 4. Animation & timing

Plate is ~7 s @ 24 fps with a slow drift; the editor can hold/extend on the last frame if narration runs long. Ease everything (no linear moves); this is a calm, deliberate instrument coming online, not a videogame HUD snapping in. Times below are relative to the beat's start (when the shot cuts in); align to the VO waveform, these are guides.

| Time (≈) | Narration cue | Element action |
|---|---|---|
| 0.0–0.6 s | (shot in) plate alone, craft drifting | Hold. Nothing overlaid yet — let the craft breathe for a half-beat. |
| 0.6–1.6 s | "…aim at an **empty patch of space**…" | **Cone draws on**: apex appears at the camera, beam + rim lines *extend* forward along +Y into the empty patch (animate length 0→full, ~1.0 s ease-out). Locked-forward — no rotation. |
| 1.6–2.6 s | "…where it **predicts** the asteroid will be…" | **Reticle locks in** at the cone's far end: corner brackets converge / dashed box scales 110%→100% and settles, crosshair fades up. A small, satisfying "lock" — quick scale + 1-frame settle, no bounce. |
| 2.4–3.2 s | (overlapping) the *predicted* / target idea | **Arrow + label** draw on: arrow wipes from label toward reticle (~0.4 s), `predicted position` fades/types up beside it. Optional leader rule wipes in under the text. |
| 3.2–5.5 s | "…and **fire blind**." | **Everything holds**, rock-steady, while the craft keeps drifting under it. This is the "held" image — let it sit. Optional: the reticle does one barely-there empty flicker (8–10% opacity dip, single beat) on "blind" to underline that nothing's there. |
| 5.5–6.5 s | "Get the **timing** wrong… a shadow." | Subtle emphasis: a faint **time tick** or the reticle pulses once (scale 100%→103%→100%, ~0.5 s) — a hair of motion, no new elements. |
| 6.5–7.5 s | "Get the **distance** wrong… it doesn't survive." | Subtle emphasis on **distance**: the dashed trajectory/leader between craft and reticle ticks once or a small range-gap shimmers — again minimal. (Hold past plate end if needed by freezing the last plate frame.) |
| out | (cut to next 🎨 "pull back" beat) | **Fast, clean exit**: cone + reticle + label fade together over ~0.3–0.4 s, or hard-cut on the edit. Don't animate them off elaborately — the next shot is doing the work. |

**Sync priorities (if you only nail three things):** cone draws on *"empty patch of space"*; reticle locks on *"predicts"*; whole thing holds dead-still through *"fire blind."*

---

## 5. Style notes

- **Awe-not-dread.** Calm, precise, a touch elegant — the confidence of a real mission diagram. No red, no alarm, no shaky-cam, no aggressive HUD glow. The "…and it doesn't survive" line lands through the *narration*, not through scary graphics.
- **Legibility first.** This plays on phones. Strokes ≥ 2 px @ 4K, label ≥ 40 px cap height, generous contrast against the dark starfield, everything inside title-safe (≥ 8% from edges).
- **Minimal & elegant.** Cone + reticle + arrow/label is the whole graphic. Resist adding readouts, coordinates, multiple labels, or extra lines. One emptiness cue max. If it starts to look like a cockpit, delete something.
- **Cohesion.** Match the channel's existing lower-third family, tracking, and cool-neutral palette (same look as the *July 5, 2026* card). One color family (cool white / pale cyan), one type family, one weight range.
- **Motion language.** Slow eases, soft fades, one tasteful "lock." Nothing snaps or bounces. The craft's own slow drift in the plate carries the life; the overlay stays composed on top of it.
- **Anchor to the craft.** Because the plate drifts slowly, parent/track the cone apex to the craft's on-screen instrument deck (a single position keyframe pair, or a quick planar track) so the beam stays glued to the camera as the craft moves. The reticle/label can stay world-locked in the sky — that subtle separation (beam moves with craft, target stays put) actually *reinforces* "the camera is aimed at a fixed predicted point."

---

## 6. Build options

- **Premiere (Essential Graphics / shape layers).** Fully doable in-app: build the cone as a Pen-tool triangle with a linear/radial opacity gradient + a feathered mask, the reticle and arrow as shape layers (stroke + dashes), and the label as an Essential Graphics text layer (reuse the existing lower-third style). Animate length/scale/opacity with keyframes (use the Graph Editor for eases). Best if you want everything in one timeline and minimal round-tripping. Track the cone apex to the craft with simple position keyframes or Premiere's built-in tracking.
- **After Effects (recommended for polish).** Cleaner control: cone via a shape layer with **Trim Paths** (draw-on) + gradient fill + feather, reticle corners with Trim Paths for the "lock," **Tracker / mocha** to pin the apex to the drifting craft, and crisp text with tracking. Easiest place to get the soft volumetric falloff and the satisfying reticle lock. Render the overlay (with alpha) and drop it over the plate in Premiere, or just dynamic-link. Use AE if you want the cone glow and lock to feel premium; otherwise Premiere shapes are entirely sufficient.

---

*Reminder: this is an overlay-only spec — the Blender Shot C plate is approved as-is (no re-render needed). All coordinates are screen-space on the 3840×2160 final; the craft sits lower-left, forward (+Y) points upper-right into open sky, and the cone/reticle/label live in that open patch.*
