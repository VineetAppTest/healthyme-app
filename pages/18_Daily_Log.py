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
    inject_keepalive_guard_v96_11,
)
from components.db import (
    save_daily_food_journal_day,
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    get_daily_log_notes_by_date,
    get_latest_daily_log_note_for_date,
)
from components.flash import set_system_message, render_system_message


BUILD_NOTE = "v102.4B26 · Daily Log label alignment and meal spacing cleanup"
MAX_MEAL_ITEMS = 9

STRUCTURED_MEAL_ORDER = [
    ("Breakfast", "breakfast"),
    ("Lunch", "lunch"),
    ("Evening Snack", "evening_snack"),
    ("Dinner", "dinner"),
    ("Bedtime", "bedtime"),
]


def _text(value):
    return "" if value is None else str(value).strip()


def _is_default(value):
    normalized = re.sub(r"[\s_-]+", " ", _text(value).lower())
    return normalized in {
        "",
        "select",
        "selected",
        "please select",
        "select option",
        "choose",
        "choose one",
        "hh",
        "mm",
        "am/pm",
    }


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
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %b %Y",
        "%d-%b-%Y",
    ):
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


def _food_item_has_data(item):
    item = _as_dict(item)
    return _has_value(item.get("food") or item.get("name")) or _has_value(
        item.get("portion_size") or item.get("portion") or item.get("quantity")
    )


def _normalise_food_items(meal):
    meal = _as_dict(meal)
    rows = []
    raw_items = meal.get("food_items")
    if isinstance(raw_items, list):
        for item in raw_items:
            item = _as_dict(item)
            row = {
                "food": _clean(item.get("food") or item.get("name")),
                "portion_size": _clean(
                    item.get("portion_size")
                    or item.get("portion")
                    or item.get("quantity")
                ),
            }
            if _food_item_has_data(row):
                rows.append(row)

    if not rows:
        legacy_food = _clean(
            meal.get("food") or meal.get("food_log") or meal.get("name")
        )
        legacy_portion = _clean(
            meal.get("portion_size") or meal.get("quantity")
        )
        if legacy_food or legacy_portion:
            rows.append({"food": legacy_food, "portion_size": legacy_portion})
    return rows[:MAX_MEAL_ITEMS]


def _meal_summary(meal):
    meal = _as_dict(meal)
    items = _normalise_food_items(meal)
    time_text = _clean(meal.get("time"))
    if items:
        first = " · ".join(
            value
            for value in [
                items[0].get("food", ""),
                items[0].get("portion_size", ""),
            ]
            if value
        )
        if len(items) > 1:
            first = f"{first} + {len(items) - 1} more item(s)"
        return " · ".join(value for value in [time_text, first] if value)
    if time_text or _has_value(meal.get("mood")) or _has_value(meal.get("energy")):
        return " · ".join(
            value for value in [time_text, "Meal details added"] if value
        )
    return "No entry yet"


def _meal_has_data(meal):
    meal = _as_dict(meal)
    if _normalise_food_items(meal):
        return True
    return any(
        _has_value(meal.get(key))
        for key in (
            "time",
            "food",
            "food_log",
            "name",
            "portion_size",
            "quantity",
            "mood_energy",
            "mood",
            "energy",
        )
    )


def _is_snacking_key(key):
    key_text = str(key or "").lower()
    return (
        key_text.startswith("snacking_")
        or key_text.startswith("snack_")
        or key_text.startswith("other_snack")
    )


def _looks_like_evening_snack(value):
    if not isinstance(value, dict):
        return False
    label_text = str(value.get("label") or "").lower()
    return "evening" in label_text and "snack" in label_text


