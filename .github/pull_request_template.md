## Objective

Describe the exact problem being solved and the approved outcome.

## Current accepted behaviour reviewed

List the existing production behaviour, merged PRs, issues, shared components and tests reviewed before coding.

- [ ] I reviewed the relevant accepted Streamlit/Flutter flow before changing code.
- [ ] I checked recent merged PRs and open issues touching this area.
- [ ] I identified what must remain unchanged.

## Scope and safety boundary

State what changes and what explicitly does not change.

- [ ] UI-only work does not alter auth, routing, roles, RLS, storage or writes.
- [ ] Existing records, history, IDs and allocations are preserved unless an approved migration is included.
- [ ] Shared behaviour is implemented in the shared layer, not patched page by page.
- [ ] Streamlit remains the accepted behavioural source of truth for Flutter parity.

## Regression review

Confirm the affected accepted behaviours were checked:

- [ ] authentication, refresh persistence and role routing;
- [ ] Member/Admin/Nutritionist permissions;
- [ ] global header spacing, signed-in row and hidden Streamlit owner toolbar;
- [ ] repository versus member-allocation boundaries;
- [ ] Profile Builder and Supplement Repository source contracts;
- [ ] form reset behaviour;
- [ ] package, scheduling and session usage;
- [ ] Member Home, Daily Log, journals and saved days;
- [ ] desktop/mobile layout where relevant.

Mark non-applicable items as `N/A` in the evidence section rather than ignoring them.

## Validation evidence

List automated checks, smoke tests, screenshots or device results.

- [ ] Focused automated tests passed.
- [ ] Relevant regression workflows passed.
- [ ] Changed journey was smoke-tested.
- [ ] Nearest previously accepted journeys were smoke-tested.
- [ ] No known regression remains.

## Flutter parity impact

For Flutter work, state which final Streamlit flow and Supabase contract were mapped, and confirm there is no information loss. For Streamlit-only corrections, state `N/A`.
