#!/usr/bin/env python3
"""
analyze_reel.py — capture an Instagram Reel (or any video) and produce a full analysis:
metadata, sampled frames, scene/transition detection, transition frames, a contact
sheet, and a human-readable report.

Pipeline
--------
1. acquire()      Download the reel with yt-dlp (video + info.json + thumbnail),
                  or use a local file.
2. probe()        Technical metadata via ffprobe + social metadata from yt-dlp's info.json.
3. detect_scenes()Transition/cut detection with PySceneDetect (content-aware).
4. dump_frames()  Save the frame at each detected cut + an evenly-sampled timeline.
5. contact_sheet()Montage grid of the transition frames.
6. report()       Write report.json and report.md.

Usage
-----
    # From a URL (needs a network that allows Instagram + your login cookies):
    python analyze_reel.py "https://www.instagram.com/reel/DXCkOJxjdnb/" \
        --cookies-from-browser chrome

    # or with an exported cookies.txt (Netscape format):
    python analyze_reel.py "<url>" --cookies cookies.txt

    # From a local file (no network needed):
    python analyze_reel.py path/to/reel.mp4

Requirements: yt-dlp, ffmpeg, ffprobe on PATH; pip install scenedetect opencv-python Pillow
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        sys.exit(f"ERROR: required tool '{binary}' not found on PATH.")


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _fmt_ts(seconds: float) -> str:
    """Seconds -> HH:MM:SS.mmm"""
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


# --------------------------------------------------------------------------- #
# 1. acquire
# --------------------------------------------------------------------------- #
def acquire(source: str, outdir: Path, cookies: Optional[str],
            cookies_from_browser: Optional[str]) -> tuple[Path, Optional[dict]]:
    """Return (path_to_video, info_json_dict|None)."""
    if os.path.exists(source):
        print(f"[acquire] using local file: {source}")
        return Path(source), None

    _require("yt-dlp")
    print(f"[acquire] downloading with yt-dlp: {source}")
    stem = outdir / "reel"
    cmd = [
        "yt-dlp",
        "-o", f"{stem}.%(ext)s",
        "--write-info-json",
        "--write-thumbnail",
        "--no-playlist",
        # prefer a single progressive mp4 so we don't need to merge:
        "-f", "best[ext=mp4]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
    ]
    if cookies:
        cmd += ["--cookies", cookies]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    cmd.append(source)

    proc = _run(cmd)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
        sys.exit(
            "ERROR: yt-dlp failed. If this is Instagram, the reel almost certainly "
            "needs authentication — pass --cookies-from-browser <browser> or "
            "--cookies cookies.txt. A gateway 403 instead means the network policy "
            "blocks instagram.com; run this where Instagram is reachable."
        )

    # locate the downloaded video (mp4 preferred, else any non-json/-thumb file)
    video = None
    for ext in ("mp4", "mkv", "webm", "mov"):
        cand = Path(f"{stem}.{ext}")
        if cand.exists():
            video = cand
            break
    if video is None:
        vids = [p for p in outdir.glob("reel.*")
                if p.suffix.lower() not in (".json", ".jpg", ".jpeg", ".png", ".webp")]
        if not vids:
            sys.exit("ERROR: could not locate downloaded video.")
        video = vids[0]

    info = None
    info_path = Path(f"{stem}.info.json")
    if info_path.exists():
        info = json.loads(info_path.read_text())
    print(f"[acquire] video -> {video}")
    return video, info


# --------------------------------------------------------------------------- #
# 2. probe metadata
# --------------------------------------------------------------------------- #
def probe(video: Path) -> dict:
    _require("ffprobe")
    proc = _run(["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", str(video)])
    if proc.returncode != 0:
        sys.exit("ERROR: ffprobe failed:\n" + proc.stderr)
    return json.loads(proc.stdout)


def summarize_technical(ff: dict) -> dict:
    fmt = ff.get("format", {})
    v = next((s for s in ff.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in ff.get("streams", []) if s.get("codec_type") == "audio"), {})

    def _fps(r):
        try:
            n, d = r.split("/")
            return round(float(n) / float(d), 3) if float(d) else None
        except Exception:
            return None

    return {
        "duration_s": float(fmt.get("duration", 0) or 0),
        "size_bytes": int(fmt.get("size", 0) or 0),
        "bitrate_bps": int(fmt.get("bit_rate", 0) or 0),
        "container": fmt.get("format_name"),
        "video": {
            "codec": v.get("codec_name"),
            "width": v.get("width"),
            "height": v.get("height"),
            "fps": _fps(v.get("avg_frame_rate", "0/0")),
            "pix_fmt": v.get("pix_fmt"),
            "nb_frames": v.get("nb_frames"),
        } if v else None,
        "audio": {
            "codec": a.get("codec_name"),
            "sample_rate": a.get("sample_rate"),
            "channels": a.get("channels"),
        } if a else None,
    }


def summarize_social(info: Optional[dict]) -> dict:
    if not info:
        return {}
    keys = ["id", "title", "description", "uploader", "uploader_id", "channel",
            "duration", "view_count", "like_count", "comment_count", "repost_count",
            "upload_date", "timestamp", "webpage_url", "thumbnail", "width", "height",
            "fps", "resolution", "ext", "track", "artist"]
    return {k: info[k] for k in keys if k in info and info[k] is not None}


# --------------------------------------------------------------------------- #
# 3. scene / transition detection
# --------------------------------------------------------------------------- #
@dataclass
class Scene:
    index: int
    start_s: float
    end_s: float
    start_frame: int
    end_frame: int

    @property
    def duration_s(self) -> float:
        return round(self.end_s - self.start_s, 3)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": _fmt_ts(self.start_s),
            "end": _fmt_ts(self.end_s),
            "start_s": round(self.start_s, 3),
            "end_s": round(self.end_s, 3),
            "duration_s": self.duration_s,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
        }


def detect_scenes(video: Path, threshold: float, min_scene_len: float) -> list[Scene]:
    """Content-aware cut detection. Returns a list of Scene objects."""
    from scenedetect import open_video, SceneManager
    from scenedetect.detectors import ContentDetector

    vid = open_video(str(video))
    fps = vid.frame_rate or 30.0
    mgr = SceneManager()
    mgr.add_detector(
        ContentDetector(threshold=threshold,
                        min_scene_len=int(round(min_scene_len * fps)))
    )
    mgr.detect_scenes(vid, show_progress=False)
    raw = mgr.get_scene_list()

    scenes: list[Scene] = []
    for i, (start, end) in enumerate(raw):
        scenes.append(Scene(
            index=i,
            start_s=start.seconds,
            end_s=end.seconds,
            start_frame=start.frame_num,
            end_frame=end.frame_num,
        ))
    # If no cuts were found, PySceneDetect returns [] -> treat whole clip as one scene.
    if not scenes:
        dur = vid.duration.seconds if vid.duration else 0.0
        scenes = [Scene(0, 0.0, dur, 0, int(dur * fps))]
    return scenes


# --------------------------------------------------------------------------- #
# 4. frame extraction
# --------------------------------------------------------------------------- #
def _grab_frame(video: Path, ts: float, dest: Path) -> bool:
    _require("ffmpeg")
    proc = _run(["ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", str(video),
                 "-frames:v", "1", "-q:v", "2", str(dest)])
    return proc.returncode == 0 and dest.exists()


def dump_transition_frames(video: Path, scenes: list[Scene], outdir: Path) -> list[dict]:
    """Save the first frame of every scene (i.e. the frame right after each cut)."""
    d = outdir / "transitions"
    d.mkdir(parents=True, exist_ok=True)
    out = []
    for s in scenes:
        # nudge slightly past the cut to land inside the new shot
        ts = s.start_s + 0.05
        fn = d / f"scene_{s.index:03d}_{_fmt_ts(s.start_s).replace(':', '-')}.jpg"
        if _grab_frame(video, ts, fn):
            out.append({"scene": s.index, "t": _fmt_ts(s.start_s), "file": str(fn)})
    print(f"[frames] {len(out)} transition frames -> {d}")
    return out


def dump_interval_frames(video: Path, duration: float, fps: float, outdir: Path) -> list[str]:
    """Evenly sample the whole clip at `fps` frames/sec for a timeline overview."""
    _require("ffmpeg")
    d = outdir / "timeline"
    d.mkdir(parents=True, exist_ok=True)
    proc = _run(["ffmpeg", "-y", "-i", str(video), "-vf", f"fps={fps}",
                 "-q:v", "3", str(d / "t_%04d.jpg")])
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-800:] + "\n")
    files = sorted(str(p) for p in d.glob("t_*.jpg"))
    print(f"[frames] {len(files)} timeline frames @ {fps}fps -> {d}")
    return files


# --------------------------------------------------------------------------- #
# 5. contact sheet
# --------------------------------------------------------------------------- #
def contact_sheet(frame_files: list[str], dest: Path, cols: int = 4,
                  thumb_w: int = 320) -> Optional[Path]:
    if not frame_files:
        return None
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("[sheet] Pillow not installed, skipping contact sheet")
        return None

    thumbs = []
    for f in frame_files:
        try:
            im = Image.open(f).convert("RGB")
        except Exception:
            continue
        ratio = thumb_w / im.width
        im = im.resize((thumb_w, int(im.height * ratio)))
        thumbs.append((Path(f).stem, im))
    if not thumbs:
        return None

    th = max(im.height for _, im in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    pad, label_h = 6, 18
    cell_h = th + label_h
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad,
                              rows * (cell_h + pad) + pad), "black")
    draw = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        r, c = divmod(i, cols)
        x = pad + c * (thumb_w + pad)
        y = pad + r * (cell_h + pad)
        sheet.paste(im, (x, y))
        draw.text((x + 3, y + im.height + 3), name[:46], fill="white")
    sheet.save(dest)
    print(f"[sheet] contact sheet -> {dest}")
    return dest


# --------------------------------------------------------------------------- #
# 6. report
# --------------------------------------------------------------------------- #
def write_report(outdir: Path, source: str, social: dict, technical: dict,
                 scenes: list[Scene], sheet: Optional[Path]) -> None:
    payload = {
        "source": source,
        "social_metadata": social,
        "technical_metadata": technical,
        "scene_count": len(scenes),
        "scenes": [s.to_dict() for s in scenes],
        "contact_sheet": str(sheet) if sheet else None,
    }
    (outdir / "report.json").write_text(json.dumps(payload, indent=2))

    durs = [s.duration_s for s in scenes]
    md = [f"# Reel analysis\n", f"**Source:** `{source}`\n"]
    if social:
        md.append("## Metadata")
        for k in ("uploader", "upload_date", "view_count", "like_count",
                  "comment_count", "duration", "webpage_url"):
            if k in social:
                md.append(f"- **{k}:** {social[k]}")
        if social.get("description"):
            md.append(f"\n> {social['description'][:500]}")
        md.append("")
    v = technical.get("video") or {}
    md += [
        "## Technical",
        f"- **Duration:** {technical.get('duration_s')} s",
        f"- **Resolution:** {v.get('width')}x{v.get('height')} @ {v.get('fps')} fps",
        f"- **Video codec:** {v.get('codec')}  |  **Audio:** "
        f"{(technical.get('audio') or {}).get('codec')}",
        f"- **Bitrate:** {round(technical.get('bitrate_bps',0)/1000)} kbps  |  "
        f"**Size:** {round(technical.get('size_bytes',0)/1e6,2)} MB",
        "",
        f"## Transitions — {len(scenes)} scene(s) detected",
    ]
    if durs:
        md.append(f"- Shortest {min(durs)}s · longest {max(durs)}s · "
                  f"avg {round(sum(durs)/len(durs),2)}s\n")
    md.append("| # | start | end | duration | frames |")
    md.append("|--|--|--|--|--|")
    for s in scenes:
        md.append(f"| {s.index} | {_fmt_ts(s.start_s)} | {_fmt_ts(s.end_s)} | "
                  f"{s.duration_s}s | {s.start_frame}-{s.end_frame} |")
    if sheet:
        md.append(f"\n![contact sheet]({Path(sheet).name})")
    (outdir / "report.md").write_text("\n".join(md) + "\n")
    print(f"[report] -> {outdir/'report.md'} and report.json")


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def analyze(source: str, outdir: Path, cookies: Optional[str],
            cookies_from_browser: Optional[str], threshold: float,
            min_scene_len: float, timeline_fps: float) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    video, info = acquire(source, outdir, cookies, cookies_from_browser)
    ff = probe(video)
    technical = summarize_technical(ff)
    social = summarize_social(info)
    duration = technical.get("duration_s", 0) or 0

    print(f"[detect] scene detection (threshold={threshold})...")
    scenes = detect_scenes(video, threshold, min_scene_len)
    print(f"[detect] {len(scenes)} scene(s) / {max(0, len(scenes)-1)} cut(s)")

    trans = dump_transition_frames(video, scenes, outdir)
    dump_interval_frames(video, duration, timeline_fps, outdir)
    sheet = contact_sheet([t["file"] for t in trans], outdir / "contact_sheet.jpg")

    write_report(outdir, source, social, technical, scenes, sheet)
    return {"video": str(video), "scenes": len(scenes), "outdir": str(outdir)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Capture and analyze an Instagram Reel / video.")
    ap.add_argument("source", help="Instagram reel URL or path to a local video file")
    ap.add_argument("--outdir", default="reel_out", type=Path)
    ap.add_argument("--cookies", help="path to cookies.txt (Netscape format)")
    ap.add_argument("--cookies-from-browser",
                    help="browser to pull IG login cookies from (chrome, firefox, ...)")
    ap.add_argument("--threshold", type=float, default=27.0,
                    help="PySceneDetect ContentDetector threshold (lower = more cuts)")
    ap.add_argument("--min-scene-len", type=float, default=0.4,
                    help="minimum scene length in seconds")
    ap.add_argument("--timeline-fps", type=float, default=1.0,
                    help="frames/sec sampled for the timeline overview")
    args = ap.parse_args()

    result = analyze(args.source, args.outdir, args.cookies,
                     args.cookies_from_browser, args.threshold,
                     args.min_scene_len, args.timeline_fps)
    print("\nDONE:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
