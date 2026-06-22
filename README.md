# 🌌 Cinematic Curiosity-Gap Channel

> **"Things you've heard of but never truly understood — explained like a film."**

A faceless, all-ages, cinematic educational YouTube channel. Every video takes a word or event the viewer already half-knows — *quantum entanglement, a mega-tsunami, black holes, an asteroid flyby* — and reveals the staggering depth underneath it, in ~12–15 minutes, in a real human voice.

The promise is identical every time: **"You've heard of this. You have no idea how deep it goes."**

This repository is the **production workspace** — strategy, scripts, research, visual plans, and voiceover recordings — for the channel and its episodes.

---

## The positioning

- **Lens — a topic qualifies if it's:** familiar · under-explored · visually rich · awe-positive & all-ages.
- **Differentiator — awe, not dread.** Most of the cinematic-faceless space trades on darkness and shock. This channel owns the opposite lane: the goosebumps-of-wonder, genuinely-watchable-with-your-kid lane.
- **The moat — a real human voice + verified facts.** Original narration and fact-checked research are now a literal monetization advantage, not a nice-to-have. **No claim enters a script without a primary-source check.**
- **Cadence — 1 cinematic long-form per week + 3–5 native vertical shorts**, the sustainable elite pace for a solo creator.

See **[GAME-PLAN.md](GAME-PLAN.md)** for the full strategy: positioning, packaging system, production pipeline, monetization roadmap, and the 90-day launch plan.

---

## Repository contents

| File | What it is |
|---|---|
| **[GAME-PLAN.md](GAME-PLAN.md)** | The channel blueprint — thesis, niche, packaging, pipeline, monetization, launch plan, and a 12-video topic bank. |
| **[AI-DOCUMENTARY-ENGINE.md](docs/AI-DOCUMENTARY-ENGINE.md)** | The fully-promptable production engine — a state-by-state pipeline from a source-style PDF → branding → script → Nano Banana character stills → Seedance 2.0 animation prompts → thumbnails. The operating manual future sessions run. |
| **[GUIDE_full_text.txt](docs/GUIDE_full_text.txt)** | Verbatim source for the engine above — the OCR-recovered *Fern Animations* "AI Documentary Cloning Engine" (exact STATE wording + full output templates). |
| **[Episode-01-Hayabusa2-Torifune-SCRIPT.md](episodes/01-hayabusa2-torifune/Episode-01-Hayabusa2-Torifune-SCRIPT.md)** | Episode 01 narration script with shot-by-shot `[VISUAL]` / `[TEXT]` / `[SFX/MUSIC]` cues. |
| **[Episode-01-AI-IMAGE-PROMPT-PACK.md](episodes/01-hayabusa2-torifune/Episode-01-AI-IMAGE-PROMPT-PACK.md)** | A paste-ready AI-image prompt for every 🎨 still, locked to one consistent cinematic grade. |
| **[Episode-01-FOOTAGE-SOURCING-LIST.md](episodes/01-hayabusa2-torifune/Episode-01-FOOTAGE-SOURCING-LIST.md)** | A specific, licensable source (+ backup + credit) for every 🎞️ real-footage cue. |
| **[Hayabusa2 Torifune Flyby Research.txt](research/Hayabusa2%20Torifune%20Flyby%20Research.txt)** | The fact-checked deep-research dossier behind the script. |
| `assets/voiceovers/*.m4a` | Voiceover narration recordings (studio and non-studio takes). |

**Layout:** `docs/` (strategy + engine) · `episodes/01-hayabusa2-torifune/` (script, prompt pack, footage list) · `research/` (dossiers + `SOURCE PDF.pdf`) · `assets/` (`reference-images/`, `voiceovers/`, `models/`) · `hayabusa2/` (the Blender 3D project).

---

## 🛰️ Episode 01 — *"We're About to Rehearse Saving Earth From an Asteroid"*

The debut episode covers JAXA's **Hayabusa2#** ("SHARP") extended mission and its high-speed flyby of near-Earth asteroid **(98943) Torifune** — a spacecraft built for slow, gentle rendezvous, now attempting a precision close pass it was never designed for, as a real-world stress test of planetary-defense technology.

- **Flyby date:** July 5, 2026
- **Target runtime:** ~13–15 min (~1,950 words of narration)
- **Hook:** the 2013 Chelyabinsk fireball → "the ones big enough to erase a city are still out there… that's about to change."

Each production doc cross-references the others, so the script, the visuals, and their sources stay in lockstep.

---

## Visual-cue legend

The script tags every shot by how it will be sourced:

| Tag | Meaning | Lives in |
|---|---|---|
| 🎞️ | Real footage (archival / licensed) | the Footage Sourcing List |
| 🎨 | AI still (stylized) | the AI-Image Prompt Pack |
| 📊 | Motion graphic | built in-house (After Effects / Premiere) |

---

## Workflow

**Claude = the writers' room + automation assistant. Premiere = the edit bay.**

Research → script → narrate → source/generate visuals → edit in Adobe Premiere → package (title + thumbnail) → cut shorts. Strategy, scripting, prompts, and sourcing live here in Markdown; the edit itself happens in Premiere.

**Two production tracks.** The primary track is the hand-built one above — real footage + in-house Blender 3D + AI stills, narrated in a human voice, cut in Premiere. The second is the **[AI Documentary Engine](docs/AI-DOCUMENTARY-ENGINE.md)**: a state-by-state prompt pipeline that ingests a source-style PDF and runs all the way to Seedance animation prompts and thumbnails. Its Writing DNA is the formal spec of this channel's prose style; its mannequin visual look is adapted, not copied (awe-not-dread, our own cinematic language). See [GAME-PLAN.md](GAME-PLAN.md) §6.

---

*Private working repository for an in-development channel. Episode content is unreleased — please don't redistribute.*
