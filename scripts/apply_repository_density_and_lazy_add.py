from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


recipe = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
exercise = ROOT / "pages" / "16_Admin_Exercise_Manager.py"
supplement = ROOT / "pages" / "39_Admin_Supplement_Manager.py"

# Opening Edit must close Add so only one large form is rendered.
replace_once(
    recipe,
    '                    st.session_state.pop("hm_recipe_repository_delete_index", None)\n                    st.rerun()',
    '                    st.session_state.pop("hm_recipe_repository_delete_index", None)\n                    st.session_state["hm_recipe_repository_add_open"] = False\n                    st.rerun()',
    "recipe edit closes add",
)
replace_once(
    exercise,
    '                st.session_state.pop("hm_exercise_repository_delete_id", None)\n                st.rerun()',
    '                st.session_state.pop("hm_exercise_repository_delete_id", None)\n                st.session_state["hm_exercise_repository_add_open"] = False\n                st.rerun()',
    "exercise edit closes add",
)
replace_once(
    supplement,
    '                st.session_state.pop("hm_supplement_repository_delete_id", None)\n                st.rerun()',
    '                st.session_state.pop("hm_supplement_repository_delete_id", None)\n                st.session_state["hm_supplement_repository_add_open"] = False\n                st.rerun()',
    "supplement edit closes add",
)

recipe_old = '''with add_tab:
    with repository_form_panel():
        st.subheader("Add Recipe")
        values = recipe_form("new_recipe_repository")
        if st.button("Save Recipe", type="primary", use_container_width=True):
            if not _clean(values.get("title")):
                st.error("Recipe title is required.")
            else:
                df = load()
                df.loc[len(df)] = [values.get(column, "") for column in RECIPE_COLUMNS]
                save(df)
                _flash("Recipe saved.")
                st.rerun()
'''
recipe_new = '''with add_tab:
    add_open = bool(st.session_state.get("hm_recipe_repository_add_open", False))
    if render_repository_disclosure(
        "Add Recipe",
        is_open=add_open,
        key="recipe_repo_add_disclosure",
    ):
        st.session_state["hm_recipe_repository_add_open"] = not add_open
        if not add_open:
            st.session_state.pop("hm_recipe_repository_edit_index", None)
            st.session_state.pop("hm_recipe_repository_delete_index", None)
        st.rerun()
    if add_open:
        with repository_form_panel():
            values = recipe_form("new_recipe_repository")
            if st.button("Save Recipe", type="primary", use_container_width=True):
                if not _clean(values.get("title")):
                    st.error("Recipe title is required.")
                else:
                    df = load()
                    df.loc[len(df)] = [values.get(column, "") for column in RECIPE_COLUMNS]
                    save(df)
                    _flash("Recipe saved.")
                    st.rerun()
'''
replace_once(recipe, recipe_old, recipe_new, "recipe lazy add")

exercise_old = '''with add_tab:
    with repository_form_panel():
        st.subheader("Add Exercise")
        values = exercise_form("new_exercise_repository")
        if st.button("Save Exercise", type="primary", use_container_width=True):
            try:
                add_exercise_repository_item(values, actor_id=_actor_id())
                _flash("Exercise saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
'''
exercise_new = '''with add_tab:
    add_open = bool(st.session_state.get("hm_exercise_repository_add_open", False))
    if render_repository_disclosure(
        "Add Exercise",
        is_open=add_open,
        key="exercise_repo_add_disclosure",
    ):
        st.session_state["hm_exercise_repository_add_open"] = not add_open
        if not add_open:
            st.session_state.pop("hm_exercise_repository_edit_id", None)
            st.session_state.pop("hm_exercise_repository_delete_id", None)
        st.rerun()
    if add_open:
        with repository_form_panel():
            values = exercise_form("new_exercise_repository")
            if st.button("Save Exercise", type="primary", use_container_width=True):
                try:
                    add_exercise_repository_item(values, actor_id=_actor_id())
                    _flash("Exercise saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
'''
replace_once(exercise, exercise_old, exercise_new, "exercise lazy add")

supplement_old = '''with add_tab:
    with repository_form_panel():
        st.subheader("Add Supplement")
        with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
            st.markdown("#### Basic Details")
            name = st.text_input(
                "Supplement Name", placeholder="e.g. Magnesium Glycinate"
            )
            dose_col, frequency_col = st.columns(2)
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
            timing_options = st.multiselect(
                "Default Timing", TIMING_OPTIONS, default=[]
            )
            custom_timing = st.text_input(
                "Additional Timing",
                placeholder="Optional custom timing; separate multiple values with commas.",
            )
            st.markdown("#### Instructions")
            instructions = st.text_area(
                "Default Instructions",
                placeholder="Reusable guidance that can be adjusted during member allocation.",
            )
            submitted = st.form_submit_button(
                "Add to Repository", use_container_width=True
            )
            if submitted:
                try:
                    add_supplement_repository_item(
                        {
                            "supplement_name": name,
                            "dosage": dosage,
                            "frequency": frequency,
                            "timing": _timing_from_choices(
                                timing_options, custom_timing
                            ),
                            "instructions": instructions,
                        },
                        actor_id=_actor_id(),
                    )
                    _flash("Supplement added to repository.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
'''
supplement_new = '''with add_tab:
    add_open = bool(st.session_state.get("hm_supplement_repository_add_open", False))
    if render_repository_disclosure(
        "Add Supplement",
        is_open=add_open,
        key="supplement_repo_add_disclosure",
    ):
        st.session_state["hm_supplement_repository_add_open"] = not add_open
        if not add_open:
            st.session_state.pop("hm_supplement_repository_edit_id", None)
            st.session_state.pop("hm_supplement_repository_delete_id", None)
        st.rerun()
    if add_open:
        with repository_form_panel():
            with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
                st.markdown("#### Basic Details")
                name = st.text_input(
                    "Supplement Name", placeholder="e.g. Magnesium Glycinate"
                )
                dose_col, frequency_col = st.columns(2)
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
                timing_options = st.multiselect(
                    "Default Timing", TIMING_OPTIONS, default=[]
                )
                custom_timing = st.text_input(
                    "Additional Timing",
                    placeholder="Optional custom timing; separate multiple values with commas.",
                )
                st.markdown("#### Instructions")
                instructions = st.text_area(
                    "Default Instructions",
                    placeholder="Reusable guidance that can be adjusted during member allocation.",
                )
                submitted = st.form_submit_button(
                    "Add to Repository", use_container_width=True
                )
                if submitted:
                    try:
                        add_supplement_repository_item(
                            {
                                "supplement_name": name,
                                "dosage": dosage,
                                "frequency": frequency,
                                "timing": _timing_from_choices(
                                    timing_options, custom_timing
                                ),
                                "instructions": instructions,
                            },
                            actor_id=_actor_id(),
                        )
                        _flash("Supplement added to repository.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
'''
replace_once(supplement, supplement_old, supplement_new, "supplement lazy add")

print("Repository Add forms now render only on demand.")
