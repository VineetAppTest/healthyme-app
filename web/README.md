# HealthyMe Next.js Web

This directory contains the replacement web presentation layer for HealthyMe.
It is intentionally isolated from the existing Streamlit application so both can
coexist during migration.

## Governing documents

- `../docs/HEALTHYME_WEB_MIGRATION_SOURCE_OF_TRUTH.md` — overall migration authority and current member-first sequence.
- `../docs/HEALTHYME_MEMBER_JOURNEY_V1.md` — governing member-experience blueprint.

A later explicit product decision supersedes older sequencing and must be incorporated back into the governing documentation.

## Migration contract

- Keep the existing HealthyMe Supabase project as the backend authority.
- Do not recreate or fork production data, IDs, Auth, RLS, storage or lifecycle rules.
- Treat accepted Streamlit Admin/Member behaviour as the functional baseline, not the UX template.
- Redesign interaction/IA where it reduces cognitive load while preserving underlying outcomes.
- Migrate one workflow at a time and retire its Streamlit equivalent only after UAT.
- Never expose a Supabase secret/service-role key to browser code.
- Keep product branding centralized so a future approved rename does not require UI rewrites.

## Local setup

1. Use Node.js 20.9 or newer.
2. Run `npm install` from this `web` directory.
3. Copy `.env.example` to `.env.local`.
4. Populate `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` with the **existing HealthyMe Supabase project** values.
5. Populate `SUPABASE_SERVICE_ROLE_KEY` only in the server environment. It is required to reproduce the current canonical `hm_users` authorization without changing RLS; it must never be exposed to browser code.
6. Run `npm run dev`.

## Validation

Before a migration PR is eligible for UAT:

- `npm run lint`
- `npm run typecheck`
- `npm run build`
- existing Streamlit regression tests remain green
- focused browser UAT is added for the migrated workflow

Member-facing slices must additionally prove that the member can understand what matters now and what to do next without remembering the old app structure.

## Vercel

Create/import a separate HealthyMe Vercel project from this repository with **Root Directory** set to `web`.
Configure the existing HealthyMe Supabase URL and publishable key in Vercel environment variables.
Configure the existing service-role key as a **server-only** Vercel environment variable for canonical role resolution. It must never use the `NEXT_PUBLIC_` prefix or be referenced by a Client Component.

## Current migration gates — member first

1. Foundation and Vercel preview.
2. **M0 — Member journey contract** — completed in `HEALTHYME_MEMBER_JOURNEY_V1.md`.
3. **M1 — Member Auth/session/role parity** — Supabase sign-in, durable SSR session, canonical `hm_users` authorization, secure logout and member route protection.
4. **M2 — Member shell + read-only Today orchestration** — lifecycle-aware Now / Next / Later / Done using existing HealthyMe reads only.
5. **M3 — Assessment/task actions** — LAF, NSP, Body-Mind, progress, due date and Submit for Admin Review parity.
6. **M4 — Plan** — unified meals, supplements and exercise with today/seven-day browse.
7. **M5 — Log** — actual behaviour journaling and existing autosave/history semantics.
8. **M6 — Schedule + communication** — acknowledgement/reschedule and nutritionist-message behaviour.
9. **M7 — Profile/reports/remaining member functions**.
10. **M8 — End-to-end member UAT and cutover**.
11. Admin migration follows as a separately controlled product journey unless a later product direction changes the sequence.

The current Streamlit application remains live and authoritative until each replacement slice is explicitly accepted.
