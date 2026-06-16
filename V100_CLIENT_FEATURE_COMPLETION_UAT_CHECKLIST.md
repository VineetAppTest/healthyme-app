# v100.0 Client Feature Completion UAT Checklist

Base build: v99.0

## P0 - Member Submission / Admin Review

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| SR-01 | Submit Status | Open Submit / Status | Page opens without error | Pending |
| SR-02 | Progress Guard | Try submit with incomplete tasks | Submit is blocked with pending progress message | Pending |
| SR-03 | Submit | Complete requested tasks and submit | Instance status becomes submitted/review_required | Pending |
| SR-04 | Admin Review Queue | Open Admin Review Queue | Submitted instance appears with progress | Pending |

## P0 - Recipe Allocation + Feedback

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| RF-01 | Admin Recipe Allocation | Allocate recipe to member | Allocation saves | Pending |
| RF-02 | Member Recipe | Member opens Recipe Repository | Allocated recipe visible | Pending |
| RF-03 | Member Feedback | Submit recipe feedback/status | Feedback saved and confirmation appears | Pending |
| RF-04 | Admin Feedback View | Admin opens recipe allocation tab for member | Member recipe feedback visible | Pending |

## P0 - Exercise Allocation + Feedback

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| EF-01 | Admin Exercise Allocation | Allocate exercise to member | Allocation saves | Pending |
| EF-02 | Member Exercise | Member opens Exercise Repository | Allocated exercise visible | Pending |
| EF-03 | Member Feedback | Submit exercise feedback/status | Feedback saved and confirmation appears | Pending |
| EF-04 | Admin Feedback View | Admin opens exercise allocation tab for member | Member exercise feedback visible | Pending |

## P1 - Regression Guard

| Test ID | Area | Test Step | Expected Result | Status |
|---|---|---|---|---|
| RG-01 | Daily Log | Open Daily Food Journal | No regression | Pending |
| RG-02 | Saved Days Filter | Apply/Clear filter | No regression | Pending |
| RG-03 | Admin Dashboard | Open Admin Dashboard | Hero/version still clean | Pending |
| RG-04 | Member Home | Open Member Home | Task progress card still clean | Pending |
