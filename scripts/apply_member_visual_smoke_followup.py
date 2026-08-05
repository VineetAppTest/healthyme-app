from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {path}, found {count}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1))


# 1. Keep the signed-in pill, Profile and Logout controls on one aligned baseline.
replace_once(
    "components/member_home_global_header_runtime.py",
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{min-height:2.46rem!important;height:auto!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}\n',
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{min-height:2.46rem!important;height:2.46rem!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}\n'
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]>div[data-testid="stVerticalBlock"]{width:100%!important;height:2.46rem!important;min-height:2.46rem!important;display:flex!important;flex-direction:column!important;justify-content:center!important;gap:0!important;margin:0!important;padding:0!important;}\n'
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) [data-testid="stButton"]{height:2.46rem!important;min-height:2.46rem!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}\n',
)
replace_once(
    "components/member_home_global_header_runtime.py",
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}',
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]>div[data-testid="stVerticalBlock"]{height:2.30rem!important;min-height:2.30rem!important;justify-content:center!important;}',
)

# 2. Make Upcoming Schedule disclosure and cards content-sized, and accept in one rerun.
replace_once(
    "components/member_home_schedule_presentation.py",
    '  width:min(420px,100%)!important;max-width:100%!important;\n',
    '  width:fit-content!important;max-width:100%!important;min-width:0!important;\n',
)
replace_once(
    "components/member_home_schedule_presentation.py",
    '    width:min(285px,calc(100vw - 2rem))!important;\n',
    '    width:fit-content!important;max-width:calc(100vw - 2rem)!important;\n',
)
replace_once(
    "components/member_home_schedule_presentation.py",
    '.hm-v101-schedule-card{\n  width:100%!important;max-width:none!important;\n  margin:0!important;padding:0!important;border-radius:0!important;\n}\n',
    '.hm-v101-schedule-card{\n  width:100%!important;max-width:none!important;min-height:0!important;\n  margin:0!important;padding:0!important;border-radius:0!important;\n}\n',
)
old_actions = '''def _render_member_home_schedule_actions(row: dict[str, Any]) -> None:
    """Render consistent acknowledgement and reschedule actions under a card."""

    import streamlit as st
    from components import db as db_api

    schedule_id = _text(row.get("id"))
    if not schedule_id:
        return

    rendered_ids = set(st.session_state.get(_ACTION_RENDERED_IDS_KEY) or ())
    if schedule_id in rendered_ids:
        return
    rendered_ids.add(schedule_id)
    st.session_state[_ACTION_RENDERED_IDS_KEY] = rendered_ids

    status = _text(row.get("status") or "scheduled").lower()
    if status not in {"scheduled", "acknowledged"}:
        return
    pending_reschedule = (
        _text(row.get("reschedule_request_status")).lower() == "pending"
    )

    st.markdown(
        "<span class='hm-member-schedule-action-anchor'></span>",
        unsafe_allow_html=True,
    )
    acknowledge_col, reschedule_col = st.columns(2, gap="small")
    with acknowledge_col:
        if status == "scheduled":
            if st.button(
                "Acknowledge",
                key=f"hm_home_ack_schedule_{schedule_id}",
                use_container_width=True,
            ):
                updated = db_api.acknowledge_member_schedule(schedule_id, row.get("member_id"))
                if updated:
                    st.rerun()
                st.error("This schedule could not be acknowledged. Please refresh and retry.")
        else:
            st.button(
                "Acknowledged",
                key=f"hm_home_acknowledged_schedule_{schedule_id}",
                use_container_width=True,
                disabled=True,
            )
    with reschedule_col:
        reschedule_label = "Reschedule pending" if pending_reschedule else "Reschedule"
        if st.button(
            reschedule_label,
            key=f"hm_home_reschedule_schedule_{schedule_id}",
            use_container_width=True,
            disabled=pending_reschedule,
        ):
            st.session_state["hm_member_schedule_active_section"] = "Upcoming Schedule"
            st.session_state[f"hm_tz_show_reschedule_{schedule_id}"] = True
            st.switch_page("pages/33_My_Schedule.py")
'''
new_actions = '''def _accept_member_home_schedule(
    schedule_id: str,
    member_id: object,
    error_key: str,
) -> None:
    """Accept before the normal Streamlit button rerun; do not trigger a second rerun."""

    import streamlit as st
    from components import db as db_api

    updated = db_api.acknowledge_member_schedule(schedule_id, member_id)
    if not updated:
        st.session_state[error_key] = (
            "This schedule could not be accepted. Please refresh and retry."
        )


def _render_member_home_schedule_actions(row: dict[str, Any]) -> None:
    """Render consistent acceptance and reschedule actions under a card."""

    import streamlit as st

    schedule_id = _text(row.get("id"))
    if not schedule_id:
        return

    rendered_ids = set(st.session_state.get(_ACTION_RENDERED_IDS_KEY) or ())
    if schedule_id in rendered_ids:
        return
    rendered_ids.add(schedule_id)
    st.session_state[_ACTION_RENDERED_IDS_KEY] = rendered_ids

    status = _text(row.get("status") or "scheduled").lower()
    if status not in {"scheduled", "acknowledged"}:
        return
    pending_reschedule = (
        _text(row.get("reschedule_request_status")).lower() == "pending"
    )
    error_key = f"_hm_home_accept_error_{schedule_id}"
    error_message = st.session_state.pop(error_key, "")
    if error_message:
        st.error(error_message)

    st.markdown(
        "<span class='hm-member-schedule-action-anchor'></span>",
        unsafe_allow_html=True,
    )
    accept_col, reschedule_col = st.columns(2, gap="small")
    with accept_col:
        if status == "scheduled":
            st.button(
                "Accept",
                key=f"hm_home_accept_schedule_{schedule_id}",
                use_container_width=True,
                on_click=_accept_member_home_schedule,
                args=(schedule_id, row.get("member_id"), error_key),
            )
        else:
            st.button(
                "Accepted",
                key=f"hm_home_accepted_schedule_{schedule_id}",
                use_container_width=True,
                disabled=True,
            )
    with reschedule_col:
        reschedule_label = "Reschedule pending" if pending_reschedule else "Reschedule"
        if st.button(
            reschedule_label,
            key=f"hm_home_reschedule_schedule_{schedule_id}",
            use_container_width=True,
            disabled=pending_reschedule,
        ):
            st.session_state["hm_member_schedule_active_section"] = "Upcoming Schedule"
            st.session_state[f"hm_tz_show_reschedule_{schedule_id}"] = True
            st.switch_page("pages/33_My_Schedule.py")
'''
replace_once(
    "components/member_home_schedule_presentation.py",
    old_actions,
    new_actions,
)

