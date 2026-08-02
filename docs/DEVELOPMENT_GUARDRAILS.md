# HealthyMe Development Guardrails

These rules apply to every new Streamlit, backend and Flutter change.

## 1. Preserve the accepted baseline

Previously accepted and production-tested behaviour is a requirement, not optional legacy code. Before changing a route, shared component, stylesheet, bootstrap, data contract or workflow, review the relevant merged PRs, issues, tests and current production behaviour.

Do not remove, rename, bypass or reintroduce an element that was previously accepted unless the new requirement explicitly changes it.

## 2. Streamlit is the accepted behavioural source of truth

The completed Streamlit Member and Admin application is the functional baseline for Flutter parity. Flutter must capture and present all required information without losing existing Member/Admin behaviour.

Streamlit is frozen for feature development. Change it only for an approved production defect, regression or an explicitly approved source-of-truth update.

## 3. Shared behaviour must stay shared

Global behaviour must be fixed in the shared layer rather than patched page by page. This includes:

- global header and top spacing;
- signed-in utility row and logout;
- Streamlit owner-toolbar suppression;
- common hero/header styling;
- navigation and route guards;
- form reset behaviour;
- shared repository and profile-source contracts.

Before adding page-specific CSS or wrappers, verify that an existing shared component is not already responsible for the behaviour.

## 4. Protected accepted behaviours

Every affected change must confirm that it does not regress these accepted areas:

- authentication, refresh persistence and role routing;
- Member/Admin/Nutritionist access boundaries;
- global header spacing and hidden Streamlit owner controls;
- Recommendation Profile Builder and repository/allocation separation;
- Supplement Management as repository and creation only;
- Admin and Member form reset behaviour;
- package, schedule and session-usage contracts;
- Member Home, Daily Log, journals and saved-day behaviour;
- production data, history, allocation IDs and existing records.

## 5. Required development sequence

Before coding:

1. State the current accepted behaviour.
2. Identify the shared components, routes, tables and tests affected.
3. Review recent merged PRs and open issues touching the same area.
4. Define what must remain unchanged.

During coding:

1. Make the smallest safe change.
2. Reuse shared components and contracts.
3. Do not modify auth, routing, RLS, storage or data writes for a UI-only request.
4. Preserve historical data and existing IDs unless migration is explicitly approved.
5. Add or update regression tests for the accepted behaviour.

Before merge:

1. Run focused tests and relevant full regression workflows.
2. Smoke-test the changed journey and the nearest previously accepted journeys.
3. Check desktop and mobile layouts where relevant.
4. Record evidence in the PR.
5. Do not merge while a known regression remains.

## 6. Regression response

When a regression is found:

- stop new feature work in the affected area;
- identify the shared root cause rather than applying repeated visual patches;
- add a regression contract so the same failure cannot silently return;
- verify both the correction and the previously accepted behaviour it interacted with.

## 7. Flutter development rule

For every Flutter implementation, map the feature against the final Streamlit flow and Supabase contract before coding. The Flutter implementation must preserve information capture, permissions, status transitions, validation, history and user-visible outcomes.