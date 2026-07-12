# H9A.10E Evening Snack Structured Meal Fix

Corrective follow-up for the Daily Log meal structure.

## Scope

- Evening Snack is restored as a normal structured meal, like Breakfast, Lunch, Dinner, and Bedtime.
- Snacking remains a separate optional repeatable section under Meal Section.
- Existing `snacking_*` storage keys remain unchanged for true snacking entries.
- Compatibility guard: if an old entry was saved during the regression as `snacking_*` with an Evening Snack label, the first such entry is surfaced as structured Evening Snack to avoid data loss.
- Full Day Report separates Evening Snack from Snacking.

## Smoke test

1. Open Member Home > Daily Log > Food Journal.
2. Confirm structured meal rows show: Breakfast, Lunch, Evening Snack, Dinner, Bedtime.
3. Confirm Evening Snack opens as one normal meal form with no Add/Remove buttons.
4. Confirm Snacking appears separately below the structured meals.
5. Confirm Snacking supports Add/Remove snacking up to 9 entries.
6. Save one Evening Snack entry and one Snacking entry.
7. Confirm Full Day Report shows Evening Snack separately from Snacking.

No SQL. No publish logic change. No Flutter/APK change.
