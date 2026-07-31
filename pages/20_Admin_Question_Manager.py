import json
import pathlib

import streamlit as st

from components.config_cache import refresh_config_cache
from components.flash import render_system_message, set_system_message
from components.guards import require_admin
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
    page_title="Question Manager",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

BASE = pathlib.Path(__file__).resolve().parents[1]
CLEANUP_KEY = "hm_question_manager_cleanup_keys"

CONFIGS = {
    "LAF": "config/laf_questions.json",
    "NSP Page 1": "config/nsp_page1_questions.json",
    "NSP Page 2": "config/nsp_page2_questions.json",
    "Body-Mind Page": "config/body_mind_questions.json",
}
TYPE_OPTIONS = [
    "text",
    "select",
    "number",
    "scale",
    "phone",
    "email",
    "checkbox",
    "date",
]


def load_json(path):
    return json.loads((BASE / path).read_text(encoding="utf-8"))


def save_json(path, data):
    (BASE / path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    refresh_config_cache()


def label_for_question(question):
    return question.get("label") or question.get("text") or question.get("code", "")


def _scope(*parts):
    return "__".join(str(part).replace(" ", "_") for part in parts)


def _version(prefix, *parts):
    key = f"hm_qm_{prefix}_version_{_scope(*parts)}"
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _bump_version(prefix, *parts):
    key = f"hm_qm_{prefix}_version_{_scope(*parts)}"
    st.session_state[key] = _version(prefix, *parts) + 1


def _schedule_cleanup(*keys):
    st.session_state[CLEANUP_KEY] = tuple(str(key) for key in keys)


def _consume_cleanup():
    for key in st.session_state.pop(CLEANUP_KEY, ()) or ():
        st.session_state.pop(key, None)


def _save_with_feedback(path, data, success_message):
    try:
        save_json(path, data)
    except Exception as exc:
        st.error(f"Unable to save changes. Your entered values have been retained. {exc}")
        return False
    set_system_message(success_message, "success")
    return True


_consume_cleanup()

topbar(
    "Admin Question Manager",
    "View all questions, including active and inactive items. Add, edit, deactivate or reactivate questions.",
    "Admin configuration",
)
render_system_message()
st.info(
    "This page shows all questions, not only active ones. Inactive/deleted items can be reactivated."
)

tab1, tab2 = st.tabs(["LAF / NSP / Body-Mind Questions", "5 Admin Assessment Pages"])

with tab1:
    selected_form = st.selectbox(
        "Select form",
        list(CONFIGS.keys()),
        key="hm_qm_selected_standard_form",
    )
    path = CONFIGS[selected_form]
    data = load_json(path)
    show_filter = st.radio(
        "Show",
        ["All questions", "Active only", "Inactive/deleted only"],
        horizontal=True,
        key=f"hm_qm_standard_filter_{_scope(selected_form)}",
    )

    indexed = []
    for idx, question in enumerate(data):
        deleted = bool(question.get("deleted"))
        if show_filter == "Active only" and deleted:
            continue
        if show_filter == "Inactive/deleted only" and not deleted:
            continue
        indexed.append((idx, question, "Inactive" if deleted else "Active"))

    card_start()
    st.subheader(f"Questions: {selected_form}")
    st.caption(f"Showing {len(indexed)} of {len(data)} total questions.")
    if not indexed:
        st.info("No questions in this view.")
    else:
        question_map = {idx: (question, status) for idx, question, status in indexed}
        selected_idx = st.selectbox(
            "Select question",
            list(question_map.keys()),
            format_func=lambda idx: (
                f"{idx} — {question_map[idx][1]} — "
                f"{question_map[idx][0].get('code', '')} — "
                f"{label_for_question(question_map[idx][0])[:90]}"
            ),
            key=f"hm_qm_selected_question_{_scope(selected_form, show_filter)}",
        )
        question = data[selected_idx]
        edit_version = _version("standard_edit", selected_form, selected_idx)
        edit_scope = _scope(selected_form, selected_idx, edit_version)
        code_key = f"hm_qm_code_{edit_scope}"
        number_key = f"hm_qm_number_{edit_scope}"
        page_key = f"hm_qm_page_{edit_scope}"
        section_key = f"hm_qm_section_{edit_scope}"
        label_key = f"hm_qm_label_{edit_scope}"
        type_key = f"hm_qm_type_{edit_scope}"
        options_key = f"hm_qm_options_{edit_scope}"
        required_key = f"hm_qm_required_{edit_scope}"
        active_key = f"hm_qm_active_{edit_scope}"

        code = st.text_input("Code", value=question.get("code", ""), key=code_key)
        number = st.text_input(
            "Number, for NSP only",
            value=str(question.get("number", "")),
            key=number_key,
        )
        page = st.text_input("Page", value=question.get("page", ""), key=page_key)
        section = st.text_input(
            "Section",
            value=question.get("section", ""),
            key=section_key,
        )
        label = st.text_area(
            "Question label/text",
            value=label_for_question(question),
            height=90,
            key=label_key,
        )
        current_type = question.get("type", "text")
        qtype = st.selectbox(
            "Type",
            TYPE_OPTIONS,
            index=TYPE_OPTIONS.index(current_type) if current_type in TYPE_OPTIONS else 0,
            key=type_key,
        )
        options_text = st.text_area(
            "Options, one per line",
            value="\n".join(question.get("options", [])),
            height=90,
            key=options_key,
        )
        required = st.checkbox(
            "Mandatory / Required",
            value=bool(question.get("required", False)),
            key=required_key,
        )
        active = st.checkbox(
            "Active",
            value=not bool(question.get("deleted")),
            key=active_key,
        )

        b1, b2 = st.columns(2)
        with b1:
            if st.button(
                "Save Question Changes",
                type="primary",
                use_container_width=True,
                key=f"hm_qm_save_standard_{edit_scope}",
            ):
                updated = dict(data[selected_idx])
                updated["code"] = code.strip()
                if number.strip():
                    try:
                        updated["number"] = int(number.strip())
                    except Exception:
                        updated["number"] = number.strip()
                else:
                    updated.pop("number", None)
                if page.strip():
                    updated["page"] = page.strip()
                else:
                    updated.pop("page", None)
                if section.strip():
                    updated["section"] = section.strip()
                else:
                    updated.pop("section", None)
                if selected_form.startswith("NSP"):
                    updated["text"] = label.strip()
                else:
                    updated["label"] = label.strip()
                updated["type"] = qtype
                options = [value.strip() for value in options_text.splitlines() if value.strip()]
                if options:
                    updated["options"] = options
                else:
                    updated.pop("options", None)
                updated["required"] = required
                updated["deleted"] = not active
                candidate = list(data)
                candidate[selected_idx] = updated
                if _save_with_feedback(path, candidate, "Question saved."):
                    _schedule_cleanup(
                        code_key,
                        number_key,
                        page_key,
                        section_key,
                        label_key,
                        type_key,
                        options_key,
                        required_key,
                        active_key,
                    )
                    _bump_version("standard_edit", selected_form, selected_idx)
                    st.rerun()
        with b2:
            if st.button(
                "Reactivate Question",
                disabled=not bool(question.get("deleted")),
                use_container_width=True,
                key=f"hm_qm_reactivate_{_scope(selected_form, selected_idx)}",
            ):
                candidate = list(data)
                candidate[selected_idx] = dict(candidate[selected_idx])
                candidate[selected_idx]["deleted"] = False
                if _save_with_feedback(path, candidate, "Question reactivated."):
                    _schedule_cleanup(
                        code_key,
                        number_key,
                        page_key,
                        section_key,
                        label_key,
                        type_key,
                        options_key,
                        required_key,
                        active_key,
                    )
                    _bump_version("standard_edit", selected_form, selected_idx)
                    st.rerun()
    card_end()

    card_start()
    st.subheader(f"Add new question to {selected_form}")
    create_version = _version("standard_create", selected_form)
    create_scope = _scope(selected_form, create_version)
    new_code_key = f"hm_qm_new_code_{create_scope}"
    new_number_key = f"hm_qm_new_number_{create_scope}"
    new_page_key = f"hm_qm_new_page_{create_scope}"
    new_section_key = f"hm_qm_new_section_{create_scope}"
    new_label_key = f"hm_qm_new_label_{create_scope}"
    new_type_key = f"hm_qm_new_type_{create_scope}"
    new_options_key = f"hm_qm_new_options_{create_scope}"
    new_required_key = f"hm_qm_new_required_{create_scope}"

    new_code = st.text_input("New code", key=new_code_key)
    new_number = st.text_input("New number, for NSP only", key=new_number_key)
    new_page = st.text_input("New page", key=new_page_key)
    new_section = st.text_input("New section", key=new_section_key)
    new_label = st.text_area("New question label/text", key=new_label_key)
    new_type = st.selectbox("New type", TYPE_OPTIONS, key=new_type_key)
    new_options = st.text_area("New options, one per line", key=new_options_key)
    new_required = st.checkbox("New question mandatory", key=new_required_key)

    if st.button(
        "Add New Question",
        type="primary",
        key=f"hm_qm_add_standard_{create_scope}",
    ):
        if not new_code.strip() or not new_label.strip():
            st.error("Code and question label/text are required.")
        else:
            item = {
                "code": new_code.strip(),
                "type": new_type,
                "required": new_required,
                "deleted": False,
            }
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
                    numbers = []
                    for existing in data:
                        try:
                            numbers.append(int(existing.get("number", 0)))
                        except Exception:
                            pass
                    item["number"] = max(numbers + [0]) + 1
                item["text"] = new_label.strip()
            else:
                item["label"] = new_label.strip()
            options = [value.strip() for value in new_options.splitlines() if value.strip()]
            if options:
                item["options"] = options
            candidate = list(data)
            candidate.append(item)
            if _save_with_feedback(path, candidate, "New question added."):
                _schedule_cleanup(
                    new_code_key,
                    new_number_key,
                    new_page_key,
                    new_section_key,
                    new_label_key,
                    new_type_key,
                    new_options_key,
                    new_required_key,
                )
                _bump_version("standard_create", selected_form)
                st.rerun()
    card_end()

with tab2:
    path = "config/admin_templates.json"
    templates = load_json(path)

    system = st.selectbox(
        "System",
        list(templates.keys()),
        key="hm_qm_admin_system",
    )
    groups = templates[system]
    show_admin_filter = st.radio(
        "Show admin items",
        ["All items", "Active only", "Inactive/deleted only"],
        horizontal=True,
        key=f"hm_qm_admin_filter_{_scope(system)}",
    )

    group_indices = list(range(len(groups)))
    selected_group_idx = st.selectbox(
        "Subheader",
        group_indices,
        format_func=lambda idx: (
            f"{idx} — {'Inactive' if groups[idx].get('deleted') else 'Active'} — "
            f"{groups[idx].get('heading', '')}"
        ),
        key=f"hm_qm_admin_group_{_scope(system)}",
    )
    group = groups[selected_group_idx]

    card_start()
    st.subheader("Edit subheader")
    group_version = _version("group_edit", system, selected_group_idx)
    group_scope = _scope(system, selected_group_idx, group_version)
    heading_key = f"hm_qm_group_heading_{group_scope}"
    group_active_key = f"hm_qm_group_active_{group_scope}"
    heading = st.text_input(
        "Subheader heading",
        value=group.get("heading", ""),
        key=heading_key,
    )
    group_active = st.checkbox(
        "Subheader active",
        value=not bool(group.get("deleted")),
        key=group_active_key,
    )
    if st.button(
        "Update Subheader",
        type="primary",
        key=f"hm_qm_update_group_{group_scope}",
    ):
        candidate = json.loads(json.dumps(templates))
        candidate[system][selected_group_idx]["heading"] = heading.strip()
        candidate[system][selected_group_idx]["deleted"] = not group_active
        if _save_with_feedback(path, candidate, "Subheader updated."):
            _schedule_cleanup(heading_key, group_active_key)
            _bump_version("group_edit", system, selected_group_idx)
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
        item_map = {idx: (item, status) for idx, item, status in indexed_items}
        selected_item_idx = st.selectbox(
            "Select item",
            list(item_map.keys()),
            format_func=lambda idx: (
                f"{idx} — {item_map[idx][1]} — {item_map[idx][0].get('label', '')[:100]}"
            ),
            key=f"hm_qm_admin_item_{_scope(system, selected_group_idx, show_admin_filter)}",
        )
        item = items[selected_item_idx]
        item_version = _version(
            "admin_item_edit",
            system,
            selected_group_idx,
            selected_item_idx,
        )
        item_scope = _scope(system, selected_group_idx, selected_item_idx, item_version)
        item_label_key = f"hm_qm_admin_item_label_{item_scope}"
        linked_code_key = f"hm_qm_admin_item_link_{item_scope}"
        item_active_key = f"hm_qm_admin_item_active_{item_scope}"
        item_label = st.text_area(
            "Question/item label",
            value=item.get("label", ""),
            height=90,
            key=item_label_key,
        )
        linked_code = st.text_input(
            "Linked NSP code, optional",
            value=item.get("linked_code") or "",
            key=linked_code_key,
        )
        item_active = st.checkbox(
            "Admin question active",
            value=not bool(item.get("deleted")),
            key=item_active_key,
        )
        if st.button(
            "Save Admin Question",
            type="primary",
            use_container_width=True,
            key=f"hm_qm_save_admin_item_{item_scope}",
        ):
            candidate = json.loads(json.dumps(templates))
            target = candidate[system][selected_group_idx]["items"][selected_item_idx]
            target["label"] = item_label.strip()
            target["linked_code"] = linked_code.strip() or None
            target["source"] = "linked" if linked_code.strip() else "manual"
            target["deleted"] = not item_active
            if _save_with_feedback(path, candidate, "Admin question saved."):
                _schedule_cleanup(item_label_key, linked_code_key, item_active_key)
                _bump_version(
                    "admin_item_edit",
                    system,
                    selected_group_idx,
                    selected_item_idx,
                )
                st.rerun()
    else:
        st.info("No items in this view.")
    card_end()

    card_start()
    st.subheader("Add new admin question")
    admin_create_version = _version("admin_create", system, selected_group_idx)
    admin_create_scope = _scope(system, selected_group_idx, admin_create_version)
    admin_new_label_key = f"hm_qm_admin_new_label_{admin_create_scope}"
    admin_new_linked_key = f"hm_qm_admin_new_linked_{admin_create_scope}"
    admin_new_label = st.text_area(
        "New admin question/item label",
        key=admin_new_label_key,
    )
    admin_new_linked = st.text_input(
        "Linked NSP code, optional",
        key=admin_new_linked_key,
    )
    if st.button(
        "Add Admin Question",
        type="primary",
        key=f"hm_qm_add_admin_{admin_create_scope}",
    ):
        if not admin_new_label.strip():
            st.error("Question label is required.")
        else:
            candidate = json.loads(json.dumps(templates))
            candidate[system][selected_group_idx].setdefault("items", []).append(
                {
                    "label": admin_new_label.strip(),
                    "linked_code": admin_new_linked.strip() or None,
                    "source": "linked" if admin_new_linked.strip() else "manual",
                    "deleted": False,
                }
            )
            if _save_with_feedback(path, candidate, "Admin question added."):
                _schedule_cleanup(admin_new_label_key, admin_new_linked_key)
                _bump_version("admin_create", system, selected_group_idx)
                st.rerun()
    card_end()

render_page_nav(
    "Question Manager",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
