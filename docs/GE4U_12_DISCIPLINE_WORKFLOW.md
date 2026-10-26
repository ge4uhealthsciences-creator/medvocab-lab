# GE4u 12-Discipline Workflow Architecture

## Goal
Maintain one shared learning platform with 12 discipline-specific content streams. Do not maintain 12 separate codebases or copy/paste page templates.

## The 12 disciplines
1. Dentistry — Dental English
2. Medicine — Medical English
3. Pharmacy — Pharmacy English
4. Nursing — Nursing English
5. Midwifery — Midwifery English
6. Social Work — Healthcare Social Work
7. Pharmaceutical Chemistry
8. Pharmaceutical Technology
9. Traditional Medicine
10. Public Health
11. Psychology
12. Nutrition

## Source-of-truth data
- `data/dental-english-pack.json`: dentistry terms and quiz.
- `data/ge4u-channel-samples.json`: the other 11 channels, each with its own terms, definitions, examples, and channel-specific quizzes.
- `ge4u-channel.html?channel=<id>`: shared sample-page renderer. Channel IDs and data are the contract; don't create 12 duplicated HTML pages.

## Daily automation
1. A scheduled GitHub Actions run starts at 23:00 UTC (06:00 Vietnam time), and also runs on pushes to `main` or manually.
2. `scripts/generate_channel_daily.py` selects a discipline deterministically, rotating through all 12 on a 12-day cycle.
3. The script assembles 3 vocabulary items and one quiz from curated source data; it does not generate unsupported clinical claims with an LLM.
4. `scripts/test_ge4u_site.py` checks the 12 case scenarios, channel IDs, channel-specific quiz shape, and the generated daily lesson.
5. GitHub Pages publishes only if the build and regression checks pass.
6. `daily-lessons.html` renders the generated lesson from `data/daily-lesson.json`.

## Editorial and safety gates
- Automated checks validate structure and answer-key consistency, not the full clinical accuracy of every statement.
- New or changed clinical definitions, explanations, or case content must be reviewed against course-approved or authoritative references by a qualified reviewer before being treated as clinically authoritative.
- If data fails validation, fail the build rather than silently publish broken or empty content.
- Keep public marketing copy, order status, and product availability consistent with the actual backend state.
- Never commit access tokens, email credentials, OTPs, customer contact data, or payment details.

## Content pipeline (target operating model)
`Source data → Discipline template → Automated validation → Editorial/subject review when needed → GitHub Pages deployment → Analytics and learner feedback → Versioned content improvement`

## Current scope
Automated daily lesson rotation and regression checks are implemented in the repository. Social posting, account creation, customer analytics, payments, and delivery automation are separate integrations and are not active merely because the website deploys.
