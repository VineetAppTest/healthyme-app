from __future__ import annotations

from pathlib import Path


PAGE = Path("pages/18_Daily_Log.py")
HOME_CLEANUP = Path("components/member_saved_days_home_cleanup.py")

page = PAGE.read_text()

css_anchor = '''        .hm-toggle-anchor + div [data-testid="stButton"] > button *,
        .hm-toggle-anchor + div .stButton > button *{color:#064E3B!important;font-size:.90rem!important;font-weight:950!important;line-height:1.18!important;white-space:normal!important;overflow-wrap:normal!important;word-break:normal!important;text-align:left!important;}
'''
css_replacement = css_anchor + '''        div[data-testid="stElementContainer"]:has(.hm-toggle-anchor) + div[data-testid="stElementContainer"] button,
        div.element-container:has(.hm-toggle-anchor) + div.element-container button{justify-content:flex-start!important;text-align:left!important;}
        div[data-testid="stElementContainer"]:has(.hm-toggle-anchor) + div[data-testid="stElementContainer"] button p,
        div.element-container:has(.hm-toggle-anchor) + div.element-container button p{width:100%!important;text-align:left!important;justify-content:flex-start!important;}
        .hm-meal-entry-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){gap:.38rem!important;align-items:flex-end!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) label p{font-size:.74rem!important;font-weight:820!important;white-space:nowrap!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) [data-baseweb="select"] > div,
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) input{min-height:2.42rem!important;padding-left:.36rem!important;padding-right:.28rem!important;}
        .hm-meal-grid-spacer{display:block;height:1px;min-height:1px;}
        @media(max-width:900px){
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;}
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(4),
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(5){grid-column:span 3!important;}
        }
'''
if css_replacement not in page:
    if css_anchor not in page:
        raise RuntimeError("Meal disclosure CSS anchor not found")
    page = page.replace(css_anchor, css_replacement, 1)

start_marker = "def _render_meal_fields(label, key, prior, date_key):\n"
end_marker = "\n\ndef _render_meal_toggle(label, key, prior, date_key):\n"
start = page.find(start_marker)
end = page.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError("Meal field renderer boundaries were not found")

