# Build Changelog

## HealthyMe Final UX Navigation + Speed Build - 11 May 2026

### Modified files

- `components/ui_common.py`
  - Added shared navigation helper functions.
  - Added user-priority action styling.
  - Added responsive navigation CSS.

- `pages/11_Evaluation_Status.py`
  - Added top and bottom navigation.

- `pages/12_Partial_Assessment_Report.py`
  - Added top and bottom navigation.

- `pages/13_Admin_Assessment_Form.py`
  - Added top and bottom navigation.

- `pages/14_Final_Assessment_Report.py`
  - Reordered page so Download Final Report appears first.
  - Moved final report structure/scoring explanation to end.
  - Added loading spinner while report file is prepared.
  - Added top and bottom navigation.

### Removed from package

- Historical version notes.
- Old UX patch helper file no longer required.
- Salary/payroll/WageWise leftover CSV/docs not used by HealthyMe runtime.
- Old Auth0/Supabase guide clutter not required to run the app.

### Not changed

- Scoring logic.
- Report calculation logic.
- Authentication logic.
- Supabase secrets or database URLs.


## v3 - Final Report Structure Lightweight Fix

- Replaced the structure/scoring toggle with a lightweight static reference card.
- Removed unnecessary rerun behavior from the structure section.
- Added cached final report generation so the Excel file is not rebuilt for minor UI interactions.
- No change to scoring, authentication, database storage, or report output.


## v4 - Navigation Blank Cleanup + Hidden Element Removal

- Back/Evaluation/Dashboard navigation now uses native `st.page_link` where possible.
- This reduces the visible blank-page flash caused by button-triggered page switching.
- Removed fake open/close HTML card wrappers that could render as empty boxes in Streamlit.
- Added empty-element cleanup CSS.
- Reduced duplicate global CSS injection.
- No scoring/auth/database/report logic changed.


## v5 - Feedback Round: Visual Flow, Allocation, Communication

- Fixed stronger button/text overlap rules.
- Cached dashboard data for smoother transitions.
- Aligned order between Today's Priority and Review & Assessment.
- Made Quick Action buttons visually consistent.
- Rebuilt Recommended Flow Guide as one clean card.
- Added Daily Log reminder queue button.
- Added recipe/exercise allocation tabs with Select All/Deselect All.
- Added member-side filtering for allocated recipes/exercises.
- Added Admin-Member Communication page and member inbox display.
- Email delivery is queued/flagged; actual production email sending still requires SMTP/email service configuration.


## v7 - Structural Reset Build

- Rebuilt Admin Dashboard into a disciplined structure:
  Executive Snapshot → Today's Priority → Main Workflows → Recommended Flow.
- Removed the chaotic 3-column priority layout.
- Removed aggressive global button styling that caused vertical/broken text.
- Standardized workflow order:
  Review Queue → Evaluation Status → Reassessment Manager.
- Made Manage Recipes / Manage Exercises allocation-first:
  Allocate to Member → Current Repository → Add → Import → Edit/Delete.
- Kept allocation, communication, daily-log reminder scaffolding.
- Added small build marker for verification only.
- No scoring, authentication, or report calculation logic changed.


## v8 - Layout Refinement

- Today's Priority returned to a horizontal desktop layout.
- First priority button no longer uses a different/primary color.
- Internal cards are slightly more compact across pages.
- Evaluation Status action labels are shortened and button wrapping hardened.
- Informational sections are reduced in visual footprint through compact alert styling.
- No assessment, scoring, auth, or report logic changed.


## v9 - Compact Tooltip Layout

- Replaced failed button-wrapping strategy with shorter visible labels and hover help text.
- Moved supporting explanations into tooltips/help wherever practical.
- Reduced page header size to keep proportions aligned with the rest of the UI.
- Made informational sections smaller and less intrusive.
- Shortened Evaluation Status action labels to reduce overlap risk.
- No scoring, auth, database, or report calculation logic changed.


## v11 - Designer Stable Build

- Rolled back the visible version-tag approach from v10.
- Rebuilt dashboard using stable compact cards instead of aggressive global CSS.
- Kept Today's Priority horizontal on desktop but removed cramped text/button pairing.
- Moved secondary explanations into button help text or collapsed Recommended Flow.
- Reduced awkward card sizing by letting content define card height.
- Kept Manage Recipes/Exercises allocation-first.
- No scoring, authentication, database, or report calculation logic changed.


## v12 - Consistent Build + Header Card Patch

- Fixed mixed build markers across pages.
- All legacy marker calls now resolve to current v12 build text.
- Retained header cards as requested.
- Restored/retained dashboard priority cards with:
  Initial Reviews / Final Reports / Reassessments.
- No scoring, authentication, database, or report calculation logic changed.


## v13 - Client-Safe Dashboard Redesign

- Redesigned dashboard around action-first priority cards.
- Removed internal design guidance copy from the user interface.
- Made Today's Priority focus on metric + action button + tiny microcopy.
- Cleaned Main Workflows into compact action cards.
- Moved Recommended Flow into collapsed expander.
- Unified old marker calls to show v13.
- No scoring, auth, database, or report calculation logic changed.


## v14 - Native Cards + Dashboard Flow Fix

- Fixed empty border/pill artifacts by removing raw HTML card wrappers from the dashboard.
- Rebuilt Today's Priority using native Streamlit bordered containers.
- Kept microcopy inside the same card as the button.
- Removed Recommended Flow expander and replaced it with a compact static flow card.
- Unified marker aliases to show v14.
- No scoring, authentication, database, or report calculation logic changed.


## v16 - WakeMe Patch

- Added `.github/workflows/wakeme.yml`.
- Added `scripts/wakeme.py`.
- Added `docs/WAKEME_SETUP.md`.
- Workflow pings the deployed app every 10 minutes.
- Workflow uses inline Python and no Node-based GitHub actions.
- Requires GitHub secret or variable `WAKEME_URLS`.
- No UI, scoring, authentication, database, or report calculation logic changed.


## v18 - Sturdy WakeMe

