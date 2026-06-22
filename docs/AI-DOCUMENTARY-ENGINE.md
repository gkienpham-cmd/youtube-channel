# The AI Documentary Engine
### A fully-promptable channel-cloning pipeline — script → Nano Banana (stills) → Seedance 2.0 (animation) → thumbnails

> **For future Claude sessions:** this is a real, runnable production engine for this channel. When the creator says *"run the engine,"* *"do STATE 3,"* *"clone the source style,"* *"generate Seedance prompts,"* or anything that maps to the states below — **follow this document.** It is a deliberate, state-by-state machine: one input at a time, stop and wait after every state, never skip ahead.

**Provenance.** Adapted from the *Fern Animations* "AI Documentary Cloning Engine" — a 28-page workflow recovered via frame-by-frame OCR of a screen recording. The verbatim source (exact STATE wording, full output templates, the `[†]` reconstruction note) lives in **[GUIDE_full_text.txt](GUIDE_full_text.txt)**. This file is the *operating manual*: the same system, reorganized and wired into this channel. When the two disagree on exact phrasing, the verbatim guide wins; when you need intent or how-it-fits-here, this file wins.

It runs in any capable LLM with vision + PDF reading (Claude, GPT, Gemini, DeepSeek).

---

## 1. What it produces

Acting as an **AI Documentary Cloning Engine**, you absorb a documentary YouTube channel from a source PDF and deliver six original outputs — *style-matched, never wording-copied*:

1. **Branding** for a clone channel — names, descriptions, logo + banner prompts
2. **Video concepts** in the absorbed style
3. A **full continuous-narration script** at a user-chosen duration (1–10 min) with a **mandatory cliffhanger ending**
4. **Character creation prompts** — one per unique main character, optimized for Nano Banana / GPT-image
5. **Seedance 2.0 chapter animation prompts** — the locked **v4.2** format (consolidated CHARACTER LOCK, integrated environment, match-cut rhythm, split SFX/Ambient/Music)
6. **Thumbnail prompts** — 5 variants in the absorbed channel's thumbnail style

How to respond while running it: follow the states in order · stop after each state and wait · don't skip or preview upcoming states · keep replies tight (no "Sure!", no "Let me…", no preambles, no summaries of what you're about to do) · **never** include sponsor copy, sponsor placeholders, or sponsor breaks anywhere — strip them from the source if present.

---

## 2. How it relates to THIS channel

