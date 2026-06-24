# CODEX Flutter Repository Strategy Audit

Audit date: 2026-06-24
Repository: `VineetAppTest/healthyme-app`
Branch: `codex-flutter-repo-strategy-audit`
FMOT reviewed against: MCD v1.8 - Supabase-Aligned Production Architecture

## 1. Executive Summary

The current repository appears to be Streamlit-only / Streamlit-first, not Flutter-ready and not a mixed Streamlit plus Flutter repository.

The visible repository contains a Python Streamlit application with `app.py`, `pages/`, `components/`, `requirements.txt`, `runtime.txt`, Auth0/OIDC login handling, Supabase persistence helpers, admin/member Streamlit pages, and local/sample JSON state. A Flutter scaffold was not found in the checked root or common subdirectory paths.

Recommendation: keep the current repository focused on Streamlit Full Admin and create a separate Flutter repository for the Flutter Member App after Vineet approves the repository strategy and Victor approves the MCD/FMO acceptance criteria. This reduces risk to the existing admin app, keeps mobile/web build pipelines independent, and gives Cody cleaner branch and PR boundaries.

## 2. Current Repository Findings

Evidence reviewed that supports a Streamlit-first reading:

- `requirements.txt` contains `streamlit==1.52.2`, `pandas`, `openpyxl`, `supabase>=2.0.0`, `authlib==1.6.5`, and `requests>=2.31.0`.
- `runtime.txt` pins `python-3.11`.
- `app.py` is the Streamlit entry point and routes authenticated users to Streamlit pages.
- `pages/01_Login.py` implements the visible login page and calls Streamlit OIDC/Auth0 login.
- `pages/10_Admin_Dashboard.py` is a Streamlit admin dashboard.
- `components/auth_session.py` restores app sessions using Streamlit/OIDC identity.
- `components/storage_backend.py` uses Supabase as a persistence backend and has local JSON fallback behavior.
- `components/normalized_store.py` supports Supabase-backed normalized tables such as `hm_users` and `hm_workflow`.
- `AGENTS.md` defines the target MCD direction: Flutter Member App, future Practitioner Lite, Streamlit Full Admin, and Supabase as backend backbone.
- `.gitignore` is present and already includes Flutter, Android, iOS, Python, Streamlit, environment, build, IDE, logs, and credential-like ignore rules.

Repository checks/searches performed:

- Direct reads of known Streamlit/admin files succeeded.
- Direct reads of common Flutter paths failed with not found responses.
- GitHub connector code searches for `pubspec`, `Flutter`, `Streamlit`, and `Supabase` returned no results, so code search did not provide reliable recursive inventory for this private repository.

## 3. Flutter Source Status

Flutter source files were not found in the checked paths.

Checked and not found:

- `pubspec.yaml`
- `lib/main.dart`
- `web/index.html`
- `android/app/build.gradle`
- `ios/Runner/Info.plist`
- `member_app/pubspec.yaml`
- `flutter_app/pubspec.yaml`
- `apps/member_flutter/pubspec.yaml`

Conclusion: no existing Flutter app scaffold is visible from the audited paths. If Flutter code exists elsewhere, its location should be explicitly provided before any Flutter task begins.

Safe options if Flutter files are absent:

- Option 1: Create a new dedicated Flutter repository after strategy approval.
- Option 2: Add a Flutter app under a clearly isolated folder in this repository after a monorepo decision is approved.
- Option 3: Pause Flutter implementation and first create a documentation-only MCD addendum defining repository ownership, auth boundaries, and CI/deployment gates.

The safest immediate option is documentation approval first, then a separate Flutter repository.

## 4. Option A: Monorepo

A monorepo would keep Streamlit Full Admin, Flutter Member App, future Practitioner Lite, Supabase migrations/docs, and MCD/docs in one GitHub repository.

Possible structure:

```text
healthyme-app/
  apps/
    streamlit_admin/
    flutter_member/
    flutter_practitioner_lite/
  supabase/
    migrations/
    policies/
  docs/
    mcd/
    fmots/
    audits/
```

Benefits:

- One repository for all code, docs, issues, branches, and PRs.
- Easier cross-reference between admin, Flutter, Supabase, and MCD changes.
- A single audit trail for Cody, Victor, and Vineet.
- Useful if the team wants one GitHub Issues board and tightly coupled releases.

Risks:

- Higher blast radius. A Flutter branch can accidentally touch Streamlit or Supabase files.
- More complex CI because Python/Streamlit, Flutter Android, Flutter iOS, Flutter Web, and Supabase checks need separate workflows and path filters.
- More noise in PR reviews because unrelated platforms live side by side.
- Harder permissions model if future contributors should touch only mobile or only admin.
- More deployment coupling even though Streamlit, mobile apps, web builds, and Supabase migrations have different release rhythms.

