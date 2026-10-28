# GE4u Supabase foundation

STATUS: scaffold only. This does not create a Supabase project, deploy functions, provision credentials, or change the live GitHub Pages site. No secret values are stored in this repository.

## Architecture
- Public learning site remains static HTML on GitHub Pages.
- Supabase Auth provides learner identity.
- Profiles are created on Auth signup; every new account defaults to role learner.
- Admin authorization uses trusted Auth app_metadata.role = admin, never editable user_metadata.
- Postgres stores page views, learning events, and audit events with RLS enabled.
- admin-overview verifies the bearer token and trusted admin role before calling a service-role-only aggregate RPC.
- track-pageview validates configured Origin and payload. It does not store IP addresses or full referrer URLs.
- A failed data query must display unavailable, not zero.

## 1. Create a Supabase project
1. Create a project in the Supabase dashboard and store the database password in a password manager.
2. Record Project URL and publishable/anon key for client-side configuration. These are public identifiers, not service-role secrets.
3. Keep the service_role key private. Never put it in HTML, JavaScript, GitHub Pages artifacts, screenshots, commits, or public build variables.
4. Configure Auth site URL and allowed redirects for the actual production site. Enable email confirmation and suitable account security before real users sign up.

## 2. Apply database migration
Install Supabase CLI and run these commands from the repository root:
    supabase login
    supabase link --project-ref YOUR_PROJECT_REF
    supabase db push
Review the migration before applying it to production. Back up existing data first; do not replace an existing identity system without a migration plan.

## 3. Configure and deploy Edge Functions
Set the allowed website origin through Supabase Edge Function secrets; never commit actual values:
    supabase secrets set ALLOWED_ORIGINS="https://ge4uhealthsciences-creator.github.io"
Supabase provides SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY to hosted Edge Functions. For local development, keep any service-role key in a local ignored .env file and never paste it into chat or commit it.

Deploy:
    supabase functions deploy admin-overview
    supabase functions deploy track-pageview

The functions disable platform JWT verification because they implement their own checks: admin-overview verifies the bearer token with Auth and requires app_metadata.role = admin; track-pageview is public but validates Origin and input. Origin is not authentication and can be spoofed by non-browser clients, so rate limiting/abuse controls are mandatory before broad production use.

## 4. Bootstrap the first administrator
1. Register your own account through Supabase Auth after the sign-up flow is configured.
2. In Supabase Dashboard, open Authentication > Users and identify your account.
3. Grant app_metadata.role = admin using trusted server-side admin tooling. Never grant admin from browser code or user-editable metadata.
4. Sign out and back in to refresh the access token claims.
5. Verify a learner token gets HTTP 403 from admin-overview and an admin token receives metrics.

Do not add a default admin password, hardcoded admin email, or shared credential to the repository.

## 5. Metric definitions
- Page views: accepted page_view events in the selected range.
- Visits: distinct session IDs with at least one page view in the range.
- Unique visitors: distinct pseudonymous visitor IDs in the range. This is a browser-level estimate, not a person-level count.
- New accounts: profiles created during the range. Auth signups are reflected by the database trigger.
- Learning analytics: meaningful only after validated learning events are sent and consent/retention rules are finalized.

The aggregate RPC uses a half-open time range [start, end). The function currently uses UTC day boundaries; adapt it to an explicit Asia/Ho_Chi_Minh calendar day before showing Vietnam-local daily reports.

## 6. Production follow-ups
- Implement a consent banner and tracker with UUID visitor/session IDs; do not send events until consent requirements are respected.
- Add rate limiting and monitoring for track-pageview; Origin checks alone are not security.
- Add a JWT-validated track-learning-event function deriving user_id from the verified token, validating channel IDs against data/ge4u-product-catalog.json, and enforcing idempotency. Never trust a user ID sent by the browser.
- Configure CORS per environment and test production, local development, and preview URLs.
- Integrate the dashboard using only the public publishable/anon key; call admin endpoints with the signed-in user's access token.
- Keep admin UI behind Auth and server-side authorization. Never publish protected admin data or service-role credentials into _site/.
- Add tests for unauthenticated requests, learner-role denial, admin success, invalid payloads, and RLS boundaries.
- Review privacy notice, retention/deletion, consent, and applicable Vietnamese data protection requirements before collecting real learner data.

## Current status
| Capability | Status |
|---|---|
| Schema and RLS baseline | Prepared in migration |
| Signup profile trigger | Prepared |
| Admin overview Edge Function | Prepared, not deployed |
| Pageview ingestion Edge Function | Prepared, not deployed |
| Supabase project / credentials | Not configured |
| Frontend sign-in / consent / analytics wiring | Not implemented |
| Learning-event ingestion | Not implemented |
| Live account and visit numbers | Unavailable until deployment and integration |

Missing data or failed queries must never be treated as zero.
