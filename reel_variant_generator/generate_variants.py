#!/usr/bin/env python3
"""
generate_variants.py - mix-and-match reel variant generator for Trial Reels.

Takes a folder of background clips and a list of text hooks, and renders every
combination (or a capped sample) as a 1080x1920 H.264 reel with the hook burned
in. Optional music folder. Built on ffmpeg (no heavy deps), so it runs anywhere
ffmpeg is installed.

Usage
-----
    python generate_variants.py \
        --clips ./clips \
        --hooks ./hooks.txt \
        --outdir ./variants \
        --style brand \
        --max 50

    # with music rotation:
    python generate_variants.py --clips ./clips --hooks ./hooks.txt \
        --music ./tracks --outdir ./variants

hooks.txt: one hook per line. Blank lines ignored. Lines starting with # ignored.

Styles
------
  brand : small, centered, understated line low in the frame (the vagabliss look)
  bold  : large, centered, wrapped block (the follow-for-follow meta look)

Requires: ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import itertools
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav"}


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        sys.exit(f"ERROR: required tool '{binary}' not found on PATH.")


def _slug(text: str, n: int = 24) -> str:
    keep = "".join(c if c.isalnum() else "-" for c in text.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")[:n] or "hook"


def _wrap_to_file(hook: str, width: int, dest: Path) -> Path:
    """Write the (wrapped) hook to a textfile so ffmpeg drawtext avoids escaping hell."""
    wrapped = "\n".join(textwrap.wrap(hook, width=width)) or hook
    dest.write_text(wrapped)
    return dest


def _drawtext(style: str, hookfile: Path) -> str:
    common = (f"textfile='{hookfile}':fontcolor=white:x=(w-text_w)/2:"
              f"borderw=4:bordercolor=black@0.55:line_spacing=12")
    if style == "bold":
        # large wrapped block, vertically centered - the growth/meta look
        return (f"drawtext=fontfile={FONT_SANS}:{common}:fontsize=64:"
                f"y=(h-text_h)/2")
    # brand: small understated line, low third
    return (f"drawtext=fontfile={FONT_SERIF}:{common}:fontsize=44:"
            f"y=h*0.72")


def render(clip: Path, hook: str, style: str, music: Path | None,
           dest: Path, tmpdir: Path) -> bool:
    _require("ffmpeg")
    width = 22 if style == "bold" else 30
    hookfile = _wrap_to_file(hook, width, tmpdir / "hook.txt")
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920," + _drawtext(style, hookfile))

    cmd = ["ffmpeg", "-y", "-i", str(clip)]
    if music:
        cmd += ["-i", str(music)]
    cmd += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", "30", "-preset", "veryfast"]
    if music:
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-shortest",
                "-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-c:a", "copy"] if _has_audio(clip) else ["-an"]
    cmd += [str(dest)]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-600:] + "\n")
        return False
    return True


def _has_audio(clip: Path) -> bool:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(clip)],
        capture_output=True, text=True)
    return bool(proc.stdout.strip())


def load_hooks(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            lines.append(s)
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description="Mix-and-match reel variant generator.")
    ap.add_argument("--clips", required=True, type=Path, help="folder of background clips")
    ap.add_argument("--hooks", required=True, type=Path, help="text file, one hook per line")
    ap.add_argument("--music", type=Path, help="optional folder of audio tracks (rotated)")
    ap.add_argument("--outdir", default=Path("variants"), type=Path)
    ap.add_argument("--style", choices=["brand", "bold"], default="brand")
    ap.add_argument("--max", type=int, default=100, help="cap on number of variants")
    args = ap.parse_args()

    clips = sorted(p for p in args.clips.iterdir() if p.suffix.lower() in VIDEO_EXTS)
    hooks = load_hooks(args.hooks)
    tracks = (sorted(p for p in args.music.iterdir() if p.suffix.lower() in AUDIO_EXTS)
              if args.music else [])
    if not clips:
        sys.exit(f"No clips in {args.clips}")
    if not hooks:
        sys.exit(f"No hooks in {args.hooks}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    tmpdir = args.outdir / ".tmp"
    tmpdir.mkdir(exist_ok=True)

    combos = list(itertools.product(clips, hooks))
    total = min(len(combos), args.max)
    print(f"[plan] {len(clips)} clips x {len(hooks)} hooks = {len(combos)} combos, "
          f"rendering {total} (music tracks: {len(tracks) or 0})")

    made = 0
    for i, (clip, hook) in enumerate(combos):
        if made >= args.max:
            print(f"[cap] stopped at --max={args.max}")
            break
        music = tracks[i % len(tracks)] if tracks else None
        name = f"{made:03d}_{clip.stem[:10]}_{_slug(hook)}.mp4"
        dest = args.outdir / name
        ok = render(clip, hook, args.style, music, dest, tmpdir)
        status = "ok" if ok else "FAIL"
        print(f"[{made+1}/{total}] {status}  {name}")
        if ok:
            made += 1

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nDONE: {made} variants -> {args.outdir}")


if __name__ == "__main__":
    main()