- Applied Salary Management System scheduling learnings.
- Added manual workflow URL override.
- Reads secret and variable separately.
- Adds cache-busting query parameter.
- Uses 5 retries with progressive waiting.
- Adds extra 10:00 AM IST safety schedule.
- Logs UTC time and configuration diagnostics.
- No app UI, scoring, authentication, database, or report calculation logic changed.


## v19 - Body-Mind Visibility Fix

- Fixed mismatch where admin could enable Body-Mind but Member Home still hid it if `admin_completed` was false.
- Body-Mind now appears whenever `body_mind_unlocked=True`.
- Recipes/exercises remain gated by `admin_completed=True`.
- Updated Body-Mind Control page copy.
- No scoring, authentication, database, or report calculation logic changed.


## v20 - Body-Mind Activation Safety

- Added duplicate activation safety for Body-Mind Connection.
- If Body-Mind is already active, Admin Assessment page now shows an informational message instead of acting like a new activation is needed.
- Body-Mind Access Control now shows 'already activated' and disables duplicate activation.
- Disabling requires an explicit checkbox to reduce accidental changes.
- No scoring, authentication, database, or final report calculation logic changed.


## v21 - Body-Mind Preserve Activation

- Fixed safety gap where Admin Assessment could unintentionally disable Body-Mind if the checkbox was unchecked/stale.
- Admin Assessment can now enable Body-Mind, but it will not disable an existing activation.
- Body-Mind disable remains only through explicit Body-Mind Access Control safety flow.
- Clarified Member Home lock message for Body-Mind vs Recipe/Exercise access.
- No scoring, authentication, database, or final report calculation logic changed.


## v22 - Body-Mind Auto Activate on Admin Complete

- Fixed split-flag confusion between `admin_completed` and `body_mind_unlocked`.
- When `admin_completed=True` is set, `body_mind_unlocked=True` is now also set.
- Final Admin Assessment completion explicitly activates Body-Mind.
- Body-Mind Access Control remains the place for explicit disable.
- No scoring, authentication, database, or final report calculation logic changed.


## v23 - Stability + Visibility Fix

- Applied clarified Body-Mind business rule:
  admin final completion + admin activation selection = Body-Mind visible.
- Removed the assumption that admin completion alone should auto-activate Body-Mind.
- Admin Assessment final submit now applies selected Body-Mind activation and preserves existing activation.
- Body-Mind Access Control requires final admin completion before activation.
- Added v23 version line below page header/topbar.
- Added minor logout transition polish.
- Removed duplicate build/patch/archive artifacts only.
- No scoring, final report calculation, auth structure, or DB schema changes.


## v24 - Body-Mind + Version Placement Fix

- Moved version display under the HealthyMe brand in the page header.
- Added shared Body-Mind activation sync helper.
- Admin Assessment final submit now syncs Body-Mind activation after admin completion if activation is selected.
- Body-Mind Access Control uses the same activation sync path.
- Member Home message now distinguishes between admin completion pending and activation pending.
- No scoring, report calculation, auth structure, or DB schema changes.


## v25 - Body-Mind State Sync Fix

- Added `body_mind_activation_requested` workflow flag.
- Body-Mind activation request is now preserved from either approved path.
- If request exists and admin final completion is done, Body-Mind unlocks.
- Body-Mind Access Control can record the activation request before final completion.
- Explicit disable clears request and visibility.
- No scoring, report calculation, auth structure, or DB schema changes.


## v26 - Finalization Lock + Body-Mind Sync

- Added finalization lock for Admin Assessment page.
- After Save and Generate Final Report succeeds, five admin pages become read-only/locked.
- Removed repeated Body-Mind sync/write calls from final generation path.
- Added `finalize_admin_assessment()` helper as the single finalization path.
- Added self-heal for historical records where finalization + activation request exists but Body-Mind is still hidden.
- Added spinner during finalization to make the 4-5 second wait visible.
- No scoring or final report calculation logic changed.


## v27 - Final Report NSP Data Integrity + Body-Mind Carry Forward

- Final Report now resolves NSP1/NSP2 from selected assessment instance first.
- If no selected instance exists, it uses the latest submitted/finalized instance.
- Legacy member-level NSP responses remain fallback.
- Added report diagnostics for NSP source, selected instance, NSP1/NSP2 counts, and Digestive score.
- Added same NSP source resolver to Partial Report.
- Carried forward v26 Body-Mind self-heal into Member Home.
- No scoring formula, Digestive mapping, auth structure, or DB schema changes.


## v28 - Body-Mind Final Unlock + Version Cleanup

- P0 fix: Body-Mind now unlocks automatically when admin final review/final report is ready.
- Member Home self-heals historical records where final report is ready but Body-Mind remains hidden.
- Body-Mind Access Control self-heals the same mismatch.
- Removed duplicate standalone version line.
- Version now appears next to HealthyMe inside the header/topbar.
- Retains v27 Final Report NSP Data Integrity fix.
- No scoring formula, final report calculation, auth structure, or DB schema changes.


## v29 - Manual Body-Mind Unlock

- Reverted v28 automatic Body-Mind unlock.
- Body-Mind now requires:
  1. Admin final completion / Save and Generate Final Report
  2. Manual admin activation from either approved path
- Final report download is not required.
- Member Home copy now states manual activation is pending after final review.
- Version remains next to HealthyMe; duplicate standalone version line remains suppressed.
- Retains v27 Final Report NSP Data Integrity fix.


## v30 - Manual Body-Mind Unlock Control Applied to Current Build

- Applied v30 directly to `healthyme-app-main (19.05.2026).zip`.
- Added explicit Body-Mind activation control on finalized Admin Assessment page.
- Added explicit Body-Mind activation control on Body-Mind Access Control page.
- Added `manually_unlock_body_mind_after_finalization()`.
- Keeps client rule: finalization is prerequisite; manual admin activation is required.


## v31 - Workflow + Body-Mind Sync

- Added central sync between workflow and assessment instance status.
- Finalized workflow now also finalizes stale assessment instances.
- Manual Body-Mind activation also repairs finalized workflow/instance status.
- Member Home now treats workflow finalization as source of truth over stale instance status.
- Body-Mind still requires manual admin activation after finalization.


