import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, stat_grid, utility_logout_bar, render_build_text_v12
from components.db import get_workflow, get_member_messages, sync_body_mind_after_admin_completion, hard_sync_body_mind_if_requested, has_explicit_body_mind_access
from components.assessment_instances import get_current_assessment_instance
from components.flash import render_system_message

st.set_page_config(page_title="Member Home", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
wf = get_workflow(user_id)
# v32 hard sync:
# If finalization is complete and manual activation request exists, repair body_mind_unlocked.
if (wf.get("admin_completed") or wf.get("final_report_ready") or wf.get("workflow_status") == "finalized") and wf.get("body_mind_activation_requested") and not wf.get("body_mind_unlocked"):
    hard_sync_body_mind_if_requested(user_id)
    wf = get_workflow(user_id)

current_instance = get_current_assessment_instance(user_id)

# v31: workflow finalization overrides stale instance review status.
workflow_finalized = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready")) or wf.get("workflow_status") == "finalized"
requested_pages = current_instance.get("requested_pages", ["nsp1", "nsp2"])
is_reassessment = current_instance.get("instance_type") == "Reassessment" and not current_instance.get("submitted_for_review")

topbar("Member Home", "Continue your wellness assessment and access your tools.", "Member experience")
render_system_message()

messages = get_member_messages(user_id, limit=3)
if messages:
    with st.expander("Messages from Admin", expanded=True):
        for msg in messages:
            st.markdown(
                f"""
                <div class='hm-comm-card'>
                  <b>{msg.get('subject','')}</b><br>
                  <span style='color:#64748B;font-size:.85rem;'>{msg.get('ts','')}</span>
                  <p>{msg.get('message','')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


stat_grid([
    {"label": "LAF", "value": "Completed" if wf.get("laf_completed") else "Pending", "note": "Lifestyle intake"},
    {"label": "Current Instance", "value": current_instance.get("instance_number"), "note": current_instance.get("instance_type")},
    {"label": "Requested NSP", "value": ", ".join(["Pg 1" if p=="nsp1" else "Pg 2" for p in requested_pages]), "note": "Current requirement"},
    {"label": "Status", "value": current_instance.get("status", wf.get("workflow_status")).replace("_", " ").title(), "note": "Current stage"},
])

if is_reassessment:
    card_start()
    st.subheader("Reassessment requested")
    st.markdown(
        f"""
        <div class='info-banner'>
          <b>Admin has requested Reassessment {current_instance.get('instance_number')}.</b><br>
          Please complete: <b>{', '.join(['NSP Page 1' if p=='nsp1' else 'NSP Page 2' for p in requested_pages])}</b><br>
          Due date: <b>{current_instance.get('due_date') or 'Not set'}</b><br>
          Note: {current_instance.get('admin_note') or '-'}
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if "nsp1" in requested_pages and st.button("Start NSP Page 1", type="primary", use_container_width=True):
            st.switch_page("pages/04_NSP_Page1.py")
    with c2:
        if "nsp2" in requested_pages and st.button("Start NSP Page 2", type="primary", use_container_width=True):
            st.switch_page("pages/05_NSP_Page2.py")
    card_end()

left, right = st.columns([1.15, .85], gap="large")

with left:
    card_start()
    st.subheader("Your next steps")

    if not wf.get("laf_completed"):
        if st.button("1. Fill LAF", type="primary", use_container_width=True):
            st.switch_page("pages/03_LAF_Form.py")
    elif current_instance.get("submitted_for_review") and not is_reassessment:
        st.info("Your latest evaluation has been submitted and is under review.")
    else:
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("1. Fill LAF", use_container_width=True, disabled=is_reassessment):
                st.switch_page("pages/03_LAF_Form.py")
        with b2:
            if st.button("2. Fill NSP Pg 1", use_container_width=True, disabled=("nsp1" not in requested_pages)):
                st.switch_page("pages/04_NSP_Page1.py")
        with b3:
            if st.button("3. Fill NSP Pg 2", use_container_width=True, disabled=("nsp2" not in requested_pages)):
                st.switch_page("pages/05_NSP_Page2.py")

    st.divider()
    x1, x2, x3 = st.columns(3)
    with x1:
        if st.button("Submit / Status", use_container_width=True):
            st.switch_page("pages/06_Submit_Status.py")
    with x2:
        if st.button("My Profile", use_container_width=True):
            st.switch_page("pages/07_My_Profile.py")
    with x3:
        if st.button("Daily Log", use_container_width=True):
            st.switch_page("pages/18_Daily_Log.py")
    card_end()

with right:
    card_start()
    st.subheader("Personalized content")

    # v19 fix:
    # Body-Mind visibility is controlled by body_mind_unlocked.
    # It should not be hidden only because admin_completed is False.
    # Recipes/exercises remain locked until admin_completed.
    body_mind_unlocked = bool(wf.get("body_mind_unlocked")) or has_explicit_body_mind_access(user_id)
    admin_completed = bool(wf.get("admin_completed"))

    if body_mind_unlocked:
        label = "Body-Mind Connection" if not wf.get("body_mind_completed") else "Body-Mind Connection ✓"
        if st.button(label, type="primary", use_container_width=True):
            st.switch_page("pages/19_Body_Mind_Connection.py")
    else:
        activation_requested = bool(wf.get("body_mind_activation_requested"))
        if admin_completed and activation_requested:
            body_mind_msg = "Activation was requested but not synced. Ask admin to activate once from Body-Mind Access Control."
        elif admin_completed:
            body_mind_msg = "Final review is complete. Admin must manually activate Body-Mind for it to appear."
        elif activation_requested:
            body_mind_msg = "Body-Mind activation is selected and will open after final admin completion."
        else:
            body_mind_msg = "Admin final assessment is required first, then admin must manually activate Body-Mind."
        st.markdown(
            f"<div class='lock-card'><b>Body-Mind Connection is not activated yet.</b><br>{body_mind_msg}</div>",
            unsafe_allow_html=True,
        )

    if not admin_completed:
        st.markdown(
            "<div class='lock-card'><b>Recipes and exercises are locked until expert review is complete.</b></div>",
            unsafe_allow_html=True,
        )
    else:
        if st.button("Recipe Repository", use_container_width=True):
            st.switch_page("pages/08_Recipe_Repository.py")
        if st.button("Exercise Repository", use_container_width=True):
            st.switch_page("pages/09_Exercise_Repository.py")

    st.divider()
    st.subheader("Journey summary")
    st.markdown(
        f"""
        <div class="member-summary-grid">
          <div class="member-summary-item {'member-summary-ok' if wf.get('laf_completed') else 'member-summary-warn'}">
            <div class="member-summary-label">LAF</div><div class="member-summary-value">{'Completed' if wf.get('laf_completed') else 'Pending'}</div>
          </div>
          <div class="member-summary-item {'member-summary-ok' if current_instance.get('nsp1_completed') else 'member-summary-warn'}">
            <div class="member-summary-label">NSP Page 1</div><div class="member-summary-value">{'Completed' if current_instance.get('nsp1_completed') else 'Pending'}</div>
          </div>
          <div class="member-summary-item {'member-summary-ok' if current_instance.get('nsp2_completed') else 'member-summary-warn'}">
            <div class="member-summary-label">NSP Page 2</div><div class="member-summary-value">{'Completed' if current_instance.get('nsp2_completed') else 'Pending'}</div>
          </div>
          <div class="member-summary-item member-summary-info">
            <div class="member-summary-label">Instance</div><div class="member-summary-value">{current_instance.get('instance_number')} - {current_instance.get('instance_type')}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    card_end()