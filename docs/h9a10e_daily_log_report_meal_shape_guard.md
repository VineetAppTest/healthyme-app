# H9A.10E Daily Log Report Meal Shape Guard

## Issue

Admin Daily Food Journal Report crashed with an AttributeError when a saved meal entry was not stored as a dictionary.

Observed traceback:

```text
AttributeError
pages/22_Admin_Daily_Log_Report.py
_meal_keys_for_day
meal.get(...)
```

## Root cause

`selected_day["meals"]` can contain older or malformed meal payloads where a meal value is a plain string/list/other shape instead of a dict. The report assumed every meal was a dict and called `.get()` directly.

## Fix

- Added `_meal_dict()` to normalise non-dict meal payloads.
- Added `_meal_label()` to safely derive labels for custom meal keys.
- Hardened `_meal_keys_for_day()` so non-dict meals cannot crash report rendering.
- Hardened `_row_for_day()` and the detailed selected-day meal table.

## Scope

- Admin-only Daily Food Journal Report.
- No SQL.
- No member UI change.
- No recommendation publish/activation logic change.

## Smoke test

1. Open Admin Daily Food Journal Report.
2. Select the same member/date that caused the crash.
3. Confirm the page renders and does not show the generic Streamlit error.
4. Confirm the meal table renders.
5. Confirm All saved days still renders.
6. Confirm Excel download still works.
7. Confirm Nutritionist Guidance form still sends guidance.
