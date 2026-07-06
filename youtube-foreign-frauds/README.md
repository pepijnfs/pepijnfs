# Foreign Frauds — YouTube fetcher

`fetch_videos.py` lists a channel's uploaded videos and pulls each one's transcript.

## Setup
```bash
pip install -r requirements.txt
export YOUTUBE_API_KEY=AIza...   # https://console.cloud.google.com/apis/credentials
```

## Run
```bash
python fetch_videos.py --handle @ForeignFrauds
python fetch_videos.py --channel-id UCxxxxxxxx --limit 25 --languages en en-US --sleep 0.5
```

Outputs:
- `data/videos.json` — channel + per-video metadata and full transcript text
- `data/transcripts/<video_id>.txt` — one plain-text transcript per video

## How it works
- **Video list:** YouTube Data API v3 (`channels.list` → uploads playlist → `playlistItems.list`). Needs an API key. Host: `www.googleapis.com`.
- **Transcripts:** the open-source [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) (v1.0+ instance API). No key; gets auto-generated captions. Host: `www.youtube.com`. The official Captions API is deliberately avoided — it is OAuth-only and cannot read auto-generated captions.

## Where it can run
- **Locally (MacBook):** both halves work.
- **Claude Code on the web (this cloud environment):** the video-listing half reaches `www.googleapis.com` fine, but the transcript half is **blocked** — the environment's network policy denies outbound connections to `www.youtube.com`. Run the transcript step locally, widen the environment's allowed domains to include `www.youtube.com`, or route `youtube-transcript-api` through a proxy (`WebshareProxyConfig`).
