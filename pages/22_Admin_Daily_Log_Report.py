import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_build_text_v15, render_page_nav
from components.db import (
    list_members,
    get_daily_logs,
    queue_daily_log_reminder,
    save_daily_log_supervision_note,
    get_daily_log_supervision_notes,
)

st.set_page_config(page_title="Daily Food Journal Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
render_page_nav("Daily Logs", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")

HEADERS = [
    "Date",
    "Time",
    "Meal Type",
    "Food",
    "Water",
    "Portion Size",
    "Mood/Energy",
    "Physical activity Time of the day and duration",
    "Poop Rounds and feeling after poop",
    "Notes",
    "Supervision Notes",
]

def normalize_daily_log(item):
    return {
        "Date": item.get("date", ""),
        "Time": item.get("time", item.get("timestamp", "")),
        "Meal Type": item.get("meal_type", ""),
        "Food": item.get("food", item.get("food_log", "")),
        "Water": item.get("water", item.get("water_ml", "")),
        "Portion Size": item.get("portion_size", ""),
        "Mood/Energy": item.get("mood_energy", ""),
        "Physical activity Time of the day and duration": item.get("physical_activity", item.get("exercise_notes", "")),
        "Poop Rounds and feeling after poop": item.get("poop", ""),
        "Notes": item.get("notes", ""),
        "Supervision Notes": item.get("supervision_notes", ""),
    }

def build_excel(member, logs, supervision_notes):
    wb = Workbook()
    ws = wb.active
    ws.title = "Food Journal"
    ws.append(["Member", member.get("name", ""), "Email", member.get("email", "")])
    ws.append([])
    ws.append(HEADERS)
    for item in logs:
        row = normalize_daily_log(item)
        ws.append([row.get(h, "") for h in HEADERS])

    if supervision_notes:
        ws.append([])
        ws.append(["Supervision Notes"])
        ws.append(["Timestamp", "Note"])
        for n in supervision_notes:
            ws.append([n.get("ts", ""), n.get("note", "")])

    header_fill = PatternFill("solid", fgColor="064E3B")
    sub_fill = PatternFill("solid", fgColor="FFF7E6")
    header_font = Font(color="FFFFFF", bold=True)
    sub_font = Font(color="064E3B", bold=True)
    thin = Side(style="thin", color="E9DFCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border
            if cell.row == 3:
                cell.fill = header_fill
                cell.font = header_font
            if cell.value == "Supervision Notes":
                cell.fill = sub_fill
                cell.font = sub_font

    widths = {
        "A": 14, "B": 18, "C": 18, "D": 38, "E": 18, "F": 18,
        "G": 18, "H": 36, "I": 34, "J": 30, "K": 38
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()

topbar("Daily Food Journal Report", "View food journal entries and add supervision notes for members.", "Admin report")

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

options = [f"{m['id']} — {m['name']} — {m['email']}" for m in members]
default_member = st.session_state.get("selected_daily_log_member_id") or st.session_state.get("selected_member_id")
default_index = 0
if default_member:
    for idx, opt in enumerate(options):
        if opt.startswith(f"{default_member} —"):
            default_index = idx
            break

selected = st.selectbox("Select member", options, index=default_index)
member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
logs = get_daily_logs(member_id)
supervision_notes = get_daily_log_supervision_notes(member_id, limit=20)

food_logs = [x for x in logs if x.get("log_type") == "food_journal" or any(k in x for k in ["meal_type", "food", "portion_size", "mood_energy", "physical_activity", "poop"])]

stat_grid([
    {"label": "Member", "value": member.get("name", ""), "note": "Selected member"},
    {"label": "Food Entries", "value": len(food_logs), "note": "Food journal rows"},
    {"label": "Supervision Notes", "value": len(supervision_notes), "note": "Admin comments"},
    {"label": "Latest", "value": food_logs[-1].get("date", "-") if food_logs else "-", "note": "Last entry"},
])

card_start()
st.subheader("Food Journal Entries")
if not food_logs:
    st.info("No food journal entries available for this member.")
else:
    rows = [normalize_daily_log(x) for x in food_logs]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Food Journal Report Excel",
        data=build_excel(member, food_logs, supervision_notes),
        file_name=f"{member.get('name','member').replace(' ','_')}_food_journal_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
card_end()

card_start()
st.subheader("Supervision note")
st.caption("This note will show under the member's food log and will also be queued as an app/email notification.")
note = st.text_area("Write supervision note for this member", placeholder="Example: Please mention water intake and poop timing in tomorrow's log.")
if st.button("Save Supervision Note / Notify Member", type="primary", use_container_width=True):
    if not note.strip():
        st.error("Please write a supervision note before saving.")
    else:
        save_daily_log_supervision_note(member_id, note.strip(), actor_id=st.session_state.get("user_id", "admin"))
        st.success("Supervision note saved and notification queued for member.")
        st.rerun()

if supervision_notes:
    st.markdown("#### Recent supervision notes")
    for n in supervision_notes[:5]:
        st.markdown(
            f"""
            <div class='info-banner'>
              <b>{n.get('ts','')}</b><br>
              {n.get('note','')}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div class='hm-v15-reminder-note'><b>Gentle reminder</b><br>Send a reminder to fill Daily Log.</div>", unsafe_allow_html=True)
if st.button("Send gentle Daily Log reminder", type="secondary", use_container_width=True, help="Queues a reminder in the app and marks it for email delivery when production email service is connected."):
    queue_daily_log_reminder(member_id)
    st.success("Reminder queued for the member and marked for email notification.")
card_end()

render_page_nav("Daily Logs", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
