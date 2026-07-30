# HealthyMe form success and reset inventory

## Required contract

Every successful write action must:

1. show a clear success message in the same form/section as the call-to-action;
2. preserve the message across any immediate Streamlit rerun;
3. clear transient entry fields after a create/send action;
4. close or leave the edit form after an update action;
5. retain saved records, selected member/profile context and audit history;
6. never clear a partially completed form after validation or backend failure.

## Admin / practitioner forms

| Workflow | Primary page | Main call-to-action(s) | Reset expectation | Delivery status |
|---|---|---|---|---|
| Create users | `17_Admin_User_Manager.py` | Create/activate user | Clear identity fields after success; retain role filter | Inventory |
| Access manager | `30_Admin_User_Access_Manager.py` | Save access | Retain selected user; clear temporary permission edits only after success | Inventory |
| Review queue / evaluation | `26_Admin_Review_Queue.py`, `11_Evaluation_Status.py` | Review/status actions | Retain selected member and assessment; close completed action panel | Inventory |
| Reassessment | `25_Admin_Reassessment_Manager.py` | Create/update reassessment | Clear new request fields; retain member | Inventory |
| Recipe manager | `15_Admin_Recipe_Manager.py` | Add, import, update, delete | Clear Add/Import after success; leave Edit after update | Implemented in this PR |
| Exercise manager | `16_Admin_Exercise_Manager.py` | Add, import, update, delete | Clear Add/Import after success; leave Edit after update | Implemented in this PR |
| Supplement manager | `39_Admin_Supplement_Manager.py` | Add, update, stop | Add form clears; edit/stop panel closes; success persists | Implemented in this PR |
| Recommendation Profile Builder | `38_Admin_Recommendation_Profile_Builder.py` | Save Setup/Meals/Exercise/Supplements, Publish | Retain loaded Profile ID; clear only newly added module row after confirmed save | Inventory |
| Packages | `41_Admin_Packages.py` | Create/edit/assign/replace | Clear create/assignment inputs; retain selected member/package after edit | Inventory |
| Scheduling | `32_Admin_Scheduling.py` | Create, reschedule, status update | Clear create/reschedule workspace after success; retain member context | Existing focused implementation; verify |
| Member communication | `31_Admin_Member_Communication.py` | Send message | Clear subject/body after confirmed send; retain recipient | Inventory |
| Daily Log guidance | `22_Admin_Daily_Log_Report.py` | Save/send guidance | Clear composer after success; retain member/date | Inventory |
| Question manager | `20_Admin_Question_Manager.py` | Add/update question | Clear create form; leave edit form after update | Inventory |
| Response editor | `21_Admin_Response_Editor.py` | Add/update response | Clear create form; leave edit form after update | Inventory |
| Admin five-page evaluation | Admin evaluation pages | Save/autosave/finalize | Never clear assessment content; success confirms persisted section | Inventory |

## Member forms

| Workflow | Primary page | Main call-to-action(s) | Reset expectation | Delivery status |
|---|---|---|---|---|
| Login | `01_Login.py` / native authorization | Sign in | Authentication-managed; do not clear or alter auth state through form hygiene | Excluded from form reset |
| My Profile | `07_My_Profile.py` | Save profile | Retain saved profile values; show success beside Save | Inventory |
| LAF | `03_LAF_Form.py` | Save/continue | Retain saved assessment answers; do not blank completed work | Inventory |
| NSP Page 1 | `04_NSP_Page1.py` | Save/continue | Retain saved answers; clear only transient validation messages | Inventory |
| NSP Page 2 | `05_NSP_Page2.py` | Save/continue | Retain saved answers; clear only transient validation messages | Inventory |
| Submit / Status | `06_Submit_Status.py` | Submit for review | Close submit action after success; retain assessment | Inventory |
| Body Mind | `19_Body_Mind_Connection.py` | Save/complete | Retain saved answers and completion status | Inventory |
| Food Journal | `18_Daily_Log.py` | Save Day | Retain the saved day; do not blank historical data | Existing daily-log contract; verify |
| Exercise Journal | `18_Daily_Log.py` | Save Exercise Entry | Retain saved entry; clear only a newly added unused row | Existing focused implementation; verify |
| My Schedule | `33_My_Schedule.py` | Acknowledge / request reschedule | Close successful request form; retain schedule | Existing focused implementation; verify |

## Delivery approach

This inventory is the source of truth for form hygiene. Content-manager forms are corrected first because they are the reported regression and have isolated create/edit semantics. Assessment and clinical forms must be corrected in workflow groups rather than through a global session-state clear, because clearing those forms indiscriminately could erase valid saved work.