def _normalise_meals(existing_meals):
    meals = existing_meals if isinstance(existing_meals, dict) else {}
    normalised = {
        "breakfast": _as_dict(meals.get("breakfast")),
        "lunch": _as_dict(meals.get("lunch")),
        "evening_snack": _as_dict(
            meals.get("evening_snack")
            or meals.get("evening_snacks")
            or meals.get("evening")
        ),
        "dinner": _as_dict(meals.get("dinner")),
        "bedtime": _as_dict(meals.get("bedtime") or meals.get("pre_bed")),
    }

    snacks = []
    evening_candidates = []
    for key, value in meals.items():
        if not isinstance(value, dict) or not _meal_has_data(value):
            continue
        key_text = str(key or "").lower()
        if key_text in {
            "breakfast",
            "lunch",
            "evening_snack",
            "evening_snacks",
            "evening",
            "dinner",
            "bedtime",
            "pre_bed",
        }:
            continue
        if _is_snacking_key(key):
            if _looks_like_evening_snack(value):
                evening_candidates.append(dict(value))
            else:
                snacks.append(dict(value))

    if not _meal_has_data(normalised.get("evening_snack")) and evening_candidates:
        normalised["evening_snack"] = evening_candidates[0]
        snacks = evening_candidates[1:] + snacks
    else:
        snacks = evening_candidates + snacks

    return normalised, snacks[:9]


def _intake_has_data(item):
    item = item if isinstance(item, dict) else {}
    return any(
        _has_value(item.get(key))
        for key in (
            "type",
            "name",
            "fluid_type",
            "time",
            "quantity",
            "qty",
            "notes",
        )
    )


def _normalise_other_fluids(items):
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        cleaned = {
            "type": _clean(
                item.get("type") or item.get("name") or item.get("fluid_type")
            ),
            "time": _clean(item.get("time")),
            "quantity": _clean(item.get("quantity") or item.get("qty")),
            "notes": _clean(item.get("notes")),
        }
        if _intake_has_data(cleaned):
            out.append(cleaned)
    return out[:9]


def _format_saved_date(day):
    if not isinstance(day, dict):
        return ""
    for key in (
        "_journal_date_key",
        "date",
        "log_date",
        "journal_date",
        "food_journal_date",
    ):
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
    if payload.get("poop_rounds") is not None and not _is_default(
        payload.get("poop_rounds")
    ):
        return True
    if any(_has_value(value) for value in payload.get("poop_timings", [])):
        return True
    return any(
        _has_value(payload.get(key))
        for key in ("feeling_after_poop", "physical_activity", "notes")
    )


