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
    load_member_exercise_contract,
    save_member_exercise_log,
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
        "source_id": _clean(
            row.get("source_id")
            or row.get("id")
            or snapshot.get("source_id")
        ),
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
    """Return Exercise assignments from independent allocation authority."""

    contract = load_member_exercise_contract(
        member_id,
        email,
        selected_date=selected_date,
    )
    exercises = [dict(item) for item in contract.get("exercises", [])]
    return {
        "ok": bool(contract.get("ok")),
        "message": contract.get("message", ""),
        "day_label": selected_date.strftime("%a, %d %b %Y"),
        "exercises": exercises,
        "catalog": exercises,
        "authority": contract.get("authority") or "member_exercise_allocations",
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
    item_order: int,
    selected_activity: str,
    selected_timing: str,
    selected_duration: str,
    remarks: str,
    status: str,
    completion_time,
    selected_definition: Dict[str, Any],
    allocation_id: str = "",
    journal_entry_key: str = "",
    profile: Dict[str, Any] | None = None,
    day_number: int | None = None,
) -> Dict[str, Any]:
    """Build a journal row without mutating its prescription authority.

    Allocation-linked rows retain `allocation_id` even when the member records a
    different actual Activity. Manual actual rows use `journal_entry_key`. The
    optional profile/day parameters are only for retained legacy history.
    """

    payload: Dict[str, Any] = {
        "member_id": member_id,
        "log_date": log_date,
        "item_order": item_order,
        "exercise_name": _clean(selected_activity),
        "source_id": _clean(
            selected_definition.get("source_id")
            or selected_definition.get("exercise_id")
        ),
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
    if _clean(allocation_id):
        payload["allocation_id"] = _clean(allocation_id)
    elif _clean(journal_entry_key):
        payload["journal_entry_key"] = _clean(journal_entry_key)
    elif _clean((profile or {}).get("id")):
        payload.update(
            {
                "profile_id": (profile or {}).get("id"),
                "profile_name": (profile or {}).get("profile_name"),
                "day_number": day_number,
            }
        )
    else:
        raise ValueError("Exercise Journal row identity is required.")
    return payload


def _existing_allocation_map(rows: Iterable[dict]) -> Dict[str, dict]:
    return {
        _clean(row.get("allocation_id")): dict(row)
        for row in rows or []
        if _clean(row.get("allocation_id"))
    }


def base_exercise_journal_rows(
    assigned: Iterable[dict],
    existing_rows: Iterable[dict],
) -> List[dict]:
    """Build rows without matching legacy history to allocations by name/order."""

    assigned_rows = [dict(row or {}) for row in assigned or []]
    saved_rows = [dict(row or {}) for row in existing_rows or []]
    by_allocation = _existing_allocation_map(saved_rows)
    consumed_ids: set[str] = set()
    rows: List[dict] = []

    for index, prescribed in enumerate(assigned_rows, start=1):
        allocation_id = _clean(prescribed.get("allocation_id"))
        prior = dict(by_allocation.get(allocation_id) or {})
        if prior.get("id"):
            consumed_ids.add(_clean(prior.get("id")))
        rows.append(
            {
                "prescribed": prescribed,
                "prior": prior,
                "allocation_id": allocation_id,
                "journal_entry_key": "",
                "legacy_profile": {},
                "legacy_day_number": None,
                "item_order": int(prior.get("item_order") or index),
            }
        )

    for prior in saved_rows:
        row_id = _clean(prior.get("id"))
        if row_id and row_id in consumed_ids:
            continue
        if _clean(prior.get("allocation_id")) and any(
            _clean(row.get("allocation_id")) == _clean(prior.get("allocation_id"))
            for row in rows
        ):
            continue
        legacy_profile = {}
        legacy_day_number = None
        journal_entry_key = _clean(prior.get("journal_entry_key"))
        if not _clean(prior.get("allocation_id")) and not journal_entry_key:
            if _clean(prior.get("profile_id")):
                legacy_profile = {
                    "id": prior.get("profile_id"),
                    "profile_name": prior.get("profile_name"),
                }
                legacy_day_number = prior.get("day_number")
            else:
                journal_entry_key = f"manual:existing:{row_id or len(rows) + 1}"
        rows.append(
            {
                "prescribed": {},
                "prior": prior,
                "allocation_id": _clean(prior.get("allocation_id")),
                "journal_entry_key": journal_entry_key,
                "legacy_profile": legacy_profile,
                "legacy_day_number": legacy_day_number,
                "item_order": int(prior.get("item_order") or len(rows) + 1),
            }
        )

    if not rows:
        rows.append(
            {
                "prescribed": {},
                "prior": {},
                "allocation_id": "",
                "journal_entry_key": "manual:1",
                "legacy_profile": {},
                "legacy_day_number": None,
                "item_order": 1,
            }
        )
    return rows


def extend_exercise_journal_rows(rows: List[dict], row_count: int) -> List[dict]:
    output = [dict(row) for row in rows]
    while len(output) < row_count:
        slot = len(output) + 1
        output.append(
            {
                "prescribed": {},
                "prior": {},
                "allocation_id": "",
                "journal_entry_key": f"manual:{slot}",
                "legacy_profile": {},
                "legacy_day_number": None,
                "item_order": slot,
            }
        )
    return output[:row_count]


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


def _definition_for_row(
    descriptor: dict,
    catalog: Dict[str, Dict[str, Any]],
    index: int,
) -> tuple[dict, dict, str, str]:
    prescribed = dict(descriptor.get("prescribed") or {})
    prior = dict(descriptor.get("prior") or {})
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
    definition = dict(catalog.get(current_activity) or prescribed or prior)
    return prescribed, prior, current_activity, current_timing


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
        st.error(contract.get("message") or "Exercise allocations could not be loaded.")
    assigned = list(contract.get("exercises") or [])
    existing_rows = list_member_exercise_logs(member_id, log_date)

    catalog = repository_activity_catalog()
    for item in assigned:
        name = _clean(item.get("name"))
        if name:
            catalog[name] = dict(item)
    for row in existing_rows:
        name = _clean(row.get("exercise_name"))
        if name and name not in catalog:
            catalog[name] = dict(row)

    base_rows = base_exercise_journal_rows(assigned, existing_rows)
    base_count = len(base_rows)
    count_key = f"{key_prefix}_row_count_{log_date}"
    st.session_state.setdefault(count_key, base_count)
    row_count = max(
        base_count,
        min(MAX_EXERCISE_ROWS, int(st.session_state[count_key])),
    )
    st.session_state[count_key] = row_count
    rows = extend_exercise_journal_rows(base_rows, row_count)

    if show_build_note:
        st.markdown(
            f"<div class='hm-exercise-date-caption'>{_esc(contract.get('day_label'))}</div>",
            unsafe_allow_html=True,
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
        [row.get("scheduled_time") for row in existing_rows]
        + list(STANDARD_TIMING_OPTIONS)
    )
    activities = list(catalog.keys())

    for index, descriptor in enumerate(rows, start=1):
        prescribed = dict(descriptor.get("prescribed") or {})
        prior = dict(descriptor.get("prior") or {})
        item_order = int(descriptor.get("item_order") or index)
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
        identity = (
            _clean(descriptor.get("allocation_id"))
            or _clean(descriptor.get("journal_entry_key"))
            or _clean((descriptor.get("legacy_profile") or {}).get("id"))
            or str(index)
        )
        widget = f"{key_prefix}_{_slug(identity)}_{log_date}_{item_order}"

        with st.container(border=True):
            st.markdown(
                f"<div class='hm-exercise-row-number'>Exercise {index}</div>",
                unsafe_allow_html=True,
            )
            timing_col, activity_col, duration_col, remarks_col = st.columns(
                [1, 1.65, 1.45, 2], gap="small"
            )
            with timing_col:
                selected_timing = st.selectbox(
                    "Timing", _options(current_timing, timings), key=f"{widget}_timing"
                )
            with activity_col:
                selected_activity = st.selectbox(
                    "Activity",
                    _unique([current_activity, *activities]),
                    key=f"{widget}_activity",
                )
            definition = dict(catalog.get(selected_activity) or prescribed or prior)
            with duration_col:
                selected_duration = st.text_input(
                    "Duration / Sets",
                    value=(
                        _clean(prior.get("duration_or_reps"))
                        or _clean(prescribed.get("duration_or_reps"))
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

            status_col, time_col, save_col = st.columns([1.1, 1.5, 1.35], gap="small")
            with status_col:
                prior_status = prior.get("status") if prior.get("status") in STATUS_OPTIONS else "Not Started"
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
                st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
                save_clicked = st.button(
                    "Save Exercise Entry",
                    key=f"{widget}_save",
                    use_container_width=True,
                    disabled=(selected_activity == "Select activity"),
                )
            if save_clicked:
                try:
                    save_member_exercise_log(
                        build_exercise_log_payload(
                            member_id=member_id,
                            log_date=log_date,
                            item_order=item_order,
                            selected_activity=selected_activity,
                            selected_timing=selected_timing,
                            selected_duration=selected_duration,
                            remarks=remarks,
                            status=status,
                            completion_time=completion_time,
                            selected_definition=definition,
                            allocation_id=_clean(descriptor.get("allocation_id")),
                            journal_entry_key=_clean(descriptor.get("journal_entry_key")),
                            profile=dict(descriptor.get("legacy_profile") or {}),
                            day_number=descriptor.get("legacy_day_number"),
                        )
                    )
                    set_system_message(
                        f"Exercise Journal entry saved for {selected_activity} on "
                        f"{selected_date.strftime('%d %b %Y')}.",
                        "success",
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Exercise Journal entry could not be saved: {exc}")

    _render_saved_days(member_id, key_prefix, date_key, pending_key)
