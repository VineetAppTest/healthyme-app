# Jarvis Team Onboarding

Jarvis is HealthyMe's independent QC and diagnostic role. Victor defines and governs approved routes, Jarvis executes them and produces evidence, and Vineet remains the final approval authority.

## Operating pattern

`Approved requirement -> route contract -> controlled execution -> video and telemetry -> expected-versus-actual result -> evidence-security check -> Victor diagnosis -> Vineet approval`

Jarvis does not invent expected behaviour. Every automated journey must be backed by an approved route manifest under `routes/`.

## Current onboarding status

| Requirement | Status | Notes |
|---|---|---|
| Playwright browser runtime | Ready | Chromium is installed by GitHub Actions. |
| Streamlit Cloud driver | Ready | Direct pages and cross-origin Streamlit iframes are supported. |
| Public route | Commissioned | `HM-PUBLIC-001`. |
| Member identity | Commissioned | Dedicated confirmed Supabase Auth user mapped to active `member`. |
| Admin identity | Commissioned | Dedicated confirmed Supabase Auth user mapped to active `admin`. |
| Member login and refresh route | Commissioned | `HM-MEMBER-001`; passed twice without retry. |
| Admin login and refresh route | Commissioned | `HM-ADMIN-001`; passed twice without retry. |
| Role separation | Ready | Member lands on Member Home; admin lands on Admin Dashboard and not Member Home. |
| Video and failure screenshots | Ready | Video always; screenshot on failure. |
| Browser and network diagnostics | Ready | Console, page errors, failed requests, HTTP errors and selected timings. |
| Environment preflight | Ready | Validates URL, suite and both role credential pairs. |
| Unique run identity | Ready | Every CI execution receives a `JARVIS_RUN_ID`. |
| Evidence privacy controls | Ready | Authentication material is redacted and evidence is scanned before upload. |
| GitHub evidence bundle | Ready | Retained for 14 days. |
| Supabase/Sentry correlation | Not active | Run ID remains evidence-only until same-origin backend instrumentation exists. |
| Flutter/mobile execution | Not included | Requires a separate Maestro or Appium adapter. |
| Mutation testing | Not authorised | Requires deterministic test data and reset/rollback controls. |

## Dedicated identities

Jarvis uses two separate identities:

### Member Jarvis

- HealthyMe ID: `jarvis_member`
- Role: `member`
- Purpose: member login, Member Home, safe navigation and refresh persistence
- Data policy: synthetic and non-sensitive only

### Admin Jarvis

- HealthyMe ID: `jarvis_admin`
- Role: `admin`
- Purpose: admin login, Admin Dashboard shell, role separation and refresh persistence
- Restriction: read-only route; no member-detail or health-data pages

Jarvis must never use Vineet's account, a real member account, an operational administrator account or a super-admin identity.

## GitHub configuration

Repository: `VineetAppTest/healthyme-app`

### Optional repository variable

- `JARVIS_BASE_URL`

The workflow already defaults to the HealthyMe production URL. Set this variable only when targeting another environment.

### Required repository secrets

- `JARVIS_MEMBER_EMAIL`
- `JARVIS_MEMBER_PASSWORD`
- `JARVIS_ADMIN_EMAIL`
- `JARVIS_ADMIN_PASSWORD`

Secrets must be stored only in GitHub Actions Secrets. They must never be pasted into route files, pull requests, issues, workflow variables, logs or chat.

## Available suites

- `public`: login-surface availability only
- `member`: member login, landing and refresh persistence
- `admin`: admin login, landing, role separation and refresh persistence
- `all`: public, member, admin and evidence-redaction contracts

## Commissioning evidence

The secured two-role build completed two consecutive runs without retry.

### Run 1

- Admin route: 21.3 seconds
- Member route: 19.7 seconds
- Public route: 8.6 seconds
- Tests: 5 passed
- Evidence-security findings: 0

### Run 2

- Admin route: 16.0 seconds
- Member route: 15.1 seconds
- Public route: 6.6 seconds
- Tests: 5 passed
- Evidence-security findings: 0

Both runs confirmed all four secrets were available, both role pairs were enabled, dependencies had no reported vulnerabilities, TypeScript checks passed and evidence upload completed.

## Evidence standard

Every Jarvis route should produce enough evidence to reproduce or narrow a failure:

- Route ID and Jarvis run ID
- Git commit and execution environment
- Host URL and application-frame URL
- Timestamped checkpoints
- Total elapsed time
- Frame navigation timing
- Console and page errors
- Failed requests and HTTP error responses
- Document, fetch and XHR timings
- Full execution video
- Failure screenshot
- HTML and JSON results
- Post-run evidence-security result

Authentication query parameters, provider payloads, JWTs, bearer tokens and sensitive nested values are redacted. Raw Playwright traces are excluded from CI because they cannot be reliably sanitized.

## Safety boundaries

Jarvis may perform dedicated-account authentication and read-only navigation when an approved route manifest exists.

Jarvis must not perform these actions until a separately approved test-data and reset mechanism exists:

- Submit health assessments
- Publish or allocate recommendation profiles
- Send messages or emails
- Create, modify or cancel schedules
- Upload member documents
- Create, deactivate or delete users
- Change roles or access
- Modify packages, payments or business records
- Test against real member health data

Every future mutation route must define its starting state, expected database effect, verification, cleanup/reset action and rollback behaviour.

## Known limitations

1. Browser evidence identifies where a visible journey slowed or failed, but does not prove a Supabase, database, Streamlit or server root cause.
2. OTP, CAPTCHA, hardware keys, consent prompts and manual email-link approval interrupt unattended automation.
3. Streamlit cold starts, iframe loading, hosting queues and provider redirects can affect timings independently of HealthyMe code.
4. Major UI redesigns may require selector maintenance unless stable test IDs or accessibility names are provided.
5. Video proves visible behaviour, not hidden database correctness.
6. Playwright tests HealthyMe web only; Flutter needs Jarvis Mobile with Maestro or Appium.
7. GitHub runner geography, CPU, bandwidth and browser differ from actual member devices.
8. Evidence is retained for 14 days unless archived elsewhere.
9. Third-party console and network noise still requires Victor's classification.
10. Admin production automation remains deliberately limited because admin pages may expose real member information.

## Definition of Jarvis settled for current web scope

Jarvis is operational for HealthyMe web authentication and landing-page QC when:

- Public, member and admin routes are implemented.
- Separate member and admin identities are configured.
- Both authenticated routes pass twice without retry.
- Role separation is confirmed.
- Evidence-security checks pass with zero findings.
- Vineet reviews the result and approves PR #310 for merge.

All technical commissioning conditions above are complete. PR approval and merge remain Vineet-controlled.

## Next capability layers

1. Add safe protected-route navigation for member and admin workflows.
2. Add privacy-safe run-ID correlation to Streamlit, Supabase and Sentry.
3. Establish repeated latency baselines and regression thresholds.
4. Build deterministic synthetic test data and reset controls before mutation journeys.
5. Add approved screenshot baselines and visual layout assertions.
6. Add Jarvis Mobile to the Flutter repository.
7. Reuse the framework for Wagewise after its source-of-truth workflows are reconstructed.
