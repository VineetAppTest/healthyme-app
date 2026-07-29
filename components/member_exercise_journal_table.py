from __future__ import annotations

import datetime as dt
import html
import re
from typing import Any, Dict, Iterable, List

import streamlit as st

from components.flash import set_system_message
from components.member_exercise_journal import (
    LOG_TABLE,
    STATUS_OPTIONS,
    _client,
    list_member_exercise_logs,
    save_member_exercise_log,
)
from components.member_recommendation_display import (
    build_member_recommendation_contract,
    load_active_recommendation_profile,
    today_day_number,
)
from components.profile_builder_source_contract import exercise_snapshot
from components.recommendation_contract import list_repository_items


STANDARD_TIMING_OPTIONS = ("Morning", "Afternoon", "Evening", "Night")
MAX_EXERCISE_ROWS = 9


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


def _display_time(value: object) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return _clean(value)
    return parsed.strftime("%I:%M %p").lstrip("0")


def _completion_time_value(value: object) -> str | None:
    raw = _clean(value)
    if not raw:
        return None
    parsed = _parse_time(raw)
    if parsed is None:
        raise ValueError("Completion time must use HH:MM or HH:MM AM/PM format.")
    return parsed.strftime("%H:%M")


def _parse_date(value: object):
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    try:
        return dt.date.fromisoformat(_clean(value)[:10])
    except Exception:
        return None


def _unique(values: Iterable[object]) -> List[str]:
    result, seen = [], set()
    for value in values:
        text = _clean(value)
        if text and text.lower() not in seen:
            result.append(text)
            seen.add(text.lower())
    return result


def _options(current: object, values: Iterable[object]) -> List[str]:
    return _unique([current, *list(values)]) or ["Not specified"]


