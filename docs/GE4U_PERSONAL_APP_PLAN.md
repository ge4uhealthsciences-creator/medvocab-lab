# GE4u Personal Learning App — plan (Bring Your Own Gemini key)

Status: design, not built. Date: 3 Nov 2026.

## Goal

A web app (installable on phones as a PWA) where each learner studies the GE4u packs they bought, and an AI tutor personalises the practice using **the learner's own Google Gemini API key**. GE4u pays nothing for AI usage and never holds learners' keys on a server.

## What already exists and is reused

- Pack data format: `data/packs/<id>.json` — groups → `[term, IPA, Vietnamese, definition, example]` plus a `review` record. Paid pack data stays in the private store, never in this public repo.
- Shared word parts: `data/word-parts.json`.
- Learning UI: `scripts/pack_template.html` (flashcards with speech, drag-and-drop matching, quiz, gap fill, word parts, saved progress). The app grows out of this template.
- Roadmap and order (basic sciences → clinical): `data/packs/curriculum.json`.

## How the learner's Gemini key works

1. The learner creates a free key in Google AI Studio and pastes it into the app's Settings.
2. The key is stored only on that device (IndexedDB), never sent to GE4u. A "Remove key" button deletes it.
3. The app calls the Gemini API directly from the browser with that key. Requests contain only the terms being studied and the learner's answers, never personal data.
4. Without a key every non-AI feature still works offline.

Risks to state plainly in the app: anyone with access to the unlocked device can use the key; the learner controls the key's quota and billing in their Google account; AI answers can be wrong and are marked "AI".

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
3. Add Settings → Gemini key, then features 2 and 3 above.
4. Add licence codes for paid packs.
5. Role-play and pronunciation.

## Open decisions for the owner

- Which Gemini model and default limits per session (cost is on the learner's key).
- Whether to also offer a GE4u-paid AI plan later (would need a server and a price).
- Licence approach (Apps Script vs Firebase).
