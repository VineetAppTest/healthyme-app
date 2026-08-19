# HealthyMe Next.js Migration Contract — 2026-08-19

## Objective

Replace the Streamlit presentation/application layer progressively with a Next.js frontend deployed independently on Vercel, while preserving HealthyMe's existing Supabase backend and accepted product behaviour.

## Non-negotiable preservation boundary

The migration must not replace or casually modify:

- the existing HealthyMe Supabase project;
- production database tables, IDs or historical records;
- Supabase Auth identities or authentication outcomes;
- Row Level Security policies;
- storage contracts;
- canonical `hm_users` authorization and role semantics;
- member/admin business rules and lifecycle states;
- accepted navigation outcomes and direct-route behaviour;
- publish, completion, acknowledgement, journal or allocation logic.

Any backend change that becomes genuinely necessary must be proposed separately, justified, reviewed and regression-tested. A frontend migration task does not implicitly authorize a backend change.

## Replacement pattern

`Existing Streamlit workflow -> reproduce in Next.js -> compare behaviour -> focused UAT -> accept -> retire only that Streamlit workflow`

The old and new frontend may coexist against the same backend during migration.

## Architecture

- Existing Streamlit application: functional reference until retired workflow-by-workflow.
- New web frontend: Next.js App Router + TypeScript in `/web`.
- Hosting target: Vercel with repository Root Directory `/web`.
- Backend: existing HealthyMe Supabase project.
- Supabase web authentication: cookie-based SSR using `@supabase/ssr` and the project's publishable key.
- Privileged keys: never shipped to browser code.

## Branding

Product branding is centralized behind configuration. `HealthyMe` remains the default product name until a replacement brand is approved after naming/domain/trademark clearance. A branding decision must not block the technical migration.

## Migration gates

### Gate 0 — Foundation

- Next.js application exists in parallel under `/web`.
- Current framework conventions are used.
- Supabase browser/server client plumbing exists.
- Vercel can target `/web` without changing Streamlit deployment.
- No production backend writes or schema changes.

### Gate 1 — Authentication/session parity

Reproduce the currently accepted HealthyMe outcomes:

- Supabase sign-in;
- durable browser session/reload behaviour;
- secure sign-out;
- canonical `hm_users` mapping;
- Admin vs Member routing;
- direct-page return behaviour;
- inactive/unauthorized user rejection;
- no silent re-login after explicit logout.

Do not retire the Streamlit login until this gate passes focused browser UAT.

### Gate 2 — Admin shell and Admin Dashboard

Reproduce accepted Admin navigation, profile/header behaviour, dashboard information and responsive presentation without changing underlying data or actions.

### Gate 3 onward — workflow migration

Proceed in controlled slices: Member/Profile workflow, Meal Builder, Exercise Allocation, Supplement Allocation, Repository/remaining Admin workflows, then member web workflows if retained.

## Validation standard

Every migrated slice must pass:

1. Next.js lint;
2. TypeScript type check;
3. production build;
4. relevant existing regression coverage;
5. new focused browser tests for the migrated screen/workflow;
6. manual UAT against the accepted Streamlit behaviour.

No old workflow is retired merely because the new page renders successfully.

## Rollback rule

Until a slice is explicitly accepted, the Streamlit implementation remains the fallback/reference. Migration changes are isolated from `main` until reviewed and merged.
