from __future__ import annotations

import datetime as dt
import html
import os
from typing import Any, Dict, List

import streamlit as st

from components.exercise_member_allocation import (
    list_member_exercise_allocations_for_date,
)
from components.flash import set_system_message

LOG_TABLE = "hm_member_exercise_logs"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
BUILD_NOTE = "v102.6P0 · Allocation-linked Member Exercise Journal"
STATUS_OPTIONS = ["Not Started", "In Progress", "Completed", "Skipped"]


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
            value = section_values.get(name) or section_values.get(lower_name)
            if value is not None:
                return _clean(value, default)
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


def _allocation_definition(row: dict[str, Any], index: int) -> dict[str, Any]:
    snapshot = dict(row.get("source_snapshot") or {})
    allocation_id = _clean(row.get("id"))
    source_id = _clean(row.get("source_id") or row.get("exercise_id"))
    return {
        "allocation_id": allocation_id,
        "source_id": source_id,
        "name": (
            _clean(row.get("exercise_name"))
            or _clean(row.get("title"))
            or _clean(snapshot.get("title"))
            or f"Exercise {index}"
        ),
        "timing_or_slot": "",
        "difficulty": _clean(snapshot.get("difficulty")),
        "duration_or_reps": (
            _clean(row.get("duration_or_reps"))
            or _clean(snapshot.get("duration_or_reps"))
        ),
        "equipment": _clean(snapshot.get("equipment")),
        "benefits": _clean(snapshot.get("benefits")),
        "instruction": (
            _clean(row.get("instructions"))
            or _clean(snapshot.get("instructions"))
        ),
        "image_reference": _clean(snapshot.get("image_url")),
        "source_context": "Exercise allocation",
        "start_date": _clean(row.get("start_date")),
        "end_date": _clean(row.get("end_date")),
        "item_order": index,
    }


def load_member_exercise_contract(
    member_id: str,
    email: str = "",
    *,
    selected_date: dt.date | None = None,
) -> Dict[str, Any]:
    """Load prescribed Exercise rows from independent Exercise allocations."""

    target = selected_date or dt.date.today()
    try:
        allocations = list_member_exercise_allocations_for_date(member_id, target)
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Exercise allocations could not be loaded: {exc}",
            "profile": {},
            "today_day": None,
            "day_label": target.strftime("%a, %d %b %Y"),
            "exercises": [],
            "authority": "member_exercise_allocations",
        }
    exercises = [
        _allocation_definition(row, index)
        for index, row in enumerate(allocations, start=1)
    ]
    return {
        "ok": True,
        "message": "Loaded independent Exercise allocations.",
        "profile": {},
        "today_day": None,
        "day_label": target.strftime("%a, %d %b %Y"),
        "exercises": exercises,
        "authority": "member_exercise_allocations",
    }


def list_member_exercise_logs(member_id: str, log_date: str) -> List[dict]:
    try:
        response = (
            _client()
            .table(LOG_TABLE)
            .select("*")
            .eq("member_id", member_id)
            .eq("log_date", log_date)
            .order("item_order")
            .execute()
        )
        return _rows(response)
    except Exception:
        return []


def save_member_exercise_log(payload: Dict[str, Any]) -> None:
    """Save v2 allocation/manual rows while retaining legacy profile rows."""

    row = dict(payload)
    allocation_id = _clean(row.get("allocation_id"))
    journal_entry_key = _clean(row.get("journal_entry_key"))
    common_required = ("member_id", "log_date", "exercise_name")
    missing = [
        field
        for field in common_required
        if not _clean(row.get(field)) and row.get(field) != 0
    ]

    if allocation_id:
        if not _clean(row.get("source_id")):
            missing.append("source_id")
        conflict = "member_id,log_date,allocation_id"
        row.setdefault("item_order", 0)
        row["journal_entry_key"] = None
        row["profile_id"] = None
        row["profile_name"] = None
        row["day_number"] = None
    elif journal_entry_key:
        if not _clean(row.get("source_id")):
            missing.append("source_id")
        conflict = "member_id,log_date,journal_entry_key"
        row.setdefault("item_order", 0)
        row["allocation_id"] = None
        row["profile_id"] = None
        row["profile_name"] = None
        row["day_number"] = None
    else:
        legacy_required = ("profile_id", "day_number", "item_order")
        missing.extend(
            field
            for field in legacy_required
            if not _clean(row.get(field)) and row.get(field) != 0
        )
        conflict = "member_id,log_date,profile_id,day_number,item_order"

    if missing:
        raise ValueError(
            f"Missing exercise log fields: {', '.join(dict.fromkeys(missing))}"
        )

    row["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (
        _client()
        .table(LOG_TABLE)
        .upsert(row, on_conflict=conflict)
        .execute()
    )


def exercise_log_map(member_id: str, log_date: str) -> Dict[int, dict]:
    """Legacy item-order map retained for historical compatibility."""
    return {
        int(row.get("item_order") or 0): row
        for row in list_member_exercise_logs(member_id, log_date)
    }


def allocation_exercise_log_map(member_id: str, log_date: str) -> Dict[str, dict]:
    return {
        _clean(row.get("allocation_id")): row
        for row in list_member_exercise_logs(member_id, log_date)
        if _clean(row.get("allocation_id"))
    }


