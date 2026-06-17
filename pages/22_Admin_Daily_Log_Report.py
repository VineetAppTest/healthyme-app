import streamlit as st
from datetime import date
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_page_nav, format_local_ts, render_back_to_top, compact_topbar
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
st.markdown("""
<style>
.hm-full-day-black-row{
  background:#111827;
  border-radius:8px;
  height:12px;
  margin:.75rem 0 .85rem 0;
  width:100%;
}
.hm-dfjr-empty-note{
  background:#E9EEF5;
  border-radius:10px;
  padding:14px 16px;
  margin:.35rem 0 1rem 0;
  color:#4B5563;
  width:100%;
  box-sizing:border-box;
}
.hm-dfjr-tight{
  margin-top:.15rem;
  margin-bottom:.35rem;
}

/* --- v92.10 Daily Food Journal Report Surface Fix --- */
.hm-dfjr-empty-note{
  background:#E9EEF5;
  border-radius:10px;
  padding:14px 16px;
  margin:.25rem 0 1.15rem 0;
  color:#334155;
  width:100%;
  box-sizing:border-box;
  min-height:52px;
  display:flex;
  align-items:center;
}
.hm-dfjr-note-wrap{
  margin-top:.2rem;
}
.hm-dfjr-note-wrap [data-testid="stWidgetLabel"],
.hm-dfjr-note-wrap label{
  display:none!important;
}
.hm-dfjr-note-wrap textarea{
  background:#E9EEF5!important;
  border:0!important;
  border-radius:10px!important;
  color:#102A43!important;
  min-height:96px!important;
}
.hm-dfjr-spacer{
  height:.45rem;
}


/* --- v92.12 Daily Food Journal Report Compact Surface Alignment --- */
.hm-dfjr-no-data-box{
  width:100%;
  box-sizing:border-box;
  background:#E9EEF5;
  border:0;
  border-radius:10px;
  min-height:92px;
  padding:16px 18px;
  color:#334155;
  display:flex;
  align-items:flex-start;
  justify-content:flex-start;
  margin:.2rem 0 .9rem 0;
}
.hm-dfjr-note-hard-wrap{
  width:100%;
  margin:.15rem 0 .55rem 0;
}
.hm-dfjr-note-hard-wrap [data-testid="stWidgetLabel"],
.hm-dfjr-note-hard-wrap label,
.hm-dfjr-note-hard-wrap p{
  display:none!important;
  visibility:hidden!important;
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.hm-dfjr-note-hard-wrap textarea{
  width:100%!important;
  box-sizing:border-box!important;
  background:#E9EEF5!important;
  border:0!important;
  border-radius:10px!important;
  min-height:92px!important;
  color:#102A43!important;
  padding:16px 18px!important;
  box-shadow:none!important;
}
.hm-dfjr-note-hard-wrap textarea::placeholder{
  color:#748094!important;
}
.hm-dfjr-tight{
  margin-top:.05rem;
  margin-bottom:.2rem;
}
.hm-dfjr-subsection{
  margin-top:1.1rem;
}
.hm-dfjr-section-gap{height:0;}

</style>
""", unsafe_allow_html=True)







# --------------------------------------------------------------------
# v97: Other Fluids report helpers
# --------------------------------------------------------------------
def normalise_other_fluids_v97(items):
    cleaned = []
    for item in (items or []):
        if not isinstance(item, dict):
            continue
        fluid_type = str(item.get("type", "") or "").strip()
        time_text = str(item.get("time", "") or "").strip()
        quantity = str(item.get("quantity", "") or "").strip()
        notes = str(item.get("notes", "") or "").strip()
        if fluid_type or time_text or quantity or notes:
            cleaned.append({
                "type": fluid_type,
                "time": time_text,
                "quantity": quantity,
                "notes": notes,
            })
    return cleaned

