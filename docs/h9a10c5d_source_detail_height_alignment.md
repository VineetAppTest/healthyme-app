# H9A.10C.5D — Source Detail Height Alignment

## Purpose

This follow-up addresses the latest smoke-test screenshots for the Recommendation Profile Builder source-detail area.

## UX correction

Exercise pulled source details now keep the second row visually even:

- Equipment
- Benefits
- Image Reference

All three fields render with the same visible height.

Supplement pulled source details now keep the row visually even:

- Source Timing
- Admin Notes

Both fields render with the same visible height.

## Scope

- Profile Builder source-detail layout polish only.
- No source snapshot contract change.
- No Supabase SQL.
- No Flutter/member-facing change.

## Route

`/Admin_Recommendation_Profile_Builder`

## Smoke test

1. Open Recommendation Profile Builder.
2. Go to Exercise Regime.
3. Select Brisk Walking or any exercise with source details.
4. Confirm Equipment, Benefits and Image Reference appear in one row with equal field heights.
5. Go to Supplement Regime.
6. Select a supplement with source details.
7. Confirm Source Timing and Admin Notes appear in one row with equal field heights.
