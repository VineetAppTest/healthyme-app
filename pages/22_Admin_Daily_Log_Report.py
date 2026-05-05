import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import list_members, get_daily_logs

st.set_page_config(page_title="Daily Log Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

def build_excel(member, logs):
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Logs"
    headers = ["Timestamp", "Member", "Email", "Food Log", "Water ML", "Sleep Hours", "Exercise Done", "Exercise Notes"]
    ws.append(headers)
    for item in logs:
        ws.append([
            item.get("timestamp", ""),
            member.get("name", ""),
            member.get("email", ""),
            item.get("food_log", ""),
            item.get("water_ml", ""),
            item.get("sleep_hours", ""),
            item.get("exercise_done", ""),
            item.get("exercise_notes", ""),
        ])
    header_fill = PatternFill("solid", fgColor="064E3B")
    header_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="E9DFCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border
            if cell.row == 1:
                cell.fill = header_fill
                cell.font = header_font
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 14), 55)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()

topbar("Daily Log Report", "View and download member daily logs.", "Admin report")

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

options = [f"{m['id']} — {m['name']} — {m['email']}" for m in members]
selected = st.selectbox("Select member", options)
member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
logs = get_daily_logs(member_id)

stat_grid([
    {"label": "Member", "value": member.get("name", ""), "note": "Selected member"},
    {"label": "Logs", "value": len(logs), "note": "Daily entries"},
    {"label": "Latest", "value": logs[-1].get("timestamp", "-") if logs else "-", "note": "Last saved"},
    {"label": "Download", "value": "Ready" if logs else "No Data", "note": "Excel report"},
])

card_start()
st.subheader("Daily Log Entries")
if not logs:
    st.info("No daily logs available for this member.")
else:
    df = pd.DataFrame(logs)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Daily Log Report Excel",
        data=build_excel(member, logs),
        file_name=f"{member.get('name','member').replace(' ','_')}_daily_log_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")