def _hm_v981_qty_text(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    cleaned = raw.replace("ML", "ml").replace("Ml", "ml").strip()
    cleaned = re.sub(r"\s*ml\s*$", "", cleaned, flags=re.I).strip()
    return cleaned

def _hm_v981_qty_display(value):
    cleaned = _hm_v981_qty_text(value)
    return f"{cleaned} ml" if cleaned else ""

def _hm_v1012_qty_number(value):
    cleaned = _hm_v981_qty_text(value)
    if not cleaned:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None

def _hm_v1012_qty_total_text(items):
    qty_texts = []
    qty_numbers = []
    all_numeric = True
    for item in items:
        cleaned = _hm_v981_qty_text(item.get("quantity"))
        if not cleaned:
            continue
        qty_texts.append(cleaned)
        number = _hm_v1012_qty_number(cleaned)
        if number is None:
            all_numeric = False
        else:
            qty_numbers.append(number)

    if qty_texts and all_numeric and len(qty_numbers) == len(qty_texts):
        total = sum(qty_numbers)
        if abs(total - int(total)) < 0.00001:
            return f"{int(total)} ml"
        return f"{total:.1f}".rstrip("0").rstrip(".") + " ml"

    if qty_texts:
        return " + ".join(qty_texts) + " ml"
    return "—"

def other_fluids_summary_v97(items):
    """v100.12 display format for Recent Saved Days and Admin report.

    Total Intake is summed per grouped fluid type.
    Example: 100 ml + 100 ml becomes Total Intake - 200 ml.
    """
    fluids = normalise_other_fluids_v97(items)
    if not fluids:
        return "—"

    grouped = []
    for item in fluids:
        fluid_type = item.get("type") or "Other Liquid"
        match = next((g for g in grouped if g["type"] == fluid_type), None)
        if not match:
            match = {"type": fluid_type, "items": []}
            grouped.append(match)
        match["items"].append(item)

    rows = []
    for idx, group in enumerate(grouped, start=1):
        total_text = _hm_v1012_qty_total_text(group["items"])

        timing_parts = []
        for item in group["items"]:
            time_text = str(item.get("time") or "").strip()
            qty_text = _hm_v981_qty_display(item.get("quantity"))
            if time_text and qty_text:
                timing_parts.append(f"{time_text} - {qty_text}")
            elif time_text:
                timing_parts.append(time_text)
            elif qty_text:
                timing_parts.append(qty_text)

        timing_text = "; ".join(timing_parts) if timing_parts else "—"
        rows.append(f"Other Liquid {idx}: Total Intake - {total_text} | {timing_text}")

    return "<br>".join(rows) if rows else "—"


MEAL_KEYS = [(r["key"], r["label"]) for r in get_meal_type_repository()]

def meal_keys_for_day(day):
    keys = list(MEAL_KEYS)
    known = {k for k, _label in keys}
    for k, meal in (day.get("meals", {}) or {}).items():
        if k not in known:
            keys.append((k, meal.get("label", k.replace("_", " ").title())))
    return keys

def flatten_day(day, supervision_notes=None):
    base = {
        "Date": day.get("date", ""),
        "Water": day.get("water_litres", ""),
        "Other Fluids": other_fluids_summary_v97(day.get("other_fluids", [])),
        "Physical Activity": day.get("physical_activity", ""),
        "Poop Rounds": day.get("poop_rounds", ""),
        "Poop Timings": ", ".join([str(x) for x in (day.get("poop_timings", []) or []) if str(x).strip()]),
        "Feeling After Poop": day.get("feeling_after_poop", ""),
        "Overall Notes": day.get("notes", ""),
        "Nutritionist Notes": " | ".join([n.get("note", "") for n in (supervision_notes or [])]),
    }
    meals = day.get("meals", {}) or {}
    for key, label in meal_keys_for_day(day):
        meal = meals.get(key, {}) or {}
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

selector_col_1, selector_col_2 = st.columns(2)
with selector_col_1:
    selected = st.selectbox("Select member", options, index=default_index)

member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
days = get_daily_food_journal_days(member_id)
available_dates = [d.get("date") for d in days if d.get("date")]
default_date_str = available_dates[0] if available_dates else str(date.today())
try:
    default_date_obj = date.fromisoformat(default_date_str)
except Exception:
    default_date_obj = date.today()

with selector_col_2:
    selected_date_obj = st.date_input("Select food log date for review / note", value=default_date_obj)
    selected_date = selected_date_obj.isoformat() if hasattr(selected_date_obj, "isoformat") else str(selected_date_obj)

selected_day = get_daily_food_journal_day(member_id, selected_date) or next((d for d in days if d.get("date") == selected_date), {"date": selected_date, "meals": {}})
date_notes = get_daily_log_supervision_notes(member_id, limit=20, log_date=selected_date)

stat_grid([
    {"label": "Member", "value": member.get("name", ""), "note": "Selected member"},
    {"label": "Saved Days", "value": len(days), "note": "Full-day food logs"},
    {"label": "Selected Date", "value": selected_date, "note": "Current review"},
    {"label": "Notes", "value": len(date_notes), "note": "For selected day"},
])

st.subheader("All saved days")
if not days:
    st.markdown("<div class='hm-dfjr-no-data-box'>No daily food logs available.</div>", unsafe_allow_html=True)
else:
    rows = []
    for d in days:
        notes_for_day = get_daily_log_supervision_notes(member_id, limit=20, log_date=d.get("date"))
        latest_note = get_latest_daily_log_note_for_date(member_id, d.get("date", ""))
        latest_note_text = ""
        if latest_note:
            latest_note_text = f"{format_local_ts(latest_note.get('ts',''))} — {latest_note.get('note','')}"
        rows.append({
            "Date": d.get("date", ""),
            "Breakfast": (d.get("meals", {}).get("breakfast", {}) or {}).get("food", ""),
            "Lunch": (d.get("meals", {}).get("lunch", {}) or {}).get("food", ""),
            "Dinner": (d.get("meals", {}).get("dinner", {}) or {}).get("food", ""),
            "Water": d.get("water_litres", ""),
            "Other Fluids": other_fluids_summary_v97(d.get("other_fluids", [])),
            "Activity": d.get("physical_activity", ""),
            "Poop Rounds": d.get("poop_rounds", ""),
            "Poop Timings": ", ".join([str(x) for x in (d.get("poop_timings", []) or []) if str(x).strip()]),
            "Feeling After Poop": d.get("feeling_after_poop", ""),
            "Notes": d.get("notes", ""),
            "Nutritionist Notes": latest_note_text,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Daily Food Journal Excel",
        data=build_excel(member, days),
        file_name=f"{member.get('name','member').replace(' ','_')}_daily_food_journal.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
card_end()

st.subheader(f"Food journal for {selected_date}")
st.markdown("<div class='hm-dfjr-tight'></div>", unsafe_allow_html=True)
if not selected_day or not selected_day.get("meals"):
    st.markdown("<div class='hm-dfjr-no-data-box'>No food journal available for this date.</div>", unsafe_allow_html=True)
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
    st.markdown("#### Other Fluids")
    other_fluid_rows = normalise_other_fluids_v97(selected_day.get("other_fluids", []))
    if other_fluid_rows:
        st.dataframe(other_fluid_rows, use_container_width=True, hide_index=True)
    else:
        st.markdown("—")
    st.markdown(f"**Physical Activity:** {selected_day.get('physical_activity','') or '-'}")
    st.markdown(f"**Poop rounds:** {selected_day.get('poop_rounds','') or '-'}")
    timings = selected_day.get("poop_timings", []) or []
    st.markdown(f"**Poop timings:** {', '.join([str(x) for x in timings if str(x).strip()]) or '-'}")
    st.markdown(f"**Feeling after poop:** {selected_day.get('feeling_after_poop','') or '-'}")
    st.markdown(f"**Overall Notes:** {selected_day.get('notes','') or '-'}")
    st.markdown("<div class='hm-full-day-black-row'></div>", unsafe_allow_html=True)
card_end()

st.markdown("<div class='hm-dfjr-subsection'></div>", unsafe_allow_html=True)
st.subheader(f"Nutritionist note for {selected_date}")
st.markdown("<div class='hm-dfjr-tight'></div>", unsafe_allow_html=True)
st.markdown("<div class='hm-dfjr-note-hard-wrap'>", unsafe_allow_html=True)
note = st.text_area(
    "Nutritionist note",
    placeholder="Example: Please add water quantity for lunch and dinner tomorrow.",
    height=92,
    label_visibility="collapsed",
    key=f"nutritionist_note_{member_id}_{selected_date}",
)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Send gentle Daily Log reminder", type="secondary", use_container_width=True):
    queue_daily_log_reminder(member_id)
    st.success("Reminder queued for the member and marked for email notification.")
card_end()

render_page_nav("Daily Logs", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")




