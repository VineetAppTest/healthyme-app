# AGENTS.md

# HealthyMe App — AI Agent Operating Instructions

This repository is governed by the HealthyMe Migration Control Document (MCD) and the latest approved FMOT.

All AI agents, coding assistants, reviewers, and execution tools must follow these instructions before modifying code.

---

## 1. Core Rule

Do not make architecture, authentication, data model, security, or flow-level changes without explicit approval.

The agent may execute assigned tasks, but must not independently redesign the product.

No coding should begin unless the task is aligned to the latest approved MCD/FMOT and the sprint scope is clear.

---

## 2. Current Architecture Direction

HealthyMe follows a Supabase-aligned production architecture.

Target architecture:

- Flutter Member App for Android and iOS
- Flutter Web Member App as supported fallback access
- Future Flutter Practitioner Lite App, architecturally enabled but deferred
- Streamlit Full Admin for deep administrative work
- Supabase as the backend backbone
- Render as preferred hosting layer for Streamlit/admin services
- Sentry as preferred monitoring/error tracking layer
- Resend as preferred transactional email layer
- GitHub as source control and delivery governance layer

---

## 3. Authentication Direction

Supabase Auth is the target authentication source for:

- Flutter Android Member App
- Flutter iOS Member App
- Flutter Web Member App
- Future Practitioner Lite App

Auth0 is not the long-term member authentication target.

Auth0 may remain only as a legacy/transition layer for existing Streamlit Full Admin if already implemented and stable.

Do not introduce new Auth0 dependency into Flutter member flows unless explicitly approved.

Do not migrate Streamlit Full Admin authentication casually. Any Auth0-to-Supabase Auth migration must be treated as a dedicated migration gate.

---

## 4. Backend Source of Truth

Supabase is the source of truth for:

- PostgreSQL database
- Authentication
- Storage
- Row-Level Security policies
- Member identity mapping
- Practitioner/member access control
- Backup and recovery layer

Do not bypass Supabase RLS protections.

Do not use client-side checks as the only access-control mechanism.

Do not expose the Supabase service role key in Flutter, Streamlit UI code, logs, commits, or frontend-accessible environments.

---

## 5. Streamlit Full Admin Position

Streamlit Full Admin remains responsible for deep administrative work.

Protected Streamlit responsibilities include:

- Member evaluation
- Partial assessment report
- Admin five-page assessment
- Final report generation
- Governance
- Repository management
- Analytics
- Historical reporting
- Admin-only review and correction flows

Do not move Streamlit Full Admin responsibilities into Flutter unless explicitly approved in the MCD.

---

## 6. Practitioner Lite Position

Practitioner Lite is architecturally enabled but deferred.

It may be considered in the future for lightweight practitioner actions, such as:

- Member review
- Quick notes
- Schedule review
- Basic intervention visibility
- On-the-go practitioner actions

Practitioner Lite must not replace Streamlit Full Admin.

Do not build Practitioner Lite features unless specifically assigned.

---

## 7. Member Web App Position

Flutter Web Member App is a supported fallback access channel.

The primary member experience remains mobile-first through Flutter Android and iOS.

The same member account should work across:

- Android app
- iOS app
- Web member app

All member-facing channels must use Supabase Auth as the target authentication layer.

---

## 8. Protected HealthyMe Flows

Do not modify these flows unless the assigned task explicitly requires it:

- Login and logout
- Member dashboard
- Life Assessment Form (LAF)
- NSP Page 1
- NSP Page 2
- Daily Food Journal
- Supplements
- Recommendations
- Scheduling and rescheduling
- Sessions ledger
- Package/subscription visibility
- Partial assessment report
- Admin five-page assessment
- Final report generation
- Body-Mind Connection activation/gating
- Version/build label visibility rules

Any change to these flows requires focused regression testing.

---

## 9. Key Business Logic Rules

Preserve the following known rules unless the MCD explicitly changes them:

### 9.1 Body-Mind Connection

Body-Mind Connection activation is manual and should occur only after the five admin pages are completed and Save & Generate Final Report is executed.

Activation from one path must disable the second path.

There must be no auto-unlock.

### 9.2 Reassessment / Task Request

Reassessment wording should use “Task Request.”

Member-facing copy should say that the nutritionist has allocated a task.

Task Request scope includes NSP Page 1 and NSP Page 2 only unless explicitly changed.

### 9.3 LAF Second Instance

Do not introduce a second instance of LAF.

Second-instance logic applies to NSP Page 1 and NSP Page 2 only as already agreed.

### 9.4 Daily Food Journal

Preserve the agreed Daily Food Journal behavior, including:

- Meals: Breakfast, Lunch, Snacks, Dinner, Bedtime
- “Other” is not the preferred label; use “Snacking” where applicable
- Poop rounds use dropdown default “Select”
- Blank full-day save is disallowed
- Date change should refresh displayed data
- Supervision note is admin-entered and member-visible for the day

### 9.5 Supplements

Preserve active/stopped supplement history.

Stopped supplements should remain visible in admin history.

Member should see active regimen only unless otherwise assigned.

Frequency and timing validation must remain intact.

### 9.6 Scheduling

Member rescheduling is allowed up to 1 second before the session start time from the member UX perspective.

Cost/session-consumption rules:

- More than 24 hours before scheduled time: no-cost reschedule
- Within 24 hours to 1 second before scheduled time: original session is treated as consumed/cancelled and the new session is additionally consumed

Do not alter this rule unless explicitly approved.

---

## 10. Version Label Rule

For HealthyMe admin builds, the version/build label must be visible under or adjacent to the HealthyMe brand on every page after admin login.

Do not display the version label in member login.

Do not place the version label in unrelated informational sections.

Do not remove version visibility from admin pages.

---

## 11. Security Rules

Never commit:

- `.env` files
- Supabase service role keys
- Auth0 secrets
- Resend API keys
- Sentry DSN if marked private
- Personal health data
- Member private records
- PDF reports containing real member data
- Database dumps containing real data

Use environment variables and platform secrets.

Do not log sensitive personal health data.

Do not expose member data in debug output.

Do not create broad public storage buckets unless explicitly approved.

Do not disable RLS unless the task explicitly requires temporary local debugging and the change is not committed.

---

## 12. Supabase Auth Migration Gates

Any migration from Auth0-member flows to Supabase Auth must include the following gates:

### Gate 1: Identity Mapping

Each member must map correctly to:

- Member email
- Member profile record
- Supabase Auth user ID
- Role
- Status
- Subscription/package status

### Gate 2: Role Mapping

Minimum roles:

- Member
- Practitioner
- Admin

Future roles may include:

- Practitioner Lite
- Read-only Admin
- Super Admin

### Gate 3: RLS Validation

Validate that:

- Members can access only their own records
- Practitioners can access only authorized/assigned member records
- Admins can access authorized admin records
- Unauthenticated access is blocked
- Storage files are protected by ownership and role policies

### Gate 4: Auth Regression

Test:

- Login
- Logout
- Session persistence
- Password reset
- Expired session handling
- Invalid credential handling
- Inactive/blocked member handling
- Cross-device login
- Web login

### Gate 5: Data-Access Regression

Test member visibility and saving behavior for:

- Dashboard
- LAF
- NSP Page 1
- NSP Page 2
- Daily Journal
- Recommendations
- Supplements
- Scheduling
- Sessions/package visibility
- Reports visible to member
- Storage/file access

---

## 13. Coding Scope Rules

When assigned a task:

1. Touch only files required for the task.
2. Avoid broad refactors unless explicitly requested.
3. Preserve existing working behavior.
4. Do not rename tables, columns, routes, files, or functions without approval.
5. Do not alter database schema unless explicitly asked.
6. Do not change UI wording unless included in the task.
7. Do not introduce new dependencies without stating why.
8. Do not remove fallback or error-handling behavior without approval.

---

## 14. Branch and Pull Request Rules

Do not push directly to `main`.

Use a dedicated branch for every task.

Recommended branch naming:

- `codex/<short-task-name>`
- `fix/<short-issue-name>`
- `sprint/<sprint-name>`
- `mcd/<architecture-update>`

Every pull request or patch summary must include:

- Task objective
- Files changed
- What changed
- What was intentionally not changed
- Tests/checks run
- Known risks
- Manual validation steps

---

## 15. Required Output After Every Coding Task

After completing a task, provide this summary:

```text
Task:
<what was assigned>

Files changed:
- <file path>
- <file path>

What changed:
- <change 1>
- <change 2>

What was not changed:
- <protected area 1>
- <protected area 2>

Tests/checks run:
- <test/check>
- <test/check>

Risks:
- <risk or "None known">

Manual validation needed:
- <step 1>
- <step 2>
```

---

## 16. Build and Test Expectations

For Flutter work, run when applicable:

- `flutter analyze`
- `flutter test`
- Android debug build check
- Web build check if web-facing behavior changed

For Streamlit work, run when applicable:

- Import check
- Page load check
- Auth/session check
- Admin flow smoke test
- Member flow smoke test where affected

For Supabase-related work, validate:

- Table access
- RLS policies
- Auth user mapping
- Storage access
- No service role key exposure

---

## 17. Documentation Rule

If a code change alters behavior, update the relevant documentation, sprint note, or implementation note.

Do not let code drift away from the MCD/FMOT.

If the task conflicts with the MCD, stop and raise the conflict instead of coding around it.

---

## 18. Decision Escalation

Escalate before coding if the task requires any of the following:

- Architecture change
- Authentication change
- RLS change
- Database schema change
- Production secrets/configuration change
- New paid service
- New user role
- New core flow
- Report-generation logic change
- Member data visibility change
- Practitioner/admin access model change

---

## 19. Operating Principle

HealthyMe must remain secure, stable, and flow-first.

Modules do not deliver value; flows do.

Do not optimize a module in a way that breaks an end-to-end flow.

The accepted architecture principle is:

```text
Flutter delivers member and future practitioner experiences.
Flutter Web provides member fallback access.
Streamlit Full Admin remains responsible for deep administrative work.
Supabase provides authentication, database, storage, RLS, and backup backbone.
Render hosts production web/admin services.
Sentry observes the platform.
Resend communicates for the platform.
GitHub governs the codebase.
Auth0 remains transition-only where already implemented.
```

---

## 20. Final Instruction

When unsure, do not assume.

Stop, summarize the uncertainty, and ask for explicit approval before changing protected logic.
