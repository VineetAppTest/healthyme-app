# HealthyMe v97.10 - Daily Log Header Gap / Recent Filter Hard Fix

- Removed accumulated empty CSS/style blocks between the page header and Food Journal Date row.
- Consolidated Daily Log CSS before the header to prevent vertical gaps.
- Added visible From Date / To Date filter immediately under Recent Saved Days.
- Filter controls remain visible even when there are no saved rows yet.
- Retained v97.8/v97.9 Snacking and Other Fluids reliability fixes.

## v97.11 - Daily Log Meal Helper NameError Hotfix

- Fixed NameError: meal_has_data was not defined before meal section rendering.
- Added defensive meal_has_data helper.
- Added defensive is_dirty helper.
- Restored visible From Date / To Date filter for Recent Saved Days.
- Retained v97.10 header gap work.

## v97.12 - Daily Log Timing Helper / Header Gap Hotfix

- Fixed NameError: meal_time_guidance was not defined.
- Restored split_12h_time_parts, meal_time_selector_options_v97_2, meal_time_guidance, validate_meal_time_window and validate_meal_time.
- Applied stronger header-to-date whitespace reduction.
- Retained visible Recent Saved Days From/To filter.

## v97.13 - Daily Log Functional Rollback + Recent Filter

- Rolled back pages/18_Daily_Log.py to the last stable functional v97.8 Daily Log baseline.
- Re-added only From Date / To Date filter for Recent Saved Days.
- Avoided further changes to meal timing, snacking, other fluids, and header styling.
- Removed helper regressions introduced in later Daily Log patches.

## v97.14 - Daily Log Spacing + Recent Filter Correction

- Removed style-only blocks between hero banner and Food Journal Date to reduce visual gap.
- Reduced spacing between Food Journal Date and Meal Sections.
- Replaced duplicate Recent Saved Days filters with one working From Date / To Date filter.
- Recent Saved Days filter now supports both YYYY-MM-DD and YYYY/MM/DD saved date formats.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.15 - Daily Log Physical Order + Recent Filter Hard Fix

- Physically moved Food Journal Date immediately after Daily Food Journal header.
- Reduced Food Journal Date to Meal Sections gap.
- Rebuilt Recent Saved Days filter inside the actual display path.
- Filter now applies before saved-day rows/cards are rendered.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.16 - Daily Log Meal Gap + Recent Filter Functional Fix

- Reduced gap between Food Journal Date and Meal Sections using targeted spacing overrides.
- Rebuilt Recent Saved Days filter to create filtered_days and render only filtered_days.
- From Date / To Date filter now applies before cards are displayed.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.17 - Daily Log Structural Stabilization

- Stabilized Daily Log by restoring the v97.8 functional page baseline.
- Moved all style-only blocks above the Daily Food Journal header.
- Kept Food Journal Date and Meal Sections in a clean render order.
- Rebuilt Recent Saved Days into one clean filter-render path.
- From Date / To Date filter now renders filtered_days only.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.18 - Daily Log Top Layout + Measurable Recent Filter Fix

- Rebuilt Food Journal Date top area without split HTML wrappers around Streamlit columns.
- Replaced Meal Sections st.subheader with compact markdown title to avoid Streamlit subheader margin.
- Rebuilt Recent Saved Days with measurable filtered_days render path.
- Added visible Showing X of Y saved days count.
- Filter parses saved dates from date, log_date, journal_date, and food_journal_date fields.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.19 - Daily Log Saved-Day Date-Key Filter Fix

- Fixed saved-day filter at data layer by injecting date/_journal_date_key into every row returned by get_daily_food_journal_days.
- Updated Daily Log filter to read _journal_date_key along with date/log_date/journal_date/food_journal_date.
- Kept visible Showing X of Y saved days count with dated-row visibility.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.20 - Daily Log Filter Source-of-Truth Fix

- Made daily_food_journals saved-day key the source of truth for date filtering and display.
- Overwrites stale inner row date with saved-day key in get_daily_food_journal_days for keyed journal rows.
- Recent Saved Days filter now prioritizes _journal_date_key before date/log_date/journal_date/food_journal_date.
- Cards display the same date source used by the filter.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.21 - Daily Log Display Date Recursion Hotfix

- Fixed RecursionError in get_saved_day_display_date_v97_20.
- Replaced recursive fallback with safe field fallback.
- Retained v97.20 source-of-truth date filtering.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.22 - Daily Log Date Parser Filter Hotfix

- Fixed Recent Saved Days date parser so dated rows should no longer remain zero.
- Parser now works with direct date/datetime imports used in the app.
- Parser supports YYYY/MM/DD, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, and datetime strings.
- Retained source-of-truth filtering using _journal_date_key.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.23 - Daily Log Button-Driven Saved Days Filter

- Changed Recent Saved Days to button-driven filtering.
- Default view shows complete saved-day data.
- Apply Date Filter explicitly activates From/To filtering.
- Clear Filter / Show All returns to complete saved-day data.
- If filter cannot be applied, page falls back to complete data.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.24 - Daily Log Mini Polish, Spacing, Fluid Timing

- Added a little space above Food Journal Date.
- Reduced space between the date helper line and Meal Sections.
- Added a little space below the Meal Sections instruction line.
- Changed Other Fluids label from Meal Timing to Fluid Timing.
- Added light border/section accents for Daily Log sections.
- Retained v97.23 button-driven saved-days filter.
- No changes to meal timing, snacking, other fluids save logic, or food journal save logic.

## v97.25 - Daily Log Food Journal Date Vertical Alignment

- Vertically center-aligned Food Journal Date label/help with the date input.
- Rebuilt the date label/help as one stacked block for proper alignment.
- No changes to saved-days filter, meal timing, snacking, other fluids, or save logic.

