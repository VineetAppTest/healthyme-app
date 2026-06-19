import html
from datetime import date

import streamlit as st

from components.guards import require_admin
from components.db import (
    add_member_supplement,
    list_members,
    list_member_supplements,
    stop_member_supplement,
    supplement_regimen_counts,
    update_member_supplement,
)
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)

st.set_page_config(page_title="Supplement Management", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supplement Management",
    "Add, edit, stop and publish member-specific supplement regimens.",
    "Admin supplements",
)


def _esc(value):
    return html.escape(str(value or ""))


def _actor_id():
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _timing_from_choices(choices, extra):
    parts = [str(x).strip() for x in (choices or []) if str(x).strip()]
    if str(extra or "").strip():
        parts.append(str(extra).strip())
    return ", ".join(parts)


def _chips(text):
    parts = [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]
    if not parts:
        return "<span class='hm-sup-mini'>As advised</span>"
    return "".join([f"<span class='hm-sup-mini'>{_esc(p)}</span>" for p in parts])


def _card(row, stopped=False):
    status_cls = " stopped" if stopped else ""
    stop_line = ""
    if stopped:
        stop_line = f"<div class='hm-sup-dose'>Stopped on: {_esc(row.get('stop_date') or 'Not specified')}</div>"
        if row.get("stop_reason"):
            stop_line += f"<div class='hm-sup-dose'>Reason: {_esc(row.get('stop_reason'))}</div>"
    return f"""
    <div class='hm-sup-card{status_cls}'>
      <div class='hm-sup-icon {'blue' if stopped else ''}'>◉</div>
      <div>
        <div class='hm-sup-name'>{_esc(row.get('supplement_name'))}</div>
        <div class='hm-sup-dose'>{_esc(row.get('dosage') or 'Dosage not specified')} · {_esc(row.get('frequency') or 'Frequency not specified')}</div>
        <div class='hm-sup-dose'>Instructions: {_esc(row.get('instructions') or 'As advised')}</div>
        <div>{_chips(row.get('timing'))}</div>
        {stop_line}
      </div>
      <div><span class='hm-sup-status'>{_esc(row.get('status'))}</span></div>
    </div>
    """


