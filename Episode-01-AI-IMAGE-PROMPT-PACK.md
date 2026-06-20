# Episode 01 — AI-Image Prompt Pack 🎨
## "We're About to Rehearse Saving Earth From an Asteroid"
**Every 🎨 shot in the script → a paste-ready prompt, one consistent cinematic look.**

> Pairs with `Episode-01-Hayabusa2-Torifune-SCRIPT.md`. Covers all 15 unique 🎨 stills (long-form) + the 4 vertical short first-frames. 📊 motion-graphic cues are *not* here — those are built in After Effects/Premiere, not generated. 🎞️ real footage is in `Episode-01-FOOTAGE-SOURCING-LIST.md`.

---

## 0. How to use this pack (read once)

Each shot below gives you **two prompts for the same image**:
- **▸ Gemini / Claude Design (prose)** — full, self-contained natural-language prompt. Paste as-is into Gemini "Nano Banana" or Claude Design. Style is baked in.
- **▸ Midjourney (parameter line)** — compact. Paste, then append your locked `--sref` code (see §2).

Generate at **16:9** for the long-form; the 4 shorts get **9:16** variants at the bottom (§5).

These are **stills**. The motion (slow push, drift, parallax) happens in Premiere — so every prompt is framed with **breathing room around the subject** for a Ken Burns move. Don't fill the frame edge-to-edge.

---

## 1. THE HOUSE LOOK 🎬 (the one consistent grade — applies to *every* shot)

This is the single style that makes all 19 images feel like one film. It's baked into every prompt below; this is the reference if you ever tweak one.

| Dimension | The lock |
|---|---|
| **Medium** | Photoreal cinematic space-documentary still. Think *Interstellar* / *Ad Astra* / a Fern cold-open frame — IMAX-grade, not a game render, not an illustration. |
| **Palette** | **Teal-and-amber.** Deep teal / navy-black shadows + a single warm amber-gold light (the Sun). Cold void, warm star. This *is* the brand grade — "awe, not dread": warmth living inside the dark. |
| **Light** | ONE hard light source = raking sunlight from a low angle. Long shadows, strong rim-light on edges, deep but never crushed blacks. Volumetric god-rays only where dust/atmosphere exists. |
| **Lens / texture** | Anamorphic feel, shallow depth of field, gentle horizontal lens flare on the sun, fine 35mm film grain, faint chromatic aberration at frame edges, realistic bokeh. |
| **Mood** | Quiet, vast, reverent, hopeful. Scale = small human-made object against an enormous calm cosmos. |
| **Composition** | Negative space + rule-of-thirds. Subject small-ish, room to push/pan. Cinematic 16:9. |

**Global negative (always avoid):** text, captions, watermarks, logos, UI/HUD, on-screen data, people (unless a shot calls for them), cartoon/anime style, garish neon, oversaturation, cluttered sci-fi greebles, motion blur smear, lens-dirt overload, distorted/extra spacecraft parts, scientifically implausible nonsense.

---

## 2. CONSISTENCY WORKFLOW 🔒 (do this first — it's how you get "one look")

Three moves, in order, before you generate the 15 shots:

1. **Generate ONE hero spacecraft render first** (Shot A2 below is the best candidate). Pick your favourite. This is your **canonical Hayabusa2**.
2. **Lock the spacecraft** across every shot it appears in:
   - *Midjourney:* feed the hero image with `--cref <url> --cw 80` (character reference, weight 80 = shape locked, lighting free).
   - *Nano Banana / Claude Design:* attach the hero image as a reference and write "match this spacecraft exactly" — Nano Banana is built for this kind of subject consistency.
3. **Lock the grade** across *all 19* shots:
   - *Midjourney:* generate one frame you love, grab its `--sref <code>` (style reference), and append that same code to **every** prompt. (Placeholder below is `--sref LOCK`.)
   - *Nano Banana / Claude:* the prose preamble already carries the grade; for extra lock, attach your favourite finished frame as a style reference each time.

**Canonical Hayabusa2 description** (baked into every probe shot so it matches your real JAXA footage):
> a boxy gold-foil-wrapped spacecraft bus, two flat square planar antenna panels on its top deck (NOT a round dish), two wide dark-blue solar-panel wings spanning ~6 m, a cylindrical sampler horn extending from its underside, small thrusters, weathered and faintly scarred by micrometeorites, a soft turquoise-blue ion-engine glow trailing from the rear.

---

