import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.db import list_members
from components.nutritionist_notes_h9a4 import (
    create_structured_nutritionist_note,
    note_rows_for_admin,
    notes_for_journal_date,
)
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)

st.set_page_config(
    page_title="Nutritionist Notes Workbench",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Nutritionist Notes Workbench",
    "H9A.4 admin-aligned notes: single-day, multi-day and general guidance linked to Food Journal context.",
    "Admin Food Journal guidance",
)

members = [m for m in list_members() if m.get("role") == "member"]
member_options = {f"{m.get('name', 'Member')} — {m.get('email', '')}": m for m in members}

st.info(
    "Use this page to create Nutritionist Notes that Flutter can later show as active guidance, "
    "then preserve under the linked saved day or days after the member reads/archives them."
)

card_start()
st.subheader("Create Nutritionist Note")
if not member_options:
    st.warning("No member records found.")
else:
    with st.form("h9a4_structured_note_form", clear_on_submit=False):
        selected_label = st.selectbox("Member", list(member_options.keys()))
        member = member_options[selected_label]
        note_type_label = st.radio(
            "Note Type",
            ["Single Day", "Date Range", "General Guidance"],
            horizontal=True,
        )
        note_type = {
            "Single Day": "single_day",
            "Date Range": "date_range",
            "General Guidance": "general",
        }[note_type_label]

        c1, c2 = st.columns(2)
        from_date = None
        to_date = None
        if note_type == "single_day":
            with c1:
                from_date = st.date_input("Note Date")
            to_date = from_date
        elif note_type == "date_range":
            with c1:
                from_date = st.date_input("From Date")
            with c2:
                to_date = st.date_input("To Date")
        else:
            st.caption("General guidance is linked to the sent date and can later appear under that sent-date context.")

        subject = st.text_input("Subject", value="Nutritionist Note")
        note_text = st.text_area("Nutritionist Note", height=140)
        submitted = st.form_submit_button("Publish / Send Note", use_container_width=True)

    if submitted:
        try:
            note = create_structured_nutritionist_note(
                member_id=member.get("id", ""),
                member_name=member.get("name", ""),
                note_type=note_type,
                subject=subject,
                note_text=note_text,
                from_date=from_date,
                to_date=to_date,
                created_by=st.session_state.get("user_email") or st.session_state.get("oidc_email") or "admin",
            )
            st.success(f"Published note {note.get('id')} with {len(note.get('related_dates', []))} linked date(s).")
        except Exception as exc:
            st.error(str(exc))
card_end()

card_start()
st.subheader("Notes Register")
selected_filter = st.selectbox("Filter by member", ["All members", *list(member_options.keys())]) if member_options else "All members"
filter_member_id = None if selected_filter == "All members" else member_options[selected_filter].get("id")
rows = note_rows_for_admin(filter_member_id)
if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download notes register CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="healthyme_h9a4_nutritionist_notes_register.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.caption("No structured notes created yet.")
card_end()

card_start()
st.subheader("Date Correlation Preview")
st.caption("Select a member and date to preview which Nutritionist Notes will appear under that saved day.")
if member_options:
    preview_label = st.selectbox("Preview Member", list(member_options.keys()), key="preview_member")
    preview_member = member_options[preview_label]
    preview_date = st.date_input("Preview Journal Date")
    preview_rows = notes_for_journal_date(preview_member.get("id", ""), preview_date, include_archived=True)
    if preview_rows:
        for note in preview_rows:
            st.markdown(f"**{note.get('subject', 'Nutritionist Note')}**  ")
            st.caption(f"Type: {note.get('note_type')} | From: {note.get('from_date')} | To: {note.get('to_date')}")
            st.write(note.get("note_text", ""))
            st.divider()
    else:
        st.caption("No note is linked to this date yet.")
card_end()

card_start()
st.subheader("H9A.4 Admin ↔ Member Contract")
st.markdown(
    """
- Admin creates the note and defines whether it is for one day, a date range, or general guidance.
- The note is stored with `related_dates` so Flutter can show it under the correct saved day/days.
- New/unarchived notes are treated as active member guidance.
- After the member archives a note, it should disappear from active guidance but remain visible under linked saved day/days.
- General guidance is linked to the sent date.
"""
)
card_end()

render_page_nav(
    "Nutritionist Notes Workbench",
    back_page="pages/22_Admin_Daily_Log_Report.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
