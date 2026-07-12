from datetime import date, datetime
import html
import re

import streamlit as st

from components.guards import require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    topbar,
    utility_logout_bar,
    format_local_ts,
    render_page_nav,
    render_back_to_top,
)
from components.db import (
    save_daily_food_journal_day,
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    get_daily_log_notes_by_date,
    get_latest_daily_log_note_for_date,
)
from components.flash import set_system_message, render_system_message


BUILD_NOTE = "v102.4B21H9A10E · Daily Log label spacing polish"


def _text(value):
    return "" if value is None else str(value).strip()


def _is_default(value):
    normalized = re.sub(r"[\s_-]+", " ", _text(value).lower())
    return normalized in {"", "select", "selected", "please select", "select option", "choose", "choose one", "hh", "mm", "am/pm"}


def _clean(value):
    return "" if _is_default(value) else _text(value)


def _has_value(value):
    return bool(_clean(value))


def _safe_html(value):
    return html.escape(_text(value))


def _as_dict(value):
    return dict(value) if isinstance(value, dict) else {}


def _parse_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = _text(value)
    if not raw:
        return None
    raw = raw.split("T")[0].split(" ")[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except Exception:
            pass
    try:
        return date.fromisoformat(raw)
    except Exception:
        return None


def _parse_time(value):
    raw = _text(value).upper()
    if not raw:
        return None
    for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).time()
        except Exception:
            pass
    return None


def _time_text(value):
    return "" if value is None else value.strftime("%I:%M %p")


def _meal_summary(meal):
    meal = _as_dict(meal)
    food = _clean(meal.get("food") or meal.get("food_log") or meal.get("name"))
    qty = _clean(meal.get("portion_size") or meal.get("quantity"))
    time_text = _clean(meal.get("time"))
    if food:
        return " · ".join([x for x in [time_text, food, qty] if x])
    return "No entry yet"


def _meal_has_data(meal):
    meal = _as_dict(meal)
    return any(_has_value(meal.get(key)) for key in ("time", "food", "food_log", "name", "portion_size", "quantity", "mood_energy", "mood", "energy"))


def _normalise_meals(existing_meals):
    meals = existing_meals if isinstance(existing_meals, dict) else {}
    normalised = {
        "breakfast": _as_dict(meals.get("breakfast")),
        "lunch": _as_dict(meals.get("lunch")),
        "dinner": _as_dict(meals.get("dinner")),
        "bedtime": _as_dict(meals.get("bedtime") or meals.get("pre_bed")),
    }
    evening_snacks = []
    for key, value in meals.items():
        key_text = str(key or "").lower()
        label_text = str((value or {}).get("label", "")).lower() if isinstance(value, dict) else ""
        if key_text.startswith("snacking_") or key_text.startswith("other_") or "snack" in key_text or "snack" in label_text or "evening" in label_text:
            if isinstance(value, dict) and _meal_has_data(value):
                evening_snacks.append(dict(value))
    return normalised, evening_snacks[:9]


def _intake_has_data(item):
    item = item if isinstance(item, dict) else {}
    return any(_has_value(item.get(key)) for key in ("type", "name", "fluid_type", "time", "quantity", "qty", "notes"))


def _normalise_other_fluids(items):
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        cleaned = {
            "type": _clean(item.get("type") or item.get("name") or item.get("fluid_type")),
            "time": _clean(item.get("time")),
            "quantity": _clean(item.get("quantity") or item.get("qty")),
            "notes": _clean(item.get("notes")),
        }
        if _intake_has_data(cleaned):
            out.append(cleaned)
    return out[:9]


def _other_fluids_summary(items):
    fluids = _normalise_other_fluids(items)
    if not fluids:
        return "—"
    rows = []
    for item in fluids:
        fluid_type = item.get("type") or "Other fluid"
        parts = [item.get("time", ""), item.get("quantity", ""), item.get("notes", "")]
        detail = " · ".join([p for p in parts if p]) or "Recorded"
        rows.append(f"{fluid_type}: {detail}")
    return "<br>".join(rows)


