# v99.0 Admin Workflow + Member Task Experience Baseline UAT

Base build: v98.6  
Sprint goal: Validate task allocation, member task visibility, completion progress, and admin visibility.

## P0 - Admin Task Allocation

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| AT-01 | Admin Dashboard | Open Admin Dashboard | Hero banner and v99.0 version visible for admin | Pending |
| AT-02 | Task Manager | Open Reassessment / Task Request Manager | Page loads without error | Pending |
| AT-03 | Member Selection | Select a test member | Current instance and existing task status visible | Pending |
| AT-04 | Task Allocation | Select NSP Page 1 + NSP Page 2 + Body-Mind | Requested task list is clear | Pending |
| AT-05 | Due Date | Select due date and note | Due date/note retained in request | Pending |
| AT-06 | Send Request | Click Send Task Request | Task request created or existing open request warning shown | Pending |
| AT-07 | Admin Status | Review Open Task Request Baseline | Shows instance, progress, due date, allocation date and next action | Pending |

## P0 - Member Task Experience

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| MT-01 | Member Home | Login as task member | Your next steps card is visible | Pending |
| MT-02 | Task Details | Review task card | Allocation date, requested pages, due date, note are visible | Pending |
| MT-03 | Progress | Review task progress card | Shows X of Y completed and per-task Done/Pending chips | Pending |
| MT-04 | NSP Page 1 | Start and complete NSP Page 1 | Progress updates to NSP Page 1 Done | Pending |
| MT-05 | NSP Page 2 | Start and complete NSP Page 2 | Progress updates to NSP Page 2 Done | Pending |
| MT-06 | Body-Mind | Start and complete Body-Mind | Progress updates to Body-Mind Done | Pending |
| MT-07 | Submit/Status | Click Submit / Status after tasks done | Member can submit for admin review | Pending |

## P0 - Admin Visibility After Member Completion

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| AV-01 | Admin Task Manager | Reopen test member after partial completion | Admin sees accurate Done/Pending task chips | Pending |
| AV-02 | Admin Task Manager | Reopen after all tasks completed | Progress shows all requested tasks completed | Pending |
| AV-03 | Submit State | Member submits for review | Admin sees review required/submitted state | Pending |
| AV-04 | Admin Review Queue | Open Admin Review Queue | Submitted task instance appears | Pending |

## P1 - Regression Guard

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| RG-01 | Daily Log | Open Daily Food Journal | No regression from v98.6 | Pending |
| RG-02 | Filter | Apply/Clear saved-day filter | No regression from v98.6 | Pending |
| RG-03 | Admin Dashboard | Open Admin Dashboard | Hero/version placement still clean | Pending |
| RG-04 | Mobile | Check Member Home task card on phone | No overlap or broken button layout | Pending |

## Closure Rule

v99.0 should be accepted as baseline only when P0 checks pass. Any broken completion/status flow should move to v99.1 as a targeted fix.
