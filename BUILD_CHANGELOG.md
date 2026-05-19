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