def _format_saved_date(day):
    if not isinstance(day, dict):
        return ""
    for key in ("_journal_date_key", "date", "log_date", "journal_date", "food_journal_date"):
        parsed = _parse_date(day.get(key))
        if parsed:
            return parsed.isoformat()
    return _text(day.get("date"))


def _saved_day_date(day):
    return _parse_date(_format_saved_date(day))


def _hydration_summary(water_litres, other_fluids):
    parts = []
    water = _clean(water_litres)
    if water:
        parts.append(f"Water: {water}")
    fluid_count = len(_normalise_other_fluids(other_fluids))
    if fluid_count:
        parts.append(f"Other fluids: {fluid_count}/9")
    return " | ".join(parts) if parts else "No hydration entry yet"


def _bowel_summary(poop_rounds, feeling_after_poop):
    rounds = None if _is_default(poop_rounds) else poop_rounds
    feeling = _clean(feeling_after_poop)
    if rounds is None and not feeling:
        return "No bowel movement entry yet"
    parts = []
    if rounds is not None:
        parts.append(f"Poop rounds: {rounds}")
    if feeling:
        parts.append(f"Feeling: {feeling}")
    return " | ".join(parts)


def _day_has_meaningful_entry(payload):
    if any(_meal_has_data(meal) for meal in (payload.get("meals") or {}).values()):
        return True
    if _has_value(payload.get("water_litres")):
        return True
    if _normalise_other_fluids(payload.get("other_fluids", [])):
        return True
    if payload.get("poop_rounds") is not None and not _is_default(payload.get("poop_rounds")):
        return True
    if any(_has_value(x) for x in payload.get("poop_timings", [])):
        return True
    return any(_has_value(payload.get(key)) for key in ("feeling_after_poop", "physical_activity", "notes"))


def _report_lines(payload):
    lines = []
    meals = payload.get("meals") or {}
    for label, key in [("Breakfast", "breakfast"), ("Lunch", "lunch")]:
        meal = meals.get(key) or {}
        if _meal_has_data(meal):
            lines.append(f"{label}: {_meal_summary(meal)}")
    snack_items = [(key, value) for key, value in meals.items() if str(key).startswith("snacking_") and _meal_has_data(value)]
    for idx, (_key, meal) in enumerate(snack_items, start=1):
        lines.append(f"Evening Snack {idx}: {_meal_summary(meal)}")
    for label, key in [("Dinner", "dinner"), ("Bedtime", "bedtime")]:
        meal = meals.get(key) or {}
        if _meal_has_data(meal):
            lines.append(f"{label}: {_meal_summary(meal)}")
    if _has_value(payload.get("water_litres")):
        lines.append(f"Water: {_clean(payload.get('water_litres'))}")
    for idx, fluid in enumerate(_normalise_other_fluids(payload.get("other_fluids", [])), start=1):
        parts = [fluid.get("time", ""), fluid.get("type", ""), fluid.get("quantity", ""), fluid.get("notes", "")]
        lines.append(f"Other fluid {idx}: {' · '.join([p for p in parts if p])}")
    if payload.get("poop_rounds") is not None and not _is_default(payload.get("poop_rounds")):
        lines.append(f"Poop rounds: {payload.get('poop_rounds')}")
    poop_times = [_clean(x) for x in payload.get("poop_timings", []) if _has_value(x)]
    if poop_times:
        lines.append(f"Poop timings: {', '.join(poop_times)}")
    if _has_value(payload.get("feeling_after_poop")):
        lines.append(f"Feeling after poop: {_clean(payload.get('feeling_after_poop'))}")
    if _has_value(payload.get("physical_activity")):
        lines.append(f"Physical activity: {_clean(payload.get('physical_activity'))}")
    if _has_value(payload.get("notes")):
        lines.append(f"Notes: {_clean(payload.get('notes'))}")
    return lines