## 3. PASTE-READY STYLE BLOCKS (if you'd rather build prompts yourself)

**STYLE SUFFIX — append to any Midjourney prompt:**
```
cinematic space documentary still, teal-and-amber color grade, deep navy shadows, single warm low-angle sunlight, anamorphic lens flare, shallow depth of field, 35mm film grain, photoreal, IMAX quality, vast and quiet, awe not dread --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```

**STYLE PREAMBLE — prepend to any Gemini/Claude prompt:**
```
A photorealistic, cinematic space-documentary still in the style of Interstellar. Color grade: teal-and-amber — deep teal and navy-black shadows with a single warm amber-gold sunlight as the only light source. Shallow depth of field, gentle anamorphic lens flare, fine 35mm film grain, deep but not crushed blacks. Mood: vast, quiet, reverent, hopeful — awe, not dread. 16:9. Leave negative space for a slow camera move. No text, no logos, no UI.
```

---

## 4. THE 15 SHOTS (long-form, 16:9)

---

### 🎨 A1 — Dark asteroid drifting past a fragile Earth
**Script:** Cold Open (L23) · *"Now… picture one ten times bigger."* · becomes a **slow push-in**.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still in the style of Interstellar. A large, dark, cratered asteroid drifts silently in the foreground, lit on one edge by a single warm amber sunlight; in the far distance, a small, fragile, blue-and-white Earth hangs against the black void, slightly out of focus. The asteroid is menacing only in scale, not in style — calm, not horror. Teal-and-navy shadows, deep blacks, fine film grain, gentle anamorphic flare, shallow depth of field. Vast and quiet. Lots of empty space around Earth for a slow push-in. No text, no logos.

**▸ Midjourney:**
```
huge dark cratered asteroid drifting in foreground, tiny fragile blue Earth far in the background bokeh, single warm amber rim-light, vast silent cosmos, cinematic space documentary still, teal-and-amber grade, deep navy shadows, anamorphic flare, 35mm grain, photoreal, awe not dread --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Earth small and soft — *fragile*, not a hero shot. This is the dread-pivot line, so keep it beautiful, not scary.

---

### 🎨 A2 — Scarred spacecraft cutting through deep space ⭐ (generate this FIRST = your hero render)
**Script:** Cold Open (L31) · *"a spacecraft that has already cheated death once…"* · slow drift.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still in the style of Interstellar. A small, weathered spacecraft cuts through deep space, sunlight raking hard across it from a low angle. The spacecraft: a boxy gold-foil-wrapped bus, two flat square planar antenna panels on its top deck (not a round dish), two wide dark-blue solar-panel wings, a cylindrical sampler horn under the body, faintly scarred by micrometeorites, a soft turquoise-blue ion-engine glow trailing behind. Set against an enormous starfield with a distant warm sun creating a long anamorphic flare. Teal-and-amber grade, deep navy shadows, shallow depth of field, 35mm film grain. Lonely, noble, vast. Negative space to the side for a drift move. No text, no logos.

**▸ Midjourney:**
```
small weathered Japanese asteroid probe, gold-foil boxy bus, two flat square planar antennas on top, wide dark-blue solar wings, sampler horn beneath, faint turquoise ion-engine glow, low raking sunlight, micrometeorite scarring, deep starfield, distant warm sun anamorphic flare, cinematic space documentary still, teal-and-amber grade, shallow depth of field, 35mm grain, photoreal, lonely and noble --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** **This is your canonical Hayabusa2.** Pick the best, then reuse via `--cref` / reference image in A5, A6, A8, A12, A13, A15.

---

### 🎨 A3 — The original Hayabusa limping through space
**Script:** Act 1 (L47, the 🎨 half of a 🎞️/🎨 cut) · *"a beautiful disaster… on failing engines and leaking fuel."*

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still in the style of Interstellar. An older, more battered spacecraft limps through deep space — a single round parabolic high-gain dish antenna (older design), solar wings slightly askew, visible damage and scorching, a faint, sputtering, uneven ion-engine glow suggesting a struggling engine, a thin wisp of venting gas catching the light. Cold teal void, one low warm sunlight, long shadows. The mood is wounded but heroic — a machine barely holding together. Deep navy shadows, 35mm grain, anamorphic flare, shallow depth of field. No text, no logos.

