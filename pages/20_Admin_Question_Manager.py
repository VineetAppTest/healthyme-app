import streamlit as st, json, pathlib
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar

st.set_page_config(page_title="Question Manager", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

BASE = pathlib.Path(__file__).resolve().parents[1]

CONFIGS = {
    "LAF": "config/laf_questions.json",
    "NSP Page 1": "config/nsp_page1_questions.json",
    "NSP Page 2": "config/nsp_page2_questions.json",
    "Body-Mind Page": "config/body_mind_questions.json",
}

def load_json(path):
    return json.loads((BASE / path).read_text(encoding="utf-8"))

def save_json(path, data):
    (BASE / path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def label_for_question(q):
    return q.get("label") or q.get("text") or q.get("code", "")

topbar(
    "Admin Question Manager",
    "View all questions, including active and inactive items. Add, edit, deactivate or reactivate questions.",
    "Admin configuration"
)

st.info("This page now shows all questions, not only active ones. Inactive/deleted items can be reactivated.")

tab1, tab2 = st.tabs(["LAF / NSP / Body-Mind Questions", "5 Admin Assessment Pages"])

with tab1:
    selected_form = st.selectbox("Select form", list(CONFIGS.keys()))
    path = CONFIGS[selected_form]
    data = load_json(path)
    show_filter = st.radio("Show", ["All questions", "Active only", "Inactive/deleted only"], horizontal=True)

    indexed = []
    for idx, q in enumerate(data):
        deleted = bool(q.get("deleted"))
        if show_filter == "Active only" and deleted:
            continue
        if show_filter == "Inactive/deleted only" and not deleted:
            continue
        status = "Inactive" if deleted else "Active"
        indexed.append((idx, q, status))

    card_start()
    st.subheader(f"Questions: {selected_form}")
    st.caption(f"Showing {len(indexed)} of {len(data)} total questions.")
    if not indexed:
        st.info("No questions in this view.")
    else:
        options = [
            f"{idx} — {status} — {q.get('code','')} — {label_for_question(q)[:90]}"
            for idx, q, status in indexed
        ]
        selected = st.selectbox("Select question", options)
        selected_idx = int(selected.split(" — ")[0])
        q = data[selected_idx]

        code = st.text_input("Code", value=q.get("code", ""))
        number = st.text_input("Number, for NSP only", value=str(q.get("number", "")))
        page = st.text_input("Page", value=q.get("page", ""))
        section = st.text_input("Section", value=q.get("section", ""))
        label = st.text_area("Question label/text", value=label_for_question(q), height=90)
        type_options = ["text", "select", "number", "scale", "phone", "email", "checkbox", "date"]
        qtype = st.selectbox("Type", type_options, index=type_options.index(q.get("type", "text")) if q.get("type", "text") in type_options else 0)
        options_text = st.text_area("Options, one per line", value="\n".join(q.get("options", [])), height=90)
        required = st.checkbox("Mandatory / Required", value=bool(q.get("required", False)))
        active = st.checkbox("Active", value=not bool(q.get("deleted")))

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Save Question Changes", type="primary", use_container_width=True):
                data[selected_idx]["code"] = code.strip()
                if number.strip():
                    try:
                        data[selected_idx]["number"] = int(number.strip())
                    except Exception:
                        data[selected_idx]["number"] = number.strip()
                if page.strip():
                    data[selected_idx]["page"] = page.strip()
                if section.strip():
                    data[selected_idx]["section"] = section.strip()
                if selected_form.startswith("NSP"):
                    data[selected_idx]["text"] = label.strip()
                else:
                    data[selected_idx]["label"] = label.strip()
                data[selected_idx]["type"] = qtype
                opts = [x.strip() for x in options_text.splitlines() if x.strip()]
                if opts:
                    data[selected_idx]["options"] = opts
                else:
                    data[selected_idx].pop("options", None)
                data[selected_idx]["required"] = required
                data[selected_idx]["deleted"] = not active
                save_json(path, data)
                st.success("Question saved.")
                st.rerun()
        with b2:
            if st.button("Reactivate Question", disabled=not bool(q.get("deleted")), use_container_width=True):
                data[selected_idx]["deleted"] = False
                save_json(path, data)
                st.success("Question reactivated.")
                st.rerun()
    card_end()

    card_start()
    st.subheader(f"Add new question to {selected_form}")
    new_code = st.text_input("New code", key="new_code")
    new_number = st.text_input("New number, for NSP only", key="new_number")
    new_page = st.text_input("New page", key="new_page")
    new_section = st.text_input("New section", key="new_section")
    new_label = st.text_area("New question label/text", key="new_label")
    new_type = st.selectbox("New type", ["text", "select", "number", "scale", "phone", "email", "checkbox", "date"], key="new_type")
    new_options = st.text_area("New options, one per line", key="new_options")
    new_required = st.checkbox("New question mandatory", key="new_required")
    if st.button("Add New Question", type="primary"):
        if not new_code.strip() or not new_label.strip():
            st.error("Code and question label/text are required.")
        else:
            item = {"code": new_code.strip(), "type": new_type, "required": new_required, "deleted": False}
            if new_number.strip():
                try:
                    item["number"] = int(new_number.strip())
                except Exception:
                    item["number"] = new_number.strip()
            if new_page.strip():
                item["page"] = new_page.strip()
            if new_section.strip():
                item["section"] = new_section.strip()
            if selected_form.startswith("NSP"):
                if "number" not in item:
                    nums = []
                    for x in data:
                        try:
                            nums.append(int(x.get("number", 0)))
                        except Exception:
                            pass
                    item["number"] = max(nums + [0]) + 1
                item["text"] = new_label.strip()
            else:
                item["label"] = new_label.strip()
            opts = [x.strip() for x in new_options.splitlines() if x.strip()]
            if opts:
                item["options"] = opts
            data.append(item)
            save_json(path, data)
            st.success("New question added.")
            st.rerun()
    card_end()

with tab2:
    path = "config/admin_templates.json"
    templates = load_json(path)

    system = st.selectbox("System", list(templates.keys()))
    groups = templates[system]

    show_admin_filter = st.radio("Show admin items", ["All items", "Active only", "Inactive/deleted only"], horizontal=True)

    group_options = [f"{idx} — {'Inactive' if g.get('deleted') else 'Active'} — {g.get('heading','')}" for idx, g in enumerate(groups)]
    selected_group = st.selectbox("Subheader", group_options)
    gidx = int(selected_group.split(" — ")[0])
    group = groups[gidx]

    card_start()
    st.subheader("Edit subheader")
    heading = st.text_input("Subheader heading", value=group.get("heading", ""))
    group_active = st.checkbox("Subheader active", value=not bool(group.get("deleted")))
    if st.button("Update Subheader", type="primary"):
        templates[system][gidx]["heading"] = heading.strip()
        templates[system][gidx]["deleted"] = not group_active
        save_json(path, templates)
        st.success("Subheader updated.")
        st.rerun()
    card_end()

    card_start()
    st.subheader("Edit admin page question")
    items = group.get("items", [])
    indexed_items = []
    for idx, item in enumerate(items):
        deleted = bool(item.get("deleted"))
        if show_admin_filter == "Active only" and deleted:
            continue
        if show_admin_filter == "Inactive/deleted only" and not deleted:
            continue
        indexed_items.append((idx, item, "Inactive" if deleted else "Active"))

    if indexed_items:
        item_options = [f"{idx} — {status} — {item.get('label','')[:100]}" for idx, item, status in indexed_items]
        selected_item = st.selectbox("Select item", item_options)
        iidx = int(selected_item.split(" — ")[0])
        item = items[iidx]
        label = st.text_area("Question/item label", value=item.get("label", ""), height=90)
        linked_code = st.text_input("Linked NSP code, optional", value=item.get("linked_code") or "")
        active = st.checkbox("Admin question active", value=not bool(item.get("deleted")))
        if st.button("Save Admin Question", type="primary", use_container_width=True):
            templates[system][gidx]["items"][iidx]["label"] = label.strip()
            templates[system][gidx]["items"][iidx]["linked_code"] = linked_code.strip() or None
            templates[system][gidx]["items"][iidx]["source"] = "linked" if linked_code.strip() else "manual"
            templates[system][gidx]["items"][iidx]["deleted"] = not active
            save_json(path, templates)
            st.success("Admin question saved.")
            st.rerun()
    else:
        st.info("No items in this view.")
    card_end()

    card_start()
    st.subheader("Add new admin question")
    new_label = st.text_area("New admin question/item label")
    new_linked = st.text_input("Linked NSP code, optional")
    if st.button("Add Admin Question", type="primary"):
        if not new_label.strip():
            st.error("Question label is required.")
        else:
            templates[system][gidx].setdefault("items", []).append({
                "label": new_label.strip(),
                "linked_code": new_linked.strip() or None,
                "source": "linked" if new_linked.strip() else "manual",
                "deleted": False,
            })
            save_json(path, templates)
            st.success("Admin question added.")
            st.rerun()
    card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")