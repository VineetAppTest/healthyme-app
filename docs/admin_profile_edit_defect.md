# Admin/Nutritionist cannot edit an existing recommendation profile

## Reported defect
Admin/Nutritionist is unable to edit an existing recommendation profile, whether the profile is allocated to a member or remains unallocated.

## Expected behaviour
- Select and load any existing profile into edit mode.
- Saved Profile Setup, Meal Structure, Exercise Regime and Supplement Regime values load correctly.
- Save modifications to the same profile unless versioning is explicitly selected.
- Editing an allocated profile does not remove or corrupt its member allocation.
- Any intentional restriction is displayed clearly instead of leaving the profile non-editable.

## Investigation scope
- `Edit Existing Profile Setup` / `Load Setup` selection and state hydration.
- Filters for allocated versus unallocated profiles.
- Widget disabled-state and Streamlit Session State behaviour after profile selection.
- Update-versus-create save path.
- Allocation linkage and profile-version handling.
- Supabase permissions, RLS and RPC/update errors.

## Acceptance tests
1. Edit and save an unallocated profile.
2. Reopen it and confirm persistence.
3. Edit and save an allocated profile.
4. Reopen it and confirm persistence.
5. Confirm the member allocation remains intact.
6. Confirm no duplicate profile is created unintentionally.
