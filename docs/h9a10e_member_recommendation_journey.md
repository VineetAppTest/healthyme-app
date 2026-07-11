# H9A.10E — Member Recommendation and Today's Journey Foundation

## Objective

Build the member-facing foundation for the active published recommendation profile.

The sprint treats Recommendation and Today's Journey as two views of one source of truth:

- **Recommendation**: the full Day 1 to Day 7 plan.
- **Today's Journey**: today's calculated slice from the same active seven-day plan.

## Source of truth

The source remains the active admin-published recommendation profile:

- `hm_recommendation_profiles`
- `hm_recommendation_profile_items`

The member side does not create, edit, publish or activate recommendations in this sprint.

## Member day mapping

Today's Journey is calculated from the profile start date:

```text
Today Day = ((today - plan_start_date) % 7) + 1
```

If the plan start date is in the future or missing, the member view falls back safely to Day 1.

## What changed

- Added `components/member_recommendation_display.py`.
- Replaced `pages/36_Todays_Journey.py` so it now reads the active profile contract rather than the older published recommendation window helper.
- Added `pages/37_Member_Plan.py` as a full seven-day recommendation entry page.
- Both views use the same component and the same active profile load path.

## Display contract

Each item card can show:

- item name
- timing or slot
- portion / dosage / frequency / timeline
- instruction
- source context
- image reference text

## Out of scope

- No member editing.
- No completion tracking.
- No image loading.
- No publish or activation logic change.
- No SQL.
- No Flutter/member APK change in this sprint.

## Smoke test

1. Publish/activate one profile for a member.
2. Login as that member.
3. Open Today's Journey from Member Home.
4. Confirm Today's Journey shows only the calculated current day.
5. Open the Full 7-Day Recommendation tab.
6. Confirm Day 1 to Day 7 are visible.
7. Confirm meal, exercise and supplement rows show final admin values.
8. Confirm source context and image reference text appear where available.
9. Confirm there is no member-side edit control.

## Acceptance

Accept only if the member can see both the full seven-day plan and today's slice from the same active published profile with no information loss.
