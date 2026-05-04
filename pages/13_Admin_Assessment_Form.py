
import streamlit as st, json, pathlib
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import get_admin_assessment, save_admin_assessment, update_workflow, get_form_response, member_has_meaningful_data, unlock_body_mind, get_workflow
from components.scoring import map_answer
from components.flash import set_system_message, render_system_message
st.set_page_config(page_title="Admin Assessment", page_icon="💚", layout="wide")
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
topbar("Fill Admin Page","Linked items are auto-pulled; manual items can be NA, 1, 2, or 3.","Admin assessment")
render_system_message()
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
                    code=item["linked_code"]; raw=nsp1.get(code) if code.startswith("nsp1_") else nsp2.get(code); val=raw if raw in ["NA","1","2","3"] else "NA"
                    st.selectbox(item["label"], ["NA","1","2","3"], index=["NA","1","2","3"].index(val), key=key, disabled=True)
                else:
                    old=existing.get(section,{}).get(key,"Select")
                    val=st.selectbox(item["label"], ["Select","NA","1","2","3"], index=["Select","NA","1","2","3"].index(old) if old in ["Select","NA","1","2","3"] else 0, key=key)
                section_data[key]=val; grand+=map_answer(val)
    all_data[section]=section_data
st.info(f"Estimated internal total: {grand}")
body_mind_unlock_choice = st.checkbox("After saving this admin assessment, make Body-Mind Connection page visible to this member", value=bool(current_wf.get("body_mind_unlocked")))
st.caption("Body-Mind can be enabled here only because this action saves the admin assessment first.")
c1,c2=st.columns(2)
with c1:
    if st.button("Save Draft", use_container_width=True):
        old_body_mind_visibility = bool(current_wf.get("body_mind_unlocked"))
        save_admin_assessment(mid, all_data)
        unlock_body_mind(mid, body_mind_unlock_choice)
        if body_mind_unlock_choice and not old_body_mind_visibility:
            set_system_message("Draft saved and Body-Mind Connection page enabled for this member.", "success", celebrate=True)
        elif not body_mind_unlock_choice and old_body_mind_visibility:
            set_system_message("Draft saved and Body-Mind Connection page disabled for this member.", "warning")
        else:
            set_system_message("Draft saved successfully.", "success")
        st.rerun()
with c2:
    if st.button("Save and Generate Final Report", type="primary", use_container_width=True):
        if not member_has_meaningful_data(mid):
            set_system_message("Member assessment is incomplete.", "error")
            st.rerun()
        else:
            old_body_mind_visibility = bool(current_wf.get("body_mind_unlocked"))
            save_admin_assessment(mid, all_data)
            unlock_body_mind(mid, body_mind_unlock_choice)
            update_workflow(mid, admin_completed=True, final_report_ready=True)
            if body_mind_unlock_choice and not old_body_mind_visibility:
                set_system_message("Admin Assessment completed, Final Assessment Report is now available, and Body-Mind Connection page enabled for this member.", "success", celebrate=True)
            elif not body_mind_unlock_choice and old_body_mind_visibility:
                set_system_message("Final report generated and Body-Mind Connection page disabled for this member.", "warning")
            else:
                set_system_message("Admin Assessment completed and Final Assessment Report is now available.", "success", celebrate=True)
            st.rerun()
if st.button("Back"): st.switch_page("pages/11_Evaluation_Status.py")
card_end()
