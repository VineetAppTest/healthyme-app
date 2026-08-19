# HealthyMe Next.js Migration Contract — 2026-08-19

> **Authority:** `docs/HEALTHYME_WEB_MIGRATION_SOURCE_OF_TRUTH.md` is the governing source of truth for this migration.  
> **Member blueprint:** `docs/HEALTHYME_MEMBER_JOURNEY_V1.md` governs the current member-first implementation.

## Objective

Replace the Streamlit presentation/application layer progressively with a Next.js frontend deployed independently on Vercel, while preserving HealthyMe's existing Supabase backend and accepted product behaviour.

The migration is a product-experience migration, not a cosmetic copy. Existing HealthyMe functionality remains the functional baseline, but the new frontend should improve information architecture, interaction clarity, responsiveness and the user's ability to understand what to do next.

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

`Existing Streamlit workflow -> understand functional/user intent -> redesign interaction in Next.js -> compare behaviour -> focused UAT -> accept -> retire only that Streamlit workflow`

The old and new frontend may coexist against the same backend during migration.

## Member experience principle — present what matters now

The member experience must not depend on the user remembering the app's structure, remembering where information is stored, or repeatedly hunting through menus to discover what applies to them.

The default experience should proactively surface the member's relevant information and next action from existing HealthyMe data. The frontend should answer, as directly as possible:

- **Now:** What applies to me at this moment?
- **Next:** What should I do next and when?
- **Later:** What is upcoming but does not require attention yet?
- **Done:** What have I already completed or acknowledged?

`Done` is never inferred from elapsed time or merely viewing a card; it requires an authoritative HealthyMe completion/acknowledgement state.

Examples include meals, supplements, exercise, consultations, allocated tasks, due dates and other member actions. Where existing plan data includes timing or dates, the frontend should use that context to surface the relevant item at the appropriate time rather than requiring the member to navigate to a separate plan page to discover it.

Proactive presentation should be useful rather than intrusive: prefer contextual cards, prioritized sections, badges and timely prompts over unnecessary blocking pop-ups. A member must still be able to browse the complete plan/history when needed.

## Architecture

- Existing Streamlit application: functional reference until retired workflow-by-workflow.
- New web frontend: Next.js App Router + TypeScript in `/web`.
- Hosting target: Vercel with repository Root Directory `/web`.
- Backend: existing HealthyMe Supabase project.
- Supabase web authentication: cookie-based SSR using `@supabase/ssr` and the project's publishable key.
- Canonical `hm_users` role resolution: server-side only, reproducing the current HealthyMe lookup without changing RLS.
- Privileged keys: never shipped to browser code.

## Branding

Product branding is centralized behind configuration. `HealthyMe` remains the default product name until a replacement brand is approved after naming/domain/trademark clearance. A branding decision must not block the technical migration.

The product name, logo and related visual identity must remain replaceable without changing application workflows, Supabase data contracts or business logic.

## Current migration gates — member first

### Gate 0 — Foundation

- Next.js application exists in parallel under `/web`.
- Current framework conventions are used.
- Supabase browser/server client plumbing exists.
- Vercel can target `/web` without changing Streamlit deployment.
- No production backend writes or schema changes.

### Member Gate M0 — Journey contract

- current functional inventory completed;
- lifecycle-aware target IA defined;
- Today / Plan / Log / More primary navigation defined;
- Now / Next / Later / Done doctrine defined;
- backend boundary confirmed.

### Member Gate M1 — Authentication/session/member-role parity

Reproduce the currently accepted HealthyMe outcomes:

- Supabase sign-in;
- durable browser session/reload behaviour;
- secure sign-out;
- canonical `hm_users` mapping using `auth_user_id` then unique email fallback;
- active Member authorization;
- Admin role recognition without exposing an unfinished Admin migration;
- direct-route protection;
- inactive/unauthorized user rejection;
- no silent re-login after explicit logout.

Do not retire the Streamlit login until this gate passes focused browser UAT.

### Member Gate M2 — Member shell + Today read-only orchestration

- persistent member navigation;
- member-local context;
- lifecycle-aware Today presentation;
- read-only current plan/messages/schedule/task state first;
- no write behaviour until the relevant contract is validated.

### Member Gate M3 onward

Proceed through Assessment/Task actions -> Plan -> Log -> Schedule/Communication -> Profile/Reports/remaining member functions -> full member UAT/cutover, as defined in `HEALTHYME_MEMBER_JOURNEY_V1.md`.

Admin migration follows as a separately controlled journey unless later product direction changes the sequence.

## Validation standard

Every migrated slice must pass:

1. Next.js lint;
2. TypeScript type check;
3. production build;
4. relevant existing regression coverage;
5. new focused browser tests for the migrated screen/workflow;
6. manual UAT against the accepted Streamlit behaviour;
7. UX review confirming that the user can understand the current state and next action without unnecessary navigation or memory dependence.

No old workflow is retired merely because the new page renders successfully.

## Rollback rule

Until a slice is explicitly accepted, the Streamlit implementation remains the fallback/reference. Migration changes are isolated from `main` until reviewed and merged.