When it makes sense:

- Small team, one release manager, low contributor count.
- Strong path-based CI and branch rules are in place.
- Victor wants a single governance hub and accepts higher repository complexity.
- Flutter and Streamlit will share many generated contracts, fixtures, or docs in the same commits.

## 5. Option B: Separate Flutter Repository

A separate Flutter repository would keep the current repository focused on Streamlit Full Admin and create a new repository for the Flutter Member App.

Possible repository split:

```text
VineetAppTest/healthyme-app
  Streamlit Full Admin
  admin pages
  admin components
  Streamlit deployment files
  docs/audits relevant to current repo

VineetAppTest/healthyme-member-app
  Flutter Android Member App
  Flutter iOS Member App
  Flutter Web Member fallback
  mobile/web tests
  Flutter-specific CI and release notes

VineetAppTest/healthyme-platform-docs or docs in agreed primary repo
  MCD
  FMOT
  architecture decisions
  Supabase schema/RLS documentation
```

Benefits:

- Lower risk to the current working Streamlit admin app.
- Cleaner Cody execution boundaries: one task branch in the repo that owns the affected surface.
- Flutter CI, Android/iOS build checks, and web build checks can run without affecting Streamlit PRs.
- Streamlit deployment and Flutter release pipelines can evolve independently.
- Easier future permission boundaries and review routing.
- Cleaner mobile app history for app-store style release tracking.

Risks:

- Cross-repo coordination is needed for shared auth, schema, and workflow contracts.
- GitHub Issues/PRs need clear labels and links between repositories.
- MCD/FMOT docs need one agreed source of truth so repos do not drift.
- Shared types/contracts may need a documented process instead of casual copying.

When it makes sense:

- Streamlit Full Admin is already a working product surface.
- Flutter Member App is a new app surface with different build, test, release, and device requirements.
- Supabase Auth and RLS design must be stabilized before mobile implementation.
- The team wants clear review ownership and lower accidental-change risk.

## 6. Recommended Approach for HealthyMe

Recommendation: use separate repositories for the current Streamlit Full Admin and the new Flutter Member App.

For HealthyMe's current scale and risk profile, separate repositories are safer than turning the existing Streamlit repository into a monorepo. The current repository already contains working Streamlit flows and admin/member app state logic. Adding Flutter scaffolding here now would increase review noise and create accidental-change risk before the Supabase Auth, identity mapping, and RLS strategy is finalized.

Recommended model:

- Keep `VineetAppTest/healthyme-app` as the Streamlit Full Admin repository for now.
- Create a new `VineetAppTest/healthyme-member-app` repository for Flutter Android, iOS, and Web Member App after Vineet approves.
- Keep future Practitioner Lite deferred. When approved, decide whether it belongs inside the Flutter member repo as a second Flutter app/package or in a separate practitioner repo.
- Keep MCD/FMOT as the governing source of truth in one agreed location and reference it from all repos.
- Keep Supabase migrations/RLS documentation in a clearly governed location before Flutter implementation begins.

## 7. Proposed Folder / Repository Structure

Recommended separate-repository structure:

```text
VineetAppTest/healthyme-app/
  AGENTS.md
  app.py
  requirements.txt
  runtime.txt
  components/
  pages/
  data/
    db_sample.json
  docs/
    audits/
    mcd-references/
  .gitignore
```

```text
VineetAppTest/healthyme-member-app/
  AGENTS.md
  pubspec.yaml
  analysis_options.yaml
  lib/
    main.dart
    app/
    features/
      auth/
      dashboard/
      life_assessment/
      nsp/
      daily_food_journal/
      supplements/
      recommendations/
      scheduling/
    shared/
      supabase/
      routing/
      design_system/
  test/
  integration_test/
  android/
  ios/
  web/
  docs/
    implementation-notes/
    test-plans/
  .github/
    workflows/
```

```text
Future repository or approved Flutter workspace path:
VineetAppTest/healthyme-practitioner-lite/  (deferred)
  AGENTS.md
  pubspec.yaml
  lib/
  test/
  android/
  ios/
  web/
```

```text
Governance location, either dedicated or explicitly chosen:
VineetAppTest/healthyme-governance/  (recommended if cross-repo work grows)
  mcd/
  fmot/
  architecture-decisions/
  supabase/
    schema-docs/
    rls-docs/
    migration-plans/
  audits/
  acceptance-criteria/
```

If Vineet/Victor prefer not to create a governance repository yet, keep governance docs in `VineetAppTest/healthyme-app/docs/` and require every other repo to link back to the approved MCD/FMOT document.

## 8. Impact on Cody Execution Workflow

Under the recommended separate-repository model:

- Cody should work only in the repository named in the execution packet.
- Streamlit Full Admin tasks should branch from `VineetAppTest/healthyme-app`.
- Flutter Member App tasks should branch from `VineetAppTest/healthyme-member-app` after it exists.
- Supabase schema/RLS tasks should only run after Victor provides a schema/RLS execution packet and Vineet approves the migration scope.
- Every PR should state which repo owns the change, which MCD/FMOT section applies, and which protected flows were intentionally not touched.
- Cross-repo work should use linked GitHub Issues and PR references rather than mixing app changes in one PR.
- Cody should not create Flutter code in the Streamlit repo unless a later approved instruction explicitly changes the repository strategy.

Branch and PR model:

- One task, one branch, one PR in the owning repo.
- Use branch names such as `codex/<short-task>` or the exact branch requested by Vineet/Victor.
- Do not push directly to `main`.
- For cross-repo changes, create separate PRs and link them in the PR bodies.
- Victor reviews architecture/MCD alignment before Vineet merges.

## 9. Impact on MCD v1.8

MCD v1.8 does not necessarily need to mandate a monorepo. It should be updated or supplemented to clarify repository ownership and source-of-truth rules.

Recommended MCD/FMO addendum topics:

- Official repository map for Streamlit Full Admin, Flutter Member App, future Practitioner Lite, Supabase governance, and MCD/FMOT docs.
- Rule that Flutter member flows must use Supabase Auth as the target auth source.
- Rule that Auth0 remains transition-only for Streamlit/admin where already stable.
- Rule that Supabase service role keys are server-only and never appear in Flutter repositories.
- Rule for where Supabase migrations/RLS policies are reviewed and stored.
- Cross-repo PR linking and acceptance criteria requirements.

No code architecture change is needed from this report alone. The report only supports the repository strategy decision.

## 10. Next Sprint Recommendation

Recommended next safe sprint: Repository Strategy Approval and Flutter Repo Bootstrap Planning.

Sprint output should be documentation-first:

- Vineet chooses monorepo vs separate repository.
- Victor records the decision in MCD/FMOT or an architecture decision note.
- Define the exact new Flutter repository name if separate repo is approved.
- Define Flutter bootstrap acceptance criteria: no app logic beyond scaffold, Supabase Auth dependency plan, environment handling, web support, CI checks, and protected-flow boundaries.
- Define which Supabase schema/RLS docs the Flutter team can rely on.
- Only after approval, create the Flutter repository/scaffold in a new task branch and PR.

## 11. Files Changed

* `docs/CODEX_FLUTTER_REPO_STRATEGY_AUDIT.md`

## 12. Tests/Checks Run

Repository checks run:

- Read `AGENTS.md`.
- Read `.gitignore`.
- Read `requirements.txt` and `runtime.txt`.
- Read Streamlit entry/auth/admin/storage files: `app.py`, `pages/01_Login.py`, `pages/10_Admin_Dashboard.py`, `components/auth_session.py`, `components/storage_backend.py`, and `components/normalized_store.py`.
- Checked common Flutter scaffold paths: `pubspec.yaml`, `lib/main.dart`, `web/index.html`, `android/app/build.gradle`, `ios/Runner/Info.plist`, `member_app/pubspec.yaml`, `flutter_app/pubspec.yaml`, and `apps/member_flutter/pubspec.yaml`.
- Checked common Supabase/deployment/doc paths: `supabase/config.toml`, `supabase/migrations/README.md`, `render.yaml`, and `README.md`.
- Ran GitHub connector code searches for `pubspec`, `Flutter`, `Streamlit`, and `Supabase`; these returned no results, so direct file reads were used as the primary evidence.

Build/test status:

- No build, Flutter analyze, Flutter test, Streamlit runtime test, Supabase query, database migration, or RLS check was run.
- This was a documentation-only audit and no app code was changed.

## 13. Risks / Open Questions

Risks:

- The GitHub connector did not provide reliable repository-wide code search results for this private repository.
- The audit used direct reads of known and common paths, not a complete recursive tree listing.
- If Flutter files exist in an unusual folder, they were not visible in the checked paths.
- A separate Flutter repository creates coordination overhead unless MCD/FMOT source-of-truth rules are clear.
- A monorepo could work, but only with strong path-based CI, branch protections, and review ownership.

Open questions for Vineet/Victor:

- Should the Flutter Member App repository be named `healthyme-member-app`, `healthyme-flutter`, or something else?
- Should future Practitioner Lite live in the same Flutter repository as a second app, or in a separate repository when approved?
- Where should the canonical MCD/FMOT live once multiple repositories exist?
- Where should Supabase migrations, RLS policies, and schema docs be governed?
- Should the current repository be renamed later to clarify that it is Streamlit Full Admin, or should the existing name remain for continuity?
- What branch protection and required checks should be enabled before Flutter implementation starts?
