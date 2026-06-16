# v98.0 Daily Log Closure + Admin/Report Validation Checklist

Base build: v97.36 GTG  
Sprint goal: Close Daily Log sprint and validate admin/report data flow.

## P0 - Member Daily Log Functional Closure

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| DL-01 | Page load | Open Daily Food Journal | Page opens without error | Pending |
| DL-02 | Food Journal Date | Select a date | Date picker updates and page remains stable | Pending |
| DL-03 | Meal Timing | Add Breakfast timing and food details | Meal fields accept data | Pending |
| DL-04 | Save Meal | Click Save Breakfast / meal save | Meal is saved for selected date | Pending |
| DL-05 | Snacking | Click Snacking | Snacking 1 appears and can be filled | Pending |
| DL-06 | Snacking Multiple | Add another snacking entry | Snacking 2 appears and saves | Pending |
| DL-07 | Other Fluids | Add Other Fluids with Fluid Timing, quantity and notes | Data is retained and displayed | Pending |
| DL-08 | Full Day Details | Fill poop, activity, cravings, overall note | Full-day fields accept data | Pending |
| DL-09 | Save Day Details Only | Click Save Day Details Only | Full-day non-meal details are saved | Pending |
| DL-10 | Save Full-Day Journal | Click Save Full-Day Journal | Full daily journal saves without error | Pending |
| DL-11 | Revisit Date | Reopen same date | Previously saved values appear correctly | Pending |

## P0 - Recent Saved Days Filter

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| RS-01 | Saved Days default | Open Recent Saved Days | All saved days are shown by default | Pending |
| RS-02 | Apply Filter | Select From/To range and click Apply Date Filter | Only matching saved days are shown | Pending |
| RS-03 | Filter Count | Review Showing X of Y count | Count matches displayed cards | Pending |
| RS-04 | Clear Filter | Click Clear Filter / Show All | Full saved-day list returns | Pending |
| RS-05 | Date Reset | After Clear Filter, check From/To fields | Fields reset to full available range | Pending |
| RS-06 | No Match | Select range with no data | No saved days found message appears | Pending |

## P0 - Admin / Report Validation

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| AR-01 | Admin Access | Login as Admin | Admin dashboard loads | Pending |
| AR-02 | Member Selection | Select member with Daily Log entries | Member context loads | Pending |
| AR-03 | Admin Daily Log Report | Open Daily Log report/history | Member saved entries are visible | Pending |
| AR-04 | Other Fluids in Report | Review Other Fluids section | Fluid Timing, fluid type, quantity, notes visible | Pending |
| AR-05 | Snacking in Report | Review snacking entries | Snacking entries appear correctly | Pending |
| AR-06 | Notes | Review daily notes | Member notes and nutritionist notes appear correctly | Pending |

## P1 - Export / Download / Layout

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| EX-01 | Export | Export/download Daily Log report if available | Export includes meal, fluids, notes, poop, activity | Pending |
| EX-02 | Laptop Layout | Check page on laptop | Layout is clean and usable | Pending |
| EX-03 | Mobile Layout | Check page on phone | Layout is usable without overlap | Pending |
| EX-04 | Regression | Open LAF, NSP, Body-Mind, Recipe, Exercise pages | Pages open without errors | Pending |

## Closure Rule

Daily Log should be marked closed only when all P0 items pass. P1 items can be scheduled into a polish sprint if non-blocking.
