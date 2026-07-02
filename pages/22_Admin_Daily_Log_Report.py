from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

import components.ui_common as ui_common
from components.current_build import apply_current_build
from components.db import (
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    get_daily_log_supervision_notes,
    get_meal_type_repository,
    list_members,
    queue_daily_log_reminder,
)
from components.guards import require_admin
from components.nutritionist_notes_h9a4 import create_structured_nutritionist_note, notes_for_journal_date
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    compact_topbar,
    format_local_ts,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    stat_grid,
    utility_logout_bar,
)

apply_current_build(ui_common)

st.set_page_config(page_title="Daily Food Journal Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

st.markdown(
    """
<style>
.hm-guidance-boundary{border:1px solid rgba(6,78,59,.18);background:rgba(236,253,245,.45);border-radius:18px;padding:14px 16px;margin:.15rem 0 .85rem 0;}
.hm-guidance-boundary strong{color:#064E3B;}
.hm-dfjr-no-data-box{background:#E9EEF5;border-radius:10px;padding:16px 18px;color:#334155;margin:.2rem 0 .9rem 0;}
.hm-full-day-black-row{background:#111827;border-radius:8px;height:12px;margin:.75rem 0 .85rem 0;width:100%;}
</style>
""",
    unsafe_allow_html=True,
)


def _safe_members():
    people = list_members()
    members = [m for m in people if str(m.get("role", "member") or "member").strip().lower() == "member"]
    if members:
        return members
    return [
        m
        for m in people
        if str(m.get("id", "")).strip().lower() not in {"admin", "admin001"}
        and str(m.get("email", "")).strip().lower() != "admin@healthyme.local"
    ]


def _meal_keys_for_day(day):
    keys = [(r["key"], r["label"]) for r in get_meal_type_repository()]
    known = {k for k, _label in keys}
    for key, meal in (day.get("meals", {}) or {}).items():
        if key not in known:
            keys.append((key, meal.get("label", key.replace("_", " ").title())))
    return keys


def _structured_notes_text(member_id, log_date):
    values = []
    for row in notes_for_journal_date(member_id, log_date, include_archived=True):
        subject = str(row.get("subject", "Nutritionist Note") or "Nutritionist Note").strip()
        note = str(row.get("note_text", "") or "").strip()
        note_type = str(row.get("note_type", "") or "").replace("_", " ").title()
        if note:
            values.append(f"{subject} ({note_type}): {note}")
    return " | ".join(values)


def _legacy_notes_text(member_id, log_date):
    values = []
    for row in get_daily_log_supervision_notes(member_id, limit=20, log_date=log_date):
        note = str(row.get("note", "") or "").strip()
        if note:
            stamp = format_local_ts(row.get("ts", ""))
            values.append(f"{stamp} — {note}" if stamp else note)
    return " | ".join(values)


def _other_fluids_summary(items):
    rows = []
    for idx, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        fluid_type = item.get("type") or "Other Liquid"
        time_text = item.get("time") or ""
        quantity = item.get("quantity") or ""
        rows.append(f"{idx}. {fluid_type} | {time_text} | {quantity}")
    return "\n".join(rows) if rows else "—"


def _row_for_day(member_id, day):
    meals = day.get("meals", {}) or {}
    return {
        "Date": day.get("date", ""),
        "Breakfast": (meals.get("breakfast", {}) or {}).get("food", ""),
        "Lunch": (meals.get("lunch", {}) or {}).get("food", ""),
        "Dinner": (meals.get("dinner", {}) or {}).get("food", ""),
        "Water": day.get("water_litres", ""),
        "Other Fluids": _other_fluids_summary(day.get("other_fluids", [])),
        "Activity": day.get("physical_activity", ""),
        "Poop Rounds": day.get("poop_rounds", ""),
        "Poop Timings": ", ".join([str(x) for x in (day.get("poop_timings", []) or []) if str(x).strip()]),
        "Feeling After Poop": day.get("feeling_after_poop", ""),
        "Notes": day.get("notes", ""),
        "Nutritionist Guidance": _structured_notes_text(member_id, day.get("date", "")) or _legacy_notes_text(member_id, day.get("date", "")),
    }


def _build_excel(member, days):
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Food Journal"
    ws.append(["Member", member.get("name", ""), "Email", member.get("email", "")])
    ws.append([])
    rows = [_row_for_day(member.get("id", ""), d) for d in days]
    headers = list(rows[0].keys()) if rows else list(_row_for_day(member.get("id", ""), {}).keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    header_fill = PatternFill("solid", fgColor="064E3B")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style="thin", color="E9DFCC"), right=Side(style="thin", color="E9DFCC"), top=Side(style="thin", color="E9DFCC"), bottom=Side(style="thin", color="E9DFCC"))
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border
            if cell.row == 3:
                cell.fill = header_fill
                cell.font = header_font
    for col in range(1, ws.max_column + 1):
        ws.column_dimensions[ws.cell(row=3, column=col).column_letter].width = 24
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


