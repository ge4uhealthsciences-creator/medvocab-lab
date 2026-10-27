# GE4u Admin & Developer Control Center

## Status
This folder contains a **local-only UI prototype and implementation notes**. It is not a production admin system. It has no authentication, database, backend API, live analytics, or live GitHub Actions data. Do not use it to manage real learner accounts.

## Deployment boundary
The current `.github/workflows/deploy.yml` copies only root-level `*.html` files into `_site/` and then publishes that folder to GitHub Pages. Keep this admin prototype nested under `admin/`; do not change the workflow to copy this folder into the public site.

The repository itself is public, so the prototype source is visible to anyone who can read the repository. It contains no secrets and no real learner data. This folder boundary is not a security control for production administration.

## Verified repository architecture (at implementation time)
- Public learning experience is a static HTML/CSS/JavaScript site.
- Channel/product metadata is stored in `data/ge4u-product-catalog.json`; the current catalogue lists 12 disciplines.
- Daily lesson generation is performed by `scripts/generate_channel_daily.py`.
- `.github/workflows/deploy.yml` builds on pushes to `main`, manual dispatch, and a scheduled cron; it runs `scripts/test_ge4u_site.py` and deploys GitHub Pages.
- The current workflow exposes no learner database, unified login, persisted cross-device learning progress, admin API, or server-side role authorization.
- `google-apps-script/Code.gs` is an order-notification endpoint, not a user identity or learning analytics backend. Its deployment configuration must be reviewed separately.

## Required production architecture
1. **Identity and roles**: use a maintained identity provider; define admin and learner roles; require server-side authorization on every protected endpoint; deny by default. Hiding a link or adding a client-side password is not authorization.
2. **Data layer**: persist users, channel entitlements, learning sessions, quiz attempts, vocabulary reviews, and audit events. Define data minimization, consent, retention, export and deletion policies.
3. **Learner APIs**: learners can read/update only their own profile and learning records. Verify ownership server-side; never trust a user ID sent by the browser alone.
4. **Admin APIs**: require an admin role and record privileged actions. Use pagination, filters, rate limits and safe error responses.
5. **Secrets**: store credentials in server environment/managed secrets, never in HTML, client JavaScript, repository files, logs, or public build artifacts.
6. **Learning analytics**: calculate metrics from persisted events. Display source and last-updated time. Show an explicit unavailable state if a source fails; do not fabricate live metrics.
7. **Operations**: query GitHub Actions workflow runs and deployments server-side or through a controlled integration; store only the minimal response needed; expose health, last successful build, commit SHA, failure summaries, and data freshness.
8. **Audit log**: append-only where feasible; record actor, action, target, UTC timestamp, outcome and request/correlation ID. Exclude passwords, tokens, OTPs and unnecessary personal data.
9. **Production hosting**: place the authenticated admin app behind a real auth boundary and a backend. Do not publish protected dashboards to GitHub Pages as if static files can be private.

## Suggested data entities
- `users`: id, identity_provider_subject, display_name, status, created_at
- `roles` / `user_roles`: role assignments
- `channel_entitlements`: user_id, channel_id, source, starts_at, expires_at, status
- `learning_events`: event_id, user_id, channel_id, event_type, item_id, result, occurred_at, schema_version
- `audit_events`: actor_id, action, target_type, target_id, outcome, request_id, occurred_at
- `service_checks`: service, status, checked_at, source, detail_code

Avoid storing more personal data than the product needs. Do not store plaintext passwords.

## Suggested API contract
- `GET /api/admin/overview`: aggregated metrics plus `source`, `as_of`, and per-source status.
- `GET /api/admin/channels`: channel catalogue and entitlement counts.
- `GET /api/admin/users?cursor=&q=&status=`: paginated, minimized user records.
- `GET /api/admin/analytics?from=&to=&channel=`: aggregates computed from learning events.
- `GET /api/admin/audit?cursor=&source=&from=&to=`: paginated audit events.
- `GET /api/admin/operations`: workflow run summary, commit SHA, deployment state, API health and freshness.
- Each endpoint must enforce admin role server-side, validate inputs, apply rate limits, and return an explicit unavailable/error state when a source is missing.

## Verification checklist
- [ ] Confirm the identity provider and production hosting target.
- [ ] Implement and test server-side role enforcement and object-level authorization.
- [ ] Add database migrations and retention controls.
- [ ] Add learning-event ingestion with duplicate/idempotency protection.
- [ ] Add admin API tests (unauthenticated, learner role, admin role, cross-user access).
- [ ] Add tests that ensure secrets and admin assets never enter public `_site/`.
- [ ] Connect GitHub Actions status and show the last successful refresh time.
- [ ] Run security review and regression tests before production release.
