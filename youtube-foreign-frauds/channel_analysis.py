#!/usr/bin/env python3
"""Analyse a YouTube channel's recent videos: performance, baseline, patterns.

Uses only the YouTube Data API v3 (host www.googleapis.com), so it runs fine in
the cloud environment where youtube.com (transcripts) is blocked.

For each of a channel's most recent uploads it pulls view/like/comment counts
and duration, then computes:
  - a baseline (median views and median views/day, age-adjusted for recency),
  - which videos over/under-perform that baseline,
  - title patterns (length, numbers, money, questions),
  - typical duration and upload cadence.

Example:
    set -a && . ./.env && set +a
    python channel_analysis.py --channel-id UCZRoNJu1OszFqABP8AuJIuw --limit 50
    python channel_analysis.py --query "ColdFusion" --limit 50 --out reports/coldfusion.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from fetch_videos import resolve_channel, list_uploaded_videos, _get

API_BASE = "https://www.googleapis.com/youtube/v3"
NOW = datetime.now(timezone.utc)

_ISO_DUR = re.compile(
    r"P(?:(?P<d>\d+)D)?T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?"
)


def parse_duration(iso: str) -> int:
    """ISO-8601 duration (e.g. 'PT12M34S') -> total seconds."""
    m = _ISO_DUR.fullmatch(iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(m.group(k) or 0) for k in ("d", "h", "m", "s"))
    return ((d * 24 + h) * 60 + mi) * 60 + s


def resolve_by_query(session: requests.Session, api_key: str, query: str) -> str:
    """Return the channelId of the top channel search result."""
    data = _get(
        session,
        "search",
        {"part": "snippet", "type": "channel", "q": query,
         "maxResults": 1, "key": api_key},
    )
    items = data.get("items") or []
    if not items:
        raise RuntimeError(f"No channel found for query {query!r}.")
    return items[0]["id"]["channelId"]


def fetch_stats(session: requests.Session, api_key: str, video_ids: list[str]) -> dict:
    """Map video_id -> {views, likes, comments, duration_sec} (batched 50/call)."""
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        data = _get(
            session,
            "videos",
            {"part": "statistics,contentDetails,snippet",
             "id": ",".join(batch), "key": api_key},
        )
        for it in data.get("items", []):
            st = it.get("statistics", {})
            out[it["id"]] = {
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "duration_sec": parse_duration(
                    it.get("contentDetails", {}).get("duration", "")
                ),
            }
    return out


def _age_days(published_at: str) -> float:
    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return max((NOW - dt).total_seconds() / 86400.0, 0.5)


def _title_features(title: str) -> dict:
    return {
        "chars": len(title),
        "has_number": bool(re.search(r"\d", title)),
        "has_money": bool(re.search(r"[$€£]|\b(?:million|billion|trillion)\b", title, re.I)),
        "is_question": title.strip().endswith("?"),
    }


def analyse(channel: dict, videos: list[dict]) -> dict:
    """Attach per-video metrics and compute channel-level aggregates."""
    # Exclude Shorts (< 60s) so the baseline reflects long-form documentaries.
    longform = [v for v in videos if v.get("duration_sec", 0) >= 60]
    used = longform or videos

    for v in used:
        v["age_days"] = round(_age_days(v["published_at"]), 1)
        v["views_per_day"] = round(v["views"] / v["age_days"], 1)
        v["engagement_pct"] = round(
            100 * (v["likes"] + v["comments"]) / v["views"], 2
        ) if v["views"] else 0.0
        v.update(_title_features(v["title"]))

    views = [v["views"] for v in used]
    vpd = [v["views_per_day"] for v in used]
    med_views = statistics.median(views)
    med_vpd = statistics.median(vpd)

    for v in used:
        # Age-adjusted performance: views/day vs the channel's median views/day.
        v["perf_ratio"] = round(v["views_per_day"] / med_vpd, 2) if med_vpd else 0.0

    ranked = sorted(used, key=lambda v: v["views_per_day"], reverse=True)
    dates = sorted(datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))
                   for v in used)
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

    return {
        "channel": channel,
        "n_videos_analysed": len(used),
        "n_shorts_excluded": len(videos) - len(used),
        "baseline": {
            "median_views": int(med_views),
            "median_views_per_day": round(med_vpd, 1),
            "median_duration_sec": int(statistics.median(v["duration_sec"] for v in used)),
            "median_engagement_pct": round(
                statistics.median(v["engagement_pct"] for v in used), 2),
            "median_days_between_uploads": statistics.median(gaps) if gaps else None,
        },
        "title_patterns": {
            "pct_with_number": round(100 * sum(v["has_number"] for v in used) / len(used)),
            "pct_with_money": round(100 * sum(v["has_money"] for v in used) / len(used)),
            "pct_question": round(100 * sum(v["is_question"] for v in used) / len(used)),
            "median_title_chars": int(statistics.median(v["chars"] for v in used)),
        },
        "top": ranked[:8],
        "bottom": ranked[-5:],
    }


def _fmt(n: int) -> str:
    for unit, div in (("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(n)


def report_md(a: dict) -> str:
    ch = a["channel"]
    b = a["baseline"]
    tp = a["title_patterns"]
    L = [
        f"## {ch['title']}  (`{ch['id']}`)",
        "",
        f"Analysed **{a['n_videos_analysed']}** most-recent long-form uploads "
        f"({a['n_shorts_excluded']} Shorts excluded). Snapshot: {NOW:%Y-%m-%d}.",
        "",
        "### Baseline",
        f"- **Median views:** {_fmt(b['median_views'])}",
        f"- **Median views/day** (age-adjusted): {b['median_views_per_day']:,.0f}",
        f"- **Typical length:** {b['median_duration_sec'] // 60}m{b['median_duration_sec'] % 60:02d}s",
        f"- **Median engagement** (likes+comments / views): {b['median_engagement_pct']}%",
        f"- **Upload cadence:** ~every {b['median_days_between_uploads']} days"
        if b["median_days_between_uploads"] is not None else "- **Upload cadence:** n/a",
        "",
        "### Title patterns",
        f"- {tp['pct_with_number']}% contain a number · {tp['pct_with_money']}% reference money "
        f"($/million/billion) · {tp['pct_question']}% are questions · median {tp['median_title_chars']} chars",
        "",
        "### Top performers (by views/day, age-adjusted)",
        "| views/day | ×baseline | total views | age | length | title |",
        "|--:|--:|--:|--:|--:|:--|",
    ]
    for v in a["top"]:
        L.append(
            f"| {v['views_per_day']:,.0f} | {v['perf_ratio']}× | {_fmt(v['views'])} | "
            f"{v['age_days']:.0f}d | {v['duration_sec']//60}m | {v['title'][:70]} |"
        )
    L += ["", "### Weakest recent (by views/day)",
          "| views/day | ×baseline | total views | age | title |",
          "|--:|--:|--:|--:|:--|"]
    for v in a["bottom"]:
        L.append(
            f"| {v['views_per_day']:,.0f} | {v['perf_ratio']}× | {_fmt(v['views'])} | "
            f"{v['age_days']:.0f}d | {v['title'][:70]} |"
        )
    return "\n".join(L) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--handle")
    src.add_argument("--channel-id")
    src.add_argument("--query", help="Channel name to search for.")
    p.add_argument("--api-key", default=os.environ.get("YOUTUBE_API_KEY"))
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--out", type=Path, help="Write markdown report here.")
    p.add_argument("--json-out", type=Path, help="Write full analysis JSON here.")
    args = p.parse_args()
    if not args.api_key:
        p.error("Set YOUTUBE_API_KEY or pass --api-key.")

    s = requests.Session()
    channel_id = args.channel_id
    if args.query:
        channel_id = resolve_by_query(s, args.api_key, args.query)

    channel = resolve_channel(
        s, args.api_key, handle=args.handle, channel_id=channel_id
    )
    print(f"Analysing {channel['title']} ...", file=sys.stderr)
    videos = list_uploaded_videos(
        s, args.api_key, channel["uploads_playlist_id"], limit=args.limit
    )
    stats = fetch_stats(s, args.api_key, [v["video_id"] for v in videos])
    for v in videos:
        v.update(stats.get(v["video_id"], {"views": 0, "likes": 0,
                                           "comments": 0, "duration_sec": 0}))

    a = analyse(channel, videos)
    md = report_md(a)
    print(md)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(a, indent=2, ensure_ascii=False,
                                            default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