## v97.29 - Daily Log Native Bordered Sections

- Rolled Daily Log visual structure back to clean v97.25 base and rebuilt sections using native Streamlit bordered containers.
- Created four true section blocks: Food Journal Date, Meal Sections, Full Day Details, Recent Saved Days.
- Kept Meal Sections and active meal entry within one continuous bordered block.
- Removed Recent Saved Days explanatory note from render path.
- Promoted Filter Recent Saved Days to subsection title without duplicate text.
- Retained button-driven filter, Fluid Timing label, meal timing, snacking, other fluids save logic, and food journal save logic.

## v97.30 - Daily Log Food Journal Date Alignment

- Aligned Food Journal Date label/help stack vertically with the date picker.
- Matched label-stack and date-input row heights.
- Adjusted date row column ratio for better horizontal balance.
- No changes to section structure, button-driven filter, meal timing, snacking, other fluids, or save logic.

## v97.31 - Daily Log Date Picker Render Alignment

- Adjusted Food Journal Date label/help block to match Streamlit date picker rendered position.
- Used physical render-position offset instead of relying on vertical centering alone.
- No changes to native bordered sections, button-driven filter, Fluid Timing label, meal timing, snacking, other fluids, or save logic.

## v97.32 - Daily Log Food Journal Date Structural Spacer

- Added a structural spacer inside the Food Journal Date label column to align it with the rendered date picker.
- Stopped relying only on vertical-centering CSS against Streamlit date_input internals.
- No changes to section structure, button-driven filter, Fluid Timing label, meal timing, snacking, other fluids, or save logic.

## v97.33 - Daily Log Filter Uses Visible Card Date

- Fixed Recent Saved Days filter to use the same visible date shown on each saved-day card.
- Button-driven filter now compares From/To against card display date, not stale/internal source fields.
- Updated filter count wording to card-dated rows for UAT visibility.
- Retained Food Journal Date alignment from v97.32.
- No changes to meal timing, snacking, other fluids, or save logic.

## v97.36 - Rollback to v97.33 + Clear Filter Dynamic Keys

- Rolled back to v97.33 as requested.
- Rebuilt Recent Saved Days filter with dynamic Streamlit date-input keys.
- Clear Filter / Show All now clears active filter state and recreates From/To date widgets at full range.
- Apply Date Filter reruns after activation for consistent display.
- Retained v97.33 visible-card-date filtering and v97.32 Food Journal Date alignment.
- No changes to meal timing, snacking, other fluids, or save logic.

## v98.0 - Daily Log Closure + Admin/Report Validation

- Built from v97.36 GTG baseline.
- No Daily Log logic changes.
- No layout redesign.
- No filter redesign.
- Freezes Daily Log for structured UAT closure.
- Adds validation checklist for:
  - Member Daily Log save/revisit
  - Save Day Details Only
  - Save Full-Day Journal
  - Snacking
  - Other Fluids / Fluid Timing
  - Recent Saved Days Apply Date Filter
  - Recent Saved Days Clear Filter / Show All
  - Admin Daily Log report visibility
  - Export/report coverage
  - Mobile/laptop layout check

## v98.1 - Daily Log + Member/Admin Polish

- Matched Filter Recent Saved Days heading font with field-label styling.
- Updated Recent Saved Days Other Fluids summary to:
  - Other Liquid 1: Total Intake - X + Y ml | 12:30 PM - X ml; 3:30 PM - Y ml
- Placed Show / Hide sample journal format and Back to Home buttons side-by-side.
- Changed Recent Saved Days label Notes to Member's Notes.
- Added padding above View History.
- Reduced Member Home task-button spacing and signed-in/header spacing.
- Added admin-only version marker under HealthyMe brand/top header where topbar is used, plus visible admin dashboard build chip.
- No changes to Daily Log save/filter logic, meal timing, snacking, or other fluids capture logic.

## v98.2 - Member Home Top Spacing Reduction

- Reduced top empty space above signed-in/logout row by approximately 60%.
- Reduced empty space between signed-in/logout row and Member Home hero card by approximately 60%.
- Kept task action button spacing polish from v98.1.
- No changes to Daily Log, saved-days filter, admin/report, meal timing, snacking, other fluids, or save logic.

## v98.3 - Member Home Invisible Spacing Collapse

- Collapsed invisible/style-only Streamlit containers suspected to be creating empty vertical space on Member Home.
- Reduced actual top block-container padding above signed-in/logout row.
- Reduced utility bar bottom margin and hero card top margin.
- Kept task action button spacing polish from v98.1/v98.2.
- No changes to Daily Log, saved-days filter, admin/report, meal timing, snacking, other fluids, or save logic.

## v98.4 - Member Home Utility Style Defer Fix

- Removed hidden CSS/style injections from inside utility_logout_bar before the signed-in/logout row.
- Deferred Member Home style-only injections to the bottom of the page to prevent invisible spacing before utility row and hero card.
- Rendered utility logout row directly before Member Home hero card.
- Added broader Streamlit container padding resets including stAppViewBlockContainer and stMainBlockContainer.
- No changes to Daily Log, saved-days filter, admin/report, meal timing, snacking, other fluids, or save logic.

## v98.5 - Admin Dashboard Top Spacing + Version Placement

- Fixed Admin Dashboard top spacing by removing early style/helper injections before visible content.
- Deferred Admin Dashboard style-only injections to the bottom of the page.
- Removed loose standalone admin version chip.
- Added compact HEALTHYME header with v98.5 version directly under it on Admin Dashboard.
- Updated app build version to v98.5.
- No changes to Member Home logic, Daily Log, saved-days filter, meal timing, snacking, other fluids, or save logic.