compact_topbar("Daily Food Journal Report", "", "Admin report")

members = _safe_members()
if not members:
    st.info("No members available.")
    st.stop()

options = [f"{m.get('id','')} — {m.get('name','Member')} — {m.get('email','')}" for m in members]
default_member = st.session_state.get("selected_daily_log_member_id") or st.session_state.get("selected_member_id")
default_index = next((idx for idx, opt in enumerate(options) if default_member and opt.startswith(f"{default_member} —")), 0)

member_selector_col, member_hint_col = st.columns([2, 3])
with member_selector_col:
    selected = st.selectbox("Select member", options, index=default_index)
member_id = selected.split(" — ")[0]
member = next(m for m in members if str(m.get("id", "")) == member_id)
days = get_daily_food_journal_days(member_id)
available_dates = [d.get("date") for d in days if d.get("date")]
default_date_str = available_dates[0] if available_dates else str(date.today())
try:
    default_date_obj = date.fromisoformat(default_date_str)
except Exception:
    default_date_obj = date.today()
with member_hint_col:
    st.caption("H9A.4: Nutritionist Guidance below is member-level guidance. It can be linked to one day, multiple days, or the sent date for general guidance.")

card_start()
st.subheader("Nutritionist Guidance")
st.markdown(
    "<div class='hm-guidance-boundary'><strong>Independent guidance block:</strong> this section is not governed by the Food Journal review date below. Choose whether the guidance applies to one date, a date range, or general guidance.</div>",
    unsafe_allow_html=True,
)
with st.form("h9a4_daily_report_structured_note", clear_on_submit=True):
    note_type_label = st.radio("Guidance Type", ["Single Day", "Date Range", "General Guidance"], horizontal=True)
    note_type = {"Single Day": "single_day", "Date Range": "date_range", "General Guidance": "general"}[note_type_label]
    c1, c2 = st.columns(2)
    from_date = None
    to_date = None
    if note_type == "single_day":
        with c1:
            from_date = st.date_input("Note Date", value=default_date_obj, key="h9a4_single_day_note_date")
        to_date = from_date
        with c2:
            st.caption("This note will be linked only to the selected note date.")
    elif note_type == "date_range":
        with c1:
            from_date = st.date_input("From Date", value=default_date_obj, key="h9a4_range_from_date")
        with c2:
            to_date = st.date_input("To Date", value=default_date_obj, key="h9a4_range_to_date")
    else:
        st.caption("General guidance is linked to the sent date and can later appear under that sent-date context.")
    subject = st.text_input("Subject", value="Nutritionist Note")
    note_text = st.text_area("Nutritionist Note", placeholder="Example: Water intake was low across these days. Please increase water before lunch and dinner.", height=120)
    submitted = st.form_submit_button("Publish / Send Nutritionist Guidance", use_container_width=True)
if submitted:
    try:
        note = create_structured_nutritionist_note(member_id=member_id, member_name=member.get("name", ""), note_type=note_type, subject=subject, note_text=note_text, from_date=from_date, to_date=to_date, created_by=st.session_state.get("user_email") or st.session_state.get("oidc_email") or "admin")
        st.success(f"Published guidance {note.get('id')} with {len(note.get('related_dates', []))} linked date(s).")
    except Exception as exc:
        st.error(str(exc))
card_end()

card_start()
st.subheader("Food Journal Review")
review_col_1, review_col_2 = st.columns(2)
with review_col_1:
    selected_date_obj = st.date_input("Select food log date for review", value=default_date_obj)