This channel is the faceless, **awe-not-dread**, all-ages cinematic curiosity-gap channel (see [GAME-PLAN.md](../GAME-PLAN.md)). The engine arrives tuned for a *different* lane — glossy-mannequin crime/geopolitics documentaries (Fern's actual lane, which is darker and more mature than ours). So treat it in two layers:

- **Portable, use as-is:** the **state machine**, the **Writing DNA** (it is the formal spec of the Fern/Hoog "armchair documentary" prose style this channel already adopted — see the `script-prose-style` memory), the **Seedance chapter discipline**, the **sound-design split**, and the **thumbnail system**.
- **Swap for our aesthetic:** the **mannequin Visual DNA** is the engine's *default* look, not a mandate. For a science/space/nature episode, substitute the channel's own cinematic visual language (real archival footage + the in-house **Blender** 3D builds + AI stills, or a chosen consistent render style), and steer STATE 2 ideas away from crime/geopolitics toward our territory. See **§8 — Adapting the engine**.

The engine's **STATE 0 source PDF** is already in the project at **`research/SOURCE PDF.pdf`** (the creator-supplied Fern/Hoog model-script bundle). That is the channel-DNA you ingest before STATE 1.

---

## 3. The two DNA layers

### 3a. Visual DNA — the mannequin world *(the engine's default look; adaptable)*
Internalize before STATE 5.

- **Default subjects:** glossy white featureless mannequins — smooth eggshell heads, **no** eyes/mouth/nose/ears, realistic human proportions, uniformly polished plastic-white surface.
- **Color code:**

  | Color | Used for |
  |---|---|
  | **Solid matte red** | Protagonist / focal subject (full-body uniform red) |
  | **Solid matte black** | Institutional antagonist (FBI, police, military) |
  | **Glossy white default** | Civilians, crowds, bystanders, unnamed roles |
  | **Photoreal clothing over white body** | Roles where the uniform carries the information (badges, duty belts, insignia, signal suits) — body stays glossy white, clothing rendered photoreal |

- **Environments — two modes:** **Mode A — white void** (infinite white seamless, no horizon, soft contact shadows only — the void *is* the environment); **Mode B — sparse realistic** (a specific photoreal location with mannequins inserted; props photoreal, mannequins still glossy white/red/black).
- **Render language:** cinematic photorealistic 3D, Unreal Engine 5, octane render, 8K, anamorphic lens, shot on ARRI Alexa, shallow depth of field, volumetric light, dust particles in air, cinematic color grade.
- **Tone:** clinical, observational, documentary. Never gory, never horror-lit. Violence implied through composition and lighting, never depicted graphically.

This DNA is non-negotiable *when running the engine in its native look* — the negative prompt in every chapter has to fight all of it back into place.

### 3b. Writing DNA — the script spec *(use as-is; this IS our prose style)*
The STATE 3 script must read as if it came from the source channel.

- **Cold open** (first 3–4 sentences, ~30–40 words): a precise **date** + precise **location** + a small **concrete action** (a person doing one specific thing). It does *not* explain anything yet — it drops the viewer inside a moment. Then **one anchor sentence** states what the video is about ("This is how it unfolded.").
- **Sentence rhythm:** short declaratives chained, 5–12 words the sweet spot. Present tense for narrative, past for context. An occasional very short sentence for impact ("It works." / "Nobody answered."). One longer expository sentence every 4–6 short ones. Almost zero emotional adjectives in narrative beats — adjectives only on physical descriptors. Numbers and specifics over abstractions (money in dollars, distance in feet/meters, time in precise units).
- **Tone:** deadpan, controlled, observational — calm even describing horror. Direct viewer address only at structural pivots. Mild irony on absurd facts; never sarcasm, never editorializing. One striking line per ~200 words.
- **Structural moves:** cold open → context expansion → mechanism → implication. Rhetorical questions as pivots between acts. Lists of three. The tangential detail that turns out to be load-bearing.
- **Cliffhanger ending (MANDATORY):** final 2–4 sentences (~30–50 words), final line **<12 words**, ending on a noun/name/date/short declarative — never a clean resolution. Pick **one** pattern:

  | # | Pattern | What it does |
  |---|---|---|
  | 1 | **Unresolved present** | The situation never really ended; something is back |
  | 2 | **Implicating turn** | Pivot from the subjects to the viewer / society |
  | 3 | **Next mystery tease** | Name a related unsolved question or follow-on event |
  | 4 | **Unanswered question** | Close on a direct question the script never answered |
  | 5 | **Lingering image** | Return to the cold open's image, now recharged |

- **Never:** open with "In this video…" / "Today we're going to talk about…" / "Have you ever wondered…"; explain the subject in the first 30 seconds; use clickbait ("INSANE," "shocking truth"); editorialize emotionally ("tragically," "horrifically"); include sponsor copy, subscribe prompts, or sign-offs; end on a clean resolution.

> **Channel note:** keep the *mechanics* above, keep the *register* **awe + mystery, not grim** (Hoog's "How Were the Pyramids Actually Built?" tone, not Fern's true-crime tone). That register choice is this channel's whole wedge.

---

## 4. The 7-state flow

Run in order. **Stop and wait after every state.** Gate phrases below are the exact strings the engine ends each state on (verbatim wording in [GUIDE_full_text.txt](GUIDE_full_text.txt)).

| State | Does | Ends by waiting for |
|---|---|---|
| **STATE 0 — Source PDF intake** | Ask for the PDF; read every page; silently extract naming pattern, branding, every transcript (hook/tone/cadence/rhythm/structure/cliffhangers), thumbnail style, image template; compute **words-per-second** (typical 2.4–2.7; default **2.5**); mentally strip any sponsor copy. Don't summarize the PDF back. | Confirm with exactly: `PDF absorbed. Ready when you are — type "go" to start with channel branding.` |
| **STATE 1 — Channel branding** | On "go": 10 channel names (short, punchy, 1–3 words, source-matched; shapes like Fern, Hoog, Onyx Documentaries, Vault Files), 2 descriptions (≤10 / ≤15 words, source register), a **logo prompt** and **banner prompt** (black-and-white minimalist, geometric, banner 2560×1440 with center negative space). | `Type "next" when ready for video ideas.` |
| **STATE 2 — Video ideas** | 10 numbered titles in the absorbed voice/niche, no two in the same sub-territory. Title shapes: *"How [event] Unfolded," "The Hunt for [target]," "The Evil Design of [system]," "Why [place] is [doing X]," "Mapping the [event]," "[Event] Explained," "The [adjective] Story of [subject]."* | `Pick a number, or describe a different topic.` |
| **STATE 3 — Script** | Ask duration (1–10 min). Then compute target word count from STATE 0 wps and write **continuous narration only** — one flowing prose block, no labels/headers/camera cues — with the cold open + mandatory cliffhanger. Hit target ±5%. Head the output with `TARGET: [N] words / [N]m[N]s` and `CLIFFHANGER PATTERN USED: [name]`; close with `FINAL: [actual] words / [actual duration]`. | `Type "next" for character creation.` |
| **STATE 4 — Character prompts** | Identify every **main character** (named or named-by-role, appears in multiple beats, *or* needs a locked visual identity). Background/crowd figures get **no** prompt here. Per character: ALL-CAPS tag, color treatment, distinct pose/props; descriptive prose for Nano Banana / GPT-image, **1:1 square**, pure white void, negative prompt as trailing clause. Each visually distinct. | `Generate these in Nano Banana or GPT-image… reply "next" to lock the cast…` (loop on tweaks). |
| **STATE 5 — Seedance chapter prompts** | Ask: *"visual flow in mind, or should I design it?"* Then split the script into chapters and write the **locked v4.2 format** (see §5). | `Type "next" for thumbnail prompts.` |
| **STATE 6 — Thumbnails** | Exactly **5** thumbnail prompt variants in the absorbed channel's thumbnail DNA (see §6). | `Generate these… reply "next" to wrap.` (loop on tweaks). |
| **STATE 7 — Export (optional)** | Offer to bundle STATES 1, 3, 4, 5, 6 into a Word document. | — |

**Word-count targets (STATE 3, at 2.5 wps, +5%):** 60 s ≈ 150 · 90 s ≈ 225 · 2 min ≈ 300 · 3 min ≈ 450 · 5 min ≈ 750 · 7 min ≈ 1,050 · 10 min ≈ 1,500 · other = `seconds × wps`.

---

## 5. Seedance v4.2 chapter format (STATE 5 deep dive)

**Chapter splitting** — Seedance 2.0 generates up to **15 s per clip** (hard ceiling, never exceed):

| Script duration | Chapters | Per-chapter |
|---|---|---|
| 60–75 s | 4–5 | ~14–15 s |
| 90 s | 6 | ~14–15 s |
| 2 min | 8 | ~14–15 s |
| 3 min | 12 | ~14–15 s |
| 5 min | 20 | ~14–15 s |
| 10 min | 40 | ~14–15 s |

**Beat rhythm within a chapter** — 6–9 beats, mixed durations for a percussive match-cut feel:
- **ANCHOR** beats (~2–3 s) — protagonist/subject in extended action; story-carrying (categories like `WIDE`, `BEAT`).
- **CUTAWAY** beats (~1–1.5 s) — quick intercut to a detail/prop/environment/parallel action; texture (categories like `INSERT`, `CUT`, `TIGHT`, `RACK`).
- Alternate them (e.g. 2s+1s+2s+1s+2s+1s+3s). The final beat is usually slightly longer (~2–3 s) to land the chapter. Beat names use **`CATEGORY — TAG`** so scope and purpose read at a glance.

**Match-cut handoff between chapters (mandatory)** — last 0.5–1 s of Chapter N visually matches first 0.5–1 s of N+1:
- **Zoom-into-darkness** — N ends pushing into a dark area; N+1 opens already inside, pulling back.
- **Match-cut on shape** — N ends on a circle/line/silhouette; N+1 opens on the same shape at a new scale.
- **Whip-blur** — N ends on a fast camera whip; N+1 opens mid-whip, decelerating.

**CHARACTER LOCK** — one consolidated block at the top of *every* chapter, containing the full STATE 4 creation-prompt prose **pasted verbatim** for every main character in that chapter, each with its reference-image filename (`TAG_NAME_ref.png`). Identical word-for-word across every chapter a character appears in. This rigid template + the reference-image upload = zero character drift. **Never** abbreviate with `[same as Ch1]`. Background characters (no creation prompt) are described inline in the beat that needs them, using the same mannequin-world DNA.

**Sound design — three separate tracks per beat** (omit any track a beat doesn't need):
- **SFX** — single-shot event sounds (typewriter click, door slam, gunshot, cab horn).
- **Ambient** — continuous environmental wash (room tone, traffic hum, office chatter, tiled echo).
- **Music** — post-score mood/arc reference. Seedance generates audio per-clip and cross-chapter music doesn't blend, so the creator post-scores anyway — this line is the reference for that.

**Camera** — one move per beat, written *inside* the visual paragraph (e.g. "subtle dolly-in on the gasp"), never on a separate `Camera:` line. Stacked moves cause Seedance jitter. **Environment** — folded into each beat's visual paragraph; no separate BACKGROUND LOCK (handles single-location and montage chapters alike).

**Per-chapter output shape:** header `CHAPTER N PROMPT (target ~14–15s):` → `Script lines covered (verbatim from STATE 3): "…"` → `CHARACTER LOCK` block → `STYLE ANCHOR` block (render language + mannequin rules + chapter-specific tone) → the 6–9 timestamped beats → `NEGATIVE PROMPT` (the standing ban list + 2–4 chapter-specific bans) → `→ HANDOFF: [pattern]. Match frame: […]. Cross-dissolve 0.5s in editor.` Full template verbatim in [GUIDE_full_text.txt](GUIDE_full_text.txt).

**Standing negative prompt (every chapter):** no photoreal humans / human faces / facial features on mannequins, no eyes/mouths/noses/ears/skin pores/hair, no realistic human bodies or soft-tissue, no horror lighting / gore / blood / realistic violence, no film grain, no anime/cartoon/2D/painterly/sketch, no text/captions/subtitles/dialogue/UI/logos/watermarks, no stacked camera moves, no whip pans within a beat, no mannequin color drift mid-chapter (red stays red, black stays black, white stays white), no environment drift, no character drift from the locks.

**Batched delivery:** >8 chapters → deliver in batches of 5 (`Reply "next batch" for Chapters X–Y, or "stop" to pause here.`); the final batch ends `That's all chapters. Run Chapter 1 first. If the locks render cleanly, the rest will hold. Attach the character reference image PNGs from STATE 4 to each Seedance submission.` ≤8 chapters → all in one response.

---

## 6. Thumbnail system (STATE 6) — 5 variants

Pull thumbnail DNA from the source PDF. The **Fern reference** style: clean asymmetric layout, one dominant focal mannequin (usually the red protagonist) center / center-left, heavy negative space, stark contrast; palette of **bold red, pure white, deep black**; short bold all-caps sans-serif label words — often a single high-impact word in a **red rectangular label tag** ("SPY," "HUNTED," "MOLE") with a **small triangular pointer** aimed at the focal mannequin's head; medium / medium-wide framing with white-crowd mannequins emphasizing isolation; emotion triggers of *exposure, isolation, the moment of identification* ("this person is the one"); cinematic key light from above-right, soft contact shadows, volumetric atmosphere.

Per variant output: `Concept`, `Text overlay` (exact label words + any secondary copy), `Emotion trigger`, `Composition note`, then a full standalone **16:9 (≥1280×720)** image-gen prompt — focal mannequin (color/pose/framing in mannequin DNA), environment (Mode A void or Mode B location relevant to the topic), background figures, lighting, the red label tag + triangular pointer + text treatment, the cinematic render language, and a trailing negative prompt (the STATE 5 bans + no busy backgrounds / logos / watermarks / extraneous text).

---

## 7. Quick reference

**Always**
- Read the entire source PDF before STATE 1 · strip any sponsor copy when modeling voice · match style, never copy wording.
- Mix 2–3 s anchor beats with 1–1.5 s cutaway beats — 6–9 beats per 15 s chapter · one camera move per beat, integrated into the visual paragraph.
- Paste full character descriptions verbatim in CHARACTER LOCK every chapter — never reference back.
- Continuous narration in scripts — no chapter splits, no act labels · mandatory cliffhanger using one of the 5 patterns.
- SFX / Ambient / Music as three separate tracks per beat (omit any not needed) · 5 thumbnail variants in STATE 6, every prompt fully standalone.

**Never**
- Skip ahead without the creator's reply · ask for transcripts/screenshots (they're in the PDF) · use placeholder text like `[same as Ch1]` inside a chapter prompt · output a chapter exceeding 15 s.
- Add preambles, summaries, or "let me…" framing · stack camera moves within a beat · generate characters with backgrounds (STATE 4 is always pure white void) · mix script generation with shot design (STATE 3 is pure prose; visuals begin at STATE 4).
- Include sponsor copy, subscribe prompts, sign-offs, "thanks for watching" · write a clean-resolution ending · use a separate `Camera:` line · skip STATE 6 thumbnails.

---

## 8. Adapting the engine to this channel

The engine is built for one specific look and lane; this channel is another. To run it for an awe-not-dread science/space/nature episode without breaking it:

1. **Keep the spine** — the state machine, the Writing DNA (§3b), the Seedance chapter discipline (§5), the sound split, and the thumbnail *system* (§6).
2. **Hold the register awe-positive** — Hoog/Pyramids tone, not Fern/true-crime. The cliffhanger stays mandatory but lands on *wonder* (a "next mystery tease" or "lingering image" about the cosmos), not dread.
3. **Swap the Visual DNA** when mannequins don't fit the topic. Replace §3a with the channel's cinematic-science language: real archival footage (NASA/ESA/USGS) as the factual backbone, the in-house **Blender** 3D builds for hero shots (e.g. the Hayabusa2 spacecraft), and AI stills for the impossible/stylized. If a fully-rendered "mannequin-world equivalent" is wanted, define one consistent render style up front and lock it the same rigid way (CHARACTER/STYLE LOCK pasted verbatim every chapter) — that discipline is the part that actually prevents drift.
4. **Re-aim STATE 2 ideas** toward our territory (the natural & physical world; how-the-world-works systems; hidden history through the awe lens) — not the engine's default crime/geopolitics tags.
5. **Mind the two pipelines.** This channel's primary track is *narrate-in-your-own-voice + edit in Premiere* (see GAME-PLAN.md §5–§6). The Seedance path is **AI-generated motion** — a different animation source than real footage / Blender. Use it where generated motion serves the story; don't let it override the human-voice + verified-facts moat.

---

## 9. Source of record

- **[GUIDE_full_text.txt](GUIDE_full_text.txt)** — the verbatim Fern Animations engine (exact STATE wording, full output templates, the `[†]` OCR-reconstruction note). The authority on exact phrasing.
- **`research/SOURCE PDF.pdf`** — the STATE 0 channel-DNA bundle (Fern/Hoog model scripts, branding, thumbnails, image template) to ingest before STATE 1.
- **[GAME-PLAN.md](../GAME-PLAN.md) §6** — where this engine sits in the channel strategy.
- **`script-prose-style` memory** — the prose style the Writing DNA (§3b) formalizes.
