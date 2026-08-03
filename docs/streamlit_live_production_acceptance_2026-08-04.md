# Streamlit live production acceptance — 2026-08-04

## Objective

Complete the final Streamlit acceptance step after merged PR #381 and before any Flutter implementation begins.

## Gate 1 — automated production entry smoke

The GitHub Actions workflow `Streamlit live production entry smoke` probes the deployed application from GitHub's hosted network.

It verifies:

- `https://healthymeappbyankita.streamlit.app/` resolves and responds;
- `https://healthymeappbyankita.streamlit.app/Login` resolves and responds;
- neither route returns a fatal missing-app or 404 marker;
- a usable Streamlit/HTML shell is returned;
- response evidence is stored for seven days as `streamlit-production-entry-evidence`.

The probe retries sleeping or temporarily unavailable Streamlit responses before failing.

## Gate 2 — authenticated Admin walkthrough

This remains a deliberate manual acceptance gate because credentials, OIDC interaction and production member data must not be embedded in source code or pull-request workflows.

Validate in this order:

1. Login reaches Admin Dashboard without a stuck `Finalising secure login` state.
2. Recipes, Exercises and Supplements repositories open from Content & Allocation.
3. Recommendation Profile Builder shows only:
   - Setup;
   - Meals;
   - Allocate Exercise & Supplement;
   - View Profiles.
4. Meals supports edit, preview and publish without exposing Exercise/Supplement write controls.
5. Allocate Exercise & Supplement carries the selected member into the independent allocation route.
6. Exercise allocation saves, updates and stops only Exercise allocation rows.
7. Supplement allocation saves, updates and stops only Supplement allocation rows.
8. View Profiles shows Draft, Active, Replaced and Archived history without write controls.
9. Admin Dashboard does not duplicate standalone Exercise/Supplement allocation buttons.
10. No route shows System Tools or obsolete build labels.

## Gate 3 — authenticated Member walkthrough

Validate with a member that has an active Meal Profile plus independent Exercise and Supplement allocations:

1. Login reaches Member Home without a stuck finalisation state.
2. Current Member Plan shows Meals from the active Meal Profile.
3. Current Member Plan shows Exercise only from independent Exercise allocation.
4. Current Member Plan shows Supplement only from independent Supplement allocation.
5. Retained historical Profile Builder Exercise/Supplement rows are not duplicated.
6. Today's Plan shows only items effective for the member-local date.
7. Stopped and expired items remain absent from the current member view.
8. Daily Log, My Schedule and navigation remain usable.
9. Refresh and browser back do not lose the authenticated route unexpectedly.

## Acceptance rule

Streamlit acceptance is complete only when:

- the automated production-entry workflow passes;
- the Admin walkthrough is explicitly recorded as passed;
- the Member walkthrough is explicitly recorded as passed;
- any observed regression is corrected and revalidated.

Flutter remains blocked until all three gates pass.

## Safety boundary

This phase does not change:

- Supabase schema, RLS or RPCs;
- Auth or role definitions;
- Meal, Exercise or Supplement persistence authorities;
- recommendation sharing;
- repository data;
- production member data;
- Flutter code.
