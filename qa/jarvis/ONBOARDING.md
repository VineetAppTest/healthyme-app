# Jarvis Team Onboarding

Jarvis is HealthyMe's independent QC and diagnostic role. Victor defines and governs the approved route, Jarvis executes it and produces evidence, and Vineet remains the final approval authority.

## Operating pattern

`Approved requirement -> route contract -> controlled execution -> video and telemetry -> expected-versus-actual result -> Victor diagnosis -> Vineet approval`

Jarvis is not a second product owner and must not invent expected behaviour. Every automated journey must be backed by an approved route manifest under `routes/`.

## Onboarding status

| Requirement | Status | Notes |
|---|---|---|
| Playwright browser runtime | Ready | Chromium is installed by GitHub Actions. |
| Streamlit Cloud application driver | Ready | Direct pages and cross-origin Streamlit iframes are supported. |
| Public read-only route | Ready | `HM-PUBLIC-001`. |
| Member login and refresh route | Code ready | `HM-MEMBER-001`; dedicated member secrets are still required. |
| Video, screenshots and traces | Ready | Video always; screenshot and trace on failure. |
| Browser and network diagnostics | Ready | Console, page errors, failed requests, HTTP errors and selected request timings. |
| Frame-aware performance timing | Ready | Navigation entries are collected from the host and app frames. |
| Environment preflight | Ready | Validates URL, reachability, suite selection and credential completeness. |
| Unique Jarvis run identity | Ready | Every CI execution receives a `JARVIS_RUN_ID`. |
| GitHub evidence bundle | Ready | Retained for 14 days. |
| Dedicated test member | Pending owner setup | Must be created and controlled by Vineet. |
| Supabase/Sentry correlation | Not yet active | The run ID is sent as a browser header, but backend systems do not yet persist it. |
| Flutter/mobile execution | Not included | Requires Maestro or Appium in the Flutter repository. |
| Automated visual-design judgment | Not included | Current routes use explicit assertions; screenshots/video support Victor's review. |

## Required dedicated member account

The account used by Jarvis must meet all of the following:

1. It is created only for automated QC.
2. Its HealthyMe role is `member`.
3. It contains no real member, health, consultation or personally sensitive data.
4. It does not require OTP, CAPTCHA or manual approval during routine sign-in.
5. Its account remains active and its password is not reused elsewhere.
6. Its test state is documented and kept stable.
7. Future mutation routes use data that can be reset deterministically.

Do not use Vineet's, an administrator's or an actual member's account.

## GitHub configuration owned by Vineet

Repository: `VineetAppTest/healthyme-app`

### Repository variable

`JARVIS_BASE_URL`

Recommended value:

`https://healthymeappbyankita.streamlit.app`

The workflow has this production URL as a safe default, so the variable is optional unless Jarvis must target another environment.

### Repository secrets

`JARVIS_MEMBER_EMAIL`

`JARVIS_MEMBER_PASSWORD`

Secrets must be entered directly in GitHub repository settings. They must never be pasted into a route file, pull request, issue, workflow log or chat message. GitHub does not allow the secret value to be read back after storage.

## First authenticated commissioning run

Run the `Jarvis Playwright QC` workflow manually with:

- Suite: `member`
- Base URL: leave empty to use the repository/default URL
- Require authenticated: `true`

The commissioning run passes only when:

1. Preflight confirms both member secrets are configured.
2. HealthyMe is reachable.
3. Secure Login is visible in the actual application frame.
4. The dedicated account reaches Member Home.
5. Logout is visible, proving the page is interactive.
6. Browser refresh retains the authenticated member session.
7. Video, report, timeline and browser diagnostics are uploaded.

## Evidence standard

Every Jarvis route must produce enough evidence for a developer to reproduce or narrow a failure:

- Route ID and Jarvis run ID
- Git commit and execution environment
- Host URL and application-frame URL
- Timestamped checkpoints
- Total elapsed time
- Frame navigation timing
- Browser console warnings/errors
- Uncaught page errors
- Failed requests
- HTTP error responses
- Timings for document, fetch and XHR responses
- Full execution video
- Failure screenshot
- Playwright trace on failure
- HTML and JSON results

Sensitive authentication query parameters and bearer tokens are redacted before diagnostic attachment.

## Safety boundaries

Jarvis may perform read-only navigation and dedicated-account authentication without additional approval when the route manifest is approved.

Jarvis must not perform any of the following until a separately approved test-data and reset mechanism exists:

- Submit health assessments
- Publish recommendation profiles
- Send messages or emails
- Create or modify schedules
- Upload member documents
- Delete or deactivate records
- Change roles or access
- Execute payment, salary or irreversible business actions
- Test against real member data

A mutation route must define its starting data, expected database effect, cleanup/reset action and rollback behaviour.

## Known limitations

### 1. Browser evidence is not full root-cause telemetry

Jarvis can identify where the visible journey slowed or failed and can capture browser/network evidence. It cannot prove a database, Supabase, Streamlit or server-side root cause until those systems record the same `JARVIS_RUN_ID`.

### 2. Authentication challenges requiring a human are not autonomous

OTP, CAPTCHA, hardware keys, consent prompts or manual email-link approval interrupt unattended automation. A test-only bypass or controlled test authentication mechanism would be required.

### 3. Streamlit Cloud can introduce external delay

Cold starts, hosting queues, iframe loading and provider redirects can affect timing independently of HealthyMe code. Jarvis records these separately where possible, but one run is not enough to establish a performance regression. Performance decisions should use repeated runs and a baseline percentile.

### 4. Selectors still depend on an approved UI contract

The driver tolerates the currently approved login wording alternatives, but major redesigns can require selector updates. Stable accessibility names or dedicated test IDs will reduce maintenance.

### 5. Video explains visible behaviour, not hidden business correctness

A correct-looking screen can still contain incorrect database state. Business-critical routes must later add API/database assertions against isolated test data.

### 6. Playwright does not test the Flutter Android application

Flutter needs its own Jarvis Mobile adapter using Maestro or Appium, an emulator/device and APK build artifacts.

### 7. Automated visual quality is currently rule-based

Jarvis can detect missing elements, overflow using explicit checks and screenshot differences once baselines exist. It does not yet independently judge whether a design is aesthetically good.

### 8. GitHub-hosted runners differ from member devices

Runner geography, CPU, bandwidth, browser version and screen size differ from Vineet's Android device and normal desktop browser. Device-specific failures require a device farm or local runner.

### 9. Evidence retention is finite

GitHub artifacts are retained for 14 days in the current workflow. Important release evidence must be preserved elsewhere if longer retention is required.

## Definition of Jarvis settled

Jarvis is considered operational for HealthyMe web QC when all of the following are true:

- Public route passes on two consecutive runs.
- Dedicated member secrets are configured.
- Authenticated login/refresh route passes on two consecutive runs.
- Vineet reviews one complete evidence bundle.
- Victor confirms route results are understandable and actionable.
- No credential or sensitive-data leakage is found in logs/artifacts.
- PR #310 is approved and merged.

## Next capability layers

1. Add Admin login and dashboard route using a separate dedicated admin account.
2. Add server-side run-ID correlation to Streamlit/Sentry/Supabase diagnostics.
3. Establish repeated latency baselines and regression thresholds.
4. Add controlled test-data reset before any mutation journeys.
5. Add visual layout assertions and approved screenshot baselines.
6. Add Jarvis Mobile to `healthyme-flutter-member`.
7. Reuse the framework for Wagewise only after its source-of-truth workflows are reconstructed.
