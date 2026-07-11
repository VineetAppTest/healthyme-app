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
SOURCE_COLUMNS = [
    "source_type",
    "source_id",
    "source_label",
    "source_snapshot",
    "source_image_url",
    "source_image_bucket",
    "source_image_path",
    "source_image_access_type",
]
ITEM_SELECT_WITH_SOURCE = ITEM_SELECT_LEGACY + "," + ",".join(SOURCE_COLUMNS)


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


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
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
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
        return int(match.group(1) or 0), _clean(match.group(2))
    return 0, raw


def parse_timeline(value: object) -> List[str]:
    raw = _clean(value)
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


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
    profile_values = {
        _clean(profile.get("assigned_member_id")),
        _clean(profile.get("assigned_member_id")).lower(),
        _clean(profile.get("assigned_member_label")),
        _clean(profile.get("assigned_member_label")).lower(),
    }
    for token in tokens:
        if token in profile_values:
            return True
        if token.lower() and token.lower() in _clean(profile.get("assigned_member_label")).lower():
            return True
    return False


@st.cache_data(ttl=90, show_spinner=False)
def load_active_recommendation_profile(member_id: str, email: str = "") -> Tuple[bool, Dict[str, Any], List[dict], str]:
    """Load the one active recommendation profile visible to the logged-in member."""
    try:
        c = _client()
        profile_result = (
            c.table(PROFILE_TABLE)
            .select("*")
            .eq("status", "active")
            .order("updated_at", desc=True)
            .limit(150)
            .execute()
        )
        profiles = [p for p in _rows(profile_result) if _profile_matches_member(p, member_id, email)]
        if not profiles:
            return True, {}, [], "No active recommendation profile found for this member."
        profile = profiles[0]
        try:
            item_result = (
                c.table(ITEM_TABLE)
                .select(ITEM_SELECT_WITH_SOURCE)
                .eq("profile_id", profile.get("id"))
                .order("day_number")
                .order("item_type")
                .order("item_order")
                .execute()
            )
            return True, profile, _rows(item_result), "Loaded active recommendation with source-backed fields."
        except Exception:
            item_result = (
                c.table(ITEM_TABLE)
                .select(ITEM_SELECT_LEGACY)
                .eq("profile_id", profile.get("id"))
                .order("day_number")
                .order("item_type")
                .order("item_order")
                .execute()
            )
            return True, profile, _rows(item_result), "Loaded active recommendation using legacy item fields."
    except Exception as exc:
        return False, {}, [], f"Could not load member recommendation: {exc}"


def clear_member_recommendation_cache() -> None:
    load_active_recommendation_profile.clear()


def row_has_content(row: dict) -> bool:
    return any(_clean(row.get(field)) for field in ("reference_label", "portion", "instruction", "scheduled_time", "intensity", "dosage_frequency"))


def source_snapshot(row: dict) -> Dict[str, Any]:
    return _as_dict(row.get("source_snapshot"))


def source_original_snapshot(row: dict) -> Dict[str, Any]:
    snapshot = source_snapshot(row)
    original = _as_dict(snapshot.get("source_original_snapshot"))
    return original or snapshot


def source_overrides(row: dict) -> Dict[str, Any]:
    return _as_dict(source_snapshot(row).get("admin_source_overrides"))


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
    return f"Day {day_number} · {date_value.strftime('%a, %d %b %Y')}"


def active_items(items: List[dict]) -> List[dict]:
    return [row for row in items if row_has_content(row)]


def items_for_day(items: List[dict], day_number: int, item_type: str = "") -> List[dict]:
    rows = [row for row in active_items(items) if _safe_int(row.get("day_number")) == day_number]
    if item_type:
        rows = [row for row in rows if row.get("item_type") == item_type]
    return rows


def member_contract_item(row: dict) -> Dict[str, Any]:
    item_type = row.get("item_type")
    frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
    base = {
        "type": item_type,
        "day_number": _safe_int(row.get("day_number")),
        "slot_name": _clean(row.get("slot_name")),
        "item_order": _safe_int(row.get("item_order")),
        "name": _clean(row.get("reference_label")),
        "instruction": _clean(row.get("instruction")),
        "source_context": source_context_text(row),
        "image_reference": image_reference_text(row),
        "source": {
            "source_type": _clean(row.get("source_type")),
            "source_id": _clean(row.get("source_id")),
            "source_label": _clean(row.get("source_label") or row.get("reference_label")),
            "admin_source_overrides": source_overrides(row),
            "original_snapshot": source_original_snapshot(row),
        },
    }
    if item_type == "meal":
        base.update({"timing_or_slot": _clean(row.get("slot_name")), "portion": _clean(row.get("portion"))})
    elif item_type == "exercise":
        base.update({
            "timing_or_slot": _clean(row.get("scheduled_time") or row.get("slot_name")),
            "difficulty": source_value(row, "difficulty") or _clean(row.get("intensity")),
            "duration_or_reps": source_value(row, "duration_or_reps"),
            "equipment": source_value(row, "equipment"),
            "benefits": source_value(row, "benefits"),
        })
    elif item_type == "supplement":
        base.update({
            "timing_or_slot": _clean(row.get("scheduled_time") or row.get("slot_name")),
            "frequency": frequency,
            "dosage": dosage,
            "source_timing": source_value(row, "timing"),
            "admin_notes": source_value(row, "admin_notes"),
        })
    return base


