# GE4u Organic Reach Queue — 4–10 November 2026

**Current phase: VIEWS & REACH ONLY.** Optimize for views, reach/impressions, non-follower reach, watch time, average view duration, completion, replays, shares and organic follower growth. Likes, comments and saves are secondary. No sales language, product/course/material promotion, prices, purchase or registration CTAs, inbox-to-buy prompts, sales links or paid ads.

## Daily learning — verified 4 November

- Lesson: **Nursing English** — Patient monitoring.
- Objective: review three core terms and complete one knowledge check.
- Vocabulary: **vital signs**, **wound dressing**, **intake and output**.
- Quiz answer: **vital signs**.
- Source: `data/daily-lesson.json`, valid JSON; date matches 2026-11-04; exactly three vocabulary entries and one valid multiple-choice quiz.
- Previous day's discipline: Pharmacy. No consecutive discipline repeat.
- `daily-lessons.html` renders a real built-in fallback before the network request; the fallback contains all 12 disciplines and selects Nursing for 4 November. Invalid, stale or unavailable JSON leaves the fallback visible rather than a permanent loading state.

## Repository and deployment checks

- Catalogue: 12 product IDs, all unique. All 24 `sample_url` and `practice_url` paths resolve to repository files.
- Latest Pages workflow: [run 41752250180](https://github.com/ge4uhealthsciences-creator/medvocab-lab/actions/runs/41752250180) — build, tests, artifact upload and deploy job succeeded.
- The live page was not independently verified from this run because the external page request failed at DNS/network resolution. Do not claim live-page verification until it is opened successfully.
- Views/reach safeguards merged:
  - [PR #4](https://github.com/ge4uhealthsciences-creator/medvocab-lab/pull/4), merge `6781cca458009bdcce354d2c17f38e9a5ef67c76`: Facebook direct publishing and legacy promo publishing disabled; generated video plans now use `views & reach only`; validation rejects sales wording and CTA flags.
  - [PR #5](https://github.com/ge4uhealthsciences-creator/medvocab-lab/pull/5), merge `f9c3d827208c806b3025801178dda37830567179`: strips legacy sales-promo lines from old plan captions before Instagram, Threads or YouTube publishing.

## Metricool publishing status — checked 4–11 November

28 planner entries were returned: **11 active scheduled posts and 17 drafts**. PENDING is not published.

### Active scheduled posts

- **Threads — 8 PENDING:** 4 Nov 09:00 Midwifery; 4 Nov 19:40 Anatomy; 5 Nov 09:00 Social Work; 5 Nov 19:40 Medical word parts; 6 Nov 19:40 Physiology; 7 Nov 19:40 Internal Medicine; 8 Nov 19:40 cross-discipline question; 9 Nov 19:40 study-skills quiz. Six legacy Threads captions were rewritten as educational-only content; two existing educational posts were retained.
- **TikTok — 3 PENDING:** 4 Nov 10:00 physical examination (Medical English); 5 Nov 10:00 umbilical cord (Midwifery); 6 Nov 10:00 sterilisation (Pharmaceutical Technology). These use existing MP4 assets, public visibility and platform-specific titles. The Psychology/insomnia video remains a draft pending the next timing check.

### Drafts — not counted as scheduled or published

- Instagram: 4 Reels drafts, now Instagram-only; Facebook was removed from these cross-posts.
- TikTok: 1 remaining video draft.
- YouTube: 4 Shorts drafts.
- Facebook: 8 drafts; **zero active Facebook scheduled posts**. Facebook remains excluded until the owner explicitly re-enables it.
- Pinterest: no Pins or drafts.

No new visual post was scheduled without usable media. The three TikTok drafts were promoted to scheduled posts only after confirming MP4 media, public visibility settings, captions and titles. Instagram and YouTube drafts remain held because the direct GitHub publisher already covers those channels; avoid parallel scheduling until the publishing path is reconciled.

## Observed performance — 28 October to 3 November

| Platform | Published content and observed results | Missing or unreliable metrics |
|---|---|---|
| Threads | 9 posts; **357 post views**, **239 account views**, 4 likes; net follower change 0. Best educational posts by observed views: Pharmacy 38, Nursing 31, Dentistry 29. | Reach, non-follower reach and watch metrics unavailable. Shares/reposts/replies are mostly null; no reliable total. |
| Instagram | 6 Reels; **43 views** and 40 summed post-level reach (not unique account reach); 0 likes, comments, saves or shares. Raw average-watch-time values ranged 0.582–7.468; connector did not specify units. | Non-follower reach unavailable. Three-second view-rate values were 0–5.9%; this is not full completion. |
| TikTok | 6 videos; **8 views** and **2 new followers**. Highest observed video: 5 views. | Reach returned 0; full-video-watched rate and average watch time were missing. |
| YouTube | 6 published videos appeared in the period; evolution reported **0 views**. | Per-video views, watch minutes and average view duration were null. |
| Pinterest | 0 impressions and 0 saves; no Pins returned. | No post-level data. |

One already-published Threads promotional post on 3 November contributed 197 of the 357 views. It is out of the current phase and must not be repeated; do not treat its performance as a content recommendation.

## Best-time recommendations — 4–10 November

Metricool ranking scores (not predicted views):

- Instagram: Friday 6 Nov 10:00 (6,734); Wednesday 4 Nov 10:00 (6,506); Thursday 5 Nov 10:00 (6,275).
- TikTok: Thursday 5 Nov 10:00 (1,471); Wednesday 4 Nov 10:00 (1,432); Friday 6 Nov 10:00 (1,379).
- YouTube: Wednesday 4 Nov 16:00 (12,033); Thursday 5 Nov 16:00 (11,979); Friday 6 Nov 16:00 (10,698).
- Threads and Pinterest: no recommendation returned by the connected endpoint.

## Publishing workflow health

- The last checked [Social auto-post run](https://github.com/ge4uhealthsciences-creator/medvocab-lab/actions/runs/41749578435) completed successfully but posted **0** items because no content was due at that run time. Its log showed the Meta token check failing for Instagram and Facebook; Threads and YouTube connections were present.
- Facebook is now disabled in the GitHub publisher code; legacy promotional posts are disabled. The old 4 November plan is sanitized at publish time. New daily video plans will contain no sales CTA and will fail validation if sales wording returns.
- The direct GitHub publisher does not post TikTok; it prepares TikTok assets for TikTok Studio. Metricool is currently scheduling the three TikTok posts above.

## Next experiments

1. Compare a direct question hook against a misconception hook; keep the rest of the video comparable.
2. Test 12–18 seconds against 20–25 seconds; prioritize average watch time and full-video completion rather than likes.
3. Put the question and readable subtitles in frame one; remove slow logo intros.
4. Change the visual every 2–3 seconds and reveal the answer before the final quarter of the video.
5. Keep a balanced rotation across all 12 disciplines; do not allow Dentistry to dominate consecutive posts.
6. Compare the 10:00 TikTok slot across the three scheduled days before changing the posting time.

## Order workflow — source/configuration only

- `google-apps-script/Code.gs` and `ORDER_NOTIFICATION_SETUP.md` were inspected. The source expects `GE4U_ORDERS_SHEET_ID` in Apps Script Script Properties and a deployed Web App `/exec` URL.
- The email is an order notification, not payment confirmation. No payment verification or automatic digital delivery is claimed.
- The Apps Script property, deployment and end-to-end email/Sheet flow were not independently verified. Owner action: confirm the property, update the existing Web App deployment to a new version, then run an owner-authorized test. No fake order or private customer data was used.

## Owner actions

1. Refresh the Meta token for Instagram. Keep Facebook excluded; do not re-enable it as part of token repair.
2. Review the 8 Facebook drafts in Metricool; leave them as drafts or remove them manually if no longer needed.
3. Verify the live Daily Practice page from a normal browser session; the GitHub Pages workflow succeeded, but this run could not independently open the live page.
4. Complete the owner-authorized Apps Script configuration and end-to-end test described above.