def _render_css():
    st.markdown(
        """
        <style>
        .hm-h9a4c-note{color:#64748B;font-size:.86rem;line-height:1.35;margin:.10rem 0 .75rem 0;}
        .hm-h9a4c-status{border:1px solid #CFE3C2;background:#F4FBF1;color:#416B2F;border-radius:14px;padding:.68rem .78rem;font-weight:800;margin:.5rem 0 .6rem 0;}
        .hm-h9a4c-warning{border:1px solid #F0C9C9;background:#FFF7F7;color:#9A3412;border-radius:14px;padding:.68rem .78rem;font-weight:800;margin:.5rem 0 .6rem 0;}
        .hm-h9a4c-cardline{border:1px solid #E7D8BE;background:#FFFDF8;border-radius:16px;padding:.75rem .85rem;margin:.58rem 0 .72rem 0;}
        .hm-exercise-placeholder{border:1px dashed #D8C18B;background:#FFFDF8;border-radius:16px;padding:1rem;margin:.5rem 0;color:#334155;}
        div[data-testid="stTabs"] [role="tablist"]{gap:.55rem;margin:.15rem 0 1rem 0;border-bottom:1px solid #E3D4BA;padding-bottom:.45rem;}
        div[data-testid="stTabs"] button[role="tab"]{border:1.4px solid #D8A84E!important;border-radius:999px!important;background:#FFFFFF!important;color:#064E3B!important;font-weight:950!important;padding:.62rem 1.18rem!important;box-shadow:0 7px 16px rgba(6,78,59,.07)!important;min-height:2.65rem!important;}
        div[data-testid="stTabs"] button[aria-selected="true"]{background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;color:#FFFFFF!important;border-color:#064E3B!important;box-shadow:0 12px 22px rgba(6,78,59,.18)!important;}
        div[data-testid="stTabs"] button[aria-selected="true"] *{color:#FFFFFF!important;}
        .hm-toggle-anchor + div [data-testid="stButton"] > button,.hm-toggle-anchor + div .stButton > button{justify-content:center!important;text-align:center!important;min-height:3.0rem!important;background:#FFFFFF!important;border:1.45px solid #D8A84E!important;border-radius:16px!important;box-shadow:0 8px 18px rgba(15,23,42,.045)!important;color:#064E3B!important;font-weight:950!important;margin:.55rem 0 .34rem 0!important;padding:.64rem .86rem!important;}
        .hm-toggle-anchor + div [data-testid="stButton"] > button *,.hm-toggle-anchor + div .stButton > button *{color:#064E3B!important;font-size:.92rem!important;font-weight:950!important;line-height:1.22!important;white-space:normal!important;overflow-wrap:normal!important;word-break:normal!important;text-align:center!important;}
        .hm-toggle-body{border:1px solid #E7D8BE;background:#FFFDF8;border-radius:16px;padding:1rem .96rem;margin:.18rem 0 .75rem 0;}
        div[data-testid="stTextInput"],div[data-testid="stTextArea"],div[data-testid="stSelectbox"],div[data-testid="stDateInput"],div[data-testid="stTimeInput"]{margin-bottom:.62rem!important;}
        div[data-testid="stTextInput"] label,div[data-testid="stTextArea"] label,div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label,div[data-testid="stTimeInput"] label{display:block!important;margin:0 0 .30rem 0!important;padding-left:.10rem!important;line-height:1.25!important;}
        div[data-testid="stDateInput"] input, div[data-testid="stTimeInput"] input, div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stSelectbox"] [data-baseweb="select"] > div{border-radius:13px!important;border:1.2px solid #DCC690!important;background:#FFFFFF!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _toggle_button(label, key, default_open=False):
    state_key = f"hm_daily_toggle_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_open
    is_open = bool(st.session_state.get(state_key))
    prefix = "▾" if is_open else "▸"
    st.markdown("<div class='hm-toggle-anchor'></div>", unsafe_allow_html=True)
    if st.button(f"{prefix} {label}", key=f"{state_key}_btn", use_container_width=True):
        st.session_state[state_key] = not is_open
        st.rerun()
    return bool(st.session_state.get(state_key))


def _render_meal_fields(label, key, prior, date_key):
    prior = _as_dict(prior)
    time_value = st.time_input(f"{label} time", value=_parse_time(prior.get("time", "")), key=f"{date_key}_{key}_time")
    food = st.text_area(f"{label} food", value=_clean(prior.get("food") or prior.get("food_log") or prior.get("name")), key=f"{date_key}_{key}_food", height=78)
    c1, c2 = st.columns(2)
    with c1:
        portion = st.text_input(f"{label} quantity / portion", value=_clean(prior.get("portion_size") or prior.get("quantity")), key=f"{date_key}_{key}_portion")
    with c2:
        mood = st.text_input(f"Mood / energy after {label.lower()}", value=_clean(prior.get("mood_energy") or prior.get("mood") or prior.get("energy")), key=f"{date_key}_{key}_mood")
    return {"label": label, "time": _time_text(time_value), "food": _clean(food), "portion_size": _clean(portion), "mood_energy": _clean(mood)}


def _render_meal_toggle(label, key, prior, date_key):
    if _toggle_button(f"{label} — {_meal_summary(prior)}", f"{date_key}_{key}"):
        st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
        payload = _render_meal_fields(label, key, prior, date_key)
        st.markdown("</div>", unsafe_allow_html=True)
        return payload
    return _as_dict(prior)


def _render_exercise_journal_placeholder():
    st.markdown("### Exercise Journal")
    st.markdown(
        """
        <div class='hm-exercise-placeholder'>
          Exercise Journal will be enabled after the exercise logging data contract is finalised.
          For now, please continue recording any exercise under <b>Food Journal → Physical Activity</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_food_journal(user_id):
    if "hm_food_journal_date" not in st.session_state:
        st.session_state["hm_food_journal_date"] = date.today()

    with st.container(border=True):
        st.markdown("### Food Journal Date")
        log_date = st.date_input("Select the date for this food journal entry", key="hm_food_journal_date")
        date_key = str(log_date)

    existing = get_daily_food_journal_day(user_id, date_key) or {}
    existing_meals, existing_evening_snacks = _normalise_meals(existing.get("meals", {}) or {})
    existing_other_fluids = _normalise_other_fluids(existing.get("other_fluids", []) or [])
    is_saved_date = bool(existing and _day_has_meaningful_entry(existing))

    with st.container(border=True):
        st.markdown("### View Saved Days")
        all_days = get_daily_food_journal_days(user_id) or []
        parsed_dates = sorted([d for d in [_saved_day_date(day) for day in all_days] if d])
        default_from = min(parsed_dates) if parsed_dates else date.today()
        default_to = max(parsed_dates) if parsed_dates else date.today()
        f_col, t_col = st.columns(2)
        with f_col:
            filter_from = st.date_input("From", value=default_from, key="hm_h9a4c_saved_from")
        with t_col:
            filter_to = st.date_input("To", value=default_to, key="hm_h9a4c_saved_to")
        filtered_days = [day for day in all_days if (d := _saved_day_date(day)) and filter_from <= d <= filter_to]
        if not filtered_days:
            st.caption("No saved days found in this range.")
        else:
            st.caption(f"Showing {len(filtered_days)} saved day(s) in the selected range.")
            for row_start in range(0, len(filtered_days), 4):
                cols = st.columns(4)
                for col, day in zip(cols, filtered_days[row_start:row_start + 4]):
                    d_text = _format_saved_date(day)
                    label_date = _parse_date(d_text)
                    button_label = label_date.strftime("%d %b") if label_date else d_text
                    with col:
                        if st.button(button_label, key=f"hm_h9a4c_load_{d_text}", use_container_width=True):
                            if label_date:
                                st.session_state["hm_food_journal_date"] = label_date
                                st.rerun()

    with st.container(border=True):
        st.markdown("### Meal Section")
        note = f"Viewing saved entries for {log_date.strftime('%d %b')}. Open a section only if you want to edit it." if is_saved_date else "Open only the meal you want to update."
        st.markdown(f"<div class='hm-h9a4c-note'>{_safe_html(note)}</div>", unsafe_allow_html=True)
        meals_payload = {}
        meals_payload["breakfast"] = _render_meal_toggle("Breakfast", "breakfast", existing_meals.get("breakfast", {}), date_key)
        meals_payload["lunch"] = _render_meal_toggle("Lunch", "lunch", existing_meals.get("lunch", {}), date_key)

        snack_count_key = f"hm_h9a4c_snack_count_{date_key}"
        if snack_count_key not in st.session_state:
            st.session_state[snack_count_key] = len(existing_evening_snacks)
        snack_count = int(st.session_state.get(snack_count_key, 0) or 0)
        if _toggle_button(f"Evening Snack — {snack_count}/9 entries", f"{date_key}_evening_snack"):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            add_col, remove_col = st.columns(2)
            with add_col:
                if st.button("+ Add evening snack", key=f"hm_h9a4c_add_snack_{date_key}", disabled=snack_count >= 9, use_container_width=True):
                    st.session_state[snack_count_key] = min(9, snack_count + 1)
                    st.rerun()
            with remove_col:
                if st.button("Remove last evening snack", key=f"hm_h9a4c_remove_snack_{date_key}", disabled=snack_count <= 0, use_container_width=True):
                    st.session_state[snack_count_key] = max(0, snack_count - 1)
                    st.rerun()
            if snack_count == 0:
                st.caption("No evening snack entry added yet.")
            for idx in range(snack_count):
                prior = existing_evening_snacks[idx] if idx < len(existing_evening_snacks) else {}
                st.markdown(f"<div class='hm-h9a4c-cardline'><b>Evening Snack {idx + 1}</b></div>", unsafe_allow_html=True)
                meals_payload[f"snacking_{idx + 1}"] = _render_meal_fields(f"Evening Snack {idx + 1}", f"snacking_{idx + 1}", prior, date_key)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            for idx, prior in enumerate(existing_evening_snacks[:snack_count], start=1):
                meals_payload[f"snacking_{idx}"] = prior

        meals_payload["dinner"] = _render_meal_toggle("Dinner", "dinner", existing_meals.get("dinner", {}), date_key)
        meals_payload["bedtime"] = _render_meal_toggle("Bedtime", "bedtime", existing_meals.get("bedtime", {}), date_key)

    water_options = ["Select", "0 Litres", "0.5 Litres", "1 Litre", "1.5 Litres", "2 Litres", "2.5 Litres", "3 Litres", "3.5 Litres", "4 Litres", "4.5 Litres", "5 Litres", "5.5 Litres", "6 Litres", "6.5 Litres", "7 Litres", "7.5 Litres", "8 Litres", "8.5 Litres", "9 Litres", "9.5 Litres", "10 Litres"]
    existing_water = _clean(existing.get("water_litres")) or "Select"
    water_litres = existing_water
    other_fluids = existing_other_fluids

    with st.container(border=True):
        if _toggle_button(f"Hydration — {_hydration_summary(existing_water, existing_other_fluids)}", f"{date_key}_hydration"):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            st.markdown("<div class='hm-h9a4c-note'>Water and other fluids are grouped together for the full day.</div>", unsafe_allow_html=True)
            water_litres = st.selectbox("Water Intake", water_options, index=water_options.index(existing_water) if existing_water in water_options else 0, key=f"hm_h9a4c_water_{date_key}")
            fluid_count_key = f"hm_h9a4c_fluid_count_{date_key}"
            if fluid_count_key not in st.session_state:
                st.session_state[fluid_count_key] = len(existing_other_fluids)
            fluid_count = int(st.session_state.get(fluid_count_key, 0) or 0)
            st.markdown(f"<div class='hm-h9a4c-cardline'><b>Other Fluid Intake</b><br>{fluid_count}/9 entries</div>", unsafe_allow_html=True)
            fc1, fc2 = st.columns(2)
            with fc1:
                if st.button("+ Add other fluid", key=f"hm_h9a4c_add_fluid_{date_key}", disabled=fluid_count >= 9, use_container_width=True):
                    st.session_state[fluid_count_key] = min(9, fluid_count + 1)
                    st.rerun()
            with fc2:
                if st.button("Remove last fluid", key=f"hm_h9a4c_remove_fluid_{date_key}", disabled=fluid_count <= 0, use_container_width=True):
                    st.session_state[fluid_count_key] = max(0, fluid_count - 1)
                    st.rerun()
            fluid_options = ["Select", "Herbal Tea", "Coconut Water", "Juice", "Cold Drink", "Tea / Coffee", "Buttermilk", "Other"]
            other_fluids = []
            if fluid_count == 0:
                st.caption("No other fluid entry added yet.")
            for idx in range(fluid_count):
                prior = existing_other_fluids[idx] if idx < len(existing_other_fluids) else {}
                st.markdown(f"<div class='hm-h9a4c-cardline'><b>Other Fluid {idx + 1}</b></div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    prior_type = prior.get("type") or "Select"
                    fluid_type = st.selectbox(f"Fluid type {idx + 1}", fluid_options, index=fluid_options.index(prior_type) if prior_type in fluid_options else 0, key=f"hm_h9a4c_fluid_type_{date_key}_{idx}")
                with c2:
                    fluid_time = st.time_input(f"Fluid timing {idx + 1}", value=_parse_time(prior.get("time")), key=f"hm_h9a4c_fluid_time_{date_key}_{idx}")
                q_col, n_col = st.columns(2)
                with q_col:
                    quantity = st.text_input(f"Quantity {idx + 1}", value=prior.get("quantity", ""), placeholder="Example: 200 ml", key=f"hm_h9a4c_fluid_qty_{date_key}_{idx}")
                with n_col:
                    notes = st.text_input(f"Notes {idx + 1}", value=prior.get("notes", ""), placeholder="Example: unsweetened", key=f"hm_h9a4c_fluid_notes_{date_key}_{idx}")
                fluid_row = {"type": _clean(fluid_type), "time": _time_text(fluid_time), "quantity": _clean(quantity), "notes": _clean(notes)}
                if _intake_has_data(fluid_row):
                    other_fluids.append(fluid_row)
            st.markdown("</div>", unsafe_allow_html=True)

    existing_poop_rounds = existing.get("poop_rounds")
    if _is_default(existing_poop_rounds):
        existing_poop_rounds = "Select"
    else:
        try:
            existing_poop_rounds = int(existing_poop_rounds)
        except Exception:
            existing_poop_rounds = "Select"
    poop_rounds = existing_poop_rounds
    existing_timings = existing.get("poop_timings", []) or []
    poop_timings = list(existing_timings)
    feeling_after_poop = _clean(existing.get("feeling_after_poop"))
    with st.container(border=True):
        if _toggle_button(f"Bowel Movement — {_bowel_summary(existing_poop_rounds, existing.get('feeling_after_poop'))}", f"{date_key}_bowel"):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            poop_options = ["Select"] + list(range(10))
            poop_rounds = st.selectbox("Poop rounds", poop_options, index=poop_options.index(existing_poop_rounds) if existing_poop_rounds in poop_options else 0, key=f"hm_h9a4c_poop_rounds_{date_key}")
            active_poop_count = int(poop_rounds) if isinstance(poop_rounds, int) else 0
            poop_timings = []
            if active_poop_count:
                for idx in range(active_poop_count):
                    timing = st.time_input(f"Poop timing {idx + 1}", value=_parse_time(existing_timings[idx]) if idx < len(existing_timings) else None, key=f"hm_h9a4c_poop_time_{date_key}_{idx}")
                    poop_timings.append(_time_text(timing))
            else:
                st.caption("No timing needed unless poop rounds are greater than 0.")
            feeling_after_poop = st.text_area("Feeling after poop", value=_clean(existing.get("feeling_after_poop")), placeholder="Example: relieved / constipated / bloated / incomplete", key=f"hm_h9a4c_poop_feeling_{date_key}", height=84)
            st.markdown("</div>", unsafe_allow_html=True)

    physical_activity = _clean(existing.get("physical_activity"))
    with st.container(border=True):
        if _toggle_button(f"Physical Activity — {physical_activity or 'No activity entry yet'}", f"{date_key}_activity"):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            physical_activity = st.text_area("Physical activity", value=physical_activity, placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM", key=f"hm_h9a4c_activity_{date_key}", height=90)
            st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Member Notes")
        day_notes = st.text_area("Notes", value=_clean(existing.get("notes")), placeholder="Any cravings, bloating, missed meals, late meals, etc.", key=f"hm_h9a4c_notes_{date_key}", height=90)

    clean_meals_payload = {key: value for key, value in meals_payload.items() if _meal_has_data(value)}
    clean_water = _clean(water_litres)
    clean_poop_rounds = None if _is_default(poop_rounds) else poop_rounds
    clean_poop_timings = [_clean(x) for x in poop_timings if _has_value(x)]
    clean_feeling = _clean(feeling_after_poop)
    clean_activity = _clean(physical_activity)
    clean_notes = _clean(day_notes)
    poop_text = ""
    if clean_poop_rounds is not None:
        poop_text = f"{clean_poop_rounds} round(s)"
        if clean_poop_timings:
            poop_text += f" at {', '.join(clean_poop_timings)}"
        if clean_feeling:
            poop_text += f" / {clean_feeling}"
    payload = {"date": date_key, "meals": clean_meals_payload, "physical_activity": clean_activity, "poop_rounds": clean_poop_rounds, "poop_timings": clean_poop_timings, "feeling_after_poop": clean_feeling, "poop": poop_text, "notes": clean_notes, "water_litres": clean_water, "other_fluids": _normalise_other_fluids(other_fluids)}

    with st.container(border=True):
        st.markdown("### Save Day")
        if _day_has_meaningful_entry(payload):
            st.markdown(f"<div class='hm-h9a4c-status'>Entries captured for {log_date.strftime('%d %b')}. You can still edit them.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='hm-h9a4c-warning'>No entries captured yet. Please add at least one real entry before saving.</div>", unsafe_allow_html=True)
        if st.button("Save Day", type="primary", use_container_width=True):
            if not _day_has_meaningful_entry(payload):
                set_system_message("Please add at least one entry before saving the day.", "error")
                st.rerun()
            save_daily_food_journal_day(user_id, date_key, payload)
            set_system_message(f"Saved food journal for {log_date.strftime('%d %b %Y')}.", "success")
            st.rerun()

    with st.container(border=True):
        st.markdown("### Full Day Report")
        st.caption(log_date.strftime("%a, %d %b %Y"))
        lines = _report_lines(payload)
        if not lines:
            st.caption("Start adding entries or tap a saved day to load the report.")
        else:
            for line in lines:
                st.markdown(f"- {_safe_html(line)}")

    with st.container(border=True):
        st.markdown(f"### Guidance linked to {log_date.strftime('%d %b')}")
        latest_note = get_latest_daily_log_note_for_date(user_id, date_key)
        history = get_daily_log_notes_by_date(user_id, date_key, limit=10)
        if not latest_note:
            st.caption("No nutritionist note or general guidance is linked to this date yet.")
        else:
            st.markdown(f"<div class='hm-h9a4c-cardline'><b>{_safe_html(format_local_ts(latest_note.get('ts', '')))}</b><br>{_safe_html(latest_note.get('note', ''))}</div>", unsafe_allow_html=True)
        if len(history) > 1 and _toggle_button("View note history", f"{date_key}_note_history"):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            for note in history:
                st.markdown(f"<div class='hm-h9a4c-cardline'><b>{_safe_html(format_local_ts(note.get('ts', '')))}</b><br>{_safe_html(note.get('note', ''))}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


st.set_page_config(page_title="Daily Log", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("Daily Log", "Capture food and activity updates for one day.", "Member tracker")
_render_css()
render_system_message()

user_id = st.session_state["user_id"]
food_tab, exercise_tab = st.tabs(["Food Journal", "Exercise Journal"])
with food_tab:
    _render_food_journal(user_id)
with exercise_tab:
    _render_exercise_journal_placeholder()

render_page_nav("Daily Log", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
