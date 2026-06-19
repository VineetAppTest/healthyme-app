# HealthyMe v102.4 — Recommendations Share + Today’s Journey UAT Checklist

## Accepted baseline
Built on: `HealthyMe_v102_3A_SUPPLEMENT_FREQ_ENDDATE_ALIGNMENT_FULL_BUILD.zip`

## Scope delivered

1. Admin-side **Recommendations Share** added.
2. One 7-day recommendation window is now the source of truth for:
   - Nutritionist Report
   - Today’s Journey
   - Meal Plan
   - Exercise Plan
   - Supplements
3. Member-side **Today’s Journey** added.
4. Today’s Journey pulls only from the published Recommendations Share for the current date.
5. Recipe-1 UX merged into the working member Recipe Repository.
6. Exercise-1 UX merged into the working member Exercise Repository.
7. Original working Recipe and Exercise pages preserved as rollback files.
8. Recipe-1 / Exercise-1 testing pages disconnected from active navigation.
9. Admin Recipe-1 / Exercise-1 testing buttons removed.
10. No PDF/download generation added.

## Rollback files

Rollback copies are stored outside active Streamlit routing:

- `rollback_v102_4/08_Recipe_Repository_LEGACY_WORKING.py.disabled`
- `rollback_v102_4/09_Exercise_Repository_LEGACY_WORKING.py.disabled`

Design reference copies are stored in:

- `rollback_v102_4/design_reference/35_Recipe_Repository_1_UX_REFERENCE.py.disabled`
- `rollback_v102_4/design_reference/36_Exercise_Repository_1_UX_REFERENCE.py.disabled`
- `rollback_v102_4/design_reference/37_Admin_Recipe_Manager_1_UX_REFERENCE.py.disabled`
- `rollback_v102_4/design_reference/38_Admin_Exercise_Manager_1_UX_REFERENCE.py.disabled`

## UAT checks

### Admin side

- Open Admin Dashboard.
- Confirm **Recipes-1** and **Exercises-1** buttons are removed.
- Confirm **Recommendations Share** button is available.
- Select a member.
- Select a 7-day start date.
- Confirm end date auto-calculates as start date + 6 days.
- Enter Nutritionist Report.
- Select meal plan items across the 7-day window.
- Select exercise items across the 7-day window.
- Confirm active supplements can be mapped into the 7-day window.
- Save Draft.
- Publish / Share to Member.

### Member side

- Open Member Home.
- Confirm **Today’s Journey** button is available.
- Confirm Recipe-1 and Exercise-1 testing buttons are not visible.
- Open Today’s Journey.
- Confirm the current-date snapshot displays meal, exercise and supplement items from the shared recommendation window.
- Confirm Nutritionist Report is visible.
- Confirm full 7-day plan is visible.
- Open Recipe Repository and confirm Recipe-1-style UX is active but data is the real assigned plan.
- Open Exercise Repository and confirm Exercise-1-style UX is active but data is the real assigned plan.

## Exclusions maintained

- No PDF generation.
- No recommendation scoring.
- No AI-generated recommendations.
- No duplicate active Recipe-1 / Exercise-1 member buttons.
