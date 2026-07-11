# H9A.10E Split Journey and Weekly Recommendation

## Intent

Refines the member-facing recommendation experience into two clear parts:

1. Today's Journey: only today's calculated slice from the active weekly recommendation.
2. Weekly Plan: the full seven-day recommendation.

Both views continue to read from the same active admin-published recommendation profile.

## Today's Journey

Today's Journey is intentionally day-specific. It shows only the current Day 1 to Day 7 slice based on the active profile start date.

Sections:
- Meals
- Supplements
- Exercises
- Today's Nutrition Guidance

## Weekly Plan

Weekly Plan shows the full seven-day recommendation and separates content into readable tabs:

- Meals
- Supplements
- Exercises
- Nutrition Guidance

Rows are rendered as cards with compact chips for timing, portions, dosage, frequency, timeline, source context and other relevant fields.

## Guardrails

- No member editing.
- No publish or activation logic change.
- No SQL.
- No Flutter or APK change.
- Same active profile remains the single source of truth.

## Routes

- pages/36_Todays_Journey.py
- pages/37_Member_Plan.py

## Smoke Test

1. Publish and activate one recommendation profile for a member.
2. Login as that member.
3. Open Today's Journey.
4. Confirm only today's calculated day is shown.
5. Confirm meal, supplement, exercise and guidance sections appear.
6. Click Open Weekly Recommendation.
7. Confirm Weekly Plan opens.
8. Confirm tabs show Meals, Supplements, Exercises and Nutrition Guidance.
9. Confirm each tab shows Day 1 to Day 7.
10. Confirm chips are readable and final admin values are preserved.
11. Confirm there are no member-side edit controls.