## v32 - Manual Body-Mind Hard Sync

- Manual Body-Mind activation is now one-click.
- Activation writes both request and visibility together.
- Member Home self-repairs only if finalization is complete AND manual activation request exists.
- Does not unlock on finalization alone.
- Reduces multiple-click activation issue.


## v33 - Body-Mind Explicit Access

- Added explicit `body_mind_access` marker independent of workflow flags.
- Manual admin activation writes both workflow unlock and explicit access marker.
- Member Home checks explicit marker as fallback.
- Body-Mind Access Control checks explicit marker as fallback.
- Removed outdated v22 Body-Mind note.
- Simplified logout to avoid double refresh behavior.


## v34 - Body-Mind NameError + Logout Fix

- Fixed `explicit_body_mind_access` NameError in Body-Mind Access Control.
- Ensured explicit Body-Mind access marker is read before visibility cards render.
- Removed outdated v22 Body-Mind note line.
- Simplified logout to avoid login page then second refresh behavior.
- Retains v33 explicit Body-Mind access marker.


## v35 - Body-Mind Page Guard Fix

- Fixed the actual Body-Mind page guard.
- Member Home already showed the Body-Mind button using explicit access marker.
- Page 19 now also checks explicit access marker.
- This resolves the button-visible-but-page-blocked issue.


## v36 - Body-Mind Text Removal + Autosave Check

- Removed Body-Mind explanatory text: "Auto-save enabled..." and consent statement line.
- Confirmed LAF, NSP Page 1, NSP Page 2, and Body-Mind have autosave behavior.
- Confirmed Admin Assessment/Five Admin Pages are not autosaved; they require Save Draft or Save and Generate Final Report.
- Retains v35 Body-Mind page access guard fix.


## v36 Refresh - Body-Mind Admin State + Autosave Check

- Body-Mind Access Control now recognizes explicit Body-Mind access and shows Active state.
- Admin pages no longer show Activate Body-Mind Connection when Body-Mind is already active.
- Activation UI normalized to one-click activation for finalized members.
- Removed old checkbox + button activation inconsistency.
- Retains Body-Mind auto-save text removal and autosave confirmation.


## v37 - Remove Body-Mind Activation Checkbox

- Removed legacy checkbox: "Make Body-Mind Connection page visible to this member".
- Normalized Body-Mind Access Control to one-click activation after finalization.
- Non-finalized members show informational text instead of disabled checkbox.
- Active members show active state and no activation button.


## v38 - Body-Mind Disabled Button UI

- Removed redundant prerequisite message in Body-Mind Access Control.
- Non-finalized members now show one prerequisite message and a disabled Activate Body-Mind Connection button.
- Finalized inactive members retain one-click activation.
- Active members show active state and no activation button.


## v39 - Admin Autosave

- Added auto-save draft behavior to Admin 5 Pages.
- Admin Assessment now saves draft values on every interaction/rerun.
- Final report generation remains manual through Save and Generate Final Report.
- Save Draft button retained as Save Draft / Confirm Changes.
- Retains v38 Body-Mind disabled button UI and previous Body-Mind access fixes.


## v40 - Body-Mind Status Sync

- Fixed Body-Mind Access Control status mismatch.
- Activation now shows Activated when Visibility is Visible.
- Both cards use the same active-state source: workflow unlock OR explicit access marker.
- Retains v39 Admin Autosave and earlier Body-Mind fixes.


## v41 - Daily Log Flow

- Implemented daily food journal format based on Sample_Food_Journal.xlsx.
- Added member-friendly structured food journal entry page.
- Added sample reference entries.
- Added Admin Daily Log button under each member in Evaluation Status.
- Added Admin supervision notes for each member's Daily Log.
- Supervision notes appear on member Daily Log and queue notification/email marker.
- Updated Daily Log Excel report to match the journal format.


## v42 - Day-based Daily Log

- Redesigned member Daily Log as one full-day journal grouped by date.
- All meal types now sit in one daily group: Early Morning, Breakfast, Mid Morning, Lunch, Evening Snack, Dinner, Bedtime, Other.
- Each meal section captures Time, Food, Water, Portion Size, and Mood/Energy.
- Full-day fields capture Physical Activity, Poop rounds/feeling, and Overall Notes.
- Admin supervision notes now attach to a specific day's food log.
- Member sees supervision notes under the selected date.
- Admin Daily Log Report supports date-specific review, notes, notification queue, and Excel download.


## v43 - Progressive Daily Log + Repository

- Member can save individual meal sections progressively.
- Member can still save the whole daily journal at once.
- Added admin-editable meal type repository.
- Default active meal sections: Breakfast, Lunch, Evening Snack, Dinner, Bedtime.
- Admin can add/remove/rename/reorder meal sections.
- Admin Daily Log Report follows the repository order.


## v44 - Daily Log One-Section + Other Slots

- Moved Reference format from sample journal to the bottom.
- Replaced bulky expand/collapse meal layout with compact section buttons.
- Only one meal section is open at a time.
- Switching sections is blocked if current section has unsaved changes.
- Added repeatable Other slots: Other 1, Other 2, etc.
- Admin repository default includes Other.
- Admin report handles dynamic Other sections.


## v45 - Daily Log Compact Other Fix

- Made Reference format from sample journal more compact and aesthetic at the bottom.
- Made meal section controls more compact.
- Forced Other section availability for existing repositories.
- Added clear + Other button for repeatable Other 1, Other 2, etc.
- Retained unsaved-change warning before switching sections.


## v46 - Admin Info Cleanup + Daily Log Layout

- Removed grey informative caption-style statements from admin-facing pages.
- Removed Daily Log helper text examples including Gentle reminder and supervision note explanation.
- Put Select member and Select food log date side by side in Admin Daily Log Report.
- Retains v45 Daily Log compact Other flow.


## v47 - Logout + Daily Log Backcompat + Reference Toggle

