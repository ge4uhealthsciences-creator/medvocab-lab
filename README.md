# MedVocab Lab

A lightweight Medical English practice site with flashcards, a searchable word bank, a quick quiz, and a daily micro-lesson.

## Features
- Responsive static website; no database or server required.
- Medical vocabulary includes IPA, Vietnamese meaning, definitions and examples.
- Daily lesson page loads `data/daily-lesson.json`.
- GitHub Actions builds and publishes to GitHub Pages on each push and on a daily schedule.
- With no API key, the lesson generator rotates a curated starter bank at no API cost.
- Optional OpenAI API generation can be enabled with a repository secret; API usage may incur charges.

## Publish
1. Open repository **Settings → Pages**.
2. Choose **GitHub Actions** as the deployment source if it is not selected.
3. Open **Actions → Daily lesson and deploy**. A push to `main` should trigger the workflow automatically.
4. After a successful deployment, find the exact public URL in **Settings → Pages** or the deploy job summary.

The scheduled run is configured for 23:00 UTC (06:00 Vietnam time). GitHub scheduled workflows may be delayed.

## Optional AI generation
1. Create an API key in OpenAI Platform and review billing and usage limits.
2. Add a repository secret named `OPENAI_API_KEY` under **Settings → Secrets and variables → Actions**.
3. Run the workflow manually and inspect the log. If the API request fails, the generator uses the curated fallback bank.

Never put API keys in source files. Do not enable paid API generation unless you accept possible charges.

## Limitations
- This is an educational prototype, not clinical decision support.
- AI-generated medical content must be reviewed by a qualified subject-matter expert before official use.
- No checkout, payment, email delivery, customer analytics, or guaranteed revenue is included.
- GitHub Pages and Actions limits depend on GitHub's current plan and policies.
