from __future__ import annotations

import datetime as dt
import html
import re
from typing import Any, Dict, Iterable, List

import streamlit as st

from components.flash import set_system_message
from components.member_exercise_journal import (
    STATUS_OPTIONS,
    exercise_log_map,
    load_member_exercise_contract,
    save_member_exercise_log,
)


STANDARD_TIMING_OPTIONS = ("Morning", "Afternoon", "Evening", "Night")


def _clean(value: object, default: str = "") -> str:
    return default if value is None else str(value).strip()


def _esc(value: object) -> str:
    return html.escape(_clean(value))


def _parse_time(value: object):
    raw = _clean(value)
    if not raw:
        return None
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
        try:
            return dt.datetime.strptime(raw, fmt).time()
        except Exception:
            pass
    return None


def _slug(value: object) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", _clean(value).lower()).strip("_")
    return cleaned or "value"


def _unique(values: Iterable[object]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        text = _clean(value)
        if not text or text.lower() in seen:
            continue
        result.append(text)
        seen.add(text.lower())
    return result


def _options_with_current(current: object, values: Iterable[object]) -> List[str]:
    options = _unique([current, *list(values)])
    return options or ["Not specified"]


def build_exercise_log_payload(
    *,
    member_id: str,
    log_date: str,
    profile: Dict[str, Any],
    day_number: int,
    item_order: int,
    selected_activity: str,
    selected_timing: str,
    selected_duration: str,
    remarks: str,
    status: str,
    completion_time,
    selected_definition: Dict[str, Any],
) -> Dict[str, Any]:
    """Build one day-specific journal row without changing repository data."""

    return {
        "member_id": member_id,
        "log_date": log_date,
        "profile_id": profile.get("id"),
        "profile_name": profile.get("profile_name"),
        "day_number": day_number,
        "item_order": item_order,
        "exercise_name": _clean(selected_activity),
        "scheduled_time": _clean(selected_timing),
        "difficulty": selected_definition.get("difficulty"),
        "duration_or_reps": _clean(selected_duration),
        "equipment": selected_definition.get("equipment"),
        "benefits": selected_definition.get("benefits"),
        "instruction": selected_definition.get("instruction"),
        "image_reference": selected_definition.get("image_reference"),
        "status": status if status in STATUS_OPTIONS else "Not Started",
        "completion_time": (
            completion_time.strftime("%H:%M") if completion_time else None
        ),
        "member_notes": _clean(remarks),
    }


def _inject_table_styles() -> None:
    st.markdown(
        """
<style id="hm-exercise-journal-table-v1">
.hm-exercise-journal-note{
  border:1px solid #E3C98E;background:#FFF7E6;color:#72551A;
  border-radius:14px;padding:.68rem .82rem;margin:.35rem 0 .8rem;
  font-size:.84rem;font-weight:680;
}
.hm-exercise-table-head{
  display:grid;grid-template-columns:1fr 1.65fr 1.45fr 2fr;gap:.6rem;
  padding:.58rem .72rem;border:1px solid #D7C28D;border-radius:12px 12px 0 0;
  background:#E5E7EB;color:#1F2937;font-size:.82rem;font-weight:900;
}
.hm-exercise-row-shell{
  border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:16px;padding:.72rem .78rem;margin:.55rem 0 .78rem;
  box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.hm-exercise-row-number{color:#064E3B;font-size:.78rem;font-weight:900;margin:0 0 .3rem;}
.hm-exercise-source-note{color:#64748B;font-size:.76rem;line-height:1.35;margin:.25rem 0 .2rem;}
.hm-exercise-progress{
  border:1px solid #D8C18B;background:#FFF7E6;border-radius:14px;
  padding:.7rem .8rem;margin:.5rem 0 1rem;color:#7A5A16;font-weight:850;
}
@media(max-width:760px){
  .hm-exercise-table-head{display:none;}
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_member_exercise_journal_table(
    member_id: str,
    member_email: str = "",
    *,
    heading: str = "Exercise Journal",
    key_prefix: str = "hm_member_exercise_table",
    show_build_note: bool = True,
) -> None:
    """Render repository-backed exercise rows in an editable journal format."""

    _inject_table_styles()
    if heading:
        st.markdown(f"### {_esc(heading)}")

    contract = load_member_exercise_contract(member_id, member_email)
    if not contract.get("ok"):
        st.error(
            contract.get("message")
            or "Exercise recommendations could not be loaded."
        )
        return

    exercises = list(contract.get("exercises") or [])
    profile = dict(contract.get("profile") or {})
    log_date = dt.date.today().isoformat()
    existing_logs = exercise_log_map(member_id, log_date)
    completed_count = sum(
        1 for row in existing_logs.values() if row.get("status") == "Completed"
    )

    if show_build_note:
        st.caption(f"Editable Exercise Journal · {contract.get('day_label', '')}")

    st.markdown(
        "<div class='hm-exercise-journal-note'>"
        "Timing and Activity are pulled from the active recommendation and remain selectable. "
        "Duration / Sets and Remarks are editable. Changes are saved only in today's journal and do not alter the recommendation profile or Exercise Repository."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='hm-exercise-progress'>"
            f"Today's progress: {completed_count} of {len(exercises)} exercise(s) completed"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    if not exercises:
        st.info(
            "No exercise has been assigned for today in the active recommendation profile."
        )
        return

    activity_catalog = {
        _clean(exercise.get("name")) or f"Exercise {index}": dict(exercise)
        for index, exercise in enumerate(exercises, start=1)
    }
    activity_values = list(activity_catalog.keys())
    timing_values = _unique(
        [exercise.get("timing_or_slot") for exercise in exercises]
        + list(STANDARD_TIMING_OPTIONS)
    )

    st.markdown(
        "<div class='hm-exercise-table-head'>"
        "<div>Timing</div><div>Activity</div><div>Duration / Sets</div><div>Remarks</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    profile_id = _clean(profile.get("id")) or "profile"
    for index, prescribed_exercise in enumerate(exercises, start=1):
        item_order = int(prescribed_exercise.get("item_order") or index)
        prior = dict(existing_logs.get(item_order) or {})
        prescribed_name = _clean(prescribed_exercise.get("name")) or f"Exercise {index}"
        current_activity = _clean(prior.get("exercise_name")) or prescribed_name
        current_timing = (
            _clean(prior.get("scheduled_time"))
            or _clean(prescribed_exercise.get("timing_or_slot"))
            or "Morning"
        )
        widget_key = f"{key_prefix}_{profile_id}_{contract.get('today_day')}_{item_order}"

        with st.container(border=True):
            st.markdown(
                f"<div class='hm-exercise-row-number'>Exercise {index}</div>",
                unsafe_allow_html=True,
            )
            timing_col, activity_col, duration_col, remarks_col = st.columns(
                [1.0, 1.65, 1.45, 2.0], gap="small"
            )
            with timing_col:
                timing_options = _options_with_current(current_timing, timing_values)
                selected_timing = st.selectbox(
                    "Timing",
                    timing_options,
                    index=0,
                    key=f"{widget_key}_timing",
                )
            with activity_col:
                activity_options = _options_with_current(
                    current_activity, activity_values
                )
                selected_activity = st.selectbox(
                    "Activity",
                    activity_options,
                    index=0,
                    key=f"{widget_key}_activity",
                )
            selected_definition = dict(
                activity_catalog.get(selected_activity) or prescribed_exercise
            )
            with duration_col:
                duration_default = (
                    _clean(prior.get("duration_or_reps"))
                    or _clean(selected_definition.get("duration_or_reps"))
                )
                selected_duration = st.text_input(
                    "Duration / Sets",
                    value=duration_default,
                    key=f"{widget_key}_{_slug(selected_activity)}_duration",
                    placeholder="Example: 30 min / 2 sets of 10",
                )
            with remarks_col:
                remarks = st.text_input(
                    "Remarks",
                    value=_clean(prior.get("member_notes")),
                    key=f"{widget_key}_remarks",
                    placeholder="Optional remarks",
                )

            source_bits = [
                _clean(selected_definition.get("difficulty")),
                _clean(selected_definition.get("equipment")),
            ]
            source_text = " · ".join(value for value in source_bits if value)
            if source_text:
                st.markdown(
                    f"<div class='hm-exercise-source-note'>Repository details: {_esc(source_text)}</div>",
                    unsafe_allow_html=True,
                )

            status_col, time_col, save_col = st.columns([1.1, 1.1, 1.35], gap="small")
            with status_col:
                prior_status = (
                    prior.get("status")
                    if prior.get("status") in STATUS_OPTIONS
                    else "Not Started"
                )
                status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(prior_status),
                    key=f"{widget_key}_status",
                )
            with time_col:
                completion_time = st.time_input(
                    "Completion time",
                    value=_parse_time(prior.get("completion_time")),
                    key=f"{widget_key}_completion_time",
                )
            with save_col:
                st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
                save_clicked = st.button(
                    "Save Exercise Entry",
                    key=f"{widget_key}_save",
                    use_container_width=True,
                )

            if save_clicked:
                try:
                    payload = build_exercise_log_payload(
                        member_id=member_id,
                        log_date=log_date,
                        profile=profile,
                        day_number=int(contract.get("today_day") or 1),
                        item_order=item_order,
                        selected_activity=selected_activity,
                        selected_timing=selected_timing,
                        selected_duration=selected_duration,
                        remarks=remarks,
                        status=status,
                        completion_time=completion_time,
                        selected_definition=selected_definition,
                    )
                    save_member_exercise_log(payload)
                    set_system_message(
                        f"Exercise Journal entry saved for {selected_activity}.",
                        "success",
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Exercise Journal entry could not be saved: {exc}")
