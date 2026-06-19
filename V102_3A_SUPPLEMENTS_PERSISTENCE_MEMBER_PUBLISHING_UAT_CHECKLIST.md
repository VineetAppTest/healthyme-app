# HealthyMe v102.3A — Supplements Persistence + Member Publishing UAT Checklist

## Scope included
- Persistent supplement records stored in the existing HealthyMe app state.
- Admin can add supplements for a selected member.
- Admin can edit active supplements.
- Admin can stop supplements without deleting the record.
- Member sees only their own active supplement regimen.
- Stopped supplements remain visible in Admin history.

## Explicitly excluded
- No PDF generation.
- No download button.
- No Recommendations module.
- No meal plan integration.
- No exercise plan integration.

## UAT steps
1. Login as Admin and open Supplement Management.
2. Select a member and add a supplement.
3. Refresh/relogin and confirm the supplement persists.
4. Edit dosage/frequency/timing/instructions and confirm changes persist.
5. Login as that member and confirm the active supplement is visible under My Supplements.
6. Login as another member and confirm they cannot see the supplement.
7. Stop the supplement from Admin.
8. Confirm it disappears from the member view.
9. Confirm it remains under Stopped Supplements / History in Admin.
10. Confirm no PDF or Recommendations module was added.

## UAT additions after member/admin UX feedback

- Member view does not show the advisory box below the regimen.
- Member view does not show the local Member Plan / Meal Diary / Supplements / Exercises pill menu.
- Hero-to-regimen spacing is compact.
- Member Home shows Supplements directly under Exercise Repository.
- Admin Edit Supplement uses the same timing option multi-select behavior as Add Supplement.

