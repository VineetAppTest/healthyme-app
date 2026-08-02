# Jarvis UAT Privacy, Test Data and Approval Rules

## Purpose

Jarvis may process UAT screens and records only long enough to validate an approved route. It must report findings without reproducing member names, emails, phone numbers, health details, schedules, recommendation content or other identifiable values.

## Evidence lifecycle

The default mode is `strict`.

- No video is recorded.
- No screenshot is recorded.
- No Playwright trace is recorded.
- Request and response bodies are never collected.
- Browser diagnostics use redacted URLs and fingerprints instead of raw console or error text.
- GitHub receives only a de-identified job summary containing route, status, duration, retry count and gate outcome.
- `actions/upload-artifact` is not used.
- All temporary evidence is deleted before the GitHub-hosted runner completes.

`diagnostic` mode may create failure-only media on the temporary runner. It is still not uploaded to GitHub and is deleted before completion.

A GitHub-hosted runner cannot automatically download evidence onto Vineet's laptop. Direct local receipt would require a separately approved self-hosted runner on a controlled computer. Until then, the safe operating model is no retained evidence file.

## UAT identities and committed fixtures

The repository contains only aliases and synthetic identifiers:

- `UAT_MEMBER_A` mapped to `jarvis_member`
- `UAT_ADMIN_A` mapped to `jarvis_admin`

Emails, passwords, phone numbers and health details are prohibited in committed fixtures. Credentials remain GitHub Actions Secrets.

## Read-only approval rule

Read-only execution is allowed only when:

1. The route has an approved route manifest.
2. The environment is classified correctly.
3. Credentials are complete for the requested role.
4. Strict privacy mode is used by default.
5. Production execution, when requested, has its explicit approval checkbox.

Read-only execution may inspect UAT data but may not report raw values.

## Mutation approval rule

Mutation execution is allowed only in UAT and requires both gates:

1. Repository variable `JARVIS_MUTATION_ENABLED=true`.
2. The workflow's `mutation_approved` checkbox is selected for that run.

Every mutation route must:

- Use only approved synthetic identities.
- Use the `jarvis_uat_` namespace for created records.
- Register every created record in the ephemeral mutation ledger.
- Mark every created record cleaned before completion.
- Mark the mutation route complete.

A missing ledger, incomplete route marker or uncleared synthetic record fails the workflow and blocks deployment eligibility.

## Deployment rule

Jarvis never deploys application code.

It may only evaluate whether an external deployment workflow is eligible. Eligibility requires:

- All approved routes passed without retries being hidden.
- Evidence-security scan passed with zero findings.
- Synthetic UAT cleanup passed.
- Production mutation was not attempted.
- Vineet's explicit owner approval was recorded when deployment intent was requested.

The deployment action remains outside the Jarvis workflow.

## Reporting standard

Allowed finding format:

- Route ID
- Failed checkpoint
- Expected behaviour category
- Actual behaviour category
- Severity
- Duration
- Reproducibility
- Jarvis run ID

Prohibited reporting:

- Member or admin names
- Emails or phone numbers
- Authentication identifiers or tokens
- Assessment answers
- Health conditions
- Meal, exercise or supplement details
- Schedule details
- Recommendation content
- Raw database rows
- Raw page, console or network payloads

## Current boundary

This change establishes the policy, fixture validation, two-key mutation gate, cleanup ledger, de-identified summary, evidence deletion and deployment evaluation. Existing routes remain read-only. Individual mutation and end-to-end routes must be added separately with their own approved manifests and route-specific cleanup implementation.
