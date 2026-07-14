from __future__ import annotations

import streamlit as st

from components.pbm_core import (
    SELECT_AGE,
    SELECT_DIET,
    SELECT_DRAFT,
    SELECT_MEMBER,
    bump_epoch,
    clean,
    clean_date,
    load_selected,
    member_maps,
    profile_from_db,
    profile_payload,
    reset_profile,
    with_placeholder,
)
from components.profile_builder_module_store import (
    list_draft_profiles_for_member,
    save_profile_shell,
)
from components.recommendation_profile_store import (
    check_profile_builder_store,
    list_profile_sources,
    load_profile,
)


def _clear_setup_edit_profile() -> None:
    st.session_state.pop("pbm_setup_edit_profile", None)


def _start_new_profile() -> None:
    reset_profile()
    st.session_state.pop("pbm_setup_edit_member", None)
    st.session_state.pop("pbm_setup_edit_profile", None)
    st.session_state["pbm_setup_message"] = "New blank profile started."


def render_setup(options) -> None:
    st.markdown(
        "<div class='hm-title'>Recommendation Profile Setup</div>"
        "<div class='hm-sub'>Create and save the profile shell only. "
        "Meals, Exercise and Supplements are selected and saved separately.</div>",
        unsafe_allow_html=True,
    )

    member_labels, label_to_id, id_to_label, member_message = member_maps()

    st.markdown(
        "<div class='hm-preview'><b>Edit Existing Profile Setup</b><br>"
        "Select a member first. Only that member's Draft Profiles will be available. "
        "Loading Setup does not load or change Meal, Exercise or Supplement rows.</div>",
        unsafe_allow_html=True,
    )

    edit_columns = st.columns([0.28, 0.42, 0.15, 0.15], gap="medium")
    edit_member_label = edit_columns[0].selectbox(
        "Member for Setup Editing",
        member_labels,
        key="pbm_setup_edit_member",
        on_change=_clear_setup_edit_profile,
    )
    edit_member_id = label_to_id.get(edit_member_label, "")

    if edit_member_id:
        ok_drafts, drafts, draft_message = list_draft_profiles_for_member(edit_member_id)
    else:
        ok_drafts, drafts, draft_message = (
            False,
            [],
            "Select a member to view their Draft Profiles.",
        )

    draft_ids = [""] + [clean(row.get("id")) for row in drafts] if ok_drafts else [""]
    draft_by_id = {
        clean(row.get("id")): row
        for row in drafts
        if clean(row.get("id"))
    }

    selected_draft = edit_columns[1].selectbox(
        "Edit Existing Profile Setup",
        draft_ids,
        format_func=lambda value: (
            SELECT_DRAFT
            if not value
            else (
                f"{draft_by_id[value].get('profile_name', 'Untitled')} · "
                f"{str(draft_by_id[value].get('updated_at', ''))[:16]}"
            )
        ),
        key="pbm_setup_edit_profile",
        disabled=not bool(edit_member_id),
    )

    edit_columns[2].markdown(
        "<div class='hm-load-label' aria-hidden='true'>&nbsp;</div>",
        unsafe_allow_html=True,
    )
    if edit_columns[2].button(
        "Load Setup",
        use_container_width=True,
        disabled=not bool(selected_draft),
    ):
        ok, message = load_selected(selected_draft, shell_only=True)
        if ok:
            loaded_member_id = clean(st.session_state["pbm_profile"].get("assigned_member_id"))
            if loaded_member_id != edit_member_id:
                reset_profile()
                st.error(
                    "The selected profile no longer belongs to the selected member. "
                    "Nothing was loaded."
                )
            else:
                st.session_state["pbm_setup_message"] = (
                    "Profile Setup loaded for editing. Recommendation modules "
                    "were not loaded or changed."
                )
                st.rerun()
        else:
            st.error(message)

    edit_columns[3].markdown(
        "<div class='hm-load-label' aria-hidden='true'>&nbsp;</div>",
        unsafe_allow_html=True,
    )
    edit_columns[3].button(
        "New Profile",
        use_container_width=True,
        on_click=_start_new_profile,
    )

    message = st.session_state.pop("pbm_setup_message", "")
    if message:
        st.success(message)

    if edit_member_id:
        if ok_drafts and not drafts:
            st.caption("No Draft Profiles were found for the selected member.")
        elif not ok_drafts:
            st.caption(draft_message)

    profile = st.session_state["pbm_profile"]
    epoch = st.session_state.get("pbm_epoch", 0)
    profile["assigned_member_label"] = id_to_label.get(
        clean(profile.get("assigned_member_id")),
        profile.get("assigned_member_label") or SELECT_MEMBER,
    )

    source_ok, sources, source_message = list_profile_sources()
    source_ids = [""] + [clean(row.get("id")) for row in sources] if source_ok else [""]
    source_by_id = {
        clean(row.get("id")): row
        for row in sources
        if clean(row.get("id"))
    }

    left, right = st.columns(2, gap="large")
    with left:
        profile["profile_name"] = st.text_input(
            "Profile Name",
            value=profile.get("profile_name", ""),
            key=f"pbm_profile_name_{epoch}",
        )
        clone_columns = st.columns([0.70, 0.30], gap="small")
        clone_id = clone_columns[0].selectbox(
            "Clone Profile Setup From",
            source_ids,
            format_func=lambda value: (
                "New profile"
                if not value
                else (
                    f"{source_by_id[value].get('profile_name', 'Untitled')} "
                    f"[{source_by_id[value].get('status', 'draft')}]"
                )
            ),
            key="pbm_profile_clone_source",
        )
        if clone_columns[1].button(
            "Clone Setup",
            use_container_width=True,
            disabled=not bool(clone_id),
        ):
            ok, source_profile, _items, clone_message = load_profile(clone_id)
            if ok:
                cloned = profile_from_db(source_profile)
                cloned["id"] = ""
                cloned["profile_name"] = f"Copy of {cloned['profile_name']}"
                cloned["clone_source_profile_id"] = clone_id
                cloned["clone_source_label"] = source_by_id[clone_id].get(
                    "profile_name",
                    "Selected profile",
                )
                st.session_state["pbm_profile"] = cloned
                st.session_state["pbm_items"] = []
                bump_epoch()
                st.success(
                    "Profile Setup cloned. Recommendation rows were not copied."
                )
                st.rerun()
            st.error(clone_message)

        profile["change_note"] = st.text_input(
            "Change Note",
            value=profile.get("change_note", ""),
            key=f"pbm_profile_change_note_{epoch}",
        )
        st.text_input("Profile Status", value="Draft", disabled=True)

    with right:
        profile["region"] = st.text_input(
            "Region / Food Culture",
            value=profile.get("region", ""),
            key=f"pbm_profile_region_{epoch}",
        )
        age_options = with_placeholder(options["age_band"], SELECT_AGE)
        current_age = profile.get("age_band")
        if current_age not in age_options:
            age_options.append(current_age)
        profile["age_band"] = st.selectbox(
            "Age Band",
            age_options,
            index=age_options.index(current_age),
            key=f"pbm_profile_age_band_{epoch}",
        )

        concerns = list(options["health_concern"])
        for concern in profile.get("health_concerns", []):
            if concern not in concerns:
                concerns.append(concern)
        profile["health_concerns"] = st.multiselect(
            "Health Concerns",
            concerns,
            default=profile.get("health_concerns", []),
            key=f"pbm_profile_health_concerns_{epoch}",
        )

        diet_options = with_placeholder(options["diet_type"], SELECT_DIET)
        current_diet = profile.get("diet_type")
        if current_diet not in diet_options:
            diet_options.append(current_diet)
        profile["diet_type"] = st.selectbox(
            "Diet Type",
            diet_options,
            index=diet_options.index(current_diet),
            key=f"pbm_profile_diet_type_{epoch}",
        )

    lower_left, lower_right = st.columns(2, gap="large")
    with lower_left:
        current_member = profile.get("assigned_member_label", SELECT_MEMBER)
        if current_member not in member_labels:
            current_member = SELECT_MEMBER
        member_label = st.selectbox(
            "Member Assignment",
            member_labels,
            index=member_labels.index(current_member),
            key=f"pbm_profile_member_{epoch}",
        )
        profile["assigned_member_label"] = member_label
        profile["assigned_member_id"] = label_to_id.get(member_label, "")
        profile["profile_note"] = st.text_area(
            "Profile-level Nutritionist Note",
            value=profile.get("profile_note", ""),
            height=150,
            key=f"pbm_profile_note_{epoch}",
        )

    with lower_right:
        profile["start_date"] = st.date_input(
            "Plan Start Date",
            value=clean_date(profile.get("start_date")),
            key=f"pbm_profile_start_date_{epoch}",
        )
        st.text_input(
            "Cycle Rule",
            value="Weekly cyclical until replaced or stopped",
            disabled=True,
        )
        st.text_input(
            "Implementation Status",
            value="Setup shell and module-specific saves enabled.",
            disabled=True,
        )

    st.caption(f"Member source: {member_message} Profile source: {source_message}")

    if st.button(
        "Save Profile Setup",
        type="primary",
        use_container_width=True,
        disabled=not check_profile_builder_store().get("ok"),
    ):
        ok, profile_id, save_message = save_profile_shell(profile_payload())
        if ok:
            profile["id"] = profile_id
            st.session_state["pbm_loaded_profile_id"] = profile_id
            st.session_state["pbm_loaded_member_id"] = profile.get(
                "assigned_member_id",
                "",
            )
            st.success(save_message)
        else:
            st.error(save_message)

    st.markdown(
        "<div class='hm-preview'><b>Setup boundary</b><br>"
        "Saving Setup creates or updates the profile shell only. It does not "
        "create, replace or delete Meal, Exercise or Supplement rows.</div>",
        unsafe_allow_html=True,
    )
