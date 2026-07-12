from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
from typing import Any, Dict, List, Tuple

import streamlit as st

PROFILE_TABLE = "hm_recommendation_profiles"
ITEM_TABLE = "hm_recommendation_profile_items"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
ITEM_SELECT_LEGACY = "item_type,day_number,slot_name,item_order,reference_label,portion,instruction,scheduled_time,intensity,dosage_frequency"
SOURCE_COLUMNS = ["source_type", "source_id", "source_label", "source_snapshot", "source_image_url", "source_image_bucket", "source_image_path", "source_image_access_type"]
ITEM_SELECT_WITH_SOURCE = ITEM_SELECT_LEGACY + "," + ",".join(SOURCE_COLUMNS)


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _esc(value: object) -> str:
    return html.escape(_clean(value))


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _as_dict(value: object) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _as_list(value: object) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [value]
        except Exception:
            return [value]
    return []


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean(value, default)
    try:
        value = st.secrets.get(name)
        if value is not None:
            return _clean(value, default)
        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean(value, default)
        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name) or section_values.get(lower_name)
                if value is not None:
                    return _clean(value, default)
            except Exception:
                continue
    except Exception:
        pass
    return default


def _client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Supabase URL/key is not configured.")
    return create_client(url, key)


def _rows(response) -> List[dict]:
    return list(getattr(response, "data", None) or [])


def parse_dosage_frequency(value: object) -> Tuple[int, str]:
    raw = _clean(value)
    if not raw:
        return 0, ""
    match = re.match(r"^Frequency:\s*(\d+)\s*;\s*Dosage:\s*(.*)$", raw)
    if match:
        return _safe_int(match.group(1)), _clean(match.group(2))
    return 0, raw


def parse_timeline(value: object) -> List[str]:
    raw = _clean(value)
    if not raw:
        return []
    return [part.strip() for part in raw.replace("|", ",").split(",") if part.strip()]


def _member_tokens(member_id: str = "", email: str = "") -> set:
    tokens = set()
    for value in (member_id, email):
        clean = _clean(value)
        if clean:
            tokens.add(clean)
            tokens.add(clean.lower())
    return {token for token in tokens if token}


def _profile_matches_member(profile: Dict[str, Any], member_id: str, email: str) -> bool:
    tokens = _member_tokens(member_id, email)
    if not tokens:
        return False
    label = _clean(profile.get("assigned_member_label"))
    profile_values = {_clean(profile.get("assigned_member_id")), _clean(profile.get("assigned_member_id")).lower(), label, label.lower()}
    for token in tokens:
        if token in profile_values:
            return True
        if token.lower() and token.lower() in label.lower():
            return True
    return False


@st.cache_data(ttl=90, show_spinner=False)
def load_active_recommendation_profile(member_id: str, email: str = "") -> Tuple[bool, Dict[str, Any], List[dict], str]:
    try:
        c = _client()
        profile_result = c.table(PROFILE_TABLE).select("*").eq("status", "active").order("updated_at", desc=True).limit(150).execute()
        profiles = [p for p in _rows(profile_result) if _profile_matches_member(p, member_id, email)]
        if not profiles:
            return True, {}, [], "No active recommendation profile found for this member."
        profile = profiles[0]
        try:
            item_result = c.table(ITEM_TABLE).select(ITEM_SELECT_WITH_SOURCE).eq("profile_id", profile.get("id")).order("day_number").order("item_type").order("item_order").execute()
            return True, profile, _rows(item_result), "Loaded active recommendation with source-backed fields."
        except Exception:
            item_result = c.table(ITEM_TABLE).select(ITEM_SELECT_LEGACY).eq("profile_id", profile.get("id")).order("day_number").order("item_type").order("item_order").execute()
            return True, profile, _rows(item_result), "Loaded active recommendation using legacy item fields."
    except Exception as exc:
        return False, {}, [], f"Could not load member recommendation: {exc}"


def clear_member_recommendation_cache() -> None:
    load_active_recommendation_profile.clear()


def row_has_content(row: dict) -> bool:
    return any(_clean(row.get(field)) for field in ("reference_label", "portion", "instruction", "scheduled_time", "intensity", "dosage_frequency"))


def active_items(items: List[dict]) -> List[dict]:
    return [row for row in items if isinstance(row, dict) and row_has_content(row)]


def source_snapshot(row: dict) -> Dict[str, Any]:
    return _as_dict(row.get("source_snapshot"))


def source_original_snapshot(row: dict) -> Dict[str, Any]:
    snapshot = source_snapshot(row)
    original = _as_dict(snapshot.get("source_original_snapshot"))
    return original or snapshot