- Replaced the member Daily Log reference expander with a compact Show / Hide sample journal format button.
- Admin Daily Log Report now reads older row-based food journal entries as well as new day-based logs.
- Logout now clears app session and calls Streamlit logout without additional rerun/switch_page calls.
- Login page authenticated logout uses the same logout handler.


## v48 - Nutritionist Message Archive

- Changed "Messages from Admin" to "Messages from Nutritionist".
- Replaced message expander with a cleaner Show / Hide nutritionist messages button.
- Added Mark as read / archive action.
- Read messages disappear from Member Home and are stored in Daily Food Journal archive.
- Daily Log supervision notes now use Nutritionist wording.


## v49 - Logout Session Hardening

- Logout now clears app session and routes to Login with logout flag.
- Login page blocks auto-restore while signed_out/logout_requested is active.
- Added Complete secure logout action on Login page.
- Removed dangerous st.logout + switch/rerun combination from deep app pages.
- Continue with Auth0 clears logout flags and starts fresh login.


## v50 - Member Home Message + Journey Compact

- Removed remaining Streamlit expander for Messages from Nutritionist.
- Added clean Show / Hide nutritionist messages button.
- Retained Mark as read / archive action.
- Reduced Journey Summary padding/spacing and removed bulky divider gap.


## v51 - Timezone + Notes Archive + Back to Top

- Nutritionist note timestamps now render in local formatted time.
- Member Home nutritionist messages also render formatted local timestamps.
- Nutritionist Notes Archive now includes all Daily Log Nutritionist Notes plus read/archived nutritionist messages.
- Added floating Back to Top control across scrolling pages.


## v52 - Login Logout Block Bottom

- Moved the signed-out / Complete secure logout section to the bottom of the login column.
- Removed the signed-out block from above Secure Login.
- Retains v51 timezone, Nutritionist Notes archive, and Back to Top fixes.


## v53 - UI Helper Import Fix

- Fixed Member Home ImportError by exposing `format_local_ts` in `components.ui_common`.
- Fixed Member Home ImportError by exposing `render_back_to_top` in `components.ui_common`.
- Shared helpers now sit near the top of `ui_common.py` so all pages can import them reliably.
- Retains v52 login logout placement and v51 timezone/archive/back-to-top fixes.


## v54 - Nutritionist Read Archive Fix

- Fixed unread/read archive flow for nutritionist messages.
- Read / Archive removes message from Member Home and stores it in Daily Food Journal archive.
- Added archive success/error feedback.
- Added auto-archive for nutritionist messages whose linked date has passed.
- Removed duplicate date-specific Nutritionist notes from the Daily Log entry screen.
- Nutritionist Notes Archive remains the storage location for notes/messages.


## v55 - Admin Dashboard Import Fix

- Fixed Admin Dashboard NameError by importing missing `card_start` / `card_end`.
- Scanned pages and repaired missing `components.ui_common` helper imports.
- Cleaned duplicate Back to Top calls.
- Retains v54 Nutritionist read/archive behavior.


## v56 - Daily Log Nutritionist Notification

- Fixed missing member notification after nutritionist saves a Daily Log note.
- Daily Log note save now writes to both member-visible messages and notification/email queue.
- Member Home shows unread Nutritionist notes.
- Read / Archive keeps the message in the Nutritionist Notes Archive.


## v57 - Daily Log + LAF Restructure

- Unread Nutritionist notifications remain visible until member reads/archives them.
- Water intake moved to Full-day details as Select / 0 to 10 Litres dropdown in 0.5 increments.
- Removed Nutritionist Notes Archive section.
- Added Nutritionist Notes column under Recent saved days.
- Latest note shows in the table; same-day note history opens for the selected date.
- Removed orange-highlighted fields from LAF.
- Moved pink-highlighted stress/lifestyle reflection fields to Body-Mind Connection.
- Removed Dietary Habits from member LAF and added disabled admin placeholder.


## v58 - LAF Restructure Correction

- Corrected v57 LAF restructure.
- Restored `major_trauma_5_years` to LAF under Page 1 / Stress and trauma.
- Removed `major_trauma_5_years` from Body-Mind Connection.
- Retained all other v57 fixes.


## v59 - Structured Poop Rounds

- Split old "Poop rounds and feeling after poop" field.
- Added Poop rounds dropdown: Select, 1 to 10.
- Dynamic timing boxes appear based on selected number of poop rounds.
- Added separate Feeling after poop text box.
- Admin Daily Log Report shows the structured poop fields.
- Retains v58 LAF restructure correction.


## v60 - Poop Layout Refinement

- Moved Feeling after poop under the Physical activity column for better visual alignment.
- Poop timing inputs now render in a 3-column grid.
- Maximum Poop rounds reduced from 10 to 9.
- Retains v59 structured poop fields and v58 LAF restructure correction.


## v61 - Stability + Premium UX Cleanup

- Applied compact internal page header treatment to working pages.
- Added shared button hierarchy and compact table styling through global CSS.
- Polished Daily Log Recent saved days table.
- Added cached config loader for static JSON configs.
- Added db facade modules to prepare safe future db.py split without changing business logic.
- Kept existing business logic unchanged.


## v62 - Recent Saved Days Premium Layout

- Replaced Recent saved days dataframe with premium card/table layout.
- Kept headers intact: Date, Meals Logged, Water, Notes, Nutritionist Notes, Action.
- Meals Logged now displays simple text progress like 3/5.
- View history opens same-day nutritionist note history only.
- UI-only patch; business logic unchanged.


## v63 - Recent Saved Days Borders + Toggle

- Added aesthetic boundary lines to the Recent saved days premium table.
- Changed View history to View / Hide history toggle behavior.
- View opens same-date note history; Hide closes it.
- UI-only patch; business logic unchanged.


## v64 - Recent Saved Days Refinement

- Reduced the View / Hide history button size.
- Improved button alignment with row content.
- Made Recent saved days table borders more prominent.
- Reduced Nutritionist Notes text size and made it more compact.
- UI-only refinement; business logic unchanged.


## v65 - Daily Log + Admin UI Fixes

