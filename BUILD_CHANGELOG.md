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