**▸ Midjourney:**
```
older battered asteroid spacecraft limping through space, single round dish antenna, askew solar panels, scorch damage, faint sputtering uneven ion glow, thin wisp of venting gas, cold teal void, one warm low sunlight, wounded but heroic, cinematic space documentary still, teal-and-amber grade, 35mm grain, anamorphic flare, photoreal --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** **Visually distinct from A2** — original Hayabusa had a *round dish*, Hayabusa2 has *flat panels*. The difference sells "older sibling." Don't use the hero `--cref` here.

---

### 🎨 A4 — Macro: dark grains in a sealed container
**Script:** Act 1 (L61) · *"a little over five grams of rock… amino acids… 4.5 billion years."*

**▸ Gemini / Claude Design:**
> An extreme macro photograph, cinematic and scientific. Tiny, jet-black asteroid grains and pebbles resting inside a sealed, sterile container, lit by a single soft warm light that catches faint mineral glints on the dark surfaces. Crisp scientific clarity but cinematic — shallow macro depth of field, the nearest grains sharp, the background falling into teal-tinted darkness. A sense of preciousness and age. Fine film grain, deep blacks. No text, no logos, no hands.

**▸ Midjourney:**
```
extreme macro of tiny jet-black asteroid grains and pebbles in a sealed sterile container, single soft warm light catching faint mineral glints, shallow macro depth of field, teal-tinted dark background, precious and ancient, cinematic scientific still, deep blacks, fine grain, photoreal --ar 16:9 --v 7 --style raw --stylize 200 --sref LOCK
```
**Notes:** Tight macro — the change of scale (after wide space shots) is the point. No `--cref`.

---

### 🎨 A5 — Rock tumbling end over end; probe screaming toward it
**Script:** Act 2 (L94) · *"screaming past it at five and a quarter kilometers every second."* · 📊 speed counter overlaid later.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still in the style of Interstellar. A dramatic sense of speed: an elongated, lumpy grey-tan asteroid tumbling end over end in the mid-distance, and our weathered gold-foil spacecraft (boxy bus, flat planar antennas, dark-blue solar wings, turquoise ion glow) streaking toward it from the foreground at extreme velocity, motion conveyed by subtle directional streaking in the starfield, not by blurring the spacecraft. Single warm low sunlight, teal-and-navy void, anamorphic flare, shallow depth of field, 35mm grain. Tense and kinetic. Room at frame-left for a speed counter overlay. No text, no logos.

**▸ Midjourney:**
```
weathered gold-foil asteroid probe streaking at extreme speed toward an elongated lumpy grey-tan tumbling asteroid, sense of velocity via star streaks not blur, single warm sunlight, teal-and-navy void, anamorphic flare, shallow depth of field, cinematic space documentary still, 35mm grain, photoreal, tense and kinetic --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Use hero `--cref` for the probe. Asteroid = **stylized/ambiguous** (this is Torifune — we've never seen it; keep it lumpy and non-specific). Leave left third clear for the `18,900 km/h` counter. **Reused as Short 2's first frame.**

---

### 🎨 A6 — Faint signal arcing across the solar system
**Script:** Act 2 (L113) · *"brain surgery from a hundred million kilometers away… software upload, 2024."* · 📊 label overlaid later.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic wide shot of the solar system. A faint, delicate thread of warm light arcs across the vast black void — a transmission travelling from a small, distant blue Earth on one side toward a tiny, far-off spacecraft on the other, both rendered small against the immense distance. The signal is elegant and barely-there, not a sci-fi laser. Teal-and-navy space, one warm sun, soft star field, anamorphic flare, deep blacks, film grain. A sense of impossible distance and human reach. No text, no logos.

**▸ Midjourney:**
```
vast solar-system wide shot, a faint delicate thread of warm light arcing across the black void from a tiny distant blue Earth to a tiny far-off spacecraft, sense of impossible distance, elegant not laser-like, teal-and-navy space, one warm sun, soft starfield, anamorphic flare, deep blacks, cinematic, film grain, photoreal --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Both Earth and probe tiny — the *distance* is the subject. Subtle signal; the 📊 "Software upload — 2024" lower-third lands on top.

---

### 🎨 A7 — Pull back to Earth, city lights glowing
**Script:** Act 3 (L131) · *"this isn't really about one asteroid. It's a rehearsal. For us."* · the emotional turn to warmth.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic view of Earth at night from orbit. The dark side of the planet glows with warm amber clusters of city lights along the coastlines, a thin blue atmospheric rim catching the last of the sun, soft clouds. Calm, intimate, precious — the human home seen from above. Teal-and-navy space above the limb, warm amber cities below, gentle anamorphic flare where the sun grazes the edge, shallow focus, 35mm grain. Hopeful and tender. Room above the limb for a slow pull-back. No text, no logos.

**▸ Midjourney:**
```
Earth at night from orbit, warm amber city lights glowing along dark coastlines, thin blue atmospheric rim lit by hidden sun, soft clouds, calm and precious, teal-and-navy space above the limb, gentle anamorphic flare, shallow focus, cinematic, 35mm grain, photoreal, hopeful and tender --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** This is the warmth pivot ("for us") — the amber cities are the emotional payoff. Keep it tender, not techy.

---

### 🎨 A8 — The small probe against the vast dark, almost noble
**Script:** Act 3 (L154) · *"this aging spacecraft… quietly writing the playbook."*

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still in the style of Interstellar. Our weathered gold-foil spacecraft (boxy bus, flat planar antennas, dark-blue solar wings, turquoise ion glow) framed small and alone against an immense field of stars, lit by a single distant warm sun that throws a long rim-light along its edge. The composition is reverent — the machine dwarfed by the cosmos but dignified, heroic in its smallness. Deep teal-and-navy void, anamorphic flare, shallow depth of field, 35mm grain. Profound stillness. Lots of negative space. No text, no logos.

**▸ Midjourney:**
```
small weathered gold-foil asteroid probe alone against an immense starfield, single distant warm sun rim-lighting its edge, dwarfed by the cosmos yet dignified and noble, deep teal-and-navy void, anamorphic flare, shallow depth of field, cinematic space documentary still, 35mm grain, photoreal, profound stillness --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Hero `--cref`. Maximum negative space — this is a "let it breathe" hold. Cousin of A15 (vary the angle so they don't feel identical).

---

### 🎨 A9 — Faint flickering point of light (deliberately ambiguous)
**Script:** Act 4 (L164) · *"we don't really know… just a faint, shifting point of light."* · **never a confident render.**

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic astrophotography still. Against a deep field of stars, one ambiguous point of light glows slightly larger and warmer than the rest — soft, out of focus, shifting, impossible to resolve into a shape. It is deliberately mysterious: you cannot tell what it is. Heavy atmospheric haze and bokeh, teal-and-navy darkness, a faint warm tint to the unknown light, fine grain, gentle chromatic aberration. The feeling is "we've never actually seen this." No text, no logos.

**▸ Midjourney:**
```
deep starfield with one ambiguous soft out-of-focus point of light, slightly larger and warmer than the surrounding stars, impossible to resolve, mysterious and unknowable, heavy bokeh and haze, teal-and-navy darkness, faint warm tint, cinematic astrophotography, fine grain, chromatic aberration, photoreal --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** ⚠️ **Accuracy guardrail:** Torifune has never been imaged. Keep it an unresolved dot — *never* a crisp asteroid. **Reused as Short 5's first frame.**

---

### 🎨 A10 — Mythic "bird-boat" gliding through stars
**Script:** Act 4 (L170) · *"Ame-no-Torifune, the heavenly bird-boat of Japanese myth."* · 🎞️ children-naming b-roll is optional alongside (see footage list).

**▸ Gemini / Claude Design:**
> A painterly-yet-cinematic mythological still: an ethereal celestial vessel shaped like a fusion of a graceful bird and an ancient wooden boat — Ame-no-Torifune, the Japanese "heavenly bird-boat" — glides serenely through a starry cosmos, trailing soft luminous mist. Inspired by Japanese mythology and traditional ink-wash aesthetics but rendered cinematically, with warm amber light along the vessel and teal-and-navy starlit darkness around it. Dreamlike, reverent, beautiful — a wish for safe passage. Anamorphic glow, fine grain, deep blacks. No text, no logos.

**▸ Midjourney:**
```
ethereal mythological celestial vessel that is part graceful bird part ancient wooden boat, Ame-no-Torifune heavenly bird-boat, gliding through a starry cosmos trailing luminous mist, Japanese myth meets cinematic sci-fi, warm amber light on the vessel, teal-and-navy starlit dark, dreamlike and reverent, anamorphic glow, fine grain, photoreal-painterly --ar 16:9 --v 7 --style raw --stylize 400 --sref LOCK
```
**Notes:** Only intentionally stylized/painterly shot — it's *myth*, so a higher `--stylize` is fine. Keep the teal-amber grade so it still belongs. **Reused as Short 4's first frame.**

---

### 🎨 A11 — Two asteroids fusing into a peanut shape
**Script:** Act 4 (L178) · *"a contact binary… two separate asteroids that drifted toward each other… and fused."*

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still. Two separate rocky asteroids drift slowly toward each other in the void, almost touching, on the verge of fusing into a single lumpy, peanut-shaped or snowman-shaped body — like the object Arrokoth. Greyish-tan stony surfaces, softly lit by one warm low sun, long shadows in the gap between them. Teal-and-navy space, deep blacks, anamorphic flare, shallow depth of field, 35mm grain. Quiet, geological, tantalizing — a slow cosmic embrace. No text, no logos.

**▸ Midjourney:**
```
two separate greyish-tan rocky asteroids drifting toward each other in space almost touching, about to fuse into a single lumpy peanut-shaped body like Arrokoth, one warm low sun casting long shadows between them, teal-and-navy void, deep blacks, anamorphic flare, shallow depth of field, cinematic space documentary still, 35mm grain, photoreal --ar 16:9 --v 7 --style raw --stylize 220 --sref LOCK
```
**Notes:** Still stylized (it's a hypothesis about Torifune). Arrokoth/snowman silhouette reads instantly as "contact binary."

---

### 🎨 A12 — Probe and asteroid closing; countdown feel
**Script:** Close (L190) · *"There are no second chances here."* · 📊 countdown clock overlaid later.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still, tense and charged. Our weathered gold-foil spacecraft (boxy bus, flat planar antennas, blue solar wings, turquoise ion glow) approaches a large, looming, elongated dark asteroid that fills part of the frame — the gap between them small and closing. Dramatic single warm sunlight rakes across both, deep teal shadows, a sense of imminent, irreversible contact. Anamorphic flare, shallow depth of field, 35mm grain, deep blacks. Suspenseful, ticking. Room in a lower corner for a countdown overlay. No text, no logos.

**▸ Midjourney:**
```
weathered gold-foil asteroid probe approaching a large looming elongated dark asteroid, small closing gap between them, tense imminent contact, dramatic single warm sunlight raking across both, deep teal shadows, suspenseful, anamorphic flare, shallow depth of field, cinematic space documentary still, 35mm grain, photoreal --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Hero `--cref` for probe; asteroid stays ambiguous/dark. Tighter, more claustrophobic than A5 — this is the climax tension beat.

---

### 🎨 A13 — The falcon flies on past the asteroid, outward
**Script:** Close (L196) · *"the falcon doesn't turn for home. It keeps going."*

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still. Our weathered gold-foil spacecraft (boxy bus, flat planar antennas, blue solar wings, turquoise ion glow) flies away from the viewer, receding outward into deep space, having left an elongated asteroid behind and small in the background. Sense of forward momentum and onward journey, the warm sun ahead of it casting a long flare, teal-and-navy void wrapping around. Hopeful, resolute, lonely. Shallow depth of field, anamorphic flare, 35mm grain, deep blacks. Open space ahead for a forward push. No text, no logos.

**▸ Midjourney:**
```
weathered gold-foil asteroid probe flying away from viewer receding outward into deep space, an elongated asteroid left small behind it, warm sun ahead casting long flare, forward momentum and onward journey, teal-and-navy void, hopeful and resolute, shallow depth of field, anamorphic flare, cinematic space documentary still, 35mm grain, photoreal --ar 16:9 --v 7 --style raw --stylize 250 --sref LOCK
```
**Notes:** Hero `--cref`. Rear-three-quarter view (we see it leaving) — the only "from behind" probe shot, which makes the "keeps going" line land.

---

### 🎨 A14 — Tiny fast-spinning rock (1998 KY26), school bus for scale
**Script:** Close (L200) · *"a rock the size of a school bus… a full rotation every five minutes."* · 📊 label + bus-for-scale overlaid later.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic space-documentary still. A very small, roughly spheroidal, dark rocky asteroid — only about the size of a school bus — hangs in deep space, conveyed as tiny and fast-spinning by faint directional motion cues at its edges. One warm low sun lights one side, deep teal shadow on the other. Sense of an almost comically small, lonely little world. Teal-and-navy void, anamorphic flare, shallow depth of field, 35mm grain, deep blacks. Negative space beside it for a "school bus for scale" graphic. No text, no logos.

**▸ Midjourney:**
```
very small roughly spheroidal dark rocky asteroid the size of a school bus alone in deep space, subtle sense of fast spin at its edges, one warm low sun lighting one side, deep teal shadow, tiny lonely little world, teal-and-navy void, anamorphic flare, shallow depth of field, cinematic space documentary still, 35mm grain, photoreal --ar 16:9 --v 7 --style raw --stylize 230 --sref LOCK
```
**Notes:** Stylized (KY26 is barely characterized). Leave clear space for the scale graphic. **Reused as Short 6's first frame.**

---

### 🎨 A15 — Wide, beautiful: probe small against a star-filled void (final awe)
**Script:** Close (L206) · *"think about what's really happening out there."* · the final swell.

**▸ Gemini / Claude Design:**
> A photorealistic, cinematic ultra-wide space-documentary still — the emotional finale. Our weathered gold-foil spacecraft (boxy bus, flat planar antennas, blue solar wings, turquoise ion glow) is a tiny, dignified speck against a breathtaking, vast field of stars and the faint glow of the Milky Way. A single warm sun off to one side throws a long, beautiful anamorphic flare across the frame. Overwhelming scale, serene beauty, hope. Deep teal-and-navy cosmos, rich star detail, shallow depth of field, 35mm grain, deep blacks. Maximum negative space, gorgeous and quiet. No text, no logos.

**▸ Midjourney:**
```
ultra-wide cinematic space finale, tiny dignified weathered gold-foil asteroid probe as a speck against a breathtaking vast starfield and faint Milky Way glow, single warm sun off to one side with long anamorphic flare, overwhelming scale and serene hope, deep teal-and-navy cosmos, rich stars, shallow depth of field, 35mm grain, photoreal --ar 16:9 --v 7 --style raw --stylize 280 --sref LOCK
```
**Notes:** Hero `--cref`. The most beautiful frame in the film — worth generating many variations and picking the best. Strong thumbnail candidate too.

---

## 5. THE 4 SHORTS — vertical first-frames (9:16)

Each is a **re-generated 9:16 version** of an existing long-form shot (don't just crop — recompose vertically with the subject centered and headroom for burn-in captions). Reuse the same prose prompt; swap the ratio and recenter.

| Short | Source shot | What to change |
|---|---|---|
| **Short 2** — *"Built to float. Asked to scream past."* | **A5** (probe streaking at rock) | `--ar 9:16`. Stack vertically: asteroid upper third, probe lower third streaking up toward it. Leave **top 15% + bottom 25%** clear for caption + CTA. |
| **Short 4** — *"Named by schoolchildren, after a god-ship"* | **A10** (mythic bird-boat) | `--ar 9:16`. Vessel centered vertically, mist trailing down. Dreamy negative space top & bottom for big text. |
| **Short 5** — *"One rock… or two fused together?"* | **A9** (ambiguous dot) | `--ar 9:16`. The unresolved point of light dead-center, heavy bokeh filling the vertical frame. |
| **Short 6** — *"A school-bus-sized world spinning every 5 min"* | **A14** (tiny KY26) | `--ar 9:16`. Tiny asteroid in the vertical center, vast space above and below for text. |

**Midjourney tip:** take your finished 16:9 frame and run `/describe` or feed it as an image prompt with `--ar 9:16` to keep the exact look while recomposing tall. Keep the same `--sref LOCK`.

> Shorts 1 (Chelyabinsk) and 3 (DART) open on **real footage**, not AI — see the footage sourcing list.

---

## 6. ACCURACY GUARDRAILS ⚠️ (from the script's pre-record checklist)

- **Torifune is never rendered as "real."** Shots A5, A9, A11, A12 show it only as ambiguous/elongated/dark/unresolved. We have never imaged it — do not produce a confident, detailed Torifune. (A9 especially: keep it a blurry dot.)
- **1998 KY26 (A14)** is barely characterized — keep it generic and stylized.
- **Ryugu is the one asteroid you may render specifically** — but in this episode Ryugu is covered by **real JAXA footage** (see footage list), so you don't need an AI Ryugu.
- **Hayabusa2 vs original Hayabusa:** flat planar antennas (Hayabusa2, A2/A5/A8/A12/A13/A15) vs single round dish (original, A3). Keep them distinct.
- **No people** except the optional naming-event b-roll (which is real footage, not AI).
- These are stills feeding a Premiere timeline — **always leave negative space** for the planned camera move and the 📊 overlays noted per shot.
