from __future__ import annotations

from pathlib import Path


PAGE = Path("pages/18_Daily_Log.py")
text = PAGE.read_text()

import_anchor = "from components.flash import set_system_message, render_system_message\n"
import_block = """from components.flash import set_system_message, render_system_message
from components.food_saved_days_presentation import (
    initialise_food_saved_days_range,
    saved_day_card_html,
    saved_day_sort_key,
    saved_days_card_css,
)
from components.member_timezone import member_local_today
"""
if "from components.food_saved_days_presentation import (" not in text:
    if text.count(import_anchor) != 1:
        raise RuntimeError(
            f"Expected one Daily Log flash import anchor, found {text.count(import_anchor)}"
        )
    text = text.replace(import_anchor, import_block, 1)

start_marker = "def _render_saved_days(user_id):\n"
end_marker = "\n\ndef _render_food_journal(user_id):\n"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError("Could not locate the Daily Log saved-days function boundaries")

replacement = '''def _render_saved_days(user_id):
    today = member_local_today(user_id)
    initialise_food_saved_days_range(st.session_state, today)

    with st.container(border=True):
        st.markdown("### View Saved Days")
        all_days = get_daily_food_journal_days(user_id) or []
        from_col, to_col = st.columns(2)
        with from_col:
            filter_from = st.date_input("From", key="hm_h9a4c_saved_from")
        with to_col:
            filter_to = st.date_input("To", key="hm_h9a4c_saved_to")

        if filter_from > filter_to:
            st.warning("From date cannot be after To date.")
            return

        filtered_days = []
        for day in all_days:
            saved_date = _saved_day_date(day)
            if saved_date and filter_from <= saved_date <= filter_to:
                filtered_days.append(day)
        filtered_days.sort(key=saved_day_sort_key, reverse=True)

        if not filtered_days:
            st.caption("No saved days found in this range.")
            return

        st.caption(f"Showing {len(filtered_days)} saved day(s) in the selected range.")
        st.markdown(saved_days_card_css(), unsafe_allow_html=True)
        for row_start in range(0, len(filtered_days), 4):
            cols = st.columns(4, gap="small")
            for column_index, (col, day) in enumerate(
                zip(cols, filtered_days[row_start : row_start + 4])
            ):
                date_text = _format_saved_date(day)
                label_date = _parse_date(date_text)
                with col:
                    with st.container(border=True):
                        st.markdown(
                            saved_day_card_html(day, date_text),
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "Open saved day",
                            key=(
                                f"hm_h9a4c_load_{date_text}_"
                                f"{row_start}_{column_index}"
                            ),
                            use_container_width=True,
                        ):
                            if label_date:
                                st.session_state["hm_food_journal_date"] = label_date
                                st.rerun()
'''

text = text[:start] + replacement + text[end:]
PAGE.write_text(text)
