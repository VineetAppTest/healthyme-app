# H9A.10E Home Buttons Alignment

## Purpose

Align the member home plan navigation with the rest of the Personalized Content actions.

## Change

- Today's Plan and My Weekly Plan remain two separate actions.
- They are no longer visually promoted as standalone tiles on Member Home.
- They now render as normal full-width buttons in the same vertical sequence as My Profile, Daily Log, My Schedule, Recipe Repository, Exercise Repository and Supplements.
- Today's Plan remains today's calculated slice from the active weekly recommendation.
- My Weekly Plan remains the complete seven-day view.

## Scope

- Member Home UI only.
- No SQL.
- No publish or activation logic change.
- No member editing.
- No Flutter/APK change.

## Smoke test

1. Login as a member with an active published profile.
2. Open Member Home.
3. Confirm Personalized Content shows normal buttons only.
4. Confirm Today's Plan and My Weekly Plan are aligned with the other buttons.
5. Confirm there are no highlighted plan tiles/cards on Member Home.
6. Open Today's Plan and confirm today's slice still works.
7. Return and open My Weekly Plan and confirm the weekly plan still works.
