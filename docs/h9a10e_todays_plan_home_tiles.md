# H9A.10E — Today's Plan and My Weekly Plan Home Tiles

## Intent

Align the member-facing language and home entry points with the agreed product split:

- Today's Plan = today's slice only.
- My Weekly Plan = complete seven-day plan.

## Scope

- Renames the visible Today page from Today's Journey to Today's Plan.
- Keeps the existing route/file to avoid breaking navigation: `pages/36_Todays_Journey.py`.
- Keeps the weekly route/file as `pages/37_Member_Plan.py`, but the visible page is My Weekly Plan.
- Adds two clear tiles/buttons on Member Home:
  - Today's Plan
  - My Weekly Plan
- Keeps today's content as a current-day slice from the weekly plan.
- Keeps My Weekly Plan split into Meals, Supplements, Exercises and Nutrition Guidance.
- Keeps tile/card/chip display for readability.

## Non-scope

- No SQL.
- No publish/activation logic change.
- No member editing.
- No Flutter/APK change.

## Smoke test

1. Login as a member with a published active profile.
2. Open Member Home.
3. Confirm two separate tiles are visible:
   - Today's Plan
   - My Weekly Plan
4. Open Today's Plan.
5. Confirm only today's calculated slice is shown.
6. Confirm content appears in tiles/chips and remains concise.
7. Return to Member Home and open My Weekly Plan.
8. Confirm the complete seven-day plan opens.
9. Confirm My Weekly Plan tabs are visible:
   - Meals
   - Supplements
   - Exercises
   - Nutrition Guidance
10. Confirm there are no member-side edit controls.
