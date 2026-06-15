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