def _report_lines(payload):
    lines = []
    meals = payload.get("meals") or {}
    for label, key in STRUCTURED_MEAL_ORDER:
        meal = meals.get(key) or {}
        if not _meal_has_data(meal):
            continue
        items = _normalise_food_items(meal)
        food_text = "; ".join(
            " — ".join(
                value
                for value in [
                    item.get("food", ""),
                    item.get("portion_size", ""),
                ]
                if value
            )
            for item in items
        )
        detail = " | ".join(
            value
            for value in [
                f"Time: {_clean(meal.get('time'))}"
                if _has_value(meal.get("time"))
                else "",
                f"Food: {food_text}" if food_text else "",
                f"Mood: {_clean(meal.get('mood'))}"
                if _has_value(meal.get("mood"))
                else "",
                f"Energy: {_clean(meal.get('energy'))}"
                if _has_value(meal.get("energy"))
                else "",
            ]
            if value
        )
        lines.append(f"{label}: {detail or 'Recorded'}")

    snack_items = [
        (key, value)
        for key, value in meals.items()
        if str(key).startswith("snacking_") and _meal_has_data(value)
    ]
    for idx, (_key, meal) in enumerate(snack_items, start=1):
        lines.append(f"Snacking {idx}: {_meal_summary(meal)}")

    if _has_value(payload.get("water_litres")):
        lines.append(f"Water: {_clean(payload.get('water_litres'))}")
    for idx, fluid in enumerate(
        _normalise_other_fluids(payload.get("other_fluids", [])), start=1
    ):
        parts = [
            fluid.get("time", ""),
            fluid.get("type", ""),
            fluid.get("quantity", ""),
            fluid.get("notes", ""),
        ]
        lines.append(
            f"Other fluid {idx}: {' · '.join(value for value in parts if value)}"
        )
    if payload.get("poop_rounds") is not None and not _is_default(
        payload.get("poop_rounds")
    ):
        lines.append(f"Poop rounds: {payload.get('poop_rounds')}")
    poop_times = [
        _clean(value)
        for value in payload.get("poop_timings", [])
        if _has_value(value)
    ]
    if poop_times:
        lines.append(f"Poop timings: {', '.join(poop_times)}")
    if _has_value(payload.get("feeling_after_poop")):
        lines.append(
            f"Feeling after poop: {_clean(payload.get('feeling_after_poop'))}"
        )
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
        .hm-h9a4c-cardline{border:1px solid #E7D8BE;background:#FFFDF8;border-radius:16px;padding:.75rem .85rem;margin:.45rem 0;}
        .hm-exercise-placeholder{border:1px dashed #D8C18B;background:#FFFDF8;border-radius:16px;padding:1rem;margin:.5rem 0;color:#334155;}
        .hm-snacking-subtitle{color:#64748B;font-size:.82rem;font-weight:720;margin:.35rem 0 .15rem 0;}
        div[data-testid="stTabs"] [role="tablist"]{gap:.55rem;margin:.15rem 0 1rem 0;border-bottom:1px solid #E3D4BA;padding-bottom:.45rem;}
        div[data-testid="stTabs"] button[role="tab"]{border:1.4px solid #D8A84E!important;border-radius:999px!important;background:#FFFFFF!important;color:#064E3B!important;font-weight:950!important;padding:.62rem 1.18rem!important;box-shadow:0 7px 16px rgba(6,78,59,.07)!important;min-height:2.65rem!important;}
        div[data-testid="stTabs"] button[aria-selected="true"]{background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;color:#FFFFFF!important;border-color:#064E3B!important;box-shadow:0 12px 22px rgba(6,78,59,.18)!important;}
        div[data-testid="stTabs"] button[aria-selected="true"] *{color:#FFFFFF!important;}
        .hm-toggle-anchor + div [data-testid="stButton"] > button,
        .hm-toggle-anchor + div .stButton > button{justify-content:flex-start!important;text-align:left!important;min-height:2.72rem!important;background:linear-gradient(135deg,#FFFDF8 0%,#FFF6E5 100%)!important;border:1.45px solid #D8A84E!important;border-radius:16px!important;box-shadow:0 7px 16px rgba(15,23,42,.045)!important;color:#064E3B!important;font-weight:950!important;margin:.50rem 0 .34rem 0!important;padding:.58rem .78rem!important;}
        .hm-toggle-anchor + div [data-testid="stButton"] > button *,
        .hm-toggle-anchor + div .stButton > button *{color:#064E3B!important;font-size:.90rem!important;font-weight:950!important;line-height:1.18!important;white-space:normal!important;overflow-wrap:normal!important;word-break:normal!important;text-align:left!important;}
        .hm-toggle-body:empty{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important;}
        .hm-toggle-body{border:1px solid #E7D8BE;background:#FFFDF8;border-radius:16px;padding:1rem 1rem 1.18rem!important;margin:.16rem 0 .76rem 0;overflow:visible!important;}
        .hm-toggle-body div[data-testid="stHorizontalBlock"]{overflow:visible!important;padding-bottom:.18rem!important;}
        .hm-toggle-body div[data-testid="column"]{overflow:visible!important;padding-bottom:.12rem!important;}
        div[data-testid="stTextInput"],div[data-testid="stSelectbox"],div[data-testid="stTimeInput"],div[data-testid="stTextArea"]{margin-bottom:.58rem!important;padding-bottom:.08rem!important;overflow:visible!important;}
        div[data-testid="stTextInput"] label,div[data-testid="stSelectbox"] label,div[data-testid="stTimeInput"] label,div[data-testid="stTextArea"] label{display:block!important;margin-bottom:.34rem!important;padding-bottom:.12rem!important;line-height:1.25!important;color:#334155!important;font-weight:720!important;overflow:visible!important;}
        div[data-testid="stTextInput"] input,div[data-testid="stTimeInput"] input,div[data-testid="stTextArea"] textarea,div[data-testid="stSelectbox"] [data-baseweb="select"] > div{border-radius:13px!important;border:1.2px solid #DCC690!important;background:#FFFFFF!important;min-height:2.70rem!important;line-height:1.3!important;padding-top:.58rem!important;padding-bottom:.58rem!important;overflow:visible!important;}
        .hm-add-food-anchor{display:block!important;height:0!important;min-height:0!important;margin:-.30rem 0 0 0!important;padding:0!important;overflow:hidden!important;}
        .hm-add-food-anchor + div [data-testid="stButton"] > button{width:auto!important;min-width:12rem!important;margin:0 0 .58rem 0!important;}
        @media(max-width:760px){
          .hm-add-food-anchor + div [data-testid="stButton"] > button{width:100%!important;}
        }
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


def _legacy_mood_and_energy(prior):
    prior = _as_dict(prior)
    mood = _clean(prior.get("mood"))
    energy = _clean(prior.get("energy"))
    combined = _clean(prior.get("mood_energy"))
    if combined and not mood and not energy:
        mood = combined
    return mood, energy


def _render_meal_fields(label, key, prior, date_key):
    prior = _as_dict(prior)
    time_value = st.time_input(
        label,
        value=_parse_time(prior.get("time", "")),
        key=f"{date_key}_{key}_time",
    )

    existing_items = _normalise_food_items(prior)
    count_key = f"hm_meal_item_count_{date_key}_{key}"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(existing_items))
    item_count = max(
        1,
        min(MAX_MEAL_ITEMS, int(st.session_state.get(count_key, 1) or 1)),
    )

    food_items = []
    for idx in range(item_count):
        prior_item = existing_items[idx] if idx < len(existing_items) else {}
        food_col, portion_col = st.columns([1.45, 1], gap="medium")
        with food_col:
            food = st.text_input(
                f"Food item {idx + 1}",
                value=prior_item.get("food", ""),
                key=f"{date_key}_{key}_food_{idx}",
                label_visibility="collapsed",
                placeholder="Enter food item",
            )
        with portion_col:
            portion = st.text_input(
                f"Portion {idx + 1}",
                value=prior_item.get("portion_size", ""),
                key=f"{date_key}_{key}_portion_{idx}",
                label_visibility="collapsed",
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


def _render_meal_toggle(label, key, prior, date_key):
    if _toggle_button(f"{label} — {_meal_summary(prior)}", f"{date_key}_{key}"):
        return _render_meal_fields(label, key, prior, date_key)
    return _as_dict(prior)


def _render_snacking_toggle(existing_snacks, date_key):
    snack_count_key = f"hm_h9a4c_snack_count_{date_key}"
    if snack_count_key not in st.session_state:
        st.session_state[snack_count_key] = len(existing_snacks)
    snack_count = int(st.session_state.get(snack_count_key, 0) or 0)
    snacking_payload = {}

    st.markdown(
        "<div class='hm-snacking-subtitle'>Optional snacking, separate from structured meals</div>",
        unsafe_allow_html=True,
    )
    if _toggle_button(f"Snacking — {snack_count}/9 entries", f"{date_key}_snacking"):
        add_col, remove_col = st.columns(2)
        with add_col:
            if st.button(
                "+ Add snacking",
                key=f"hm_h9a4c_add_snack_{date_key}",
                disabled=snack_count >= 9,
                use_container_width=True,
            ):
                st.session_state[snack_count_key] = min(9, snack_count + 1)
                st.rerun()
        with remove_col:
            if st.button(
                "Remove last snacking",
                key=f"hm_h9a4c_remove_snack_{date_key}",
                disabled=snack_count <= 0,
                use_container_width=True,
            ):
                st.session_state[snack_count_key] = max(0, snack_count - 1)
                st.rerun()
        if snack_count == 0:
            st.caption("No snacking entry added yet.")
        for idx in range(snack_count):
            prior = existing_snacks[idx] if idx < len(existing_snacks) else {}
            st.markdown(
                f"<div class='hm-h9a4c-cardline'><b>Snacking {idx + 1}</b></div>",
                unsafe_allow_html=True,
            )
            snacking_payload[f"snacking_{idx + 1}"] = _render_meal_fields(
                f"Snacking {idx + 1}",
                f"snacking_{idx + 1}",
                prior,
                date_key,
            )
    else:
        for idx, prior in enumerate(existing_snacks[:snack_count], start=1):
            snacking_payload[f"snacking_{idx}"] = prior
    return snacking_payload


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


def _render_saved_days(user_id):
    today = date.today()
    st.session_state.setdefault("hm_h9a4c_saved_from", today)
    st.session_state.setdefault("hm_h9a4c_saved_to", today)

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

        if not filtered_days:
            st.caption("No saved days found in this range.")
            return

        st.caption(f"Showing {len(filtered_days)} saved day(s) in the selected range.")
        for row_start in range(0, len(filtered_days), 4):
            cols = st.columns(4)
            for col, day in zip(cols, filtered_days[row_start : row_start + 4]):
                date_text = _format_saved_date(day)
                label_date = _parse_date(date_text)
                button_label = label_date.strftime("%d %b") if label_date else date_text
                with col:
                    if st.button(
                        button_label,
                        key=f"hm_h9a4c_load_{date_text}",
                        use_container_width=True,
                    ):
                        if label_date:
                            st.session_state["hm_food_journal_date"] = label_date
                            st.rerun()


def _render_food_journal(user_id):
    if "hm_food_journal_date" not in st.session_state:
        st.session_state["hm_food_journal_date"] = date.today()

    with st.container(border=True):
        st.markdown("### Food Journal Date")
        log_date = st.date_input(
            "Select the date for this food journal entry",
            key="hm_food_journal_date",
        )
        date_key = str(log_date)

    existing = get_daily_food_journal_day(user_id, date_key) or {}
    existing_meals, existing_snacks = _normalise_meals(existing.get("meals", {}) or {})
    existing_other_fluids = _normalise_other_fluids(
        existing.get("other_fluids", []) or []
    )
    is_saved_date = bool(existing and _day_has_meaningful_entry(existing))

    with st.container(border=True):
        st.markdown("### Meal Section")
        if is_saved_date:
            st.markdown(
                f"<div class='hm-h9a4c-note'>Viewing saved entries for {log_date.strftime('%d %b')}. Open a section only if you want to edit it.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='hm-h9a4c-note'>Open only the meal you want to update.</div>",
                unsafe_allow_html=True,
            )

        meals_payload = {}
        for label, key in STRUCTURED_MEAL_ORDER:
            meals_payload[key] = _render_meal_toggle(
                label, key, existing_meals.get(key, {}), date_key
            )
        meals_payload.update(_render_snacking_toggle(existing_snacks, date_key))

    water_options = [
        "Select",
        "0 Litres",
        "0.5 Litres",
        "1 Litre",
        "1.5 Litres",
        "2 Litres",
        "2.5 Litres",
        "3 Litres",
        "3.5 Litres",
        "4 Litres",
        "4.5 Litres",
        "5 Litres",
        "5.5 Litres",
        "6 Litres",
        "6.5 Litres",
        "7 Litres",
        "7.5 Litres",
        "8 Litres",
        "8.5 Litres",
        "9 Litres",
        "9.5 Litres",
        "10 Litres",
    ]
    existing_water = _clean(existing.get("water_litres")) or "Select"
    water_litres = existing_water
    other_fluids = existing_other_fluids

    with st.container(border=True):
        if _toggle_button(
            f"Hydration — {_hydration_summary(existing_water, existing_other_fluids)}",
            f"{date_key}_hydration",
        ):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            st.markdown(
                "<div class='hm-h9a4c-note'>Water and other fluids are grouped together for the full day.</div>",
                unsafe_allow_html=True,
            )
            water_litres = st.selectbox(
                "Water Intake",
                water_options,
                index=(
                    water_options.index(existing_water)
                    if existing_water in water_options
                    else 0
                ),
                key=f"hm_h9a4c_water_{date_key}",
            )
            fluid_count_key = f"hm_h9a4c_fluid_count_{date_key}"
            if fluid_count_key not in st.session_state:
                st.session_state[fluid_count_key] = len(existing_other_fluids)
            fluid_count = int(st.session_state.get(fluid_count_key, 0) or 0)
            st.markdown(
                f"<div class='hm-h9a4c-cardline'><b>Other Fluid Intake</b><br>{fluid_count}/9 entries</div>",
                unsafe_allow_html=True,
            )
            add_col, remove_col = st.columns(2)
            with add_col:
                if st.button(
                    "+ Add other fluid",
                    key=f"hm_h9a4c_add_fluid_{date_key}",
                    disabled=fluid_count >= 9,
                    use_container_width=True,
                ):
                    st.session_state[fluid_count_key] = min(9, fluid_count + 1)
                    st.rerun()
            with remove_col:
                if st.button(
                    "Remove last fluid",
                    key=f"hm_h9a4c_remove_fluid_{date_key}",
                    disabled=fluid_count <= 0,
                    use_container_width=True,
                ):
                    st.session_state[fluid_count_key] = max(0, fluid_count - 1)
                    st.rerun()

            fluid_options = [
                "Select",
                "Herbal Tea",
                "Coconut Water",
                "Juice",
                "Cold Drink",
                "Tea / Coffee",
                "Buttermilk",
                "Other",
            ]
            other_fluids = []
            if fluid_count == 0:
                st.caption("No other fluid entry added yet.")
            for idx in range(fluid_count):
                prior = (
                    existing_other_fluids[idx]
                    if idx < len(existing_other_fluids)
                    else {}
                )
                st.markdown(
                    f"<div class='hm-h9a4c-cardline'><b>Other Fluid {idx + 1}</b></div>",
                    unsafe_allow_html=True,
                )
                type_col, time_col = st.columns(2)
                with type_col:
                    prior_type = prior.get("type") or "Select"
                    fluid_type = st.selectbox(
                        f"Fluid type {idx + 1}",
                        fluid_options,
                        index=(
                            fluid_options.index(prior_type)
                            if prior_type in fluid_options
                            else 0
                        ),
                        key=f"hm_h9a4c_fluid_type_{date_key}_{idx}",
                    )
                with time_col:
                    fluid_time = st.time_input(
                        f"Fluid timing {idx + 1}",
                        value=_parse_time(prior.get("time")),
                        key=f"hm_h9a4c_fluid_time_{date_key}_{idx}",
                    )
                quantity_col, notes_col = st.columns(2)
                with quantity_col:
                    quantity = st.text_input(
                        f"Quantity {idx + 1}",
                        value=prior.get("quantity", ""),
                        placeholder="Example: 200 ml",
                        key=f"hm_h9a4c_fluid_qty_{date_key}_{idx}",
                    )
                with notes_col:
                    notes = st.text_input(
                        f"Notes {idx + 1}",
                        value=prior.get("notes", ""),
                        placeholder="Example: unsweetened",
                        key=f"hm_h9a4c_fluid_notes_{date_key}_{idx}",
                    )
                fluid_row = {
                    "type": _clean(fluid_type),
                    "time": _time_text(fluid_time),
                    "quantity": _clean(quantity),
                    "notes": _clean(notes),
                }
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
        if _toggle_button(
            f"Bowel Movement — {_bowel_summary(existing_poop_rounds, existing.get('feeling_after_poop'))}",
            f"{date_key}_bowel",
        ):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            poop_options = ["Select"] + list(range(10))
            poop_rounds = st.selectbox(
                "Poop rounds",
                poop_options,
                index=(
                    poop_options.index(existing_poop_rounds)
                    if existing_poop_rounds in poop_options
                    else 0
                ),
                key=f"hm_h9a4c_poop_rounds_{date_key}",
            )
            active_poop_count = int(poop_rounds) if isinstance(poop_rounds, int) else 0
            poop_timings = []
            if active_poop_count:
                for idx in range(active_poop_count):
                    timing = st.time_input(
                        f"Poop timing {idx + 1}",
                        value=(
                            _parse_time(existing_timings[idx])
                            if idx < len(existing_timings)
                            else None
                        ),
                        key=f"hm_h9a4c_poop_time_{date_key}_{idx}",
                    )
                    poop_timings.append(_time_text(timing))
            else:
                st.caption("No timing needed unless poop rounds are greater than 0.")
            feeling_after_poop = st.text_area(
                "Feeling after poop",
                value=_clean(existing.get("feeling_after_poop")),
                placeholder="Example: relieved / constipated / bloated / incomplete",
                key=f"hm_h9a4c_poop_feeling_{date_key}",
                height=84,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    physical_activity = _clean(existing.get("physical_activity"))
    with st.container(border=True):
        if _toggle_button(
            f"Physical Activity — {physical_activity or 'No activity entry yet'}",
            f"{date_key}_activity",
        ):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            physical_activity = st.text_area(
                "Physical activity",
                value=physical_activity,
                placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
                key=f"hm_h9a4c_activity_{date_key}",
                height=90,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Member Notes")
        day_notes = st.text_area(
            "Notes",
            value=_clean(existing.get("notes")),
            placeholder="Any cravings, bloating, missed meals, late meals, etc.",
            key=f"hm_h9a4c_notes_{date_key}",
            height=90,
        )

    clean_meals_payload = {
        key: value for key, value in meals_payload.items() if _meal_has_data(value)
    }
    clean_water = _clean(water_litres)
    clean_poop_rounds = None if _is_default(poop_rounds) else poop_rounds
    clean_poop_timings = [
        _clean(value) for value in poop_timings if _has_value(value)
    ]
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

    payload = {
        "date": date_key,
        "meals": clean_meals_payload,
        "physical_activity": clean_activity,
        "poop_rounds": clean_poop_rounds,
        "poop_timings": clean_poop_timings,
        "feeling_after_poop": clean_feeling,
        "poop": poop_text,
        "notes": clean_notes,
        "water_litres": clean_water,
        "other_fluids": _normalise_other_fluids(other_fluids),
    }

    with st.container(border=True):
        st.markdown("### Save Day")
        if _day_has_meaningful_entry(payload):
            st.markdown(
                f"<div class='hm-h9a4c-status'>Entries captured for {log_date.strftime('%d %b')}. You can still edit them.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='hm-h9a4c-warning'>No entries captured yet. Please add at least one real entry before saving.</div>",
                unsafe_allow_html=True,
            )
        if st.button("Save Day", type="primary", use_container_width=True):
            if not _day_has_meaningful_entry(payload):
                set_system_message(
                    "Please add at least one entry before saving the day.", "error"
                )
                st.rerun()
            save_daily_food_journal_day(user_id, date_key, payload)
            set_system_message(
                f"Saved food journal for {log_date.strftime('%d %b %Y')}.",
                "success",
            )
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
            st.caption(
                "No nutritionist note or general guidance is linked to this date yet."
            )
        else:
            st.markdown(
                f"<div class='hm-h9a4c-cardline'><b>{_safe_html(format_local_ts(latest_note.get('ts', '')))}</b><br>{_safe_html(latest_note.get('note', ''))}</div>",
                unsafe_allow_html=True,
            )
        if len(history) > 1 and _toggle_button(
            "View note history", f"{date_key}_note_history"
        ):
            st.markdown("<div class='hm-toggle-body'>", unsafe_allow_html=True)
            for note in history:
                st.markdown(
                    f"<div class='hm-h9a4c-cardline'><b>{_safe_html(format_local_ts(note.get('ts', '')))}</b><br>{_safe_html(note.get('note', ''))}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    _render_saved_days(user_id)


st.set_page_config(
    page_title="Daily Log",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
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

render_page_nav(
    "Daily Log",
    back_page="pages/02_Member_Home.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
inject_keepalive_guard_v96_11()
