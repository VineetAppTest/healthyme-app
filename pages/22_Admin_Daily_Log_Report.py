import streamlit as st
from datetime import date
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_page_nav, format_local_ts, render_back_to_top, compact_topbar, render_context_selector_header
from components.db import (
    list_members,
    get_daily_food_journal_days,
    get_daily_food_journal_day,
    queue_daily_log_reminder,
    save_daily_log_supervision_note,
    get_daily_log_supervision_notes,
    get_meal_type_repository,
    get_daily_log_notes_by_date,
    get_latest_daily_log_note_for_date,
)

st.set_page_config(page_title="Daily Food Journal Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()
render_page_nav("Daily Logs", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")

MEAL_KEYS = [(r["key"], r["label"]) for r in get_meal_type_repository()]


def display_date(d):
    try:
        return date.fromisoformat(str(d)).strftime("%d/%m/%Y")
    except Exception:
        return str(d or "")

def meal_text(meal):
    meal = meal or {}
    tm = str(meal.get("time", "")).strip()
    food = str(meal.get("food", "")).strip()
    if tm and food:
        return f"{tm}: {food}"
    return food

def labelled_poop_timings(day):
    timings = [str(x or "").strip() for x in (day.get("poop_timings", []) or []) if str(x or "").strip()]
    return ", ".join([f"Poop Timing {idx + 1}: {val}" for idx, val in enumerate(timings)])

def meal_keys_for_day(day):
    preferred = ["breakfast", "lunch", "evening_snack", "dinner", "bedtime"]
    configured = {k: ("Snacking" if str(label).lower() == "other" else label) for k, label in MEAL_KEYS}
    keys = [(k, configured[k]) for k in preferred if k in configured]
    known = {k for k, _label in keys}
    for k, label in MEAL_KEYS:
        if k not in known and k != "other":
            keys.append((k, "Snacking" if str(label).lower() == "other" else label))
            known.add(k)
    other_count = 0
    for k, meal in (day.get("meals", {}) or {}).items():
        if k in known:
            continue
        if str(k).startswith("other_"):
            other_count += 1
            label = "Snacking" if other_count == 1 else f"Snacking {other_count - 1}"
        else:
            label = meal.get("label", k.replace("_", " ").title())
            if str(label).lower().startswith("other"):
                other_count += 1
                label = "Snacking" if other_count == 1 else f"Snacking {other_count - 1}"
        keys.append((k, label))
        known.add(k)
    return keys

def flatten_day(day, supervision_notes=None):
    base = {
        "Date": display_date(day.get("date", "")),
        "Water": day.get("water_litres", ""),
        "Physical Activity": day.get("physical_activity", ""),
        "Poop Rounds": day.get("poop_rounds", ""),
        "Poop Timings": labelled_poop_timings(day),
        "Feeling After Poop": day.get("feeling_after_poop", ""),
        "Overall Notes": day.get("notes", ""),
        "Nutritionist Notes": " | ".join([n.get("note", "") for n in (supervision_notes or [])]),
    }
    meals = day.get("meals", {}) or {}
    for key, label in meal_keys_for_day(day):
        meal = meals.get(key, {}) or {}
        base[f"{label}"] = meal_text(meal)
        base[f"{label} Time"] = meal.get("time", "")
        base[f"{label} Food"] = meal.get("food", "")
        base[f"{label} Portion"] = meal.get("portion_size", "")
        base[f"{label} Mood/Energy"] = meal.get("mood_energy", "")
    return base

def build_excel(member, days):
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Food Journal"
    ws.append(["Member", member.get("name", ""), "Email", member.get("email", "")])
    ws.append([])
    # Build headers using all saved days so dynamic Other sections are included.
    headers = []
    for d in days:
        for h in flatten_day(d).keys():
            if h not in headers:
                headers.append(h)
    if not headers:
        headers = list(flatten_day({}).keys())
    ws.append(headers)
    for day in days:
        notes = get_daily_log_supervision_notes(member.get("id"), limit=50, log_date=day.get("date"))
        row = flatten_day(day, notes)
        ws.append([row.get(h, "") for h in headers])

    header_fill = PatternFill("solid", fgColor="064E3B")
    header_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="E9DFCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border
            if cell.row == 3:
                cell.fill = header_fill
                cell.font = header_font

    for col in range(1, ws.max_column + 1):
        letter = ws.cell(row=3, column=col).column_letter
        ws.column_dimensions[letter].width = 24 if col > 1 else 14

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()

compact_topbar("Daily Food Journal Report", "", "Admin report")

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

card_start()
st.markdown("### 📋 Review Context")
st.caption("This selection controls the member and food-log date visible on the page.")
selector_col_1, selector_col_2 = st.columns(2)
with selector_col_1:
    selected = st.selectbox("👤 Select member", options, index=default_index)

member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
days = get_daily_food_journal_days(member_id)
available_dates = [d.get("date") for d in days if d.get("date")]

with selector_col_2:
    selected_date = st.selectbox("📅 Select food log date for review / note", available_dates or [str(date.today())], format_func=display_date)
card_end()
render_context_selector_header(
    "Currently Reviewing",
    [("Member", member.get("name", "")), ("Food Log Date", display_date(selected_date))],
    "Changing these values changes the report, note area, and saved-day view below.",
)

selected_day = get_daily_food_journal_day(member_id, selected_date) or next((d for d in days if d.get("date") == selected_date), {"date": selected_date, "meals": {}})
date_notes = get_daily_log_supervision_notes(member_id, limit=20, log_date=selected_date)

stat_grid([
    {"label": "Member", "value": member.get("name", ""), "note": "Selected member"},
    {"label": "Saved Days", "value": len(days), "note": "Full-day food logs"},
    {"label": "Selected Date", "value": display_date(selected_date), "note": "Current review"},
    {"label": "Notes", "value": len(date_notes), "note": "For selected day"},
])

card_start()
st.subheader(f"Food journal for {display_date(selected_date)}")
if not selected_day or not selected_day.get("meals"):
    st.info("No food journal available for this date.")
else:
    meal_rows = []
    for key, label in meal_keys_for_day(selected_day):
        meal = (selected_day.get("meals", {}) or {}).get(key, {}) or {}
        meal_rows.append({
            "Meal Type": label,
            "Time": meal.get("time", ""),
            "Food": meal.get("food", ""),
                        "Portion Size": meal.get("portion_size", ""),
            "Mood/Energy": meal.get("mood_energy", ""),
        })
    st.dataframe(meal_rows, use_container_width=True, hide_index=True)
    st.markdown("#### Full-day details")
    st.markdown(f"**Water Intake:** {selected_day.get('water_litres','') or '-'}")
    st.markdown(f"**Physical Activity:** {selected_day.get('physical_activity','') or '-'}")
    st.markdown(f"**Poop rounds:** {selected_day.get('poop_rounds','') or '-'}")
    st.markdown(f"**Poop timings:** {labelled_poop_timings(selected_day) or '-'}")
    st.markdown(f"**Feeling after poop:** {selected_day.get('feeling_after_poop','') or '-'}")
    st.markdown(f"**Overall Notes:** {selected_day.get('notes','') or '-'}")

    st.download_button(
        "Download Daily Food Journal Excel",
        data=build_excel(member, days),
        file_name=f"{member.get('name','member').replace(' ','_')}_daily_food_journal.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
card_end()

card_start()
st.subheader(f"Nutritionist note for {display_date(selected_date)}")
note = st.text_area("Nutritionist note", placeholder="Example: Please add water quantity for lunch and dinner tomorrow.")
if st.button("Save Supervision Note / Notify Member", type="primary", use_container_width=True):
    if not note.strip():
        st.error("Please write a nutritionist note before saving.")
    else:
        save_daily_log_supervision_note(member_id, note.strip(), actor_id=st.session_state.get("user_id", "admin"), log_date=selected_date)
        st.success("Nutritionist note saved. Member notification is now visible on Member Home and queued for email.")
        st.rerun()

if date_notes:
    st.markdown("#### Notes for this day")
    for n in date_notes[:8]:
        st.markdown(
            f"""
            <div class='info-banner'>
              <b>{format_local_ts(n.get('ts',''))}</b><br>
              {n.get('note','')}
            </div>
            """,
            unsafe_allow_html=True,
        )

if st.button("Send gentle Daily Log reminder", type="secondary", use_container_width=True):
    queue_daily_log_reminder(member_id)
    st.success("Reminder queued for the member and marked for email notification.")
card_end()

card_start()
st.subheader("All saved days")
if not days:
    st.info("No daily food logs available.")
else:
    rows = []
    for d in days:
        notes_for_day = get_daily_log_supervision_notes(member_id, limit=20, log_date=d.get("date"))
        latest_note = get_latest_daily_log_note_for_date(member_id, d.get("date", ""))
        latest_note_text = ""
        if latest_note:
            latest_note_text = f"{format_local_ts(latest_note.get('ts',''))} — {latest_note.get('note','')}"
        rows.append({
            "Date": display_date(d.get("date", "")),
            "Breakfast": meal_text((d.get("meals", {}).get("breakfast", {}) or {})),
            "Lunch": meal_text((d.get("meals", {}).get("lunch", {}) or {})),
            "Evening Snack": meal_text((d.get("meals", {}).get("evening_snack", {}) or {})),
            "Dinner": meal_text((d.get("meals", {}).get("dinner", {}) or {})),
            "Bedtime": meal_text((d.get("meals", {}).get("bedtime", {}) or {})),
            "Water": d.get("water_litres", ""),
            "Activity": d.get("physical_activity", ""),
            "Poop Rounds": d.get("poop_rounds", ""),
            "Poop Timings": labelled_poop_timings(d),
            "Feeling After Poop": d.get("feeling_after_poop", ""),
            "Notes": d.get("notes", ""),
            "Nutritionist Notes": latest_note_text,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
card_end()

render_page_nav("Daily Logs", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
