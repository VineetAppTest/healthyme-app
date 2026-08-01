# Jarvis QC

Jarvis is the independent HealthyMe browser-QC layer. It moves through an approved route, records the full visible journey, captures browser telemetry and returns evidence that Victor can diagnose before Vineet approves a release.

## Operating pattern

`Approved route -> Playwright movement -> video and trace -> browser telemetry -> expected-versus-actual result -> diagnostic evidence`

This foundation is intentionally isolated under `qa/jarvis/`. It does not modify HealthyMe authentication, routing, session persistence, database logic or application UI.

## Included routes

### HM-PUBLIC-001

Confirms that the HealthyMe login surface loads and at least one configured authentication provider is visible. This route needs no credentials.

### HM-MEMBER-001

Performs the first critical authenticated journey:

1. Open HealthyMe Login.
2. Enter the dedicated member test account.
3. Submit Supabase login.
4. Confirm Member Home is visible and usable.
5. Refresh the browser.
6. Confirm the member remains logged in.

The approved route definition is stored in `routes/HM-MEMBER-001.yml`.

## Evidence produced

Every run creates:

- Full browser video
- Failure screenshot
- Playwright trace retained on failure
- HTML and JSON test reports
- A timestamped checkpoint timeline
- Console warnings and errors
- Failed browser requests
- HTTP error responses
- Browser navigation timing

The GitHub Actions workflow uploads the evidence as a retained workflow artifact.

## GitHub configuration

Create the following repository configuration before running the authenticated route:

- Repository variable `JARVIS_BASE_URL`
  - Example: `https://healthymeappbyankita.streamlit.app`
- Repository secret `JARVIS_MEMBER_EMAIL`
- Repository secret `JARVIS_MEMBER_PASSWORD`

Use a dedicated non-production test member. Never commit credentials to the repository.

Without the two member secrets, `HM-MEMBER-001` is skipped while the public login route still runs.

## Local execution

From `qa/jarvis`:

```bash
npm install
npx playwright install chromium
npm test
```

For an authenticated local run:

```bash
JARVIS_BASE_URL="https://healthymeappbyankita.streamlit.app" \
JARVIS_MEMBER_EMAIL="test-member@example.com" \
JARVIS_MEMBER_PASSWORD="replace-me" \
npm test
```

## Current diagnostic boundary

Version 0.1 captures user-visible behaviour and browser-side telemetry. Supabase, Sentry and server-side correlation will be added through a shared Jarvis run ID in the next stage. That correlation is what will convert a visible delay or failure into a stronger root-cause diagnosis.