def build_member_recommendation_contract(profile: dict, items: List[dict]) -> Dict[str, Any]:
    rows = active_items(items)
    today_day = today_day_number(profile)
    return {
        "profile": {
            "id": _clean(profile.get("id")),
            "profile_name": _clean(profile.get("profile_name")),
            "assigned_member_id": _clean(profile.get("assigned_member_id")),
            "assigned_member_label": _clean(profile.get("assigned_member_label")),
            "start_date": _clean(profile.get("start_date")),
            "cycle_rule": _clean(profile.get("cycle_rule"), "Weekly cyclical until replaced or stopped"),
            "profile_note": _clean(profile.get("profile_note")),
            "region": _clean(profile.get("region")),
            "age_band": _clean(profile.get("age_band")),
            "diet_type": _clean(profile.get("diet_type")),
            "health_concerns": profile.get("health_concerns") or [],
        },
        "today_day": today_day,
        "days": [
            {
                "day_number": day,
                "day_label": day_label(profile, day),
                "is_today": day == today_day,
                "items": [member_contract_item(row) for row in items_for_day(rows, day)],
            }
            for day in range(1, 8)
        ],
    }


def _item_display_fields(row: dict) -> Dict[str, str]:
    item_type = row.get("item_type")
    frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
    if item_type == "meal":
        return {
            "title": _clean(row.get("reference_label"), "Meal"),
            "timing": _clean(row.get("slot_name"), "As advised"),
            "primary": f"Portion: {_clean(row.get('portion'), 'As advised')}",
            "secondary": source_context_text(row),
        }
    if item_type == "exercise":
        difficulty = source_value(row, "difficulty") or _clean(row.get("intensity"), "As advised")
        duration = source_value(row, "duration_or_reps")
        meta = " · ".join([value for value in [difficulty, duration] if value])
        return {
            "title": _clean(row.get("reference_label"), "Exercise"),
            "timing": _clean(row.get("scheduled_time") or row.get("slot_name"), "As advised"),
            "primary": meta or "As advised",
            "secondary": source_context_text(row),
        }
    if item_type == "supplement":
        timeline = _clean(row.get("scheduled_time") or row.get("slot_name"), "As advised")
        freq_text = str(frequency) if frequency else "As advised"
        return {
            "title": _clean(row.get("reference_label"), "Supplement"),
            "timing": timeline,
            "primary": f"Frequency: {freq_text} · Dosage: {dosage or 'As advised'}",
            "secondary": source_context_text(row),
        }
    return {"title": _clean(row.get("reference_label"), "Recommendation"), "timing": "As advised", "primary": "", "secondary": ""}