def source_value(row: dict, field: str, default: str = "") -> str:
    snapshot = source_snapshot(row)
    original = source_original_snapshot(row)
    return _clean(snapshot.get(field) or original.get(field), default)


def image_reference_text(row: dict) -> str:
    parts = []
    for field in ("source_image_url", "source_image_bucket", "source_image_path"):
        value = _clean(row.get(field))
        if value:
            parts.append(value)
    if not parts:
        image = _as_dict(source_original_snapshot(row).get("image"))
        for field in ("image_url", "image_bucket", "image_path"):
            value = _clean(image.get(field))
            if value:
                parts.append(value)
    return " | ".join(parts)


def source_context_text(row: dict) -> str:
    item_type = row.get("item_type")
    if item_type == "meal":
        parts = [source_value(row, "meal_type"), source_value(row, "diet_type"), source_value(row, "prep_time"), source_value(row, "calories")]
    elif item_type == "exercise":
        parts = [source_value(row, "category"), source_value(row, "difficulty"), source_value(row, "duration_or_reps"), source_value(row, "equipment")]
    elif item_type == "supplement":
        parts = [source_value(row, "timing"), source_value(row, "admin_notes")]
    else:
        parts = []
    return " | ".join([part for part in parts if part])


def date_from_profile_start(start_date: object) -> dt.date:
    raw = _clean(start_date)
    try:
        return dt.date.fromisoformat(raw[:10])
    except Exception:
        return dt.date.today()


def day_date(profile: dict, day_number: int) -> dt.date:
    return date_from_profile_start(profile.get("start_date")) + dt.timedelta(days=max(0, day_number - 1))