selected_date = selected_date_obj.isoformat() if hasattr(selected_date_obj, "isoformat") else str(selected_date_obj)
with review_col_2:
    st.caption("This date selector controls the journal review below. It does not control whether guidance can be one-day, multi-day, or general.")
selected_day = get_daily_food_journal_day(member_id, selected_date) or next((d for d in days if d.get("date") == selected_date), {"date": selected_date, "meals": {}})
structured_date_notes = notes_for_journal_date(member_id, selected_date, include_archived=True)
legacy_date_notes = get_daily_log_supervision_notes(member_id, limit=20, log_date=selected_date)
stat_grid([
    {"label": "Member", "value": member.get("name", ""), "note": "Selected member"},
    {"label": "Saved Days", "value": len(days), "note": "Full-day food logs"},
    {"label": "Review Date", "value": selected_date, "note": "Journal date below"},
    {"label": "Linked Guidance", "value": len(structured_date_notes) + len(legacy_date_notes), "note": "For review date"},
])
card_end()

card_start()
st.subheader("All saved days")
if not days:
    st.markdown("<div class='hm-dfjr-no-data-box'>No daily food logs available.</div>", unsafe_allow_html=True)
else:
    rows = [_row_for_day(member_id, d) for d in days]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button("Download Daily Food Journal Excel", data=_build_excel(member, days), file_name=f"{member.get('name','member').replace(' ','_')}_daily_food_journal.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
card_end()

card_start()
st.subheader(f"Food journal for {selected_date}")
if not selected_day or not selected_day.get("meals"):
    st.markdown("<div class='hm-dfjr-no-data-box'>No food journal available for this date.</div>", unsafe_allow_html=True)
else:
    meal_rows = []
    for key, label in _meal_keys_for_day(selected_day):
        meal = (selected_day.get("meals", {}) or {}).get(key, {}) or {}
        meal_rows.append({"Meal Type": label, "Time": meal.get("time", ""), "Food": meal.get("food", ""), "Portion Size": meal.get("portion_size", ""), "Mood/Energy": meal.get("mood_energy", "")})
    st.dataframe(pd.DataFrame(meal_rows), use_container_width=True, hide_index=True)
    st.markdown("#### Full-day details")
    st.markdown(f"**Water Intake:** {selected_day.get('water_litres','') or '-'}")
    st.markdown(f"**Other Fluids:** {_other_fluids_summary(selected_day.get('other_fluids', []))}")
    st.markdown(f"**Physical Activity:** {selected_day.get('physical_activity','') or '-'}")
    st.markdown(f"**Poop rounds:** {selected_day.get('poop_rounds','') or '-'}")
    timings = selected_day.get("poop_timings", []) or []
    st.markdown(f"**Poop timings:** {', '.join([str(x) for x in timings if str(x).strip()]) or '-'}")
    st.markdown(f"**Feeling after poop:** {selected_day.get('feeling_after_poop','') or '-'}")
    st.markdown(f"**Overall Notes:** {selected_day.get('notes','') or '-'}")
    st.markdown("<div class='hm-full-day-black-row'></div>", unsafe_allow_html=True)
card_end()

card_start()
st.subheader(f"Guidance linked to {selected_date}")
if structured_date_notes:
    for row in structured_date_notes:
        st.markdown(f"**{row.get('subject', 'Nutritionist Note')}**")
        st.caption(f"Type: {row.get('note_type')} | From: {row.get('from_date')} | To: {row.get('to_date')} | Archived: {bool(row.get('member_archived', False))}")
        st.write(row.get("note_text", ""))
        st.divider()
elif legacy_date_notes:
    st.caption("Legacy date-specific notes")
    for row in legacy_date_notes:
        st.markdown(f"**{format_local_ts(row.get('ts',''))}**")
        st.write(row.get("note", ""))
else:
    st.caption("No structured guidance is linked to this review date yet.")
if st.button("Send gentle Daily Log reminder", type="secondary", use_container_width=True):
    queue_daily_log_reminder(member_id)
    st.success("Reminder queued for the member and marked for email notification.")
card_end()

render_page_nav("Daily Food Journal Report", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
