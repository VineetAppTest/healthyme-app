
import streamlit as st, json, pathlib
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_page_nav, render_build_text_v12
from components.db import get_admin_assessment, save_admin_assessment, update_workflow, get_form_response, member_has_meaningful_data, unlock_body_mind, get_workflow, sync_body_mind_after_admin_completion, request_body_mind_activation, finalize_admin_assessment, manually_unlock_body_mind_after_finalization, sync_member_finalization_state
from components.scoring import map_answer
from components.flash import set_system_message, render_system_message
from components.admin_value_resolver import resolve_admin_linked_value
st.set_page_config(page_title="Admin Assessment", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
mid=st.session_state.get("selected_member_id")
if not mid: st.switch_page("pages/11_Evaluation_Status.py")
templates=json.loads((pathlib.Path(__file__).resolve().parents[1]/"config"/"admin_templates.json").read_text())
existing=get_admin_assessment(mid); current_wf = get_workflow(mid)
selected_instance_id = st.session_state.get("selected_instance_id")
if selected_instance_id:
    db_tmp = load_db() if "load_db" in globals() else None
    # load_db may not be imported in older builds; fall back below if unavailable
try:
    from components.db import load_db as _hm_load_db
    _db_for_instance = _hm_load_db()
    _inst_resp = _db_for_instance.get("assessment_instance_responses", {}).get(selected_instance_id, {}) if selected_instance_id else {}
except Exception:
    _inst_resp = {}
nsp1=_inst_resp.get("nsp1") or get_form_response("nsp1_responses", mid)
nsp2=_inst_resp.get("nsp2") or get_form_response("nsp2_responses", mid)
laf=get_form_response("laf_responses", mid)
render_page_nav("Admin Assessment", back_page="pages/11_Evaluation_Status.py", location="top")
topbar("Fill Admin Page","Linked items are auto-pulled; manual items can be NA, 1, 2, or 3.","Admin assessment")
render_system_message()

# v26 finalization lock:
# Once final report/admin review is complete, the form is frozen.
current_wf = get_workflow(mid)
is_finalized = bool(current_wf.get("admin_completed")) or bool(current_wf.get("final_report_ready"))

if is_finalized:

    # v31: repair stale review/instance status for finalized records.
    current_wf = sync_member_finalization_state(mid, body_mind_unlock=None)
    card_start()
    st.success("Final admin assessment is already completed. The final report is ready and this form is now locked.")
    st.markdown(
        """
        <div class='info-banner'>
          <b>No further action is required on the five admin pages.</b><br>
          To review member status or reports, use Evaluation Status. To manage Body-Mind access, use Body-Mind Access Control.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # v30: Even after finalization lock, manual Body-Mind activation must remain available.
    latest_wf_locked = get_workflow(mid)
    if latest_wf_locked.get("body_mind_unlocked"):
        st.success("Body-Mind Connection is active for this member.")
    else:
        st.warning("Body-Mind Connection is not active yet. Final admin work is complete, so you can activate it now.")
        confirm_bm_unlock = st.checkbox("Show Body-Mind Connection to this member", key=f"bm_unlock_locked_{mid}")
        if st.button("Activate Body-Mind Connection", type="primary", use_container_width=True, disabled=not confirm_bm_unlock):
            ok, msg = manually_unlock_body_mind_after_finalization(mid)
            if ok:
                set_system_message(msg, "success", celebrate=True)
            else:
                set_system_message(msg, "error")
            st.rerun()

    c_locked_1, c_locked_2, c_locked_3 = st.columns(3)
    with c_locked_1:
        if st.button("Evaluation Status", use_container_width=True):
            st.switch_page("pages/11_Evaluation_Status.py")
    with c_locked_2:
        if st.button("Body-Mind Access", use_container_width=True):
            st.switch_page("pages/23_Admin_Body_Mind_Control.py")
    with c_locked_3:
        if st.button("Final Report", type="primary", use_container_width=True):
            st.switch_page("pages/14_Final_Assessment_Report.py")
    card_end()
    render_page_nav("Admin Assessment", back_page="pages/11_Evaluation_Status.py", location="bottom")
    st.stop()

card_start()
if not member_has_meaningful_data(mid): st.warning("Member assessment is incomplete. Final report generation is disabled until member data exists.")
all_data={}; grand=0
for section, groups in templates.items():
    st.header(section); section_data={}
    for group in [g for g in groups if not g.get("deleted")]:
        st.subheader(group["heading"])
        cols=st.columns(2)
        for idx,item in enumerate([x for x in group["items"] if not x.get("deleted")]):
            with cols[idx%2]:
                key=f"{section}|{group['heading']}|{item['label']}"
                if item.get("linked_code"):
                    old=existing.get(section,{}).get(key,"Select")
                    val, meta = resolve_admin_linked_value(item, nsp1=nsp1, nsp2=nsp2, laf=laf, stored=old)
                    st.caption(f"Auto-populated from {meta.get('source_label','linked source')}.")
                    st.selectbox(item["label"], ["NA","1","2","3"], index=["NA","1","2","3"].index(val), key=key, disabled=True)
                else:
                    old=existing.get(section,{}).get(key,"Select")
                    val=st.selectbox(item["label"], ["Select","NA","1","2","3"], index=["Select","NA","1","2","3"].index(old) if old in ["Select","NA","1","2","3"] else 0, key=key)
                section_data[key]=val; grand+=map_answer(val)
    all_data[section]=section_data
st.info(f"Estimated internal total: {grand}")
body_mind_already_unlocked = bool(current_wf.get("body_mind_unlocked"))
body_mind_activation_requested = bool(current_wf.get("body_mind_activation_requested"))

if body_mind_already_unlocked:
    st.info("Body-Mind Connection is already activated for this member. No further activation is required from this page.")
    body_mind_unlock_choice = True
else:
    body_mind_unlock_choice = st.checkbox(
        "After saving this admin assessment, make Body-Mind Connection page visible to this member",
        value=bool(body_mind_activation_requested),
    )
    st.caption("Body-Mind can be enabled here only because this action saves the admin assessment first.")

# v21 safety:
# The Admin Assessment page can enable Body-Mind, but must not accidentally disable it.
# Disabling should happen only from Body-Mind Access Control via explicit disable confirmation.
def _effective_body_mind_unlock():
    latest_wf = get_workflow(mid)
    return bool(latest_wf.get("body_mind_unlocked")) or bool(latest_wf.get("body_mind_activation_requested")) or bool(body_mind_unlock_choice)

c1,c2=st.columns(2)
with c1:
    if st.button("Save Draft", use_container_width=True):
        old_body_mind_visibility = bool(get_workflow(mid).get("body_mind_unlocked"))
        save_admin_assessment(mid, all_data)
        if body_mind_unlock_choice:
            request_body_mind_activation(mid)
        if body_mind_unlock_choice and not old_body_mind_visibility:
            set_system_message("Draft saved. Body-Mind activation request has been recorded.", "success", celebrate=True)
        elif old_body_mind_visibility:
            set_system_message("Draft saved. Body-Mind Connection remains activated for this member.", "info")
        else:
            set_system_message("Draft saved successfully.", "success")
        st.rerun()
with c2:
    if st.button("Save and Generate Final Report", type="primary", use_container_width=True):
        if not member_has_meaningful_data(mid):
            set_system_message("Member assessment is incomplete.", "error")
            st.rerun()
        else:
            with st.spinner("Finalizing admin assessment and preparing final report..."):
                result = finalize_admin_assessment(
                    mid,
                    all_data,
                    activation_selected=bool(body_mind_unlock_choice),
                )

            if result.get("body_mind_unlocked"):
                set_system_message(
                    "Admin Assessment completed, Final Assessment Report is ready, and Body-Mind Connection is activated.",
                    "success",
                    celebrate=True,
                )
            else:
                set_system_message(
                    "Admin Assessment completed and Final Assessment Report is ready. Body-Mind was not activated because activation was not selected.",
                    "success",
                    celebrate=True,
                )
            st.rerun()
card_end()
render_page_nav("Admin Assessment", back_page="pages/11_Evaluation_Status.py", location="bottom")
