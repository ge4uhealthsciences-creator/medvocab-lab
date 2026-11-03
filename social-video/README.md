# GE4u social video pipeline

Phase: **views & reach only**. No prices, sales links, purchase or registration CTAs.

## What it does

Every day it produces 12 vertical videos (1080×1920, 30 fps, AI voiceover, burnt-in text), one per discipline, 4 per platform:

| Platform | Format | Length | Primary metric |
|---|---|---|---|
| TikTok | "Pronounce it": hook → 3-2-1 → term ×2 → IPA, Vietnamese meaning, definition, example → "your turn" | ~16 s | avg watch time, full-video-watched rate |
| Instagram Reels | "3-second quiz": hook → definition + A/B/C → countdown → reveal → example | ~13 s | non-follower reach, shares |
| YouTube Shorts | "3 terms": hook → 3 terms with IPA, meaning, definition → "how many did you know?" | ~22 s | views, avg view duration |

The discipline→platform assignment shifts each day, so every discipline rotates through all three platforms. Hook variants rotate by slot and are logged in the plan (`hook_variant`) for hook experiments.

## Files

- `ge4u_video.py` — `plan` builds the day's plan JSON; `render` produces the MP4s.
- `setup_tts.sh` — downloads sherpa-onnx + Kokoro (offline TTS) from GitHub releases.
- `../data/social-video-bank.json` — extra vocabulary (20 terms per discipline), merged with the existing channel data and the Dental pack.
- `../.github/workflows/social-video.yml` — renders daily at 04:30 Vietnam time, validates, publishes the MP4s as GitHub Release `media-YYYY-MM-DD` (public URLs for Metricool), keeps the last 7 releases, and records the plan under `marketing/video-plans/`.

Scheduling into Metricool is done by a separate daily Claude task that reads the release, checks for duplicates, and schedules each item at its slot time. This keeps rendering, scheduling, daily lessons and orders independent.

## Run locally

```bash
bash social-video/setup_tts.sh
python3 social-video/ge4u_video.py plan --date 2026-11-04 --out out/2026-11-04
python3 social-video/ge4u_video.py render --plan out/2026-11-04/plan.json
```
