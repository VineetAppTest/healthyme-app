# v101.4 Existing Member NSP Score Recalculation UAT Checklist

Base build: v101.3

## Admin Utility

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| REC-01 | Admin Dashboard | Open System Tools | NSP Recalculate button is visible | Pending |
| REC-02 | Recalc Page | Open NSP Score Recalculation | Page loads without error | Pending |
| REC-03 | Selected Member | Recalculate one member | Member snapshot is created/updated | Pending |
| REC-04 | All Members | Recalculate all existing members | All member snapshots/audit entries are created | Pending |
| REC-05 | Status Table | Review status table | Last calculated date/top system appears | Pending |

## Scoring Guard

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| SG-01 | Mapping | Use sample Excel values | Totals match v101.3 expected totals | Pending |
| SG-02 | Report | Open Partial/Final report | Report reflects Excel-aligned mapping | Pending |
| SG-03 | Raw Answers | Recalculate | Raw NSP answers remain unchanged | Pending |

## Regression Guard

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| RG-01 | Scheduling | Open Admin Scheduling | No regression | Pending |
| RG-02 | Reschedule | Member Request Reschedule | No regression | Pending |
| RG-03 | Daily Log | Open/save Daily Log | No regression | Pending |
| RG-04 | Recipe/Exercise | Open pages | No regression | Pending |
