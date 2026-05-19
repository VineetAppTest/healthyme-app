"""Daily Log database facade.

v61 cleanup foundation: imports existing stable functions from db.py.
No business logic changed yet; this prepares safe future split.
"""
from components.db import (
    save_daily_food_journal_day,
    save_daily_food_journal_meal,
    save_daily_food_journal_day_details,
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    save_daily_log_supervision_note,
    get_daily_log_supervision_notes,
    get_daily_log_notes_by_date,
    get_latest_daily_log_note_for_date,
)
