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

Primary surface: `Daily Log → Exercise Journal`.

The Exercise Journal tab renders the full prescribed-exercise experience directly. It must not require a second button or redirect before showing exercise details.

The standalone route `/Member_Exercise` remains available for direct-page compatibility and uses the same shared renderer and data contract.

1. Resolve the logged-in member.
2. Load the active recommendation profile.
3. Calculate the current Day 1–7 slice using the profile start date.
4. Filter active items to `item_type = exercise`.
5. Render one read-only prescription card per exercise directly inside Exercise Journal.
6. Allow only status, completion time and member notes to be edited.
7. Upsert progress against the immutable profile/day/item identity.
8. Reuse the same renderer on the standalone My Exercise route so the two surfaces cannot diverge.

## Admin reporting flow

The Daily Food and Exercise report no longer reads or exports `physical_activity`.

The report now displays:

- Exercise prescription fields from the active recommendation profile when no execution log exists.
- Member completion status, completion time and notes from `hm_member_exercise_logs` when available.
- Version linkage through profile ID, day number and item order.

Legacy `physical_activity` data may remain in historical database payloads for audit continuity, but it is no longer an active capture or reporting contract.

## Flutter-ready contract

Flutter must consume the same active recommendation contract and write to the same exercise-log table. No Flutter-only exercise field should be introduced.

The Flutter Exercise Journal should open directly to the exercise details and progress controls, matching the Streamlit tab. It should not introduce an intermediate Open My Exercise screen.

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
- Daily Log Exercise Journal and the direct My Exercise route must use the same shared renderer.

## Deployment order

1. Confirm `sql/h9a11_member_exercise_logs.sql` has been run in Supabase SQL Editor.
2. Deploy the Streamlit build.
3. Open `Daily Log → Exercise Journal` with a member who has an active profile containing exercise rows.
4. Confirm exercise details appear immediately without a redirect button.
5. Save one completion status and confirm it reloads.
6. Open `/Member_Exercise` directly and confirm the same details and saved progress appear.
7. Open `/Admin_Daily_Log_Report` and confirm the Exercise section reflects recommendation/log data and no Physical Activity field is displayed.
