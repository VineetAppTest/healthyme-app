import html
import re
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


TIMING_OPTIONS = ["Morning", "Midday", "Evening", "Before Bed", "With Food", "Empty Stomach", "After Meals"]
FREQUENCY_WORD_COUNTS = {
    "once": 1,
    "one": 1,
    "twice": 2,
    "two": 2,
    "thrice": 3,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _custom_timing_parts(extra):
    raw = str(extra or "").strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,;|\n]+", raw) if part.strip()]


def _timing_from_choices(choices, extra):
    parts = [str(x).strip() for x in (choices or []) if str(x).strip()]
    parts.extend(_custom_timing_parts(extra))
    return ", ".join(parts)


def _timing_count(choices, extra):
    return len([x for x in (choices or []) if str(x).strip()]) + len(_custom_timing_parts(extra))


def _frequency_expected_count(frequency):
    raw = str(frequency or "").strip().lower()
    if not raw:
        return None

    number_match = re.search(r"\b(\d{1,2})\s*(?:x|time|times)\b", raw)
    if number_match:
        try:
            return int(number_match.group(1))
        except Exception:
            return None

    x_match = re.search(r"\b(\d{1,2})\s*x\b", raw)
    if x_match:
        try:
            return int(x_match.group(1))
        except Exception:
            return None

    for word, count in FREQUENCY_WORD_COUNTS.items():
        if re.search(rf"\b{re.escape(word)}\b", raw):
            return count

    return None


def _frequency_timing_error(frequency, choices, extra):
    expected = _frequency_expected_count(frequency)
    if expected is None:
        return ""
    actual = _timing_count(choices, extra)
    if actual != expected:
        return f"Frequency indicates {expected} timing(s), but {actual} timing(s) were selected/entered. Please align Frequency and Timing before saving."
    return ""


def _chips(text):
    parts = [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]
    if not parts:
        return "<span class='hm-sup-mini'>As advised</span>"
    return "".join([f"<span class='hm-sup-mini'>{_esc(p)}</span>" for p in parts])


def _split_timing_for_edit(text):
    parts = [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]
    option_lookup = {opt.lower(): opt for opt in TIMING_OPTIONS}
    selected = []
    extra_parts = []
    for part in parts:
        matched = option_lookup.get(part.lower())
        if matched:
            if matched not in selected:
                selected.append(matched)
        else:
            extra_parts.append(part)
    return selected, ", ".join(extra_parts)


def _safe_date_value(value):
    raw = str(value or "").strip()
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(raw[:10])
    except Exception:
        return date.today()


def _safe_optional_date_value(value, default_date=None):
    raw = str(value or "").strip()
    if not raw:
        return default_date or date.today()
    try:
        return date.fromisoformat(raw[:10])
    except Exception:
        return default_date or date.today()