- Member Recent saved days now shows Meal type and food.
- Admin Daily Log full-day details now includes Water Intake before Physical Activity.
- Removed helper info text from Admin-Member Communication.
- Reduced extra space in Send Message and Recent messages sections.
- Fixed bottom Back to Dashboard button overlap.


## v66 - Nutritionist Message Dedupe

- Fixed duplicate Messages from Nutritionist issue.
- Nutritionist Daily Log note save is now idempotent for same member/date/message.
- Duplicate member messages are deduped before display.
- Duplicate notification queue rows are prevented for same source message.


## v67 - View History Alignment Fix

- Reduced Recent saved days View / Hide history button size.
- Restored cleaner alignment closer to previous build behavior.
- Reduced action column width and removed button stretching.
- UI-only fix; business logic unchanged.


## v68 - View History Micro Alignment

- Reduced View / Hide history button font size.
- Pulled action button upward to align better with row text.
- Tightened action column width and surrounding spacing.
- UI-only micro patch; business logic unchanged.


## v69 - Inline History Button Alignment

- Removed separate Streamlit button row that caused View History misalignment.
- View / Hide control now renders inside the same Action table cell.
- History opens inline for the same date using an HTML details panel.
- UI-only alignment fix; business logic unchanged.


## v70 - Streamlit Native Recent Saved Days

- Removed v69 raw inline HTML table/details implementation.
- Rebuilt Recent saved days using Streamlit-native columns and buttons.
- Prevents raw HTML from appearing on screen.
- Keeps View / Hide history state behavior.
- UI-only correction; business logic unchanged.


## v71 - Compact Nutritionist History Block

- Made Nutritionist note history section more compact.
- Reduced font size and padding of history cards.
- Reduced spacing between history cards.
- UI-only micro patch; business logic unchanged.


## v72 - Final Report Import Fix

- Fixed Final Assessment Report NameError by adding missing `utility_logout_bar` import.
- Scanned all pages and repaired missing `ui_common` helper imports.
- Retains v71 compact Nutritionist note history styling.
- No business logic changed.


## v73 - Guard Import Fix

- Fixed Final Assessment Report NameError by adding missing `require_admin` import.
- Scanned all pages and repaired missing `require_admin` / `require_member` imports.
- Re-scanned `ui_common` helper imports.
- No business logic changed.


## v74 - Final Report JSON Import Fix

- Fixed Final Assessment Report NameError by adding missing `json` import.
- Scanned pages for common missing standard-library imports.
- No business logic changed.


## v75 - Final Report Diagnostics UI

- Moved Report data diagnostics under the Final Assessment Report download button.
- Replaced expander with a cleaner Show/Hide diagnostics button.
- Removed Download Final Report explanatory helper text.
- UI-only cleanup; business logic unchanged.


## v76 - Mobile Daily Log Timing Fix

- Fixed mobile Poop Timing order to show 1,2,3,4... instead of column order 1,4,7.
- Active Poop Timing fields now show placeholder: Enter the Poop Time.
- Inactive Poop Timing fields remain disabled with placeholder: Not active.
- Meal Timing now shows recommended timing by meal type.


## v77 - Meal Timing + Daily Log UI Alignment Fix

- Restored fixed meal sections: Breakfast, Lunch, Evening Snacks, Dinner, Bedtime.
- Replaced Other with + Snacking and repeatable Snacking sections.
- Added 12-hour HH:MM AM/PM meal timing validation.
- Enforced client-approved meal timing windows.
- Snacking is allowed only outside standard meal windows.
- Improved Recent saved days table vertical alignment.
- Standardized save button colors to HealthyMe schema.

## v78 - Daily Log Compact Time Picker and Layout Polish

- Removed visible version text from member-facing header branding.
- Meal Timing now uses Hour / Minute / AM-PM selectors.
- Reduced Feeling after poop vertical space.
- Save meal button now spans the full row.

## v79 - Micro Polish Build

- Tightened Daily Log meal selector spacing and helper text.
- Rebalanced the laptop Full-day details layout.
- Moved Feeling after poop to a full-width compact row to remove excess blank space.
- Applied compact polish to Daily Log controls while keeping business logic unchanged.

## v80 - Daily Log Laptop Balance Fix

- Rebalanced meal section buttons using Option A.
- Standard meals now render as Breakfast/Lunch/Evening Snacks, then Dinner/Bedtime.
- Snacking sections render separately as Snacking 1, Snacking 2, Snacking 3.
- Tightened Full-day details layout to reduce laptop blank space.
- No timing/save/business logic changed.

## v81 - Daily Log Full-day Rebalance + Poop Zero Fix

- Restored 0 option in Poop rounds.
- Rebalanced Full-day details for laptop view.
- Moved Overall notes under Physical activity to remove unused blank space.
- Kept Feeling after poop as a compact full-width row.
- No meal timing or save logic changed.

## v82 - Full-day Details HealthyMe Structure Alignment

- Implemented the accepted Full-day details structure in HealthyMe style.
- Water intake and Poop rounds aligned in the top row.
- Physical activity aligned left; Poop timings and Feeling after poop aligned right.
- Overall notes moved to a full-width row.
- Poop rounds reduced to 0-6 and Poop timings reduced to 6 fields.

## v83 - Physical Activity Height Balance Fix

- Increased the Physical activity text area height in Full-day details to reduce empty space on laptop.
- No other logic or layout behavior changed from v82.

## v84 - Date + Button + Header Alignment Polish

- Made the Food journal date section more prominent.
- Restored Save Full-Day Journal to standard HealthyMe button styling.
- Improved Recent saved days header alignment.

## v85 - Date Context Emphasis Polish

- Strengthened the Food journal date section visually without adding helper text.
- Increased prominence using a stronger HealthyMe-style card treatment and bolder date input styling.

## v86 - Body-Mind Cached Loader Fix

- Fixed Body-Mind Connection NameError caused by missing `load_body_mind_questions_cached`.
- Added a local cached wrapper that calls `load_body_mind_questions()`.
- No unlock/save business logic changed.

## v87 - Body-Mind Loader Regression Guard

