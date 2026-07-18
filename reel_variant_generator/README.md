# reel_variant_generator

Mix-and-match reel variant generator for Trial Reels. Point it at a folder of background
clips and a list of text hooks, and it renders every combination (or a capped sample) as a
1080x1920 H.264 reel with the hook burned in. Built on ffmpeg, no heavy install.

## Why
Trial reels are pure experimentation, so volume wins. This turns a handful of clips plus a
list of hooks into dozens of testable variants in one command.

## Install
Just needs `ffmpeg` on PATH. (Already present in this environment.)

## Use
```bash
python generate_variants.py \
    --clips ./clips \        # folder of background clips (mp4/mov/...)
    --hooks ./hooks.txt \    # one hook per line
    --outdir ./variants \
    --style brand \          # brand = small understated line | bold = big follow-for-follow block
    --max 50                 # cap on how many to render

# rotate music across variants:
python generate_variants.py --clips ./clips --hooks ./hooks.txt --music ./tracks --outdir ./variants
```
`N clips x M hooks = N*M variants`, capped by `--max`. Output files are named by index, clip,
and hook slug.

## Styles
- **brand**: small, centered, serif, low in the frame. The vagabliss look. Use the colon
  open-loop hooks from `hooks.example.txt`.
- **bold**: large centered wrapped block. The follow-for-follow / small-creator meta look.

## Getting your clips in
- Local: drop clips in a folder and pass `--clips`.
- Google Drive: this environment has a Drive connector. Put source clips in a Drive folder and
  they can be pulled in, and rendered variants pushed back. (Ask and it will be wired up.)

## Scale and limits
- This sandbox has limited disk, so render in small batches here (a few dozen). For hundreds,
  run this locally or in CI where disk is not capped.
- Trial Reels require a public account with 1,000+ followers to unlock.

## Upgrade path: Remotion
For animated, branded templates (motion text, transitions, logo), Remotion is the better tool:
define the reel as React, pass props (clip, hook, music), render N variants from a script. It is
heavier (Node + headless Chrome per render) but produces polished output. This ffmpeg version is
the fast, lightweight route for static-text variants.

## Note on inputs
The machine is neutral. The highest-value use is testing many hooks and edits of your real travel
content on cold audiences via trial reels. Follow-for-follow bait inflates follower count with
unengaged accounts, which lowers engagement rate (the number brands pay on) and can trip spam
detection, so feed it good content, not just growth-bait text.
