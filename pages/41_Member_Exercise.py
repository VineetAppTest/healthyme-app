from datetime import date, datetime
import html

import streamlit as st

from components.flash import render_system_message, set_system_message
from components.guards import require_member
from components.member_exercise_journal import (
    exercise_log_map,
    load_member_exercise_contract,
    save_member_exercise_log,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


BUILD_NOTE = "v102.5 · Member Exercise Journal"
STATUS_OPTIONS = ["Not Started", "In Progress", "Completed", "Skipped"]


def _clean(value):
    return "" if value is None else str(value).strip()


def _esc(value):
    return html.escape(_clean(value))


def _parse_time(value):
    raw = _clean(value)
    if not raw:
        return None
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(raw, fmt).time()
        except Exception:
            pass
    return None


st.set_page_config(page_title="My Exercise", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("My Exercise", "View today's prescribed exercises and record progress.", "Member tracker")
render_system_message()

st.markdown(
    """
<style>
.hm-exercise-card{border:1px solid #E3D4BA;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:18px;padding:.9rem 1rem;margin:.65rem 0;box-shadow:0 8px 20px rgba(15,23,42,.045);}
.hm-exercise-title{color:#064E3B;font-size:1.05rem;font-weight:950;margin-bottom:.35rem;}
.hm-exercise-meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.45rem;margin:.35rem 0 .65rem 0;}
.hm-exercise-meta div{border:1px solid #E8DDC7;border-radius:12px;background:#FFFFFF;padding:.48rem .58rem;color:#334155;font-size:.82rem;}
.hm-exercise-meta b{display:block;color:#064E3B;font-size:.73rem;text-transform:uppercase;letter-spacing:.02em;margin-bottom:.12rem;}
.hm-exercise-copy{color:#334155;font-size:.88rem;line-height:1.45;margin:.35rem 0;}
.hm-exercise-progress{border:1px solid #D8C18B;background:#FFF7E6;border-radius:14px;padding:.7rem .8rem;margin:.5rem 0 1rem 0;color:#7A5A16;font-weight:850;}
@media(max-width:760px){.hm-exercise-meta{grid-template-columns:1fr;}}
</style>
""",
    unsafe_allow_html=True,
)

member_id = st.session_state.get("user_id", "")
member_email = st.session_state.get("user_email") or st.session_state.get("email") or ""
contract = load_member_exercise_contract(member_id, member_email)

if not contract.get("ok"):
    st.error(contract.get("message") or "Exercise recommendations could not be loaded.")
    st.stop()

exercises = contract.get("exercises", [])
profile = contract.get("profile", {})
log_date = date.today().isoformat()
existing_logs = exercise_log_map(member_id, log_date)
completed_count = sum(1 for row in existing_logs.values() if row.get("status") == "Completed")

st.caption(f"{BUILD_NOTE} · {contract.get('day_label', '')}")
st.markdown(
    f"<div class='hm-exercise-progress'>Today's progress: {completed_count} of {len(exercises)} exercise(s) completed</div>",
    unsafe_allow_html=True,
)

if not exercises:
    st.info("No exercise has been assigned for today in the active recommendation profile.")
else:
    for index, exercise in enumerate(exercises, start=1):
        item_order = int(exercise.get("item_order") or index)
        prior = existing_logs.get(item_order, {})
        name = _clean(exercise.get("name")) or f"Exercise {index}"
        st.markdown(
            f"""
            <div class='hm-exercise-card'>
              <div class='hm-exercise-title'>{_esc(name)}</div>
              <div class='hm-exercise-meta'>
                <div><b>Time of Day</b>{_esc(exercise.get('timing_or_slot') or '-')}</div>
                <div><b>Difficulty</b>{_esc(exercise.get('difficulty') or '-')}</div>
                <div><b>Duration / Repetitions</b>{_esc(exercise.get('duration_or_reps') or '-')}</div>
                <div><b>Equipment</b>{_esc(exercise.get('equipment') or '-')}</div>
                <div><b>Category / Source</b>{_esc(exercise.get('source_context') or '-')}</div>
                <div><b>Image Reference</b>{_esc(exercise.get('image_reference') or '-')}</div>
              </div>
              <div class='hm-exercise-copy'><b>Benefits:</b> {_esc(exercise.get('benefits') or '-')}</div>
              <div class='hm-exercise-copy'><b>Instructions:</b> {_esc(exercise.get('instruction') or '-')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        status_col, time_col = st.columns(2)
        with status_col:
            prior_status = prior.get("status") if prior.get("status") in STATUS_OPTIONS else "Not Started"
            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(prior_status),
                key=f"exercise_status_{item_order}",
            )
        with time_col:
            completion_time = st.time_input(
                "Completion time",
                value=_parse_time(prior.get("completion_time")),
                key=f"exercise_time_{item_order}",
            )
        notes = st.text_area(
            "Member notes",
            value=_clean(prior.get("member_notes")),
            placeholder="Example: Completed comfortably / slight discomfort / reduced pace.",
            key=f"exercise_notes_{item_order}",
            height=88,
        )
        if st.button("Save Progress", key=f"save_exercise_{item_order}", use_container_width=True):
            try:
                save_member_exercise_log(
                    {
                        "member_id": member_id,
                        "log_date": log_date,
                        "profile_id": profile.get("id"),
                        "profile_name": profile.get("profile_name"),
                        "day_number": contract.get("today_day"),
                        "item_order": item_order,
                        "exercise_name": name,
                        "scheduled_time": exercise.get("timing_or_slot"),
                        "difficulty": exercise.get("difficulty"),
                        "duration_or_reps": exercise.get("duration_or_reps"),
                        "equipment": exercise.get("equipment"),
                        "benefits": exercise.get("benefits"),
                        "instruction": exercise.get("instruction"),
                        "image_reference": exercise.get("image_reference"),
                        "status": status,
                        "completion_time": completion_time.strftime("%H:%M") if completion_time else None,
                        "member_notes": notes.strip(),
                    }
                )
                set_system_message(f"Progress saved for {name}.", "success")
                st.rerun()
            except Exception as exc:
                st.error(f"Exercise progress could not be saved: {exc}")

render_page_nav(
    "My Exercise",
    back_page="pages/18_Daily_Log.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