st.markdown("""
<style>
.hm-sup-page{max-width:1180px;margin:0 auto;}
.hm-sup-sub{color:#475569;font-size:.90rem;font-weight:660;line-height:1.45;margin:.10rem 0 1rem 0;max-width:760px;}
.hm-sup-layout{display:grid;grid-template-columns:1.2fr .8fr;gap:1rem;margin:.8rem 0 1rem 0;align-items:start;}
.hm-sup-panel{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-sup-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem;gap:.75rem;}
.hm-sup-title{color:#064E3B;font-size:1.02rem;font-weight:950;}
.hm-sup-badge{background:#DDF7F3;color:#006D6F;border-radius:999px;padding:.22rem .58rem;font-size:.72rem;font-weight:900;white-space:nowrap;}
.hm-sup-card{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.72rem 0;display:grid;grid-template-columns:40px 1fr auto;gap:.75rem;align-items:center;}
.hm-sup-card.stopped{background:#F8F5EE;border-style:dashed;opacity:.94;}
.hm-sup-icon{width:34px;height:34px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-sup-icon.blue{background:#E5E7EB;color:#475569;}
.hm-sup-name{color:#1F2937;font-size:.92rem;font-weight:920;margin-bottom:.15rem;}
.hm-sup-dose{color:#64748B;font-size:.78rem;font-weight:760;margin:.10rem 0;}
.hm-sup-mini{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .40rem;font-size:.66rem;font-weight:850;color:#475569;margin:.28rem .15rem 0 0;}
.hm-sup-status{font-size:.72rem;font-weight:900;color:#006D6F;border:1px solid #BEEBE4;background:#F0FDFA;border-radius:999px;padding:.22rem .5rem;}
.hm-sup-note{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:.85rem;color:#7A5A16;font-size:.82rem;font-weight:790;margin:.85rem 0;}
.hm-sup-empty{border:1px dashed #D9C28F;background:#FFFDF8;border-radius:16px;padding:1rem;color:#64748B;font-size:.85rem;font-weight:760;margin:.8rem 0;}
@media(max-width:850px){.hm-sup-layout{grid-template-columns:1fr}.hm-sup-card{grid-template-columns:34px 1fr}.hm-sup-card>div:last-child{grid-column:2}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-page'>", unsafe_allow_html=True)
st.markdown("<div class='hm-sup-sub'>v102.3A stores the regimen against the selected member. Active supplements are published to that member only; stopped supplements remain visible here for history.</div>", unsafe_allow_html=True)

members = list_members()
if not members:
    st.warning("No active members found. Create or activate a member before assigning supplements.")
    render_page_nav("Supplement Management", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
    render_back_to_top()
    st.stop()

member_options = {f"{m.get('name') or 'Member'} — {m.get('email') or m.get('id')}": m for m in members}
selected_label = st.selectbox("Select Member", list(member_options.keys()), key="hm_v1023a_supp_member")
selected_member = member_options[selected_label]
member_id = selected_member["id"]
counts = supplement_regimen_counts(member_id)

left, right = st.columns([1.25, .75], gap="large")

with left:
    st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-sup-title-row'><div class='hm-sup-title'>Active Supplements</div><div class='hm-sup-badge'>{counts['active']} Active</div></div>", unsafe_allow_html=True)
    active_rows = list_member_supplements(member_id=member_id, status="Active")
    if not active_rows:
        st.markdown("<div class='hm-sup-empty'>No active supplements have been assigned to this member yet.</div>", unsafe_allow_html=True)
    for row in active_rows:
        st.markdown(_card(row), unsafe_allow_html=True)
        c1, c2, c3 = st.columns([.55, .45, 2.4])
        with c1:
            if st.button("Edit", key=f"hm_v1023a_edit_{row['id']}"):
                st.session_state["hm_v1023a_edit_id"] = row["id"]
                st.rerun()
        with c2:
            if st.button("Stop", key=f"hm_v1023a_stop_open_{row['id']}"):
                st.session_state["hm_v1023a_stop_id"] = row["id"]
                st.rerun()

        if st.session_state.get("hm_v1023a_edit_id") == row["id"]:
            with st.form(f"hm_v1023a_edit_form_{row['id']}"):
                st.markdown("**Edit supplement**")
                e_name = st.text_input("Supplement Name", value=row.get("supplement_name", ""), key=f"edit_name_{row['id']}")
                e1, e2 = st.columns(2)
                with e1:
                    e_dosage = st.text_input("Dosage", value=row.get("dosage", ""), key=f"edit_dose_{row['id']}")
                    e_frequency = st.text_input("Frequency", value=row.get("frequency", ""), key=f"edit_freq_{row['id']}")
                with e2:
                    e_timing = st.text_input("Timing", value=row.get("timing", ""), key=f"edit_time_{row['id']}")
                    e_start = st.text_input("Start Date", value=row.get("start_date", ""), key=f"edit_start_{row['id']}")
                e_instructions = st.text_area("Member Instructions", value=row.get("instructions", ""), key=f"edit_inst_{row['id']}")
                e_notes = st.text_area("Admin Notes", value=row.get("admin_notes", ""), key=f"edit_notes_{row['id']}")
                save_col, cancel_col = st.columns(2)
                with save_col:
                    save_edit = st.form_submit_button("Save Changes", use_container_width=True)
                with cancel_col:
                    cancel_edit = st.form_submit_button("Cancel", use_container_width=True)
                if save_edit:
                    try:
                        update_member_supplement(row["id"], {
                            "supplement_name": e_name,
                            "dosage": e_dosage,
                            "frequency": e_frequency,
                            "timing": e_timing,
                            "start_date": e_start,
                            "instructions": e_instructions,
                            "admin_notes": e_notes,
                        }, actor_id=_actor_id())
                        st.session_state.pop("hm_v1023a_edit_id", None)
                        st.success("Supplement updated and member regimen refreshed.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                if cancel_edit:
                    st.session_state.pop("hm_v1023a_edit_id", None)
                    st.rerun()

        if st.session_state.get("hm_v1023a_stop_id") == row["id"]:
            with st.form(f"hm_v1023a_stop_form_{row['id']}"):
                st.markdown("**Stop supplement**")
                s_date = st.date_input("Stop Date", value=date.today(), key=f"stop_date_{row['id']}")
                s_reason = st.text_area("Stop Reason / Note", key=f"stop_reason_{row['id']}", placeholder="Optional reason for history")
                stop_col, cancel_col = st.columns(2)
                with stop_col:
                    stop_now = st.form_submit_button("Confirm Stop", use_container_width=True)
                with cancel_col:
                    cancel_stop = st.form_submit_button("Cancel", use_container_width=True)
                if stop_now:
                    try:
                        stop_member_supplement(row["id"], stop_date=s_date, stop_reason=s_reason, actor_id=_actor_id())
                        st.session_state.pop("hm_v1023a_stop_id", None)
                        st.success("Supplement stopped. It is removed from member view and retained in admin history.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                if cancel_stop:
                    st.session_state.pop("hm_v1023a_stop_id", None)
                    st.rerun()

    with st.expander(f"Stopped Supplements / History ({counts['stopped']})", expanded=False):
        stopped_rows = list_member_supplements(member_id=member_id, status="Stopped")
        if not stopped_rows:
            st.info("No stopped supplements yet for this member.")
        for row in stopped_rows:
            st.markdown(_card(row, stopped=True), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-sup-title'>Add Supplement</div>", unsafe_allow_html=True)
    with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
        name = st.text_input("Supplement Name", placeholder="e.g. Magnesium Glycinate")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            dosage = st.text_input("Dosage", placeholder="e.g. 400 mg")
        with c2:
            frequency = st.text_input("Frequency", placeholder="e.g. Once daily")
        timing_options = st.multiselect(
            "Timing",
            ["Morning", "Midday", "Evening", "Before Bed", "With Food", "Empty Stomach", "After Meals"],
            default=[],
        )
        custom_timing = st.text_input("Additional Timing", placeholder="Optional custom timing")
        start_date = st.date_input("Start Date", value=date.today())
        instructions = st.text_area("Member Instructions", placeholder="What the member should follow")
        admin_notes = st.text_area("Admin Notes", placeholder="Internal note; visible only to admin")
        submitted = st.form_submit_button("Add & Publish to Member", use_container_width=True)
        if submitted:
            try:
                add_member_supplement(member_id, {
                    "supplement_name": name,
                    "dosage": dosage,
                    "frequency": frequency,
                    "timing": _timing_from_choices(timing_options, custom_timing),
                    "start_date": start_date,
                    "instructions": instructions,
                    "admin_notes": admin_notes,
                }, actor_id=_actor_id())
                st.success("Supplement added and published to this member's active regimen.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-note'>v102.3A scope guard: persistence and member publishing are active. PDF and Recommendations module are intentionally not included in this build.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Supplement Management", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.3A: Admin Supplement Management with persistent member-specific publishing.
