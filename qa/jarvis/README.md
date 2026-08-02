# Jarvis QC

Jarvis is the independent HealthyMe web-QC layer. It moves through approved routes, records the visible journey, captures browser telemetry and returns evidence that Victor diagnoses before Vineet approves a release.

## Operating pattern

`Approved route -> Playwright movement -> video and telemetry -> expected-versus-actual result -> evidence-security check -> diagnostic evidence`

The framework is isolated under `qa/jarvis/`. It does not modify HealthyMe authentication, routing, session persistence, database logic or application UI.

Read `ONBOARDING.md` for the full account policy, safety boundaries, commissioning status and limitations.

## Included routes

### HM-PUBLIC-001

Confirms that HealthyMe is reachable and that the actual login surface contains Secure Login, Email, Password and an approved Supabase sign-in action. It requires no credentials and performs no sign-in.

### HM-MEMBER-001

Uses the dedicated Jarvis member identity to verify:

1. Secure Login is available.
2. Member credentials are accepted.
3. The role lands on Member Home.
4. Logout is available.
5. Browser refresh preserves the member session.

### HM-ADMIN-001

Uses the dedicated Jarvis admin identity to verify:

1. Secure Login is available.
2. Admin credentials are accepted.
3. The role lands on Admin Dashboard.
4. Main Workflows and Logout are available.
5. Member Home is not shown to the admin identity.
6. Browser refresh preserves the admin session.

The admin route is intentionally read-only and does not open member-detail or health-data pages.

Approved route definitions are stored under `routes/`.

## Evidence produced

Every execution can create:

- Full browser video
- Failure screenshot
- HTML and JSON test reports
- Jarvis run metadata
- Timestamped checkpoint timeline
- Host and application-frame navigation timing
- Console warnings and errors
- Uncaught page errors
- Failed browser requests
- HTTP error responses
- Document, fetch and XHR timing
- Evidence-security verification result

Authentication query parameters, provider payloads, JWTs and bearer tokens are redacted. Generated text evidence is scanned before upload and the workflow fails if an unredacted sensitive value or trace archive is found.

Playwright traces are disabled in CI because raw traces can retain browser internals and authentication material that cannot be reliably sanitized.

## GitHub configuration

Optional repository variable:

- `JARVIS_BASE_URL`

Required repository secrets:

- `JARVIS_MEMBER_EMAIL`
- `JARVIS_MEMBER_PASSWORD`
- `JARVIS_ADMIN_EMAIL`
- `JARVIS_ADMIN_PASSWORD`

Member and admin identities must be separate, active, confirmed Supabase Auth users mapped to separate `hm_users` roles. Never commit or paste credentials into source files, issues, pull requests or logs.

## GitHub Actions execution

The workflow supports:

- Automatic validation when Jarvis files change
- Manual `all`, `public`, `member` or `admin` suite selection
- Optional environment URL override
- Optional strict requirement for requested authenticated credentials
- Environment and credential preflight
- TypeScript validation
- Locked dependencies and critical dependency audit
- Chromium execution
- Post-run evidence privacy enforcement
- A 14-day evidence bundle

## Local execution

From `qa/jarvis`:

```bash
npm ci
npm run typecheck
npm run preflight
npx playwright install chromium
npm test
npm run verify:evidence
```

For authenticated local runs, provide credentials only through the local shell or an excluded local secret store.

## Current diagnostic boundary

Version 0.3 captures visible behaviour, role-specific landing, refresh persistence, frame-aware timing and browser/network telemetry for public, member and admin routes. A shared `JARVIS_RUN_ID` is stored in evidence, but is not yet correlated with HealthyMe, Supabase or Sentry server telemetry.
