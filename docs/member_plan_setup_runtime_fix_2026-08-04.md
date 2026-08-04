# Member Plan Builder Setup runtime correction

Date: 2026-08-04
Issue: #360

## Production finding

The rebuilt Setup screen raised a `StreamlitAPIException` because `mpb_plan_selector` was modified after the selectbox using that key had already been instantiated in the same render.

## Correction

- selector changes from New Plan, Clone Complete Plan and Save Setup are queued for the next rerun;
- queued state is applied before the selectbox is created;
- normal dropdown selection still auto-loads the complete plan;
- the instructional Setup sentence and visible Meal Plan label are removed;
- the dropdown, New Plan and Clone Complete Plan controls share one bottom-aligned row;
- no Meal, Exercise, Supplement, profile-store or authentication business rule is changed.

## Acceptance

1. Open Member Plan Builder > Setup without a native-route error.
2. Confirm the dropdown and both buttons are aligned.
3. Confirm no instructional sentence or visible Meal Plan label appears.
4. Select an existing plan and confirm it loads automatically.
5. Click New Plan and confirm the blank plan opens without a widget-state exception.
6. Clone a complete plan and confirm the new Draft is selected.
7. Save Setup and confirm the saved plan remains selected.
