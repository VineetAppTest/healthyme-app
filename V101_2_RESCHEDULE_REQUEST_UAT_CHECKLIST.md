# v101.2 Member Reschedule Request UAT Checklist

Base build: v101.1

## Member Reschedule Request

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| RS-01 | My Schedule | Open scheduled item | Request Reschedule button is visible | Pending |
| RS-02 | Reschedule >24 hrs | Request date/time outside 24-hour window | Informational message says prior session will not be counted if approved | Pending |
| RS-03 | Reschedule within 24 hrs | Request date/time within 24 hours | Warning explains prior session may be counted and confirm checkbox is required | Pending |
| RS-04 | Submit request | Submit reschedule request | Request is saved as pending | Pending |
| RS-05 | Duplicate guard | Existing pending request | Member cannot submit another pending request for same schedule | Pending |

## Admin Reschedule Review

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| AR-01 | Admin Scheduling | Select member with pending request | Reschedule request appears | Pending |
| AR-02 | Approve | Approve reschedule | Old schedule marked rescheduled; new schedule created | Pending |
| AR-03 | Reject | Reject reschedule | Request rejected; member notification queued | Pending |
| AR-04 | 24-hour rule | Approve within-24-hour request | Old schedule flagged session_counted=true | Pending |

## Regression Guard

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| RG-01 | Scheduling create | Create normal schedule | No regression | Pending |
| RG-02 | Member acknowledge | Acknowledge schedule | No regression | Pending |
| RG-03 | Daily Log | Open/save Daily Log | No regression | Pending |
| RG-04 | Recipe/Exercise | Open pages | No regression | Pending |