- Replaced fragile Body-Mind cached loader with a robust page-local loader.
- Loader tries shared loader sources first, then local JSON files, then embedded fallback questions.
- Added a regression scan so `load_body_mind_questions_cached()` cannot be called before definition.
- No Body-Mind unlock/save logic changed.

## v88.1 - Mobile Visual Spacing Polish

- Visual-only spacing polish on top of v88.
- Tightened Snacking helper spacing.
- Tightened Recent saved days label/value rows.
- Reduced helper-text visual weight for mobile.
- No data/save/business logic changed.

## v89R - Rollback to Stable v88.1 + Input Control Guard

- Rolled back incorrect v89 hybrid input-control implementation.
- Restored the last stable v88.1 Daily Log visual/mobile spacing state.
- Added guard note: do not globally alter Streamlit controls for a mobile-only requirement.
- No business logic, save logic, Body-Mind logic, report logic, or nutritionist-note logic changed.

## v90 - Mobile-Specific Input UX Spike

- Replaced Meal Timing sliders with 3 dropdown cells: HH, MM, AM/PM.
- Replaced Water Intake slider with dropdown from Select, 0 to 10 Litres in 0.5 increments.
- Replaced Poop Rounds slider with dropdown from Select, 0 to 6.
- Confirmed that true mobile-only widget rendering should not be forced globally in Streamlit without a proper front-end/mobile detection layer.
- No save/business logic changed.

## v90A - Mobile Detection Spike

- Added controlled mobile mode using `?device=mobile`.
- Added temporary diagnostic banner showing device mode and rendered control set.
- Desktop default keeps v90 dropdown controls.
- Mobile test branch renders native time picker and segmented/chip controls only when explicitly activated.
- No save/business logic changed beyond mapping selected input values to the existing payload fields.

## v90A.1 - Mobile Detection NameError Fix

- Fixed Daily Log NameError by moving `get_device_mode_for_spike()` definition above the diagnostic call.
- Added scan to verify helper definitions occur before their first call.
- No save/business logic changed.

## v91 - Mobile-only Stepper Input Controls

- Mobile-only branch: Water Intake uses a stepper from 0 to 10 litres in 0.5 increments.
- Mobile-only branch: Poop Rounds uses a stepper from 0 to 6.
- Mobile-only branch: Meal Timing keeps native time picker.
- Desktop/default branch remains unchanged with dropdown controls.
- Mobile mode activates only with `?device=mobile`.
- No save/business logic changed beyond mapping the selected values to existing payload fields.

## v91.1 - Mobile Auto-Detect + Compact Stepper Fix

- Added best-effort automatic mobile detection from request/user-agent headers.
- Kept query overrides: `?device=mobile` and `?device=desktop`.
- Compact stepper layout for Water Intake and Poop Rounds.
- Changed plus button to visible `＋`.
- Desktop/default branch remains dropdown based.
- No save/business logic changed.

## v91.2 - Mobile Time + Horizontal Stepper Fix

- Added manual `Use mobile input controls` fallback toggle.
- Native time picker is available when mobile controls are active.
- Changed stepper styling to force a compact horizontal `- value +` layout where Streamlit allows.
- No save/business logic changed.

## v91.3 - Mobile Control Stability Fix

- Replaced broken custom column-based stepper with stable `st.number_input` controls for mobile mode.
- Keeps Water Intake range 0–10 litres in 0.5 increments.
- Keeps Poop Rounds range 0–6.
- Keeps mobile time input where mobile mode is active.
- Desktop/default branch remains dropdown based.
- Notes: true custom horizontal steppers and guaranteed native mobile time picker need a custom Streamlit component or native/Flutter front end.

## v92 - Custom Mobile Time Component + Validation Restore

- Added a local custom Streamlit component for mobile meal timing using browser `input type=time`.
- Mobile Meal Timing no longer relies on `st.time_input`.
- Restored visible timing-window validation feedback.
- Improved mobile number_input look and feel for Water Intake and Poop Rounds.
- Desktop/default branch remains unchanged.

## v92.1 - Mobile Time Active + Number Button Size Fix

- Improved custom mobile time input styling so it does not look greyed out.
- Explicitly removed disabled/readonly attributes from the custom time input.
- Increased Water Intake and Poop Rounds number_input button/icon size on mobile.
- No save/business logic changed.

## v92.2 - Component Rollback + Mobile Stability Fix

- Removed failing custom Streamlit component for mobile time input.
- Restored safe Streamlit-native 3-cell Meal Timing controls in mobile mode.
- Kept meal timing validation visible.
- Kept improved number_input styling for Water Intake and Poop Rounds.
- No save/business logic changed.

## v92.3 - Input Styling Alignment

- Matched Meal Timing selectbox styling with Water/Poop number input color schema on mobile.
- Retained safe 3-cell Meal Timing controls.
- Retained visible timing validation.
- No custom component added.
- No save/business logic changed.

## v92.4 - Input Format Schema Alignment

- Aligned Meal Timing, Water Intake, and Poop Rounds into consistent HealthyMe-style input bands.
- Matched label hierarchy, border, radius, color, control height, and spacing.
- Collapsed duplicate Streamlit labels where schema labels are shown.
- No save/business logic changed.

## v92.5 - Daily Log Input Schema Repair

- Removed unreliable HTML schema-band wrapping around Streamlit widgets.
- Applied direct styling to actual selectbox and number_input widgets.
- Fixed duplicate/collapsed label mismatch for Water and Poop controls.
- Balanced Feeling after poop and Physical activity heights.
- Kept timing validation active.
- No save/business logic changed.

## v92.6 - Daily Food Journal Report Date Selector Fix

- Moved All saved days above selected-date journal detail where detected.
- Removed date_input min/max restrictions so all calendar dates can be selected.
- No save/business logic changed.

## v92.8 - Daily Food Journal Report Correction

- Corrected v92.7 implementation gaps.
- Moved Download Daily Food Journal Excel directly under All saved days.
- Ensured date selector is a date_input allowing all calendar dates.
- Restored Full-day details heading and added the black row after that section.
- Kept Back/Dashboard navigation at page bottom.
- No save/business logic changed.

