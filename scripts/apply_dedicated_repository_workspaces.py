from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMMON_IMPORT = '''from components.repository_workspace_common import (
    actor_id as workspace_actor_id,
    clear_widget_prefix,
    clear_workspace,
    inject_workspace_ui,
    workspace_mode,
    workspace_panel,
)
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing marker: {label}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Expected one match for {label}; found {count}")
    return updated


def add_common_import(text: str) -> str:
    marker = "from components.repository_page_ui import ("
    return replace_once(text, marker, COMMON_IMPORT + marker, "repository workspace import")


RECIPE_RENDERER = r'''
def _render_recipe_workspace() -> None:
    mode, item_id = workspace_mode("recipe")
    df = load()
    row = {}
    index = None
    if mode == "edit":
        try:
            index = int(item_id)
        except (TypeError, ValueError):
            st.error("The selected recipe could not be identified.")
            if st.button("Back to Recipe Repository"):
                clear_workspace("recipe")
                st.switch_page("pages/15_Admin_Recipe_Manager.py")
            return
        if index not in df.index:
            st.error("The selected recipe is no longer available.")
            if st.button("Back to Recipe Repository"):
                clear_workspace("recipe")
                st.switch_page("pages/15_Admin_Recipe_Manager.py")
            return
        row = df.loc[index].to_dict()

    inject_workspace_ui()
    title = "Edit Recipe" if mode == "edit" else "Add Recipe"
    subtitle = (
        f"Update {_clean(row.get('title')) or 'the selected recipe'}."
        if mode == "edit"
        else "Create a reusable recipe definition for future meal plans."
    )
    topbar(title, subtitle, "Recipe workspace")
    prefix = f"recipe_workspace_{mode}_{index if index is not None else 'new'}"
    success_key = "hm_recipe_workspace_success"

    with workspace_panel():
        values = recipe_form(prefix, row)
        action_col, cancel_col, message_col = st.columns([1.05, .8, 2.8], gap="small")
        with action_col:
            submitted = st.button(
                "Save Changes" if mode == "edit" else "Save Recipe",
                type="primary",
                use_container_width=True,
                key=f"{prefix}_save",
            )
        with cancel_col:
            cancelled = st.button(
                "Cancel",
                use_container_width=True,
                key=f"{prefix}_cancel",
            )
        with message_col:
            message = st.session_state.pop(success_key, None)
            if message:
                st.success(message)

        if cancelled:
            clear_workspace("recipe")
            clear_widget_prefix(prefix)
            st.switch_page("pages/15_Admin_Recipe_Manager.py")

        if submitted:
            if not _clean(values.get("title")):
                st.error("Recipe title is required.")
            elif mode == "edit" and index is not None:
                for column in RECIPE_COLUMNS:
                    df.at[index, column] = values.get(column, "")
                save(df)
                _flash("Recipe updated.")
                clear_workspace("recipe")
                clear_widget_prefix(prefix)
                st.switch_page("pages/15_Admin_Recipe_Manager.py")
            else:
                df.loc[len(df)] = [values.get(column, "") for column in RECIPE_COLUMNS]
                save(df)
                clear_widget_prefix(prefix)
                st.session_state[success_key] = "Recipe saved successfully. The form has been cleared."
                st.rerun()

    render_page_nav(
        title,
        back_page="pages/15_Admin_Recipe_Manager.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()


if st.session_state.get("_hm_recipe_workspace_embedded"):
    _render_recipe_workspace()
    st.stop()


'''


EXERCISE_RENDERER = r'''
def _render_exercise_workspace() -> None:
    mode, item_id = workspace_mode("exercise")
    rows = list_exercise_repository(active_only=False)
    row = {}
    exercise_id = None
    if mode == "edit":
        exercise_id = str(item_id or "")
        row = next((item for item in rows if str(item.get("id")) == exercise_id), None)
        if row is None:
            st.error("The selected exercise is no longer available.")
            if st.button("Back to Exercise Repository"):
                clear_workspace("exercise")
                st.switch_page("pages/16_Admin_Exercise_Manager.py")
            return

    inject_workspace_ui()
    title = "Edit Exercise" if mode == "edit" else "Add Exercise"
    subtitle = (
        f"Update {_clean(row.get('title')) or 'the selected exercise'}."
        if mode == "edit"
        else "Create a reusable exercise definition for member allocation."
    )
    topbar(title, subtitle, "Exercise workspace")
    prefix = f"exercise_workspace_{mode}_{exercise_id or 'new'}"
    success_key = "hm_exercise_workspace_success"

    with workspace_panel():
        values = exercise_form(prefix, row)
        action_col, cancel_col, message_col = st.columns([1.05, .8, 2.8], gap="small")
        with action_col:
            submitted = st.button(
                "Save Changes" if mode == "edit" else "Save Exercise",
                type="primary",
                use_container_width=True,
                key=f"{prefix}_save",
            )
        with cancel_col:
            cancelled = st.button(
                "Cancel",
                use_container_width=True,
                key=f"{prefix}_cancel",
            )
        with message_col:
            message = st.session_state.pop(success_key, None)
            if message:
                st.success(message)

        if cancelled:
            clear_workspace("exercise")
            clear_widget_prefix(prefix)
            st.switch_page("pages/16_Admin_Exercise_Manager.py")

        if submitted:
            try:
                if mode == "edit" and exercise_id:
                    update_exercise_repository_item(
                        exercise_id,
                        values,
                        actor_id=workspace_actor_id(),
                    )
                    _flash("Exercise updated.")
                    clear_workspace("exercise")
                    clear_widget_prefix(prefix)
                    st.switch_page("pages/16_Admin_Exercise_Manager.py")
                else:
                    add_exercise_repository_item(values, actor_id=workspace_actor_id())
                    clear_widget_prefix(prefix)
                    st.session_state[success_key] = "Exercise saved successfully. The form has been cleared."
                    st.rerun()
            except Exception as exc:
                st.error(str(exc))

    render_page_nav(
        title,
        back_page="pages/16_Admin_Exercise_Manager.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()


if st.session_state.get("_hm_exercise_workspace_embedded"):
    _render_exercise_workspace()
    st.stop()


'''


SUPPLEMENT_RENDERER = r'''
def _render_supplement_workspace() -> None:
    mode, item_id = workspace_mode("supplement")
    rows = list_supplement_repository(active_only=False)
    row = {}
    supplement_id = None
    if mode == "edit":
        supplement_id = str(item_id or "")
        row = next((item for item in rows if str(item.get("id")) == supplement_id), None)
        if row is None:
            st.error("The selected supplement is no longer available.")
            if st.button("Back to Supplement Repository"):
                clear_workspace("supplement")
                st.switch_page("pages/39_Admin_Supplement_Manager.py")
            return

    inject_workspace_ui()
    title = "Edit Supplement" if mode == "edit" else "Add Supplement"
    subtitle = (
        f"Update {row.get('supplement_name') or 'the selected supplement'}."
        if mode == "edit"
        else "Create reusable supplement defaults for direct member allocation."
    )
    topbar(title, subtitle, "Supplement workspace")
    prefix = f"supplement_workspace_{mode}_{supplement_id or 'new'}"
    success_key = "hm_supplement_workspace_success"
    selected_timing, custom_timing = _split_timing(row.get("timing"))

    with workspace_panel():
        if mode == "add":
            with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
                st.markdown("#### Basic Details")
                name_col, dose_col, frequency_col = st.columns(3, gap="small")
                with name_col:
                    name = st.text_input("Supplement Name", placeholder="e.g. Magnesium Glycinate")
                with dose_col:
                    dosage = st.text_input("Default Dosage", placeholder="e.g. 400 mg")
                with frequency_col:
                    frequency = st.selectbox(
                        "Default Frequency",
                        FREQUENCY_OPTIONS,
                        index=0,
                        key="hm_v1023a_add_frequency",
                    )
                st.markdown("#### Timing")
                timing_col, custom_col = st.columns([1.35, 1], gap="small")
                with timing_col:
                    timing_options = st.multiselect("Default Timing", TIMING_OPTIONS, default=[])
                with custom_col:
                    custom = st.text_input(
                        "Additional Timing",
                        placeholder="Optional custom timing; separate values with commas.",
                    )
                st.markdown("#### Instructions")
                instructions = st.text_area(
                    "Default Instructions",
                    placeholder="Reusable guidance that can be adjusted during member allocation.",
                )
                action_col, cancel_col, message_col = st.columns([1.05, .8, 2.8], gap="small")
                with action_col:
                    submitted = st.form_submit_button("Add to Repository", use_container_width=True)
                with cancel_col:
                    cancelled = st.form_submit_button("Cancel", use_container_width=True)
                with message_col:
                    message = st.session_state.pop(success_key, None)
                    if message:
                        st.success(message)

            if cancelled:
                clear_workspace("supplement")
                st.switch_page("pages/39_Admin_Supplement_Manager.py")
            if submitted:
                try:
                    add_supplement_repository_item(
                        {
                            "supplement_name": name,
                            "dosage": dosage,
                            "frequency": frequency,
                            "timing": _timing_from_choices(timing_options, custom),
                            "instructions": instructions,
                        },
                        actor_id=workspace_actor_id(),
                    )
                    st.session_state[success_key] = "Supplement saved successfully. The form has been cleared."
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.markdown("#### Basic Details")
            name_col, dose_col, frequency_col = st.columns(3, gap="small")
            with name_col:
                name = st.text_input(
                    "Supplement Name",
                    value=row.get("supplement_name", ""),
                    key=f"{prefix}_name",
                )
            with dose_col:
                dosage = st.text_input(
                    "Default Dosage",
                    value=row.get("dosage", ""),
                    key=f"{prefix}_dosage",
                )
            with frequency_col:
                frequency_value = row.get("frequency") if row.get("frequency") in FREQUENCY_OPTIONS else FREQUENCY_OPTIONS[0]
                frequency = st.selectbox(
                    "Default Frequency",
                    FREQUENCY_OPTIONS,
                    index=FREQUENCY_OPTIONS.index(frequency_value),
                    key=f"{prefix}_frequency",
                )
            st.markdown("#### Timing")
            timing_col, custom_col = st.columns([1.35, 1], gap="small")
            with timing_col:
                timing_options = st.multiselect(
                    "Default Timing",
                    TIMING_OPTIONS,
                    default=selected_timing,
                    key=f"{prefix}_timing",
                )
            with custom_col:
                custom = st.text_input(
                    "Additional Timing",
                    value=custom_timing,
                    key=f"{prefix}_custom_timing",
                )
            st.markdown("#### Instructions")
            instructions = st.text_area(
                "Default Instructions",
                value=row.get("instructions", ""),
                key=f"{prefix}_instructions",
            )
            action_col, cancel_col, spacer = st.columns([1.05, .8, 2.8], gap="small")
            with action_col:
                submitted = st.button("Save Changes", type="primary", use_container_width=True, key=f"{prefix}_save")
            with cancel_col:
                cancelled = st.button("Cancel", use_container_width=True, key=f"{prefix}_cancel")

            if cancelled:
                clear_workspace("supplement")
                clear_widget_prefix(prefix)
                st.switch_page("pages/39_Admin_Supplement_Manager.py")
            if submitted:
                try:
                    update_supplement_repository_item(
                        supplement_id,
                        {
                            "supplement_name": name,
                            "dosage": dosage,
                            "frequency": frequency,
                            "timing": _timing_from_choices(timing_options, custom),
                            "instructions": instructions,
                        },
                        actor_id=workspace_actor_id(),
                    )
                    _flash("Supplement updated.")
                    clear_workspace("supplement")
                    clear_widget_prefix(prefix)
                    st.switch_page("pages/39_Admin_Supplement_Manager.py")
                except Exception as exc:
                    st.error(str(exc))

    render_page_nav(
        title,
        back_page="pages/39_Admin_Supplement_Manager.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()


if st.session_state.get("_hm_supplement_workspace_embedded"):
    _render_supplement_workspace()
    st.stop()


'''


def transform_recipe(path: Path) -> None:
    text = add_common_import(path.read_text(encoding="utf-8"))
    text = replace_once(text, "st.markdown(\n    \"\"\"\n<style>", RECIPE_RENDERER + "st.markdown(\n    \"\"\"\n<style>", "recipe renderer")
    text = regex_once(
        text,
        r'''                if st\.button\(\n                    "Edit",\n                    key=f"recipe_repo_edit_\{index\}",\n                    use_container_width=True,\n                \):\n.*?                    st\.rerun\(\)''',
        '''                if st.button(
                    "Edit",
                    key=f"recipe_repo_edit_{index}",
                    use_container_width=True,
                ):
                    st.session_state["hm_recipe_workspace_mode"] = "edit"
                    st.session_state["hm_recipe_workspace_id"] = int(index)
                    st.session_state.pop("hm_recipe_repository_delete_index", None)
                    st.switch_page("pages/15A_Admin_Recipe_Form.py")''',
        "recipe edit navigation",
    )
    text = regex_once(
        text,
        r'''\n            if st\.session_state\.get\("hm_recipe_repository_edit_index"\) == int\(index\):.*?\n            if st\.session_state\.get\("hm_recipe_repository_delete_index"\) == int\(index\):''',
        '\n            if st.session_state.get("hm_recipe_repository_delete_index") == int(index):',
        "recipe inline edit removal",
    )
    text = regex_once(
        text,
        r'''with add_tab:\n.*?\nrender_page_nav\(''',
        '''with add_tab:
    st.caption("Add and Edit now open in a dedicated workspace so this repository stays fast and easy to scan.")
    if st.button("Add Recipe", type="primary", use_container_width=False):
        st.session_state["hm_recipe_workspace_mode"] = "add"
        st.session_state.pop("hm_recipe_workspace_id", None)
        st.switch_page("pages/15A_Admin_Recipe_Form.py")
render_page_nav(''',
        "recipe add workspace",
    )
    path.write_text(text, encoding="utf-8")


def transform_exercise(path: Path) -> None:
    text = add_common_import(path.read_text(encoding="utf-8"))
    text = replace_once(text, "st.markdown(\n    \"\"\"\n<style>", EXERCISE_RENDERER + "st.markdown(\n    \"\"\"\n<style>", "exercise renderer")
    text = regex_once(
        text,
        r'''            if st\.button\(\n                "Edit",\n                key=f"exercise_repo_edit_\{exercise_id\}",\n                use_container_width=True,\n            \):\n.*?                st\.rerun\(\)''',
        '''            if st.button(
                "Edit",
                key=f"exercise_repo_edit_{exercise_id}",
                use_container_width=True,
            ):
                st.session_state["hm_exercise_workspace_mode"] = "edit"
                st.session_state["hm_exercise_workspace_id"] = exercise_id
                st.session_state.pop("hm_exercise_repository_delete_id", None)
                st.switch_page("pages/16A_Admin_Exercise_Form.py")''',
        "exercise edit navigation",
    )
    text = regex_once(
        text,
        r'''\n        if st\.session_state\.get\("hm_exercise_repository_edit_id"\) == exercise_id:.*?\n        if st\.session_state\.get\("hm_exercise_repository_delete_id"\) == exercise_id:''',
        '\n        if st.session_state.get("hm_exercise_repository_delete_id") == exercise_id:',
        "exercise inline edit removal",
    )
    text = regex_once(
        text,
        r'''with add_tab:\n.*?\nrender_page_nav\(''',
        '''with add_tab:
    st.caption("Add and Edit now open in a dedicated workspace so this repository stays fast and easy to scan.")
    if st.button("Add Exercise", type="primary", use_container_width=False):
        st.session_state["hm_exercise_workspace_mode"] = "add"
        st.session_state.pop("hm_exercise_workspace_id", None)
        st.switch_page("pages/16A_Admin_Exercise_Form.py")
render_page_nav(''',
        "exercise add workspace",
    )
    path.write_text(text, encoding="utf-8")


def transform_supplement(path: Path) -> None:
    text = add_common_import(path.read_text(encoding="utf-8"))
    text = replace_once(text, "st.markdown(\n    \"\"\"\n<style>", SUPPLEMENT_RENDERER + "st.markdown(\n    \"\"\"\n<style>", "supplement renderer")
    text = regex_once(
        text,
        r'''            if st\.button\(\n                "Edit",\n                key=f"supplement_repo_edit_\{supplement_id\}",\n                use_container_width=True,\n            \):\n.*?                st\.rerun\(\)''',
        '''            if st.button(
                "Edit",
                key=f"supplement_repo_edit_{supplement_id}",
                use_container_width=True,
            ):
                st.session_state["hm_supplement_workspace_mode"] = "edit"
                st.session_state["hm_supplement_workspace_id"] = supplement_id
                st.session_state.pop("hm_supplement_repository_delete_id", None)
                st.switch_page("pages/39A_Admin_Supplement_Form.py")''',
        "supplement edit navigation",
    )
    text = regex_once(
        text,
        r'''\n        if st\.session_state\.get\("hm_supplement_repository_edit_id"\) == supplement_id:.*?\n        if st\.session_state\.get\("hm_supplement_repository_delete_id"\) == supplement_id:''',
        '\n        if st.session_state.get("hm_supplement_repository_delete_id") == supplement_id:',
        "supplement inline edit removal",
    )
    text = regex_once(
        text,
        r'''with add_tab:\n.*?\nrender_page_nav\(''',
        '''with add_tab:
    st.caption("Add and Edit now open in a dedicated workspace so this repository stays fast and easy to scan.")
    if st.button("Add Supplement", type="primary", use_container_width=False):
        st.session_state["hm_supplement_workspace_mode"] = "add"
        st.session_state.pop("hm_supplement_workspace_id", None)
        st.switch_page("pages/39A_Admin_Supplement_Form.py")
render_page_nav(''',
        "supplement add workspace",
    )
    path.write_text(text, encoding="utf-8")


def write_entry(path: Path, flag: str, manager: str, run_name: str) -> None:
    path.write_text(
        f'''from __future__ import annotations\n\nimport runpy\nfrom pathlib import Path\n\nimport streamlit as st\n\n\nst.session_state["{flag}"] = True\ntry:\n    runpy.run_path(\n        str(Path(__file__).resolve().with_name("{manager}")),\n        run_name="{run_name}",\n    )\nfinally:\n    st.session_state.pop("{flag}", None)\n''',
        encoding="utf-8",
    )


def main() -> None:
    transform_recipe(ROOT / "pages" / "15_Admin_Recipe_Manager.py")
    transform_exercise(ROOT / "pages" / "16_Admin_Exercise_Manager.py")
    transform_supplement(ROOT / "pages" / "39_Admin_Supplement_Manager.py")
    write_entry(
        ROOT / "pages" / "15A_Admin_Recipe_Form.py",
        "_hm_recipe_workspace_embedded",
        "15_Admin_Recipe_Manager.py",
        "__hm_recipe_workspace__",
    )
    write_entry(
        ROOT / "pages" / "16A_Admin_Exercise_Form.py",
        "_hm_exercise_workspace_embedded",
        "16_Admin_Exercise_Manager.py",
        "__hm_exercise_workspace__",
    )
    write_entry(
        ROOT / "pages" / "39A_Admin_Supplement_Form.py",
        "_hm_supplement_workspace_embedded",
        "39_Admin_Supplement_Manager.py",
        "__hm_supplement_workspace__",
    )


if __name__ == "__main__":
    main()
