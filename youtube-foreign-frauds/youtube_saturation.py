#!/usr/bin/env python3
"""Measure how saturated a topic already is on YouTube.

For each candidate fraud, search YouTube for existing videos and pull their view
counts. A topic whose best existing video has few views (or comes only from small
channels) is UNDER-COVERED -> an opportunity. Runs entirely on the Data API
(www.googleapis.com), so it works in the cloud environment.

Reads candidates from a JSON file: [{"name": ..., "query": ..., "region": ...,
"scale": ..., "note": ...}, ...] and writes a ranked saturation report.

    set -a && . ./.env && set +a
    python youtube_saturation.py --candidates candidates.json --out reports/saturation.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

from fetch_videos import _get

API_BASE = "https://www.googleapis.com/youtube/v3"


def _fmt(n: int) -> str:
    for unit, div in (("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(n)


def probe_topic(session, api_key: str, query: str, max_results: int = 12) -> dict:
    """Search YouTube for a topic; return coverage stats from existing videos."""
    search = _get(session, "search", {
        "part": "snippet", "type": "video", "q": query,
        "maxResults": max_results, "order": "viewCount", "key": api_key,
    })
    ids = [it["id"]["videoId"] for it in search.get("items", []) if "videoId" in it["id"]]
    if not ids:
        return {"n_videos": 0, "top_views": 0, "top_title": None,
                "top_channel": None, "sum_top_views": 0}

    stats = _get(session, "videos", {
        "part": "statistics,snippet", "id": ",".join(ids), "key": api_key,
    })
    vids = []
    for it in stats.get("items", []):
        vids.append({
            "views": int(it.get("statistics", {}).get("viewCount", 0)),
            "title": it["snippet"]["title"],
            "channel": it["snippet"]["channelTitle"],
        })
    vids.sort(key=lambda v: v["views"], reverse=True)
    top = vids[0]
    return {
        "n_videos": len(vids),
        "top_views": top["views"],
        "top_title": top["title"],
        "top_channel": top["channel"],
        "sum_top_views": sum(v["views"] for v in vids),
    }


def opportunity_score(cov: dict) -> float:
    """Higher = better opportunity. Rewards low existing coverage.

    We invert the best existing video's view count: a topic where the biggest
    treatment has <100K views is wide open; >5M means it's been done well already.
    """
    top = cov["top_views"]
    if top == 0:
        return 100.0
    if top < 50_000:
        return 90.0
    if top < 250_000:
        return 75.0
    if top < 1_000_000:
        return 55.0
    if top < 5_000_000:
        return 30.0
    return 10.0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--api-key", default=os.environ.get("YOUTUBE_API_KEY"))
    p.add_argument("--out", type=Path)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    if not args.api_key:
        p.error("Set YOUTUBE_API_KEY or pass --api-key.")

    candidates = json.loads(args.candidates.read_text())
    s = requests.Session()
    rows = []
    for c in candidates:
        print(f"Probing: {c['name']} ...", file=sys.stderr)
        cov = probe_topic(s, args.api_key, c["query"])
        cov["opportunity"] = opportunity_score(cov)
        rows.append({**c, **cov})

    rows.sort(key=lambda r: r["opportunity"], reverse=True)

    lines = [
        "# Fraud candidates — YouTube saturation & opportunity",
        "",
        "`opportunity` is higher when the biggest existing video on the topic has "
        "FEWER views (i.e. the story is under-covered). Ranked best-opportunity first.",
        "",
        "| opp | candidate | region | scale | best existing video | its views | by |",
        "|--:|:--|:--|:--|:--|--:|:--|",
    ]
    for r in rows:
        lines.append(
            f"| {r['opportunity']:.0f} | **{r['name']}** | {r.get('region','')} | "
            f"{r.get('scale','')} | {(r['top_title'] or '—')[:48]} | "
            f"{_fmt(r['top_views'])} | {(r['top_channel'] or '—')[:22]} |"
        )
    lines += ["", "## Notes", ""]
    for r in rows:
        lines.append(f"- **{r['name']}** ({r.get('region','')}, {r.get('scale','')}) — "
                     f"{r.get('note','')}")
    md = "\n".join(lines) + "\n"
    print(md)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
