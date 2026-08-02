# HealthyMe Coding Instructions

Read `docs/DEVELOPMENT_GUARDRAILS.md` before modifying this repository.

## Non-negotiable rules

1. Preserve previously accepted and production-tested behaviour unless the current requirement explicitly replaces it.
2. Review relevant merged PRs, issues, tests and shared components before coding.
3. Treat the final Streamlit Member/Admin application as the behavioural source of truth for Flutter.
4. Fix global behaviour in shared components. Do not create page-specific workarounds for shared header, toolbar, navigation, form or repository behaviour.
5. For UI-only requests, do not change authentication, routing, roles, RLS, Supabase writes or business logic.
6. Preserve existing data, history, identifiers and allocations unless an approved migration is part of the requirement.
7. Add or update regression tests whenever a previously accepted behaviour could be affected.
8. Run focused and relevant regression checks before opening or merging a PR.
9. Explicitly document what was reviewed, what remains unchanged and what was smoke-tested.
10. Stop and reconcile conflicts between a new request and the accepted baseline instead of silently overriding prior work.

## Protected global behaviours

Pay particular attention to:

- top spacing and the shared signed-in header;
- hidden Streamlit owner controls;
- login persistence and role routing;
- Member/Admin/Nutritionist permissions;
- repository versus member-allocation separation;
- Recommendation Profile Builder source contracts;
- form reset behaviour;
- package, schedule and session-usage contracts;
- Member Home, Daily Log, journals and saved days.

Every PR must use `.github/pull_request_template.md` and provide regression evidence.