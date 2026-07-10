# H9A.10C.4 Exercise Source Detail Fix

Follow-up after PR #90 smoke testing.

## Issue

Meal and Supplement could show Pulled Source Details, but Exercise did not show the second row after selection.

## Cause

The Exercise row has multiple selectboxes: Exercise, Time of Day and Intensity. The page-level source detail renderer could receive the later selectbox value instead of the actual Exercise title.

## Fix

The source contract now recovers the actual selected Exercise title from Streamlit row state when the lookup receives a non-source value such as Morning or -- Select intensity.

## Scope

- No SQL change.
- No Flutter change.
- No member-facing change.
- Fix is limited to Profile Builder source detail lookup for Exercise.

## Smoke test

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Go to Exercise Regime.
3. Select an Exercise.
4. Confirm Pulled Source Details appears below the row.
5. Confirm Category, Difficulty, Duration/Reps, Equipment, Instructions, Benefits and Image Reference fields populate where repository data exists.