def _render_item_card(row: dict) -> None:
    fields = _item_display_fields(row)
    instruction = _clean(row.get("instruction"))
    image_ref = image_reference_text(row)
    source_context = fields.get("secondary", "")
    source_html = f"<div class='hm-rec-source'>Source: {_esc(source_context)}</div>" if source_context else ""
    instruction_html = f"<div class='hm-rec-instruction'>Instruction: {_esc(instruction)}</div>" if instruction else ""
    image_html = f"<div class='hm-rec-image'>Image ref: {_esc(image_ref)}</div>" if image_ref else ""
    st.markdown(
        f"""
        <div class='hm-rec-item'>
          <div class='hm-rec-item-title'>{_esc(fields.get('title'))}</div>
          <div class='hm-rec-meta'>{_esc(fields.get('timing'))}</div>
          <div class='hm-rec-primary'>{_esc(fields.get('primary'))}</div>
          {instruction_html}
          {source_html}
          {image_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_section(title: str, rows: List[dict], empty: str) -> None:
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown(f"<div class='hm-rec-empty'>{_esc(empty)}</div>", unsafe_allow_html=True)
        return
    for row in rows:
        _render_item_card(row)


def _render_day(profile: dict, items: List[dict], day: int) -> None:
    meals = items_for_day(items, day, "meal")
    exercises = items_for_day(items, day, "exercise")
    supplements = items_for_day(items, day, "supplement")
    st.markdown(f"<div class='hm-rec-day-label'>{_esc(day_label(profile, day))}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        _render_section("Meals", meals, "No meal recommendation for this day.")
    with c2:
        _render_section("Exercises", exercises, "No exercise recommendation for this day.")
    with c3:
        _render_section("Supplements", supplements, "No supplement recommendation for this day.")


def _render_summary(profile: dict, items: List[dict], today_day: int, message: str) -> None:
    rows = active_items(items)
    meal_count = len([row for row in rows if row.get("item_type") == "meal"])
    exercise_count = len([row for row in rows if row.get("item_type") == "exercise"])
    supplement_count = len([row for row in rows if row.get("item_type") == "supplement"])
    source_count = len([row for row in rows if source_snapshot(row)])
    st.markdown(
        f"""
        <div class='hm-rec-hero'>
          <div class='hm-rec-title'>{_esc(profile.get('profile_name') or 'My Recommendation')}</div>
          <div class='hm-rec-sub'>This is your active nutritionist-published recommendation. Recommendation shows all seven days; Today's Journey shows only today's calculated slice.</div>
          <div class='hm-rec-sub'><b>Start date:</b> {_esc(profile.get('start_date') or 'NA')} · <b>Today maps to:</b> Day {today_day} · <b>Cycle:</b> {_esc(profile.get('cycle_rule') or 'Weekly cyclical until replaced or stopped')}</div>
          <div class='hm-rec-sub'><b>Profile note:</b> {_esc(profile.get('profile_note') or 'NA')}</div>
          <div class='hm-rec-source'>{_esc(message)}</div>
        </div>
        <div class='hm-rec-count-grid'>
          <div class='hm-rec-count'><b>{meal_count}</b><span>Meal rows</span></div>
          <div class='hm-rec-count'><b>{exercise_count}</b><span>Exercise rows</span></div>
          <div class='hm-rec-count'><b>{supplement_count}</b><span>Supplement rows</span></div>
          <div class='hm-rec-count'><b>{source_count}/{len(rows)}</b><span>Source-backed rows</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inject_styles() -> None:
    st.markdown(
        """
<style>
.hm-rec-hero{border:1px solid #E3C98E;background:linear-gradient(135deg,#FFFDF8 0%,#FFF4DA 100%);border-radius:22px;padding:1rem 1.1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.55rem 0 .85rem;}
.hm-rec-title{color:#064E3B;font-size:1.25rem;font-weight:950;margin:0 0 .22rem;}
.hm-rec-sub{color:#475569;font-size:.86rem;font-weight:720;line-height:1.45;margin:.12rem 0;}
.hm-rec-count-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.65rem 0 1rem;}
.hm-rec-count{border:1px solid #E3C98E;background:#FFFDF8;border-radius:15px;padding:.70rem .80rem;box-shadow:0 5px 15px rgba(15,23,42,.035);}
.hm-rec-count b{display:block;color:#064E3B;font-size:1rem;font-weight:950;}.hm-rec-count span{color:#64748B;font-size:.76rem;font-weight:780;}
.hm-rec-day-label{color:#064E3B;font-size:1.02rem;font-weight:950;margin:.80rem 0 .45rem;}
.hm-rec-section-title{color:#72551A;font-size:.86rem;font-weight:950;margin:.15rem 0 .35rem;}
.hm-rec-item{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.72rem .78rem;margin:.42rem 0;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-rec-item-title{color:#064E3B;font-size:.90rem;font-weight:950;margin-bottom:.10rem;}
.hm-rec-meta,.hm-rec-primary,.hm-rec-instruction,.hm-rec-source,.hm-rec-image{color:#334155;font-size:.78rem;font-weight:720;line-height:1.38;margin:.10rem 0;}
.hm-rec-primary{color:#1F2937;font-weight:820;}.hm-rec-source{color:#64748B;}.hm-rec-image{color:#72551A;word-break:break-word;}
.hm-rec-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:14px;padding:.72rem;color:#64748B;font-size:.80rem;font-weight:740;line-height:1.4;}
@media(max-width:850px){.hm-rec-count-grid{grid-template-columns:1fr}.hm-rec-day-label{font-size:.96rem}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_member_recommendation_view(default_view: str = "today") -> None:
    _inject_styles()
    member_id = _clean(st.session_state.get("user_id"))
    email = _clean(st.session_state.get("user_email"))

    if st.button("Refresh Recommendation", use_container_width=True):
        clear_member_recommendation_cache()
        st.rerun()

    ok, profile, items, message = load_active_recommendation_profile(member_id, email)
    if not ok:
        st.error(message)
        return
    if not profile:
        st.markdown("<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>", unsafe_allow_html=True)
        return

    today_day = today_day_number(profile)
    _render_summary(profile, items, today_day, message)

    if default_view == "recommendation":
        full_tab, today_tab = st.tabs(["Full 7-Day Recommendation", "Today’s Journey"])
    else:
        today_tab, full_tab = st.tabs(["Today’s Journey", "Full 7-Day Recommendation"])

    with today_tab:
        st.markdown("<div class='hm-rec-sub'>Today’s Journey is the current day’s slice from the same active seven-day recommendation profile.</div>", unsafe_allow_html=True)
        _render_day(profile, items, today_day)

    with full_tab:
        st.markdown("<div class='hm-rec-sub'>Full Recommendation shows Day 1 to Day 7 from the active published profile.</div>", unsafe_allow_html=True)
        for day in range(1, 8):
            with st.expander(day_label(profile, day), expanded=(day == today_day)):
                _render_day(profile, items, day)