def _slug(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", _clean(value).lower()).strip("_") or "value"


def _normalise_repository_row(row: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = exercise_snapshot(row)
    image = dict(snapshot.get("image") or {})
    return {
        "name": _clean(snapshot.get("title")),
        "difficulty": _clean(snapshot.get("difficulty")),
        "duration_or_reps": _clean(snapshot.get("duration_or_reps")),
        "equipment": _clean(snapshot.get("equipment")),
        "benefits": _clean(snapshot.get("benefits")),
        "instruction": _clean(snapshot.get("instructions")),
        "image_reference": " | ".join(
            _clean(image.get(field))
            for field in ("image_url", "image_bucket", "image_path")
            if _clean(image.get(field))
        ),
    }


def repository_activity_catalog() -> Dict[str, Dict[str, Any]]:
    try:
        rows = list_repository_items("exercises", active_only=True)
    except Exception:
        return {}
    catalog: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        item = _normalise_repository_row(dict(row or {}))
        if item["name"]:
            catalog[item["name"]] = item
    return catalog


def exercise_contract_for_date(
    member_id: str,
    email: str,
    selected_date: dt.date,
) -> Dict[str, Any]:
    ok, profile, items, message = load_active_recommendation_profile(member_id, email)
    if not ok or not profile:
        return {
            "ok": ok,
            "message": message,
            "profile": {},
            "day_number": 1,
            "day_label": selected_date.strftime("%a, %d %b %Y"),
            "exercises": [],
            "catalog": [],
        }
    contract = build_member_recommendation_contract(profile, items)
    day_number = int(today_day_number(profile, selected_date) or 1)
    day_row = next(
        (
            row
            for row in contract.get("days", [])
            if int(row.get("day_number") or 0) == day_number
        ),
        {},
    )
    all_exercises = [
        dict(item)
        for day in contract.get("days", [])
        for item in day.get("items", [])
        if item.get("type") == "exercise"
    ]
    return {
        "ok": True,
        "message": message,
        "profile": dict(contract.get("profile") or {}),
        "day_number": day_number,
        "day_label": f"Day {day_number} · {selected_date.strftime('%a, %d %b %Y')}",
        "exercises": [
            dict(item)
            for item in day_row.get("items", [])
            if item.get("type") == "exercise"
        ],
        "catalog": all_exercises,
    }


def list_saved_exercise_rows(member_id: str, limit: int = 900) -> List[dict]:
    try:
        response = (
            _client()
            .table(LOG_TABLE)
            .select("*")
            .eq("member_id", member_id)
            .order("log_date", desc=True)
            .order("item_order")
            .limit(limit)
            .execute()
        )
        return list(getattr(response, "data", None) or [])
    except Exception:
        return []


def saved_exercise_dates(rows: Iterable[dict]) -> List[dt.date]:
    values = {_parse_date(row.get("log_date")) for row in rows or []}
    return sorted((value for value in values if value), reverse=True)


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
        "completion_time": _completion_time_value(completion_time),
        "member_notes": _clean(remarks),
    }


def _inject_styles() -> None:
    st.markdown(
        """
<style id="hm-exercise-journal-table-v3">
.hm-exercise-row-number{
  color:#064E3B;font-size:.82rem;font-weight:900;margin:0 0 .3rem;
}
.hm-exercise-source-note{
  color:#48645A;font-size:.78rem;line-height:1.4;margin:.28rem 0 .15rem;
}
.hm-exercise-date-caption{
  color:#5E746B;font-size:.78rem;margin:.15rem 0 .55rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_saved_days(
    member_id: str,
    key_prefix: str,
    date_key: str,
    pending_key: str,
) -> None:
    today = dt.date.today()
    from_key, to_key = f"{key_prefix}_saved_from", f"{key_prefix}_saved_to"
    st.session_state.setdefault(from_key, today)
    st.session_state.setdefault(to_key, today)
    with st.container(border=True):
        st.markdown("### View Saved Days")
        from_col, to_col = st.columns(2)
        with from_col:
            filter_from = st.date_input("From", key=from_key)
        with to_col:
            filter_to = st.date_input("To", key=to_key)
        if filter_from > filter_to:
            st.warning("From date cannot be after To date.")
            return
        dates = [
            saved_date
            for saved_date in saved_exercise_dates(
                list_saved_exercise_rows(member_id)
            )
            if filter_from <= saved_date <= filter_to
        ]
        if not dates:
            st.caption("No saved exercise days found in this range.")
            return
        st.caption(f"Showing {len(dates)} saved exercise day(s) in the selected range.")
        for start in range(0, len(dates), 4):
            cols = st.columns(4)
            for col, saved_date in zip(cols, dates[start : start + 4]):
                with col:
                    if st.button(
                        saved_date.strftime("%d %b"),
                        key=f"{key_prefix}_load_{saved_date}",
                        use_container_width=True,
                    ):
                        st.session_state[pending_key] = saved_date
                        st.rerun()


def render_member_exercise_journal_table(
    member_id: str,
    member_email: str = "",
    *,
    heading: str = "Exercise Journal",
    key_prefix: str = "hm_member_exercise_table",
    show_build_note: bool = True,
) -> None:
    _inject_styles()
    if heading:
        st.markdown(f"### {_esc(heading)}")

    date_key, pending_key = f"{key_prefix}_date", f"{key_prefix}_pending_date"
    if pending_key in st.session_state:
        st.session_state[date_key] = st.session_state.pop(pending_key)
    st.session_state.setdefault(date_key, dt.date.today())
    with st.container(border=True):
        st.markdown("### Exercise Journal Date")
        selected_date = st.date_input(
            "Select the date for this exercise journal entry",
            key=date_key,
        )
    log_date = selected_date.isoformat()

    contract = exercise_contract_for_date(member_id, member_email, selected_date)
    if not contract.get("ok"):
        st.error(
            contract.get("message")
            or "Exercise recommendations could not be loaded."
        )
    profile = dict(contract.get("profile") or {})
    assigned = list(contract.get("exercises") or [])
    profile_items = list(contract.get("catalog") or [])
    existing_rows = list_member_exercise_logs(member_id, log_date)
    existing = {
        int(row.get("item_order") or idx): dict(row)
        for idx, row in enumerate(existing_rows, 1)
    }

    catalog = repository_activity_catalog()
    catalog.update(
        {
            _clean(item.get("name")): dict(item)
            for item in profile_items
            if _clean(item.get("name"))
        }
    )
    for row in existing_rows:
        name = _clean(row.get("exercise_name"))
        if name and name not in catalog:
            catalog[name] = dict(row)

    base_count = max(1, len(assigned), len(existing_rows))
    count_key = f"{key_prefix}_row_count_{log_date}"
    st.session_state.setdefault(count_key, base_count)
    row_count = max(
        base_count,
        min(MAX_EXERCISE_ROWS, int(st.session_state[count_key])),
    )
    st.session_state[count_key] = row_count

    if show_build_note:
        st.markdown(
            f"<div class='hm-exercise-date-caption'>{_esc(contract.get('day_label'))}</div>",
            unsafe_allow_html=True,
        )
    if not profile.get("id"):
        st.warning(
            "An active recommendation profile is required before a new Exercise "
            "Journal entry can be saved. Existing saved days remain viewable."
        )

    add_col, remove_col = st.columns(2)
    with add_col:
        if st.button(
            "+ Add exercise entry",
            key=f"{key_prefix}_add_{log_date}",
            disabled=row_count >= MAX_EXERCISE_ROWS,
            use_container_width=True,
        ):
            st.session_state[count_key] = min(MAX_EXERCISE_ROWS, row_count + 1)
            st.rerun()
    with remove_col:
        if st.button(
            "Remove last exercise entry",
            key=f"{key_prefix}_remove_{log_date}",
            disabled=row_count <= base_count,
            use_container_width=True,
        ):
            st.session_state[count_key] = max(base_count, row_count - 1)
            st.rerun()

    timings = _unique(
        [item.get("timing_or_slot") for item in profile_items]
        + [row.get("scheduled_time") for row in existing_rows]
        + list(STANDARD_TIMING_OPTIONS)
    )
    activities = list(catalog.keys())
    profile_id = _clean(profile.get("id")) or "profile"

    for index in range(1, row_count + 1):
        prescribed = dict(assigned[index - 1]) if index <= len(assigned) else {}
        prior = dict(existing.get(index) or {})
        item_order = int(
            prior.get("item_order") or prescribed.get("item_order") or index
        )
        current_activity = (
            _clean(prior.get("exercise_name"))
            or _clean(prescribed.get("name"))
            or "Select activity"
        )
        current_timing = (
            _clean(prior.get("scheduled_time"))
            or _clean(prescribed.get("timing_or_slot"))
            or "Morning"
        )
        widget = (
            f"{key_prefix}_{profile_id}_{contract.get('day_number')}_"
            f"{log_date}_{item_order}"
        )
        with st.container(border=True):
            st.markdown(
                f"<div class='hm-exercise-row-number'>Exercise {index}</div>",
                unsafe_allow_html=True,
            )
            timing_col, activity_col, duration_col, remarks_col = st.columns(
                [1, 1.65, 1.45, 2],
                gap="small",
            )
            with timing_col:
                selected_timing = st.selectbox(
                    "Timing",
                    _options(current_timing, timings),
                    key=f"{widget}_timing",
                )
            with activity_col:
                activity_options = _unique([current_activity, *activities])
                selected_activity = st.selectbox(
                    "Activity",
                    activity_options,
                    key=f"{widget}_activity",
                )
            definition = dict(
                catalog.get(selected_activity) or prescribed or prior
            )
            with duration_col:
                selected_duration = st.text_input(
                    "Duration / Sets",
                    value=(
                        _clean(prior.get("duration_or_reps"))
                        or _clean(definition.get("duration_or_reps"))
                    ),
                    key=f"{widget}_{_slug(selected_activity)}_duration",
                    placeholder="Example: 30 min / 2 sets of 10",
                )
            with remarks_col:
                remarks = st.text_input(
                    "Remarks",
                    value=_clean(prior.get("member_notes")),
                    key=f"{widget}_remarks",
                    placeholder="Optional remarks",
                )

            details = " · ".join(
                value
                for value in (
                    _clean(definition.get("difficulty")),
                    _clean(definition.get("equipment")),
                )
                if value
            )
            if details:
                st.markdown(
                    f"<div class='hm-exercise-source-note'>Repository details: "
                    f"{_esc(details)}</div>",
                    unsafe_allow_html=True,
                )

            status_col, time_col, save_col = st.columns(
                [1.1, 1.5, 1.35],
                gap="small",
            )
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
                    key=f"{widget}_status",
                )
            with time_col:
                completion_time = st.text_input(
                    "Completion time (optional)",
                    value=_display_time(prior.get("completion_time")),
                    key=f"{widget}_completion_time",
                    placeholder="Example: 10:30 PM",
                )
            with save_col:
                st.markdown(
                    "<div style='height:1.55rem'></div>",
                    unsafe_allow_html=True,
                )
                save_clicked = st.button(
                    "Save Exercise Entry",
                    key=f"{widget}_save",
                    use_container_width=True,
                    disabled=(
                        selected_activity == "Select activity"
                        or not bool(profile.get("id"))
                    ),
                )
            if save_clicked:
                try:
                    save_member_exercise_log(
                        build_exercise_log_payload(
                            member_id=member_id,
                            log_date=log_date,
                            profile=profile,
                            day_number=int(contract.get("day_number") or 1),
                            item_order=item_order,
                            selected_activity=selected_activity,
                            selected_timing=selected_timing,
                            selected_duration=selected_duration,
                            remarks=remarks,
                            status=status,
                            completion_time=completion_time,
                            selected_definition=definition,
                        )
                    )
                    set_system_message(
                        "Exercise Journal entry saved for "
                        f"{selected_activity} on "
                        f"{selected_date.strftime('%d %b %Y')}.",
                        "success",
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Exercise Journal entry could not be saved: {exc}")

    _render_saved_days(member_id, key_prefix, date_key, pending_key)
