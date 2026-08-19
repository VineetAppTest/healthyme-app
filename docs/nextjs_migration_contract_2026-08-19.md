# HealthyMe Next.js Migration Contract — 2026-08-19

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

Examples include meals, supplements, exercise, consultations, allocated tasks, due dates and other member actions. Where existing plan data includes timing or dates, the frontend should use that context to surface the relevant item at the appropriate time rather than requiring the member to navigate to a separate plan page to discover it.

For example, an upcoming meal or exercise may become prominent in a `Now`/`Next` area when its scheduled time approaches, with the essential instruction and direct action available from that context. The underlying allocation, timing, completion and status logic remains authoritative in the existing HealthyMe backend; the frontend changes how clearly and proactively that information is presented.

Proactive presentation should be useful rather than intrusive: prefer contextual cards, prioritized sections, badges and timely prompts over unnecessary blocking pop-ups. A member must still be able to browse the complete plan/history when needed.

This principle applies especially to the member-facing web migration and should remain aligned with the intuitiveness principles used for the HealthyMe native app.

## Architecture

- Existing Streamlit application: functional reference until retired workflow-by-workflow.
- New web frontend: Next.js App Router + TypeScript in `/web`.
- Hosting target: Vercel with repository Root Directory `/web`.
- Backend: existing HealthyMe Supabase project.
- Supabase web authentication: cookie-based SSR using `@supabase/ssr` and the project's publishable key.
- Privileged keys: never shipped to browser code.

## Branding

Product branding is centralized behind configuration. `HealthyMe` remains the default product name until a replacement brand is approved after naming/domain/trademark clearance. A branding decision must not block the technical migration.

The product name, logo and related visual identity must remain replaceable without changing application workflows, Supabase data contracts or business logic.

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

Each migrated member-facing slice must also be assessed against the `Now / Next / Later / Done` principle so that navigation parity does not become an excuse to reproduce avoidable hunting or memory-dependent behaviour from the old frontend.

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
