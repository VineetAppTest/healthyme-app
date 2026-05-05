import streamlit as st, json, pathlib
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import load_db, save_db_direct, update_member_response_with_audit, list_members

st.set_page_config(page_title="Response Editor", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

BASE = pathlib.Path(__file__).resolve().parents[1]

FORM_STORES = {
    "LAF": ("laf_responses", "config/laf_questions.json"),
    "NSP Page 1": ("nsp1_responses", "config/nsp_page1_questions.json"),
    "NSP Page 2": ("nsp2_responses", "config/nsp_page2_questions.json"),
    "Body-Mind Page": ("body_mind_responses", "config/body_mind_questions.json"),
    "5 Admin Assessment Pages": ("admin_assessments", "config/admin_templates.json"),
}

def load_json(path):
    return json.loads((BASE / path).read_text(encoding="utf-8"))

def question_label(q):
    return q.get("label") or q.get("text") or q.get("code")

def build_audit_excel(member, audit_rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Response Audit Log"
    headers = ["Timestamp", "Member", "Member Email", "Admin ID", "Form", "Field Code", "Old Value", "New Value", "Rationale"]
    ws.append(headers)
    for item in audit_rows:
        ws.append([
            item.get("timestamp", ""),
            member.get("name", ""),
            member.get("email", ""),
            item.get("admin_id", ""),
            item.get("form_name", ""),
            item.get("field_code", ""),
            item.get("old_value", ""),
            item.get("new_value", ""),
            item.get("rationale", ""),
        ])
    style_excel(ws)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()

def style_excel(ws):
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
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 14), 60)

def flatten_standard_questions(form_name, cfg_path):
    data = load_json(cfg_path)
    fields = []
    for q in data:
        status = "Inactive" if q.get("deleted") else "Active"
        fields.append({
            "field_code": q.get("code", ""),
            "display": f"{status} — {q.get('code','')} — {question_label(q)[:100]}",
            "question": question_label(q),
            "type": q.get("type", "text"),
            "options": q.get("options", []),
            "deleted": bool(q.get("deleted")),
        })
    return fields

def flatten_admin_questions():
    templates = load_json("config/admin_templates.json")
    fields = []
    for system, groups in templates.items():
        for group in groups:
            heading = group.get("heading", "")
            for item in group.get("items", []):
                label = item.get("label", "")
                key = f"{system}|{heading}|{label}"
                status = "Inactive" if item.get("deleted") or group.get("deleted") else "Active"
                fields.append({
                    "field_code": key,
                    "display": f"{status} — {system} > {heading} — {label[:100]}",
                    "question": label,
                    "system": system,
                    "subheader": heading,
                    "type": "select",
                    "options": ["NA", "1", "2", "3"],
                    "deleted": bool(item.get("deleted") or group.get("deleted")),
                })
    return fields

def get_current_value(db, member_id, form_name, field):
    if form_name == "5 Admin Assessment Pages":
        system = field["system"]
        key = field["field_code"]
        return db.setdefault("admin_assessments", {}).setdefault(member_id, {}).setdefault(system, {}).get(key, "")
    store, _ = FORM_STORES[form_name]
    return db.setdefault(store, {}).setdefault(member_id, {}).get(field["field_code"], "")

def set_current_value(db, member_id, form_name, field, new_value):
    if form_name == "5 Admin Assessment Pages":
        system = field["system"]
        key = field["field_code"]
        db.setdefault("admin_assessments", {}).setdefault(member_id, {}).setdefault(system, {})[key] = str(new_value)
    else:
        store, _ = FORM_STORES[form_name]
        db.setdefault(store, {}).setdefault(member_id, {})[field["field_code"]] = str(new_value)

topbar(
    "Admin Response Editor",
    "Edit any member response, including blank/unanswered fields, and record rationale with timestamp.",
    "Audited admin correction"
)

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_options = [f"{m['id']} — {m['name']} — {m['email']}" for m in members]
selected_member = st.selectbox("Select member", member_options)
member_id = selected_member.split(" — ")[0]

db = load_db()
member_lookup = {m["id"]: m for m in members}
member = member_lookup.get(member_id, {})

selected_form = st.selectbox("Select response area", list(FORM_STORES.keys()))
store, cfg = FORM_STORES[selected_form]

if selected_form == "5 Admin Assessment Pages":
    fields = flatten_admin_questions()
else:
    fields = flatten_standard_questions(selected_form, cfg)

show_filter = st.radio("Show fields", ["All fields", "Answered only", "Unanswered only"], horizontal=True)
filtered_fields = []
for f in fields:
    val = get_current_value(db, member_id, selected_form, f)
    answered = str(val).strip() not in ["", "Select", "None"]
    if show_filter == "Answered only" and not answered:
        continue
    if show_filter == "Unanswered only" and answered:
        continue
    filtered_fields.append(f)

card_start()
st.subheader("All responses / fields")
st.caption(f"Showing {len(filtered_fields)} of {len(fields)} fields for {selected_form}.")
if not filtered_fields:
    st.info("No fields match the selected view.")
else:
    selected_field_display = st.selectbox("Select field to edit", [f["display"] for f in filtered_fields])
    field = next(f for f in filtered_fields if f["display"] == selected_field_display)
    old_value = get_current_value(db, member_id, selected_form, field)

    st.markdown(f"**Question:** {field['question']}")
    st.markdown(f"**Current value:** `{old_value}`")

    if field["type"] in ["select", "scale"]:
        opts = field.get("options", [])
        if field["type"] == "scale" and not opts:
            opts = [str(i) for i in range(1, 11)]
        opts = ["Select"] + [x for x in opts if x != "Select"]
        if selected_form.startswith("NSP") and "NA" not in opts:
            opts.insert(1, "NA")
        idx = opts.index(old_value) if old_value in opts else 0
        new_value = st.selectbox("New value", opts, index=idx)
    elif field["type"] == "checkbox":
        new_value = st.checkbox("New value", value=(str(old_value).lower() == "true" or old_value is True))
    else:
        new_value = st.text_area("New value", value=str(old_value), height=120)

    rationale = st.text_area("Rationale / note for change", placeholder="Mandatory. Example: Corrected after conversation with member.", height=100)

    if st.button("Save Edited Response with Audit Note", type="primary", use_container_width=True):
        if str(new_value) == str(old_value):
            st.info("No value changed.")
        elif not rationale.strip():
            st.error("Rationale/note is mandatory for edited member responses.")
        else:
            set_current_value(db, member_id, selected_form, field, new_value)
            save_db_direct(db)
            update_member_response_with_audit(
                st.session_state.get("user_id", "admin"),
                member_id,
                selected_form,
                field["field_code"],
                old_value,
                str(new_value),
                rationale.strip(),
            )
            st.success("Response updated and audit note saved with timestamp.")
            st.rerun()
card_end()

card_start()
st.subheader("Audit log for this member")
audit = [x for x in load_db().get("response_audit_log", []) if x.get("member_id") == member_id]
if not audit:
    st.info("No response edits recorded yet.")
else:
    st.download_button(
        "Download Member Response Audit Report",
        data=build_audit_excel(member, audit),
        file_name=f"{member.get('name','member').replace(' ','_')}_response_audit_log.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    for item in reversed(audit[-30:]):
        st.markdown(
            f"""
            **{item.get('timestamp','')}** — {item.get('form_name','')} / `{item.get('field_code','')}`  
            Old: `{item.get('old_value','')}` → New: `{item.get('new_value','')}`  
            Rationale: {item.get('rationale','')}
            """
        )
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")