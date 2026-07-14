# H9A.11 — Member Exercise Journal Contract

## Decision

The generic `physical_activity` field is retired from the member experience and from admin reporting. Exercise information must come from the active Recommendation Profile Builder exercise rows. Members may record execution status and observations, but may not edit the prescribed exercise.

## Source of truth

Admin Profile Builder item rows where `item_type = exercise`.

Read-only member fields:

- Exercise name
- Time of Day / scheduled slot
- Difficulty
- Duration or repetitions
- Category/source context
- Equipment
- Benefits
- Instruction
- Image reference
- Active profile ID and profile name
- Day number and item order

Member-write fields:

- Status: Not Started / In Progress / Completed / Skipped
- Completion time
- Member notes
- Log date

## Streamlit member flow

Routes:

- `/Daily_Log`
- `/Member_Exercise`

1. Resolve the logged-in member.
2. Food Journal captures meals, hydration, bowel movement and member notes only.
3. Physical Activity is no longer displayed, edited, validated or saved through Daily Log.
4. Exercise Journal provides a direct action to open `/Member_Exercise`.
5. Load the active recommendation profile.
6. Calculate the current Day 1–7 slice using the profile start date.
7. Filter active items to `item_type = exercise`.
8. Render one read-only prescription card per exercise.
9. Allow only status, completion time and member notes to be edited.
10. Upsert progress against the immutable profile/day/item identity.

## Admin reporting flow

The Daily Food and Exercise report no longer reads or exports `physical_activity`.

The report now displays:

- Exercise prescription fields from the active recommendation profile when no execution log exists.
- Member completion status, completion time and notes from `hm_member_exercise_logs` when available.
- Version linkage through profile ID, day number and item order.

Legacy `physical_activity` data may remain in historical database payloads for audit continuity, but it is no longer an active capture or reporting contract.

## Flutter-ready contract

Flutter must consume the same active recommendation contract and write to the same exercise-log table. No Flutter-only exercise field should be introduced.

Recommended Flutter model:

```text
MemberExerciseLog
- id
- memberId
- logDate
- profileId
- profileName
- dayNumber
- itemOrder
- exerciseName
- scheduledTime
- difficulty
- durationOrReps
- equipment
- benefits
- instruction
- imageReference
- status
- completionTime
- memberNotes
- createdAt
- updatedAt
```

## Non-regression boundaries

- Members cannot alter prescribed exercise details.
- Publishing or replacing a profile does not rewrite historical exercise logs.
- Historical completion remains tied to the profile active on the logged date.
- Food, hydration, bowel movement and nutritionist guidance contracts remain separate.
- No generic physical-activity free-text field should be reintroduced in Streamlit or Flutter.
- Historical `physical_activity` values are not deleted by this sprint.

## Deployment order

1. Run `sql/h9a11_member_exercise_logs.sql` in Supabase SQL Editor.
2. Deploy the Streamlit build.
3. Open Daily Log and confirm Physical Activity is absent.
4. Open Exercise Journal and select `Open My Exercise`.
5. Confirm `/Member_Exercise` loads for a member with an active profile containing exercise rows.
6. Save one completion status and confirm it reloads.
7. Open `/Admin_Daily_Log_Report` and confirm the Exercise section reflects recommendation/log data and no Physical Activity field is displayed.
