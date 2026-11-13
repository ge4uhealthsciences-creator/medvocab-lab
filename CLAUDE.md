# GE4u – medvocab-lab

Read **AUTOPILOT.md** first: it lists what Claude may do on its own in this repo and what it must never do.

- Use gh REST only in Claude sessions (GraphQL is blocked).
- Daily media: GitHub Release `media-YYYY-MM-DD` (MP4s, plan.json, posted.json). Live per-post status: `status/today.csv` on branch `status`.
- Free poster: `social-post/post.py` (+ `.github/workflows/social-post.yml`). Video render: `social-video/` (+ `social-video.yml`, 18:00 VN).
- TikTok: posted by `social-post/post.py` via TikTok Content Posting API (secrets TIKTOK_CLIENT_KEY/SECRET/REFRESH_TOKEN, repo variable TIKTOK_PRIVACY). Ids in `marketing/tiktok-studio-scheduled.json` (manual Studio uploads) are skipped.
- Game: `ge4u-hospital-3d.html` (three.js r128) + `ge4u-game-gate.js` (Firebase project medical-english-b8ff5).