def today_day_number(profile: dict, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    start = date_from_profile_start(profile.get("start_date"))
    delta_days = (today - start).days
    if delta_days < 0:
        return 1
    return (delta_days % 7) + 1


def day_label(profile: dict, day_number: int) -> str:
    date_value = day_date(profile, day_number)
    return f"Day {day_number} · {date_value.strftime('%a, %d %b')}"


def items_for_day(items: List[dict], day_number: int, item_type: str = "") -> List[dict]:
    rows = [row for row in active_items(items) if _safe_int(row.get("day_number")) == day_number]
    if item_type:
        rows = [row for row in rows if row.get("item_type") == item_type]
    return rows


def _section_count(items: List[dict], item_type: str, day: int | None = None) -> int:
    rows = active_items(items)
    if day is not None:
        rows = [row for row in rows if _safe_int(row.get("day_number")) == day]
    return len([row for row in rows if row.get("item_type") == item_type])


def _chip(label: str, value: object = "") -> str:
    label_text = _clean(label)
    value_text = _clean(value)
    if not label_text and not value_text:
        return ""
    if value_text:
        return f"<span class='hm-chip'><b>{_esc(label_text)}</b>{_esc(value_text)}</span>"
    return f"<span class='hm-chip'>{_esc(label_text)}</span>"


def _chips(values: List[Tuple[str, object] | str]) -> str:
    rendered = []
    for value in values:
        chip = _chip(value[0], value[1]) if isinstance(value, tuple) else _chip(str(value))
        if chip:
            rendered.append(chip)
    return "".join(rendered)


def _item_title(row: dict) -> str:
    fallback = {"meal": "Meal", "exercise": "Exercise", "supplement": "Supplement"}.get(row.get("item_type"), "Recommendation")
    return _clean(row.get("reference_label"), fallback)


def _item_chips(row: dict) -> List[Tuple[str, object] | str]:
    item_type = row.get("item_type")
    if item_type == "meal":
        return [("Slot", row.get("slot_name") or "As advised"), ("Portion", row.get("portion") or "As advised"), ("Type", source_value(row, "meal_type")), ("Diet", source_value(row, "diet_type")), ("Prep", source_value(row, "prep_time")), ("Calories", source_value(row, "calories"))]
    if item_type == "exercise":
        return [("Time", row.get("scheduled_time") or row.get("slot_name") or "As advised"), ("Difficulty", source_value(row, "difficulty") or row.get("intensity") or "As advised"), ("Duration/Reps", source_value(row, "duration_or_reps")), ("Equipment", source_value(row, "equipment")), ("Category", source_value(row, "category"))]
    if item_type == "supplement":
        frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
        timeline = parse_timeline(row.get("scheduled_time") or row.get("slot_name"))
        chips: List[Tuple[str, object] | str] = [("Frequency", frequency or "As advised"), ("Dosage", dosage or "As advised")]
        chips.extend([("Timeline", item) for item in timeline] or [("Timeline", "As advised")])
        chips.append(("Source Timing", source_value(row, "timing")))
        return chips
    return [("Timing", row.get("scheduled_time") or row.get("slot_name") or "As advised")]


def _render_item(row: dict, compact: bool = False) -> None:
    instruction = _clean(row.get("instruction"))
    source_context = source_context_text(row)
    image_ref = image_reference_text(row)
    body_parts = []
    if instruction:
        body_parts.append(f"<div class='hm-rec-line'><b>Instruction:</b> {_esc(instruction)}</div>")
    if source_context:
        body_parts.append(f"<div class='hm-rec-source'><b>Source context:</b> {_esc(source_context)}</div>")
    if image_ref and not compact:
        body_parts.append(f"<div class='hm-rec-image'><b>Image ref:</b> {_esc(image_ref)}</div>")
    st.markdown(f"""<div class='hm-rec-card {'compact' if compact else ''}'><div class='hm-rec-card-title'>{_esc(_item_title(row))}</div><div class='hm-chip-row'>{_chips(_item_chips(row))}</div>{''.join(body_parts)}</div>""", unsafe_allow_html=True)


def _render_section(title: str, rows: List[dict], empty: str, compact: bool = False) -> None:
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown(f"<div class='hm-rec-empty'>{_esc(empty)}</div>", unsafe_allow_html=True)
        return
    for row in rows:
        _render_item(row, compact=compact)


def _weekly_toggle(label: str, key: str, default_open: bool = False) -> bool:
    state_key = f"hm_weekly_toggle_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_open
    is_open = bool(st.session_state.get(state_key))
    prefix = "▾" if is_open else "▸"
    st.markdown("<div class='hm-weekly-toggle-anchor'></div>", unsafe_allow_html=True)
    if st.button(f"{prefix} {label}", key=f"{state_key}_btn", use_container_width=True):
        st.session_state[state_key] = not is_open
        st.rerun()
    return bool(st.session_state.get(state_key))


def _render_today(profile: dict, items: List[dict]) -> None:
    today_day = today_day_number(profile)
    st.markdown(f"<div class='hm-rec-day-label'>Today · {_esc(day_label(profile, today_day))}</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-rec-sub'>This is only today's slice from your weekly recommendation. It is not a separate plan.</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        _render_section("Meals", items_for_day(items, today_day, "meal"), "No meal recommendation for today.", compact=True)
    with c2:
        _render_section("Supplements", items_for_day(items, today_day, "supplement"), "No supplement recommendation for today.", compact=True)
    with c3:
        _render_section("Exercises", items_for_day(items, today_day, "exercise"), "No exercise recommendation for today.", compact=True)


def _render_weekly_type(profile: dict, items: List[dict], item_type: str, title: str, empty: str) -> None:
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    current_day = today_day_number(profile)
    for day in range(1, 8):
        rows = items_for_day(items, day, item_type)
        if _weekly_toggle(day_label(profile, day), f"{item_type}_{day}", default_open=(day == current_day)):
            st.markdown("<div class='hm-weekly-toggle-body'>", unsafe_allow_html=True)
            if not rows:
                st.caption(empty)
            for row in rows:
                _render_item(row)
            st.markdown("</div>", unsafe_allow_html=True)


def _guidance_items(profile: dict, items: List[dict], day: int | None = None) -> List[Tuple[str, str]]:
    values: List[Tuple[str, str]] = []
    for field in ("nutrition_guidance", "nutrition_guidance_note", "nutritionist_guidance", "nutritionist_note", "weekly_guidance", "profile_guidance", "profile_level_nutrition_note", "nutrition_note", "member_guidance", "guidance_note", "additional_guidance", "ancillary_guidance"):
        text = _clean(profile.get(field))
        if text:
            values.append(("Guidance", text))
    rows = active_items(items)
    if day is not None:
        rows = [row for row in rows if _safe_int(row.get("day_number")) == day]
    for row in rows:
        if _clean(row.get("item_type")).lower() not in {"guidance", "nutrition_guidance", "nutrition"}:
            continue
        label = _clean(row.get("reference_label"), "Guidance")
        text = _clean(row.get("instruction") or row.get("portion") or row.get("scheduled_time"))
        if text:
            values.append((label, text))
    seen = set()
    unique = []
    for label, value in values:
        marker = (label.lower(), value.lower())
        if marker not in seen:
            seen.add(marker)
            unique.append((label, value))
    return unique


def _render_guidance(profile: dict, items: List[dict], day: int | None = None, title: str = "Nutrition Guidance") -> None:
    values = _guidance_items(profile, items, day=day)
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    if not values:
        st.markdown("<div class='hm-rec-empty'>No Guidance shared.</div>", unsafe_allow_html=True)
        return
    chips = _chips([(label, value) for label, value in values[:24]])
    st.markdown(f"<div class='hm-guidance-box'><div class='hm-chip-row'>{chips}</div></div>", unsafe_allow_html=True)


def _render_weekly(profile: dict, items: List[dict]) -> None:
    meal_tab, supplement_tab, exercise_tab, guidance_tab = st.tabs(["Meals", "Supplements", "Exercises", "Nutrition Guidance"])
    with meal_tab:
        _render_weekly_type(profile, items, "meal", "Weekly Meal Recommendation", "No meals scheduled for this day.")
    with supplement_tab:
        _render_weekly_type(profile, items, "supplement", "Weekly Supplement Recommendation", "No supplements scheduled for this day.")
    with exercise_tab:
        _render_weekly_type(profile, items, "exercise", "Weekly Exercise Recommendation", "No exercises scheduled for this day.")
    with guidance_tab:
        _render_guidance(profile, items, day=None, title="Weekly Nutrition Guidance")


def _inject_styles() -> None:
    st.markdown("""
<style>
.hm-rec-day-label{color:#064E3B;font-size:1.02rem;font-weight:950;margin:.80rem 0 .45rem;}.hm-rec-sub{color:#475569;font-size:.86rem;font-weight:720;line-height:1.45;margin:.12rem 0;}.hm-rec-section-title{color:#72551A;font-size:.92rem;font-weight:950;margin:.70rem 0 .38rem;}.hm-rec-card{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.72rem .78rem;margin:.42rem 0;box-shadow:0 8px 18px rgba(15,23,42,.04);}.hm-rec-card.compact{min-height:9.5rem;}.hm-rec-card-title{color:#064E3B;font-size:.91rem;font-weight:950;margin-bottom:.18rem;}.hm-rec-line,.hm-rec-source,.hm-rec-image{color:#334155;font-size:.78rem;font-weight:720;line-height:1.38;margin:.18rem 0;}.hm-rec-source{color:#64748B;}.hm-rec-image{color:#72551A;word-break:break-word;}.hm-rec-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:14px;padding:.72rem;color:#64748B;font-size:.80rem;font-weight:740;line-height:1.4;}.hm-chip-row{display:flex;flex-wrap:wrap;gap:.30rem .34rem;margin:.20rem 0;}.hm-chip{display:inline-flex;align-items:center;gap:.28rem;border:1px solid #D9C28F;background:#FFF9EC;color:#334155;border-radius:999px;padding:.20rem .46rem;font-size:.72rem;font-weight:760;line-height:1.25;max-width:100%;}.hm-chip b{color:#064E3B;font-weight:950;margin-right:.10rem;}.hm-guidance-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.78rem .86rem;box-shadow:0 8px 18px rgba(15,23,42,.04);}.hm-weekly-toggle-anchor + div [data-testid="stButton"] > button,.hm-weekly-toggle-anchor + div .stButton > button{justify-content:center!important;text-align:center!important;min-height:3.0rem!important;background:#FFFFFF!important;border:1.45px solid #D8A84E!important;border-radius:16px!important;box-shadow:0 8px 18px rgba(15,23,42,.045)!important;color:#064E3B!important;font-weight:950!important;margin:.55rem 0 .34rem 0!important;padding:.64rem .86rem!important;}.hm-weekly-toggle-anchor + div [data-testid="stButton"] > button *,.hm-weekly-toggle-anchor + div .stButton > button *{color:#064E3B!important;font-size:.92rem!important;font-weight:950!important;line-height:1.22!important;white-space:normal!important;overflow-wrap:normal!important;word-break:normal!important;text-align:center!important;}.hm-weekly-toggle-body{border:1px solid #E7D8BE;background:#FFFDF8;border-radius:16px;padding:1rem .96rem;margin:.18rem 0 .75rem 0;}@media(max-width:850px){.hm-rec-card.compact{min-height:auto}.hm-rec-day-label{font-size:.96rem}}
</style>
""", unsafe_allow_html=True)


def _load_for_member() -> Tuple[bool, Dict[str, Any], List[dict], str]:
    member_id = _clean(st.session_state.get("user_id"))
    email = _clean(st.session_state.get("user_email") or st.session_state.get("oidc_email"))
    return load_active_recommendation_profile(member_id, email)


def _render_refresh() -> None:
    return None


def render_today_journey_view() -> None:
    _inject_styles()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        st.markdown("<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>", unsafe_allow_html=True)
        return
    _render_today(profile, items)


def render_weekly_recommendation_view() -> None:
    _inject_styles()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        st.markdown("<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>", unsafe_allow_html=True)
        return
    _render_weekly(profile, items)