# 3. Compact Member Home schedule/task surfaces while preserving the 2-card row.
replace_once(
    "pages/02_Member_Home.py",
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"]{display:flex!important;align-items:center!important;min-height:2.46rem!important;}\n',
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"]{display:flex!important;align-items:center!important;height:2.46rem!important;min-height:2.46rem!important;}\n'
    'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"] > div[data-testid="stVerticalBlock"]{width:100%!important;height:2.46rem!important;min-height:2.46rem!important;display:flex!important;flex-direction:column!important;justify-content:center!important;gap:0!important;margin:0!important;padding:0!important;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    'div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-home-grid-anchor),div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-message-grid-anchor){height:100%!important;padding:.58rem .64rem .64rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}\n',
    'div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-home-grid-anchor){height:auto!important;min-height:0!important;align-self:flex-start!important;padding:.52rem .60rem .58rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}\n'
    'div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-message-grid-anchor){height:100%!important;padding:.58rem .64rem .64rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v101-schedule-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:5.85rem;box-shadow:none!important;}\n',
    '.hm-v101-schedule-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:0!important;box-shadow:none!important;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:.82rem .86rem .88rem;margin:.58rem 0 .72rem 0;min-height:15.75rem;box-sizing:border-box;}\n',
    '.hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:1rem 1rem 1.04rem;margin:.58rem 0 .78rem 0;min-height:0;box-sizing:border-box;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v990-progress-head{display:flex;align-items:center;justify-content:space-between;gap:.65rem;flex-wrap:wrap;margin:0 0 .38rem 0;}\n',
    '.hm-v990-progress-head{display:flex;align-items:center;justify-content:space-between;gap:.78rem;flex-wrap:wrap;margin:0 0 .52rem 0;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v990-progress-line{height:8px;border-radius:999px;background:#EFE7D6;overflow:hidden;margin:.28rem 0 .42rem 0;}\n',
    '.hm-v990-progress-line{height:8px;border-radius:999px;background:#EFE7D6;overflow:hidden;margin:.38rem 0 .56rem 0;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v990-admin-note{color:#334155;font-size:.80rem;line-height:1.42;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:.46rem .58rem;margin:.40rem 0 .16rem 0;}\n',
    '.hm-v990-admin-note{color:#334155;font-size:.80rem;line-height:1.48;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:.56rem .64rem;margin:.56rem 0 .24rem 0;}\n',
)
replace_once(
    "pages/02_Member_Home.py",
    '.hm-v990-submit-note{color:#64748B;font-size:.80rem;font-weight:720;margin:.36rem 0 .58rem 0;}\n',
    '.hm-v990-submit-note{color:#64748B;font-size:.80rem;font-weight:720;line-height:1.42;margin:.48rem 0 .32rem 0;}\n',
)

