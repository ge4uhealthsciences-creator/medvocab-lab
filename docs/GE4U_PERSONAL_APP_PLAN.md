# GE4u Personal Learning App — plan

Status: design, not built. Date: 3 Nov 2026.

## Goal

A web app (installable on phones as a PWA) where each learner studies the GE4u packs they bought, and an AI tutor personalises the practice through a GE4u-hosted Gemini backend. Learners only tap **Đồng ý** once; they never handle API keys.

## What already exists and is reused

- Pack data format: `data/packs/<id>.json` — groups → `[term, IPA, Vietnamese, definition, example]` plus a `review` record. Paid pack data stays in the private store, never in this public repo.
- Shared word parts: `data/word-parts.json`.
- Learning UI: `scripts/pack_template.html` (flashcards with speech, drag-and-drop matching, quiz, gap fill, word parts, saved progress). The app grows out of this template.
- Roadmap and order (basic sciences → clinical): `data/packs/curriculum.json`.

## How AI is provided (revised: learners only tap "Đồng ý")

Learners are not technical, so they must not create or paste API keys. Default design:

1. **GE4u-hosted AI.** The app sends tutor requests to a small GE4u backend (Google Apps Script web app first; Firebase later if load grows). The backend holds GE4u's own Gemini key in Script Properties and calls the cheapest suitable model (Flash-Lite class).
2. **One consent screen.** The first time a learner opens an AI feature they see a short Vietnamese notice (what is sent: only the terms being studied and their answers; no name, phone or email) and tap **Đồng ý**. No key, no code.
3. **Paid Gemini tier, not the free tier.** Google's pricing page states free-tier content is used to improve Google's products and paid-tier content is not (https://ai.google.dev/gemini-api/docs/pricing). For learners' data, use the paid tier.
4. **Limits per licence.** Each licence code gets a daily AI quota (for example a number of tutor turns per day) enforced by the backend, so one pack sale cannot create open-ended AI cost.
5. **Optional for advanced users only:** an "Use my own Gemini key" switch in Settings, hidden by default.

Cost note (check current prices before launch): Flash-Lite class pricing is listed per million tokens; a short tutor turn is roughly a thousand tokens, so per-learner daily cost is small but not zero. A one-time 99k pack cannot fund unlimited AI forever: either keep a daily cap, include AI for a fixed period (e.g. 3 months), or sell an AI add-on.

Without network or consent, every non-AI feature still works offline.

## Personalisation features (in order of value)

1. **Spaced repetition** (no AI needed): each term gets a due date from the learner's answers (SM-2 style). The home screen shows "Ôn hôm nay: N từ".
2. **Weak-term drills** (AI): Gemini writes new example sentences and distractor options for the terms the learner keeps missing, at their level.
3. **Explain my mistake** (AI): after a wrong answer, a short Vietnamese explanation comparing the confused terms, using the word parts (e.g. *-itis* vs *-osis*).
4. **Clinical role-play** (AI): short patient–doctor or pharmacist–patient dialogues using the pack's terms; the learner types or speaks a reply and gets feedback.
5. **Pronunciation check** (later): browser speech recognition compares the learner's spoken term with the target.

All AI output is checked against the pack data before it is shown (the target term must appear; Vietnamese meaning must match the pack), so the tutor cannot drift from the verified vocabulary.

## Access control for paid packs

- Today: each pack is a single offline HTML file sent after payment (can be shared on).
- App phase: a buyer receives a licence code; the app downloads the pack data only with a valid code. Options to evaluate: Google Apps Script + Sheet (already in use for orders) as a tiny licence service, or Firebase (a `firebase/` folder already exists in the repo).

## Build steps

1. Turn the template into a PWA shell: pack library, offline cache, progress in IndexedDB.
2. Add spaced repetition and the "Ôn hôm nay" queue.
3. Add the Apps Script AI backend (paid Gemini tier, quota per licence) and the consent screen, then features 2 and 3 above.
4. Add licence codes for paid packs.
5. Role-play and pronunciation.

## Open decisions for the owner

- Daily AI quota per licence and how long AI is included with a pack (cost is on GE4u).
- Whether to sell an AI add-on after the included period.
- Licence approach (Apps Script vs Firebase).