def _card(row, stopped=False):
    status_cls = " stopped" if stopped else ""
    end_line = f"<div class='hm-sup-dose'>End date: {_esc(row.get('end_date') or 'NA')}</div>"
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
        <div class='hm-sup-dose'>Start date: {_esc(row.get('start_date') or 'As advised')}</div>
        {end_line}
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
.hm-sup-na{font-size:.78rem;font-weight:820;color:#64748B;background:#FFFDF8;border:1px dashed #D9C28F;border-radius:12px;padding:.55rem;margin-top:.18rem;}
@media(max-width:850px){.hm-sup-layout{grid-template-columns:1fr}.hm-sup-card{grid-template-columns:34px 1fr}.hm-sup-card>div:last-child{grid-column:2}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-page'>", unsafe_allow_html=True)

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

                dose_col, freq_col = st.columns(2)
                with dose_col:
                    e_dosage = st.text_input("Dosage", value=row.get("dosage", ""), key=f"edit_dose_{row['id']}")
                with freq_col:
                    e_frequency = st.text_input("Frequency", value=row.get("frequency", ""), key=f"edit_freq_{row['id']}")

                edit_timing_default, edit_custom_default = _split_timing_for_edit(row.get("timing", ""))
                timing_col, add_timing_col = st.columns(2)
                with timing_col:
                    e_timing_options = st.multiselect(
                        "Timing",
                        TIMING_OPTIONS,
                        default=edit_timing_default,
                        key=f"edit_time_choices_{row['id']}",
                    )
                with add_timing_col:
                    e_custom_timing = st.text_input("Additional Timing", value=edit_custom_default, key=f"edit_time_extra_{row['id']}")

                d1, d2 = st.columns(2)
                with d1:
                    e_start = st.date_input("Start Date", value=_safe_date_value(row.get("start_date", "")), key=f"edit_start_{row['id']}")
                with d2:
                    existing_end = str(row.get("end_date") or "").strip()
                    set_e_end = st.checkbox("Set End Date", value=bool(existing_end), key=f"edit_end_enabled_{row['id']}")
                    if set_e_end:
                        e_end = st.date_input("End Date", value=_safe_optional_date_value(existing_end, e_start), key=f"edit_end_{row['id']}")
                    else:
                        st.markdown("<div class='hm-sup-na'>End Date: NA</div>", unsafe_allow_html=True)
                        e_end = None

                n1, n2 = st.columns(2)
                with n1:
                    e_instructions = st.text_area("Member Instructions", value=row.get("instructions", ""), key=f"edit_inst_{row['id']}")
                with n2:
                    e_notes = st.text_area("Admin Notes", value=row.get("admin_notes", ""), key=f"edit_notes_{row['id']}")

                save_col, cancel_col = st.columns(2)
                with save_col:
                    save_edit = st.form_submit_button("Save Changes", use_container_width=True)
                with cancel_col:
                    cancel_edit = st.form_submit_button("Cancel", use_container_width=True)
                if save_edit:
                    timing_error = _frequency_timing_error(e_frequency, e_timing_options, e_custom_timing)
                    if timing_error:
                        st.error(timing_error)
                    elif e_end and e_end < e_start:
                        st.error("End Date cannot be earlier than Start Date.")
                    else:
                        try:
                            update_member_supplement(row["id"], {
                                "supplement_name": e_name,
                                "dosage": e_dosage,
                                "frequency": e_frequency,
                                "timing": _timing_from_choices(e_timing_options, e_custom_timing),
                                "start_date": e_start,
                                "end_date": e_end or "",
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

    history_key = f"hm_v1023a_history_open_{member_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = False
    history_label = f"{'-' if st.session_state[history_key] else '+'} Stopped Supplements / History ({counts['stopped']})"
    if st.button(history_label, key=f"hm_v1023a_history_toggle_{member_id}", use_container_width=True):
        st.session_state[history_key] = not st.session_state[history_key]
        st.rerun()
    if st.session_state[history_key]:
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
            TIMING_OPTIONS,
            default=[],
        )
        custom_timing = st.text_input("Additional Timing", placeholder="Optional custom timing. Use commas for multiple custom timings.")
        start_date = st.date_input("Start Date", value=date.today())
        set_end_date = st.checkbox("Set End Date", value=False, key="hm_v1023a_add_end_enabled")
        if set_end_date:
            end_date = st.date_input("End Date", value=start_date, key="hm_v1023a_add_end_date")
        else:
            st.markdown("<div class='hm-sup-na'>End Date: NA</div>", unsafe_allow_html=True)
            end_date = None
        note1, note2 = st.columns(2)
        with note1:
            instructions = st.text_area("Member Instructions", placeholder="What the member should follow")
        with note2:
            admin_notes = st.text_area("Admin Notes", placeholder="Internal note; visible only to admin")
        submitted = st.form_submit_button("Add & Publish to Member", use_container_width=True)
        if submitted:
            timing_error = _frequency_timing_error(frequency, timing_options, custom_timing)
            if timing_error:
                st.error(timing_error)
            elif end_date and end_date < start_date:
                st.error("End Date cannot be earlier than Start Date.")
            else:
                try:
                    add_member_supplement(member_id, {
                        "supplement_name": name,
                        "dosage": dosage,
                        "frequency": frequency,
                        "timing": _timing_from_choices(timing_options, custom_timing),
                        "start_date": start_date,
                        "end_date": end_date or "",
                        "instructions": instructions,
                        "admin_notes": admin_notes,
                    }, actor_id=_actor_id())
                    st.success("Supplement added and published to this member's active regimen.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Supplement Management", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.3A: Admin Supplement Management with persistent member-specific publishing.
# UX layout update: Admin info messages removed; Edit form aligns Dosage/Frequency and Timing/Additional Timing side by side.
