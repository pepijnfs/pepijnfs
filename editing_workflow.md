# @vagabliss — Reel Editing SOP

The repeatable recipe for every reel. Tuned to the verified best practices: hook on frame 1,
a visual change every ~1.5–2s, captions/text for sound-off, one save CTA, 15–25s.

## Tools
- **CapCut** (free) — best for beat-sync + auto-captions. (InShot / Premiere Rush also fine.)

## The structure (4 acts, ~20s)
| Act | Time | What |
|---|---|---|
| **Hook** | 0–1.5s | Your single most jaw-dropping shot + hook text on frame 1 |
| **Build** | 1.5–14s | Beat-synced montage, ~1.5s per shot, escalating |
| **The Stay** | 14–18s | The hotel/room/terrace — your differentiator |
| **CTA** | 18–20s | Best lingering shot + "Save this for your Lake Lucerne trip 📍" |

## Vitznau shot order (from what you filmed)
1. **Hook** — the flower-lined jetty leading to lake + mountains (walk-forward shot)
2. Water reflections → tilt up to peaks
3. Flowers detail (low, lake blurred behind)
4. Boat / lake steamer or swan (motion)
5. Rigi cog railway or the grand hotel (the "where is this" anchor)
6. **The Stay** — the hotel/terrace/room
7. **CTA end** — you walking away down the jetty (the human signature)

## Beat-sync — the one skill that matters
1. **Pick the music FIRST** (see licensing below). Add it to the timeline.
2. CapCut: tap the track → **"Beats" → auto-detect** (or tap manually to the beat). Markers appear.
3. Trim each clip so its **cut lands on a beat marker** — aim ~1.5s per shot like the reference reel.
4. Put your **punchiest visual moment on a strong downbeat.**

## Text (your signature — keep identical every reel)
- Hook text on **frame 1**, hold ~2–3s. **Serif, white, drop shadow, top-third.**
- Optional small location label (`Vitznau, Switzerland 🇨🇭`) lower-third.
- Auto-captions only if there's talking (this one's a silent montage — skip).

## Music & licensing
- **Personal account:** you can use Instagram's full trending-audio library — do it, trending
  audio helps reach. Pick something calm/cinematic and cut to its beat.
- **If a post is a paid hotel promo:** switch to the **Meta Sound Collection** / licensed audio,
  or the audio can get muted.

## Colour
- One filter/LUT on the **whole** reel for consistency. Warm, slightly lifted, golden tones.
  Same preset every post → cohesive grid.

## Export
- **1080×1920, 9:16**, highest quality, **30fps** (or match your footage), high bitrate.
- Upload the file **natively** to Instagram (don't screen-record or re-share — kills quality
  and can trip the recycled-content penalty).

## Before you post — self-check
- [ ] Hook readable in the first second?
- [ ] A visual change at least every ~2s (no static shot >3–4s)?
- [ ] The *stay* is shown, not just scenery?
- [ ] Exactly one CTA, and it's "save"?
- [ ] Caption uses the template + max 5 hashtags at the end of the caption?

## Verify with data
Export a draft → run it through `reel_analyzer` (`python reel_analyzer/analyze_reel.py draft.mp4`)
to check scene count, average shot length, and cut cadence against the benchmark before you post.
