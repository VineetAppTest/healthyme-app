# v101.5 Global Header, Version & Button Polish UAT Checklist

Base build: v101.4

## Version Display

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| VP-01 | Admin pages | Open Admin Dashboard / Eval Status / Scheduling / Recalculate | Version shows latest v101.5 adjacent to HealthyMe only | Pending |
| VP-02 | Member pages | Open Member Login / Member Home / My Schedule | No version shown beside HealthyMe | Pending |
| VP-03 | Stale version | Search visible pages | No v95.14 or older app-facing version text visible | Pending |

## Global Header Structure

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| GH-01 | Admin pages | Open common admin pages | Signed in / Logout row appears before Hero Banner | Pending |
| GH-02 | Member pages | Open common member pages | Signed in / Logout row appears before Hero Banner | Pending |
| GH-03 | Spacing | Compare pages | Space before/after Hero Banner is consistent | Pending |

## Button Polish

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| BP-01 | Admin pages | Review buttons | No black/default buttons; HealthyMe pistachio/saffron style used | Pending |
| BP-02 | Member pages | Review buttons | No black/default buttons; HealthyMe pistachio/saffron style used | Pending |
| BP-03 | Forms | Review inputs/dropdowns/date/time | Rounded HealthyMe controls display consistently | Pending |

## Regression Guard

| Test ID | Area | Step | Expected Result | Status |
|---|---|---|---|---|
| RG-01 | NSP Scoring | Open reports/recalculate | No scoring mapping regression | Pending |
| RG-02 | Scheduling | Create schedule/reschedule | No scheduling regression | Pending |
| RG-03 | Daily Log | Open/save Daily Log | No Daily Log regression | Pending |
| RG-04 | Recipe/Exercise | Open pages | No content flow regression | Pending |
