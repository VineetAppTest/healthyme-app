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