def _inject_exercise_styles() -> None:
    st.markdown(
        """
<style>
.hm-exercise-card{
  border:1px solid #E3D4BA;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:18px;
  padding:.9rem 1rem;
  margin:.65rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.hm-exercise-title{
  color:#064E3B;
  font-size:1.05rem;
  font-weight:950;
  margin-bottom:.35rem;
}
.hm-exercise-meta{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.45rem;
  margin:.35rem 0 .65rem 0;
}
.hm-exercise-meta div{
  border:1px solid #E8DDC7;
  border-radius:12px;
  background:#FFFFFF;
  padding:.48rem .58rem;
  color:#334155;
  font-size:.82rem;
}
.hm-exercise-meta b{
  display:block;
  color:#064E3B;
  font-size:.73rem;
  text-transform:uppercase;
  letter-spacing:.02em;
  margin-bottom:.12rem;
}
.hm-exercise-copy{
  color:#334155;
  font-size:.88rem;
  line-height:1.45;
  margin:.35rem 0;
}
.hm-exercise-progress{
  border:1px solid #D8C18B;
  background:#FFF7E6;
  border-radius:14px;
  padding:.7rem .8rem;
  margin:.5rem 0 1rem 0;
  color:#7A5A16;
  font-weight:850;
}
@media(max-width:760px){
  .hm-exercise-meta{grid-template-columns:1fr;}
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_member_exercise_journal(
    member_id: str,
    member_email: str = "",
    *,
    heading: str = "Exercise Journal",
    key_prefix: str = "hm_member_exercise",
    show_build_note: bool = True,
) -> None:
    """Render prescribed allocations with member progress controls."""

    _inject_exercise_styles()
    if heading:
        st.markdown(f"### {_esc(heading)}")

    contract = load_member_exercise_contract(member_id, member_email)
    if not contract.get("ok"):
        st.error(contract.get("message") or "Exercise allocations could not be loaded.")
        return

    exercises = contract.get("exercises", [])
    log_date = dt.date.today().isoformat()
    existing_logs = allocation_exercise_log_map(member_id, log_date)
    completed_count = sum(
        1 for row in existing_logs.values() if row.get("status") == "Completed"
    )

    if show_build_note:
        st.caption(f"{BUILD_NOTE} · {contract.get('day_label', '')}")

    st.markdown(
        (
            "<div class='hm-exercise-progress'>"
            f"Today's progress: {completed_count} of {len(exercises)} "
            "exercise(s) completed"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    if not exercises:
        st.info("No Exercise allocation applies for today.")
        return

    for index, exercise in enumerate(exercises, start=1):
        allocation_id = _clean(exercise.get("allocation_id"))
        prior = existing_logs.get(allocation_id, {})
        name = _clean(exercise.get("name")) or f"Exercise {index}"
        widget_key = f"{key_prefix}_{allocation_id or index}"

        st.markdown(
            f"""
            <div class='hm-exercise-card'>
              <div class='hm-exercise-title'>{_esc(name)}</div>
              <div class='hm-exercise-meta'>
                <div><b>Difficulty</b>{_esc(exercise.get('difficulty') or '-')}</div>
                <div><b>Duration / Repetitions</b>{_esc(exercise.get('duration_or_reps') or '-')}</div>
                <div><b>Equipment</b>{_esc(exercise.get('equipment') or '-')}</div>
              </div>
              <div class='hm-exercise-copy'><b>Benefits:</b> {_esc(exercise.get('benefits') or '-')}</div>
              <div class='hm-exercise-copy'><b>Instructions:</b> {_esc(exercise.get('instruction') or '-')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        status_col, time_col = st.columns(2)
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
                key=f"{widget_key}_time",
            )

        notes = st.text_area(
            "Member notes",
            value=_clean(prior.get("member_notes")),
            placeholder=(
                "Example: Completed comfortably / slight discomfort / reduced pace."
            ),
            key=f"{widget_key}_notes",
            height=88,
        )

        if st.button(
            "Save Progress",
            key=f"{widget_key}_save",
            use_container_width=True,
        ):
            try:
                save_member_exercise_log(
                    {
                        "member_id": member_id,
                        "log_date": log_date,
                        "allocation_id": allocation_id,
                        "source_id": exercise.get("source_id"),
                        "item_order": index,
                        "exercise_name": name,
                        "scheduled_time": exercise.get("timing_or_slot"),
                        "difficulty": exercise.get("difficulty"),
                        "duration_or_reps": exercise.get("duration_or_reps"),
                        "equipment": exercise.get("equipment"),
                        "benefits": exercise.get("benefits"),
                        "instruction": exercise.get("instruction"),
                        "image_reference": exercise.get("image_reference"),
                        "status": status,
                        "completion_time": (
                            completion_time.strftime("%H:%M")
                            if completion_time
                            else None
                        ),
                        "member_notes": notes.strip(),
                    }
                )
                set_system_message(f"Progress saved for {name}.", "success")
                st.rerun()
            except Exception as exc:
                st.error(f"Exercise progress could not be saved: {exc}")