## v92.10 - Daily Food Journal Report Surface Fix

- Removed visible redundant Nutritionist note label.
- Aligned Food Journal empty-state box and Nutritionist note text area surface treatment.
- Added spacing balance between the two sections.
- No report business logic changed.

## v92.11 - Daily Food Journal Report Hard UI Patch

- Hard-patched Food Journal no-data surface and Nutritionist note textarea surface.
- Collapsed and scoped the redundant Nutritionist note label.
- No report business logic changed.

## v93 - Recipe + Exercise UX/Admin Upgrade

- Upgraded existing Recipe and Exercise member modules to mockup-inspired landing and detail flows.
- Added admin-side fields for image URL, title, timing/duration, calories and details.
- Expanded recipe/exercise CSV schemas while retaining existing allocation logic.
- Kept current CSV repository architecture; persistent image upload should later use Supabase Storage.

## v94 - Supabase Storage Hybrid Image Upload

- Added Supabase Storage image upload helper.
- Added public/private bucket handling for recipe and exercise assets.
- Admin can upload images and select visibility.
- Member pages resolve public URLs or signed private URLs at runtime.
- CSV schemas expanded with image_bucket, image_path and image_access_type.

## v94.1 - Image Preview Guard Fix

- Fixed Admin Recipe Manager image preview crash when image_url is blank, nan, none, or a non-URL value.
- Added the same preview guard to Admin Exercise Manager.
- No storage upload logic or member-side UX changed.

## v94.2 - Member Content UI Alignment

- Aligned Recipe and Exercise page headers closer to HealthyMe app style.
- Removed the large Recipe/Exercise tab header block.
- Kept search + filter + favourite controls in one line.
- Removed the extra Open Recipes/Open Exercises redirection buttons.
- Retained v94.1 image preview guard and v94 Supabase Storage hybrid logic.

## v94.3 - Member Content Hard Layout Fix

- Directly removed Body-Mind Connection primary button styling from Member Home.
- Replaced Recipe/Exercise custom header with standard HealthyMe compact topbar.
- Rebuilt search/filter/favourite controls using real Streamlit columns.
- Removed extra Recipe/Exercise redirect buttons.
- Retained v94 Storage and v94.1 preview guard logic.

## v94.4 - Content Button Functional Alignment

- Normalized Body-Mind member-home and page buttons to general HealthyMe button style.
- Kept Recipe/Exercise pages on compact_topbar header.
- Rebuilt Recipe/Exercise toolbar with functional search, filter and favourites.
- Added card-level favourite toggles.
- Retained v94 Supabase Storage and v94.1 image preview guard.

## v94.5 - Card Action Button Proportion Fix

- Aligned Recipe and Exercise card action buttons to same height.
- Kept the View button wide and the favourite button compact/square.
- Retained v94 Storage, v94.1 preview guard and v94.4 functional filter/favourite logic.

## v94.6 - Page-Level Button Normalization

- Applied page-level Recipe/Exercise button normalization because wrapper-scoped CSS was not affecting Streamlit's rendered button structure.
- Forced View and favourite buttons to the same height.
- Kept View button wide and favourite button compact/proportional.
- Retained v94 Storage, v94.1 preview guard and v94.4 functional search/filter/favourite logic.

## v95 - NSP Reassessment Instance Hardening

- Client confirmed reassessment scope is NSP Page 1, NSP Page 2, or both only.
- Added instance-aware admin assessment storage.
- Admin Assessment page can open reassessment instances even if initial member workflow is already finalized.
- Final Report and report engine now respect selected instance admin review/final readiness.
- Review Queue uses instance-level final readiness instead of global workflow readiness.

## v95.1 - Full Report Button Status Fix

- Fixed Evaluation Status member action row.
- Full Report button is no longer disabled when report is pending.
- Button now navigates to Final Assessment Report page, where pending state is handled.
- Added CSS to keep the four action buttons aligned.
- Retained v95 NSP reassessment instance hardening.

## v95.2 - Final Report Top System Card Fix

- Fixed top summary card on Final Report.
- Removed hardcoded Digestive Score card.
- Card now shows the highest selected NSP system and score, matching Selected top systems preview.
- Retained v95 NSP reassessment hardening and v95.1 Full Report button fix.

## v95.3 - Evaluation Status Button Normalization

- Fixed the four action buttons on Evaluation Status so they render with the same height and equal-width column behavior.
- Aligned button radius, padding, and primary styling to the HealthyMe standard template.
- Retained v95.2 Final Report top system card fix.

## v95.4 - Evaluation Status Micro-Polish

- Added a micro-polish pass to the Evaluation Status member action block.
- Refined vertical spacing around the workflow note and button row.
- Normalized the action-button shadow and visual weight to better match the HealthyMe standard template.
- Retained all existing v95.3 and v95.2 behavior and fixes.

## v95.5 - Eval Status Member Row Action Fix

- Removed the broken member-toggle wrapper that was causing blank thin rows.
- Updated the member row instruction to match actual behavior.
- Added explicit [+] and [−] markers to member buttons.
- Added hard action-row styling for Partial Report / Admin Page / Full Report / Daily Logs.
- Retained v95.4, v95.3 and v95.2 fixes.

## v95.6 - Eval Status Fixed Action Grid

- Replaced repeated wrapper-based attempts with a fixed 4-column action grid.
- Forced Partial Report, Admin Page, Full Report and Daily Logs into equal-width grid cells.
- Normalized action-button height, width, radius, padding and visual styling.
- Retained v95.5 member row fix and all prior v95 fixes.

## v95.7 - Admin Version + Button Template Fix

- Added visible Admin Build version marker on Admin Dashboard and Evaluation Status.
- Changed Evaluation Status action buttons to the general HealthyMe outlined button style.
- Preserved fixed 4-column layout for Partial Report, Admin Page, Full Report and Daily Logs.
- Retained v95.6 fixed action grid and all earlier v95 fixes.

## v95.8 - Admin Version Placement + Action Height Fix

