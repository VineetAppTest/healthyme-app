# Jarvis QC

Jarvis is the independent HealthyMe web-QC layer. It moves through an approved route, records the visible journey, captures browser telemetry and returns evidence that Victor diagnoses before Vineet approves a release.

## Operating pattern

`Approved route -> Playwright movement -> video and telemetry -> expected-versus-actual result -> diagnostic evidence`

The framework is isolated under `qa/jarvis/`. It does not modify HealthyMe authentication, routing, session persistence, database logic or application UI.

Read `ONBOARDING.md` for the complete setup, test-account policy, safety boundaries, commissioning gate and limitations.

## Included routes

### HM-PUBLIC-001

Confirms that HealthyMe is reachable and that the actual login application surface contains:

- Secure Login
- Email
- Password
- An approved Supabase sign-in action
- No public sign-up boundary

This route supports both a directly rendered application and the cross-origin iframe used by Streamlit Community Cloud. It requires no credentials and performs no sign-in. The app-surface driver permits one visible browser reload when a Community Cloud cold start stalls halfway through the wait.

### HM-MEMBER-001

Performs the first critical authenticated journey:

1. Open HealthyMe Login.
2. Resolve the application page or Streamlit iframe.
3. Enter a dedicated member test account.
4. Submit the approved Supabase sign-in action.
5. Confirm Member Home is visible and usable.
6. Refresh the host browser page.
7. Re-resolve the application surface.
8. Confirm the member remains logged in.

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

Authentication query parameters, opaque provider payloads, JWTs and bearer tokens are redacted from Jarvis diagnostic attachments. The workflow scans generated text evidence before upload and fails if an unredacted sensitive value or trace archive is found.

Playwright traces are disabled in CI because a raw trace can retain browser internals and authentication material that cannot be reliably sanitized. A developer may opt into a local-only trace with `JARVIS_ENABLE_LOCAL_TRACE=true` and must not upload it.

## GitHub configuration

The production URL is built into the workflow as a default. A repository variable is needed only to target another environment:

- `JARVIS_BASE_URL`

The authenticated route requires two repository secrets:

- `JARVIS_MEMBER_EMAIL`
- `JARVIS_MEMBER_PASSWORD`

Use a dedicated, non-sensitive QC member. Never commit or paste credentials into source files, issues, pull requests or logs.

Without both member secrets, the member route skips during ordinary PR validation. A manual run with `Require authenticated = true` fails preflight until both secrets exist.

## GitHub Actions execution

The workflow supports:

- Automatic public validation when Jarvis files change
- Manual `all`, `public` or `member` suite selection
- Optional environment URL override
- Optional strict requirement for authenticated credentials
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

For an authenticated local run, provide the three environment variables only in the local shell or an excluded local secret store.

## Current diagnostic boundary

Version 0.2 captures visible behaviour, frame-aware timing and browser/network telemetry. A shared `JARVIS_RUN_ID` is stored in the evidence bundle, but it is not sent to HealthyMe, Supabase or Sentry yet. Server-side instrumentation must first provide a same-origin, privacy-safe correlation mechanism.
