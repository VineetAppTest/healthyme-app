# HealthyMe Next.js Web

This directory contains the replacement web presentation layer for HealthyMe.
It is intentionally isolated from the existing Streamlit application so both can
coexist during migration.

## Migration contract

- Keep the existing HealthyMe Supabase project as the backend authority.
- Do not recreate or fork production data, IDs, Auth, RLS, storage or lifecycle rules.
- Treat the accepted Streamlit Admin/Member behaviour as the functional baseline.
- Migrate one workflow at a time and retire its Streamlit equivalent only after UAT.
- Never expose a Supabase secret/service-role key to browser code.
- Keep product branding centralized so a future approved rename does not require UI rewrites.

## Local setup

1. Use Node.js 20.9 or newer.
2. Run `npm install` from this `web` directory.
3. Copy `.env.example` to `.env.local`.
4. Populate `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` with the existing HealthyMe Supabase project values.
5. Run `npm run dev`.

## Validation

Before a migration PR is eligible for UAT:

- `npm run lint`
- `npm run typecheck`
- `npm run build`
- existing Streamlit regression tests remain green
- focused browser UAT is added for the migrated workflow

## Vercel

Create/import a Vercel project from this repository with **Root Directory** set to `web`.
Configure the existing HealthyMe Supabase URL and publishable key in Vercel environment variables.
Do not add or expose the Supabase service-role key unless a future server-only use case is explicitly approved and reviewed.

## Initial gates

1. Foundation and Vercel preview.
2. Supabase Auth/session parity and canonical `hm_users` role routing.
3. Admin shell and Admin Dashboard parity.
4. Member/Profile workflow parity.
5. Meal Builder.
6. Exercise Allocation.
7. Supplement Allocation.
8. Repository and remaining Admin workflows.
9. Member web workflows, if retained.

The current Streamlit application remains live and authoritative until each gate is accepted.