# 4. Give each open meal a real compact bordered card.
replace_once(
    "pages/18_Daily_Log.py",
    '        .hm-meal-time-grid-anchor,.hm-meal-food-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}\n',
    '        .hm-meal-time-grid-anchor,.hm-meal-food-grid-anchor,.hm-meal-entry-card-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}\n'
    '        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-meal-entry-card-anchor){height:auto!important;min-height:0!important;padding:.68rem .76rem .78rem!important;margin:.06rem 0 .52rem 0!important;border:1.25px solid #D8A84E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}\n'
    '        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-meal-entry-card-anchor)>div{padding:0!important;gap:.30rem!important;}\n'
    '        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-meal-entry-card-anchor) div[data-testid="stTextInput"],div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-meal-entry-card-anchor) div[data-testid="stSelectbox"]{margin-bottom:.24rem!important;padding-bottom:0!important;}\n'
    '        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-meal-entry-card-anchor) label{margin-bottom:.18rem!important;padding-bottom:0!important;}\n',
)
old_meal_toggle = '''def _render_meal_toggle(label, key, prior, date_key):
    if _toggle_button(f"{label} — {_meal_summary(prior)}", f"{date_key}_{key}"):
        return _render_meal_fields(label, key, prior, date_key)
    return _as_dict(prior)
'''
new_meal_toggle = '''def _render_meal_toggle(label, key, prior, date_key):
    if _toggle_button(f"{label} — {_meal_summary(prior)}", f"{date_key}_{key}"):
        with st.container(border=True):
            st.markdown(
                "<span class='hm-meal-entry-card-anchor'></span>",
                unsafe_allow_html=True,
            )
            return _render_meal_fields(label, key, prior, date_key)
    return _as_dict(prior)
'''
replace_once("pages/18_Daily_Log.py", old_meal_toggle, new_meal_toggle)

# 5. Let Saved Days cards use their content height instead of fixed empty space.
replace_once(
    "components/food_saved_days_presentation.py",
    '      height:100%!important;min-height:12rem!important;padding:.66rem .72rem!important;\n',
    '      height:auto!important;min-height:0!important;align-self:flex-start!important;padding:.66rem .72rem!important;\n',
)
replace_once(
    "components/food_saved_days_presentation.py",
    '    .hm-saved-day-card{display:flex;flex-direction:column;gap:.27rem;min-height:8.8rem;}\n',
    '    .hm-saved-day-card{display:flex;flex-direction:column;gap:.27rem;min-height:0;}\n',
)

