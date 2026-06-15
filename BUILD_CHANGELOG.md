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
