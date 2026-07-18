# reel_analyzer

Capture an Instagram Reel (or any video) and produce a **full analysis**: metadata,
sampled frames, scene/transition detection, per-cut frames, a contact sheet, and a
human-readable report.

## What it produces

Running the tool writes an output folder like:

```
reel_out/
├── reel.mp4                # the downloaded reel (when given a URL)
├── reel.info.json          # yt-dlp social metadata (caption, author, counts, ...)
├── report.md               # human-readable summary + transition table
├── report.json             # machine-readable: metadata + every scene w/ timestamps
├── contact_sheet.jpg       # montage of the frame at each cut, labelled with timecode
├── transitions/            # one frame per detected shot (right after each cut)
│   └── scene_000_00-00-00.000.jpg ...
└── timeline/               # evenly sampled frames (default 1 fps) for a scrub view
    └── t_0001.jpg ...
```

`report.md` includes a transition table:

| # | start | end | duration | frames |
|--|--|--|--|--|
| 0 | 00:00:00.000 | 00:00:03.000 | 3.0s | 0-75 |
| 1 | 00:00:03.000 | 00:00:06.000 | 3.0s | 75-150 |

## Install

```bash
pip install -r requirements.txt      # yt-dlp, scenedetect, opencv-python, Pillow
# plus ffmpeg + ffprobe on PATH (apt install ffmpeg / brew install ffmpeg)
```

## Usage

Instagram requires you to be logged in to fetch a reel, so pass your browser cookies:

```bash
# Pull cookies straight from a logged-in browser profile:
python analyze_reel.py "https://www.instagram.com/reel/DXCkOJxjdnb/" \
    --cookies-from-browser chrome

# ...or use an exported Netscape cookies.txt:
python analyze_reel.py "https://www.instagram.com/reel/DXCkOJxjdnb/" \
    --cookies cookies.txt

# Already have the file? Skip the network entirely:
python analyze_reel.py reel.mp4
```

### Options

| flag | default | meaning |
|--|--|--|
| `--outdir` | `reel_out` | output directory |
| `--cookies` | – | path to Netscape `cookies.txt` |
| `--cookies-from-browser` | – | browser to read IG login cookies from (`chrome`, `firefox`, ...) |
| `--threshold` | `27.0` | PySceneDetect `ContentDetector` sensitivity — **lower = more cuts** |
| `--min-scene-len` | `0.4` | minimum shot length in seconds (suppresses flicker) |
| `--timeline-fps` | `1.0` | frames/sec sampled for the timeline overview |

## How transition detection works

Cuts are found with **PySceneDetect's `ContentDetector`**, which compares consecutive
frames in HSV space and flags a cut when the frame-to-frame content delta exceeds
`--threshold`. Each detected shot becomes a `Scene` with start/end timecodes and frame
numbers; the frame just after each cut is exported so you can eyeball every transition.

- Lots of fast cuts / motion-heavy edit → **lower** `--threshold` (e.g. `20`).
- Over-detecting on a shaky single take → **raise** `--threshold` (e.g. `35`) or
  increase `--min-scene-len`.
- Hard cuts detect cleanly; slow dissolves/fades may register as one long scene —
  lower the threshold to catch them.

## Note on networks

Downloading needs a network that can reach `instagram.com` **and** valid login cookies.
Locked-down/CI environments often block Instagram at the egress proxy (a gateway `403`);
in that case run the download step on a machine that can reach Instagram, then analyze
the resulting `.mp4` anywhere with `python analyze_reel.py reel.mp4`.