- Corrected the admin build version display to v95.8.
- Removed the separate version pill and placed the version inline beside HealthyMe on admin headers.
- Normalized the Evaluation Status action buttons so Full Report matches the other buttons in height and proportions.

## v95.10 - Eval Status Nav Row Revert Fix

- Fixed the broken Back/Dashboard overlap introduced in v95.9.
- Restored Evaluation Status top and bottom nav to stable render_page_nav.
- Removed overly broad CSS sibling selectors affecting unrelated rows.
- Kept action buttons scoped to the opened-member action grid.

## v95.11 - Full Report Button Height Hard Fix

- Hard-normalized Partial Report, Admin Page, Full Report, and Daily Logs to the same height.
- Added stricter action-row-only CSS to prevent Full Report from rendering taller.
- Retained the v95.10 safe navigation-row fix.

## v95.12 - Evaluation Status Final Micro-Polish

- Final polish pass limited to Evaluation Status page only.
- Refined top/bottom nav spacing, hero spacing, member row spacing, member status cards and action row rhythm.
- Kept action buttons locked to the same height, including Full Report.
- Updated inline admin version label to v95.12.
- No logic changes.

## v95.13 - Full Report Button DOM Normalization

- Removed the `help="Open final assessment report"` parameter from the Full Report button.
- This makes Full Report render with the same Streamlit button structure as the other three action buttons.
- Added a scoped action-row hardener for child/pseudo-element height consistency.
- No logic changes.

## v96 - Task Request Core Build

- Create Task Request uses checkbox task selection for NSP Page 1, NSP Page 2 and Body-Mind Connection.
- Visible reassessment wording moves toward Task Request language.
- Body-Mind Control hidden from dashboard and linked from Create Task Request.
- Review Queue wording moves toward Review/Admin Review.
- Recipe nutrition expands with Protein, Fat, Carbohydrates and additional metrics.
- Exercise calories removed from admin/member exercise UI.

## v96.1 - LAF Cached Loader Fix

- Fixed LAF Form NameError caused by missing cached loader.
- Added local cached question loader guard for LAF.
- Added equivalent guard checks for NSP Page 1 and NSP Page 2 where needed.
- Retained v96 Task Request core changes.

## v96.2 - Task Instance Visibility Fix

- LAF no longer appears as a fillable action in second/task instances.
- Member Home now shows only requested task items for active Task Requests.
- Body-Mind Connection is now stored as a task request item and can be completed against the active instance.
- Consent/Submit now checks requested task completion before allowing submission.

## v96.3 - Member Home Task Cleanup

- Removed redundant Task Requested block from Member Home.
- Moved task request details into Your next steps information box.
- Updated copy to “Nutritionist has allocated a Task.”
- Updated task action buttons to Start NSP Page 1 / Start NSP Page 2 / Start Body-Mind Connection.
- Removed member progress/status summary block because it duplicated the task/action view.
- Removed Body-Mind from Personalized Content; it is shown under Your next steps only when requested.

## v96.4 - Task Allocation Date Display

- Added Task allocation date under Member Home → Your next steps task information.
- Added Task allocation date under Admin Task Request Manager → Assessment history.
- Uses the existing assessment instance created_date as the allocation date.

## v96.5 - Submission Status Task Allocation Date History

- Added Task allocation date under Submission Status → Assessment history.
- Uses existing assessment instance created_date as the allocation date.
- Retains v96.4 allocation date display in Member Home and Admin Task Request Manager.

## v96.6 - Body-Mind Next Steps Pending Fix

- Body-Mind Connection now appears under Member Home → Your next steps until completed.
- It appears even if the active task request only includes NSP Page 1 / NSP Page 2, provided Body-Mind is pending and available through the member workflow.
- Body-Mind remains removed from Personalized Content.
- Body-Mind page access now supports admin-completed/unlocked and task-request paths.

## v96.7 - Recipe / Exercise Navigation and HTML Fix

- Fixed raw HTML span showing in Exercise Repository cards.
- Removed inline favourite span from Recipe and Exercise card HTML; favourite remains as real Streamlit button.
- Removed top Back to exercises / Back to recipes detail buttons.
- Detail-page bottom Back now returns to the corresponding repository list.
- Dashboard button from detail returns to Member Home.
- Removed Exercise detail calories/estimate pill.

## v96.8 - Admin Dashboard Compact Workflows

- Realigned Admin Dashboard Main Workflows into compact two-column structure.
- Left column: Review & Assessment, Content & Allocation, Member & Access.
- Right column: Communication & Scheduling, Reports & Logs, System Tools.
- Reduced vertical spacing and button/card height.
- Scheduling is shown as a placeholder when no scheduling page exists yet.

## v96.9 - Admin Dashboard Uniform Subpoint Boxes

- Admin Dashboard Main Workflows now follows the reference structure.
- Main headers: Review & Assessment, Content & Allocation, Member & Access, Communication & Scheduling, Reports & Logs, System Tools.
- All subpoints use the same scheduling-style compact box schema.
- Existing routes retained.

## v96.10 - Task / Recipe / Response Fixes

- Task Request Manager cleaned and rebuilt into adjacent Create Task Request + Assessment History columns.
- Removed top Body-Mind access info message and bottom select-task info message.
- Removed “Select Task Type(s)” text.
- Moved Body-Mind Control button below Send Task Request.
- Blocked new task allocation when the current/latest instance is not completed/submitted.
- Fixed Recipe Manager macro schema and NameError for protein/fat/carbohydrates/additional nutrition.
- Moved Allocate to Member tab to the last tab in Recipe Manager.
- Added Recipe Repository macro display for Protein, Fat, Carbohydrates and additional nutrition metrics.
- Updated Admin Response Editor success message and clears rationale after save.

## v96.11 - KeepAlive / Task Compact / CSV Templates

- Added browser keep-alive guard while the app tab is open.
- Reworked Task Request Manager into compact columns.
- Right column now contains Assessment History and a Body-Mind Control section.
- Added CSV format download button to Recipe Manager import tab.
- Added CSV format download button to Exercise Manager import tab.