replacement = '''def _render_meal_fields(label, key, prior, date_key):
    prior = _as_dict(prior)
    parsed_time = _parse_time(prior.get("time", ""))
    prior_hour = f"{((parsed_time.hour - 1) % 12) + 1:02d}" if parsed_time else "HH"
    prior_minute = f"{parsed_time.minute:02d}" if parsed_time else "MM"
    prior_period = ("AM" if parsed_time.hour < 12 else "PM") if parsed_time else "AM/PM"

    hour_options = ["HH"] + [f"{value:02d}" for value in range(1, 13)]
    minute_options = ["MM"] + [f"{value:02d}" for value in range(60)]
    period_options = ["AM/PM", "AM", "PM"]

    existing_items = _normalise_food_items(prior)
    count_key = f"hm_meal_item_count_{date_key}_{key}"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(existing_items))
    item_count = max(
        1,
        min(MAX_MEAL_ITEMS, int(st.session_state.get(count_key, 1) or 1)),
    )

    food_items = []
    selected_hour = prior_hour
    selected_minute = prior_minute
    selected_period = prior_period

    for idx in range(item_count):
        prior_item = existing_items[idx] if idx < len(existing_items) else {}
        hour_col, minute_col, period_col, food_col, portion_col = st.columns(
            [0.72, 0.78, 0.92, 2.15, 1.35],
            gap="small",
        )
        with hour_col:
            st.markdown(
                "<span class='hm-meal-entry-grid-anchor'></span>",
                unsafe_allow_html=True,
            )
            if idx == 0:
                selected_hour = st.selectbox(
                    "Hour",
                    hour_options,
                    index=hour_options.index(prior_hour),
                    key=f"hm_daily_hour_v12_{date_key}_{key}",
                )
            else:
                st.markdown("<span class='hm-meal-grid-spacer'></span>", unsafe_allow_html=True)
        with minute_col:
            if idx == 0:
                selected_minute = st.selectbox(
                    "Minutes",
                    minute_options,
                    index=minute_options.index(prior_minute),
                    key=f"hm_daily_minute_v12_{date_key}_{key}",
                )
            else:
                st.markdown("<span class='hm-meal-grid-spacer'></span>", unsafe_allow_html=True)
        with period_col:
            if idx == 0:
                selected_period = st.selectbox(
                    "AM/PM",
                    period_options,
                    index=period_options.index(prior_period),
                    key=f"hm_daily_ampm_v12_{date_key}_{key}",
                )
            else:
                st.markdown("<span class='hm-meal-grid-spacer'></span>", unsafe_allow_html=True)
        with food_col:
            food = st.text_input(
                f"Food Item {idx + 1}",
                value=prior_item.get("food", ""),
                key=f"{date_key}_{key}_food_{idx}",
                placeholder="Enter food item",
            )
        with portion_col:
            portion = st.text_input(
                f"Portion {idx + 1}",
                value=prior_item.get("portion_size", ""),
                key=f"{date_key}_{key}_portion_{idx}",
                placeholder="Enter portion",
            )
        row = {"food": _clean(food), "portion_size": _clean(portion)}
        if _food_item_has_data(row):
            food_items.append(row)

    st.markdown("<span class='hm-add-food-anchor'></span>", unsafe_allow_html=True)
    if st.button(
        "+ Add food item",
        key=f"hm_add_food_item_{date_key}_{key}",
        disabled=item_count >= MAX_MEAL_ITEMS,
    ):
        st.session_state[count_key] = min(MAX_MEAL_ITEMS, item_count + 1)
        st.rerun()

    time_value = None
    if (
        selected_hour != "HH"
        and selected_minute != "MM"
        and selected_period != "AM/PM"
    ):
        time_value = datetime.strptime(
            f"{selected_hour}:{selected_minute} {selected_period}",
            "%I:%M %p",
        ).time()

    prior_mood, prior_energy = _legacy_mood_and_energy(prior)
    mood_col, energy_col = st.columns(2, gap="medium")
    with mood_col:
        mood = st.text_input(
            f"Mood after {label.lower()}",
            value=prior_mood,
            key=f"{date_key}_{key}_mood",
            placeholder="How did you feel?",
        )
    with energy_col:
        energy = st.text_input(
            f"Energy after {label.lower()}",
            value=prior_energy,
            key=f"{date_key}_{key}_energy",
            placeholder="How was your energy?",
        )

    clean_mood = _clean(mood)
    clean_energy = _clean(energy)
    legacy_food = "; ".join(
        item.get("food", "") for item in food_items if item.get("food")
    )
    legacy_portion = "; ".join(
        item.get("portion_size", "")
        for item in food_items
        if item.get("portion_size")
    )
    combined_mood_energy = " | ".join(
        value
        for value in [
            f"Mood: {clean_mood}" if clean_mood else "",
            f"Energy: {clean_energy}" if clean_energy else "",
        ]
        if value
    )

    return {
        "label": label,
        "time": _time_text(time_value),
        "food_items": food_items,
        "food": legacy_food,
        "portion_size": legacy_portion,
        "mood": clean_mood,
        "energy": clean_energy,
        "mood_energy": combined_mood_energy,
    }
'''
page = page[:start] + replacement + page[end:]
PAGE.write_text(page)

cleanup = HOME_CLEANUP.read_text()
cleanup_start = cleanup.find("def _install_saved_days_window() -> None:\n")
cleanup_end = cleanup.find("\n\ndef _install_member_home_cleanup() -> None:\n", cleanup_start)
if cleanup_start < 0 or cleanup_end < 0:
    raise RuntimeError("Saved-days compatibility runtime boundaries were not found")
cleanup_replacement = '''def _install_saved_days_window() -> None:
    """Retired compatibility hook.

    Saved Days now owns its date defaults, four-column cards, hydration rows and
    Open saved day action directly in ``pages/18_Daily_Log.py``. The former runtime
    wrapper injected a second Meal Section, forced the four-column grid into one
    column and intercepted the Open action. Keep this function as a no-op because
    older bootstraps still import and call it.
    """

    return None
'''
cleanup = cleanup[:cleanup_start] + cleanup_replacement + cleanup[cleanup_end:]
HOME_CLEANUP.write_text(cleanup)