# 6. Rename schedule actions and remove explicit second reruns on initial actions.
insert_anchor = '\n\ndef render_member_schedule_page() -> None:\n'
insert_block = '''

def _accept_member_schedule_once(schedule_id: object, user_id: object) -> None:
    """Persist acceptance during the button callback, before the normal rerun."""

    result_key = f"_hm_tz_accept_result_{schedule_id}"
    accepted = acknowledge_member_schedule(schedule_id, user_id)
    st.session_state[result_key] = "accepted" if accepted else "error"


def _toggle_member_reschedule_form(state_key: str) -> None:
    """Toggle the form in the button callback without an explicit second rerun."""

    st.session_state[state_key] = not st.session_state.get(state_key, False)


def render_member_schedule_page() -> None:
'''
replace_once("components/schedule_timezone_ui.py", insert_anchor, insert_block)
replace_once(
    "components/schedule_timezone_ui.py",
    '        "View, acknowledge or request a reschedule for upcoming sessions.",\n',
    '        "View, accept or reschedule upcoming sessions.",\n',
)
old_schedule_actions = '''            action_col_1, action_col_2 = st.columns(2, gap="medium")
            with action_col_1:
                if status == "scheduled":
                    if st.button(
                        "Acknowledge schedule",
                        key=f"hm_tz_ack_schedule_{row.get('id')}",
                        use_container_width=True,
                    ):
                        acknowledge_member_schedule(row.get("id"), user_id)
                        st.success("Schedule acknowledged.")
                        st.rerun()
            with action_col_2:
                can_request = (
                    status in ["scheduled", "acknowledged"]
                    and row.get("reschedule_request_status") != "pending"
                )
                if st.button(
                    "Request Reschedule",
                    key=f"hm_tz_open_reschedule_{row.get('id')}",
                    use_container_width=True,
                    disabled=not can_request,
                ):
                    state_key = f"hm_tz_show_reschedule_{row.get('id')}"
                    st.session_state[state_key] = not st.session_state.get(state_key, False)
                    st.rerun()
'''
new_schedule_actions = '''            schedule_id = row.get("id")
            accept_result_key = f"_hm_tz_accept_result_{schedule_id}"
            accept_result = st.session_state.pop(accept_result_key, "")
            if accept_result == "error":
                st.error("This schedule could not be accepted. Please refresh and retry.")

            state_key = f"hm_tz_show_reschedule_{schedule_id}"
            action_col_1, action_col_2 = st.columns(2, gap="medium")
            with action_col_1:
                if status == "scheduled":
                    st.button(
                        "Accept",
                        key=f"hm_tz_accept_schedule_{schedule_id}",
                        use_container_width=True,
                        on_click=_accept_member_schedule_once,
                        args=(schedule_id, user_id),
                    )
                elif status == "acknowledged":
                    st.button(
                        "Accepted",
                        key=f"hm_tz_accepted_schedule_{schedule_id}",
                        use_container_width=True,
                        disabled=True,
                    )
            with action_col_2:
                can_request = (
                    status in ["scheduled", "acknowledged"]
                    and row.get("reschedule_request_status") != "pending"
                )
                st.button(
                    "Reschedule",
                    key=f"hm_tz_open_reschedule_{schedule_id}",
                    use_container_width=True,
                    disabled=not can_request,
                    on_click=_toggle_member_reschedule_form,
                    args=(state_key,),
                )
'''
replace_once("components/schedule_timezone_ui.py", old_schedule_actions, new_schedule_actions)
replace_once(
    "components/schedule_timezone_ui.py",
    '            state_key = f"hm_tz_show_reschedule_{row.get(\'id\')}"\n',
    '            state_key = f"hm_tz_show_reschedule_{schedule_id}"\n',
)
replace_once(
    "components/schedule_timezone_ui.py",
    '                    st.markdown("#### Request reschedule")\n',
    '                    st.markdown("#### Reschedule")\n',
)
