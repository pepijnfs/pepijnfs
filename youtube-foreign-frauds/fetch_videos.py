#!/usr/bin/env python3
"""Fetch videos and their transcripts for a YouTube channel.

Two data sources are used:

1. YouTube Data API v3 (official) -> lists the channel's uploaded videos.
   Requires a free API key. Set it via --api-key or the YOUTUBE_API_KEY env var.
   Get one at: https://console.cloud.google.com/apis/credentials
   (enable "YouTube Data API v3" for the project first).

2. youtube-transcript-api (open source) -> pulls the transcript for each video,
   including auto-generated captions. No key needed. The official Captions API
   is intentionally NOT used: it is OAuth-only and cannot read auto-generated
   captions, which is where most transcript text lives.

Example:
    export YOUTUBE_API_KEY=AIza...
    python fetch_videos.py --handle @ForeignFrauds
    python fetch_videos.py --channel-id UCxxxxxxxx --limit 25 --languages en en-US
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from youtube_transcript_api import YouTubeTranscriptApi

# Exception classes live at the package root in v1.0+, but be defensive so the
# script still imports on older/newer layouts.
try:
    from youtube_transcript_api import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError:  # pragma: no cover - fallback for layout changes
    from youtube_transcript_api._errors import (  # type: ignore
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )

API_BASE = "https://www.googleapis.com/youtube/v3"


# --------------------------------------------------------------------------- #
# YouTube Data API v3 helpers
# --------------------------------------------------------------------------- #
def _get(session: requests.Session, path: str, params: dict) -> dict:
    resp = session.get(f"{API_BASE}/{path}", params=params, timeout=30)
    if resp.status_code != 200:
        # The API returns a helpful JSON error body; surface it verbatim.
        raise RuntimeError(
            f"YouTube API {path} -> HTTP {resp.status_code}: {resp.text}"
        )
    return resp.json()


def resolve_channel(
    session: requests.Session,
    api_key: str,
    *,
    handle: str | None,
    channel_id: str | None,
) -> dict:
    """Return {'id', 'title', 'uploads_playlist_id'} for the channel."""
    params = {"part": "snippet,contentDetails", "key": api_key}
    if channel_id:
        params["id"] = channel_id
    elif handle:
        # forHandle accepts the handle with or without the leading '@'.
        params["forHandle"] = handle.lstrip("@")
    else:
        raise ValueError("Provide either --handle or --channel-id.")

    data = _get(session, "channels", params)
    items = data.get("items") or []
    if not items:
        raise RuntimeError(
            "No channel found. Double-check the handle/ID "
            f"({handle or channel_id})."
        )
    ch = items[0]
    return {
        "id": ch["id"],
        "title": ch["snippet"]["title"],
        "uploads_playlist_id": ch["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def list_uploaded_videos(
    session: requests.Session,
    api_key: str,
    uploads_playlist_id: str,
    *,
    limit: int | None,
) -> list[dict]:
    """Page through the uploads playlist, newest first."""
    videos: list[dict] = []
    page_token = None
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        data = _get(session, "playlistItems", params)
        for item in data.get("items", []):
            snip = item["snippet"]
            videos.append(
                {
                    "video_id": item["contentDetails"]["videoId"],
                    "title": snip["title"],
                    "published_at": item["contentDetails"].get(
                        "videoPublishedAt", snip.get("publishedAt")
                    ),
                    "description": snip.get("description", ""),
                }
            )
            if limit and len(videos) >= limit:
                return videos

        page_token = data.get("nextPageToken")
        if not page_token:
            return videos


# --------------------------------------------------------------------------- #
# Transcript helper
# --------------------------------------------------------------------------- #
def fetch_transcript(
    ytt_api: YouTubeTranscriptApi,
    video_id: str,
    languages: list[str],
) -> dict:
    """Return {'status', 'language', 'segments', 'text'} for one video."""
    try:
        fetched = ytt_api.fetch(video_id, languages=languages)
        segments = fetched.to_raw_data()  # [{'text','start','duration'}, ...]
        return {
            "status": "ok",
            "language": getattr(fetched, "language_code", languages[0]),
            "segments": segments,
            "text": " ".join(s["text"] for s in segments).strip(),
        }
    except TranscriptsDisabled:
        return {"status": "transcripts_disabled", "segments": [], "text": ""}
    except NoTranscriptFound:
        return {"status": "no_transcript_in_language", "segments": [], "text": ""}
    except VideoUnavailable:
        return {"status": "video_unavailable", "segments": [], "text": ""}
    except Exception as exc:  # noqa: BLE001 - keep the batch running
        return {"status": f"error: {exc}", "segments": [], "text": ""}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--handle", help="Channel handle, e.g. @ForeignFrauds")
    src.add_argument("--channel-id", help="Channel ID, e.g. UCxxxxxxxx")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("YOUTUBE_API_KEY"),
        help="YouTube Data API key (or set YOUTUBE_API_KEY).",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max number of videos to fetch (default: all).",
    )
    parser.add_argument(
        "--languages", nargs="+", default=["en"],
        help="Preferred transcript languages, in priority order (default: en).",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("data"),
        help="Output directory (default: ./data).",
    )
    parser.add_argument(
        "--sleep", type=float, default=0.0,
        help="Seconds to pause between transcript fetches (be polite / avoid blocks).",
    )
    args = parser.parse_args()

    if not args.api_key:
        parser.error(
            "No API key. Pass --api-key or set YOUTUBE_API_KEY. "
            "The transcript step needs no key, but listing the channel's videos does."
        )

    session = requests.Session()
    ytt_api = YouTubeTranscriptApi()

    print("Resolving channel...", file=sys.stderr)
    channel = resolve_channel(
        session, args.api_key, handle=args.handle, channel_id=args.channel_id
    )
    print(f"  {channel['title']}  ({channel['id']})", file=sys.stderr)

    print("Listing uploaded videos...", file=sys.stderr)
    videos = list_uploaded_videos(
        session, args.api_key, channel["uploads_playlist_id"], limit=args.limit
    )
    print(f"  {len(videos)} videos", file=sys.stderr)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir = args.out_dir / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)

    with_transcript = 0
    for i, video in enumerate(videos, 1):
        vid = video["video_id"]
        print(f"[{i}/{len(videos)}] {vid}  {video['title'][:70]}", file=sys.stderr)
        result = fetch_transcript(ytt_api, vid, args.languages)
        video["transcript_status"] = result["status"]
        video["transcript_language"] = result.get("language")
        video["transcript"] = result["text"]

        if result["status"] == "ok":
            with_transcript += 1
            # Save each transcript as its own plain-text file for easy reading.
            (transcripts_dir / f"{vid}.txt").write_text(
                result["text"], encoding="utf-8"
            )
        else:
            print(f"    -> {result['status']}", file=sys.stderr)

        if args.sleep:
            time.sleep(args.sleep)

    # One combined JSON file with everything (metadata + full transcript text).
    out_json = args.out_dir / "videos.json"
    out_json.write_text(
        json.dumps(
            {"channel": channel, "videos": videos},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"\nDone. {with_transcript}/{len(videos)} videos had a transcript.\n"
        f"  JSON:        {out_json}\n"
        f"  Transcripts: {transcripts_dir}/<video_id>.txt",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
