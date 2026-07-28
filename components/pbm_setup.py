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
    EDIT_SCOPE_ALL,
    EDIT_SCOPE_UNALLOCATED,
    list_profiles_for_editing,
    save_profile_shell,
)
from components.recommendation_profile_store import (
    check_profile_builder_store,
    list_profile_sources,
    load_profile,
)

ALL_PROFILE_SCOPE = "All editable profiles"
UNALLOCATED_PROFILE_SCOPE = "Unallocated profiles"


def _clear_setup_edit_profile() -> None:
    st.session_state.pop("pbm_setup_edit_profile", None)


def _start_new_profile() -> None:
    reset_profile()
    st.session_state.pop("pbm_setup_edit_scope", None)
    st.session_state.pop("pbm_setup_edit_profile", None)
    st.session_state["pbm_setup_message"] = "New blank Draft profile started."


def _profile_scope_options(member_labels):
    assigned_members = [label for label in member_labels if label != SELECT_MEMBER]
    return [ALL_PROFILE_SCOPE, UNALLOCATED_PROFILE_SCOPE] + assigned_members


def _scope_value(scope_label, label_to_id):
    if scope_label == UNALLOCATED_PROFILE_SCOPE:
        return EDIT_SCOPE_UNALLOCATED
    if scope_label == ALL_PROFILE_SCOPE:
        return EDIT_SCOPE_ALL
    return label_to_id.get(scope_label, EDIT_SCOPE_ALL)


def _profile_option_label(row) -> str:
    status = clean(row.get("status"), "draft").upper()
    assignment = clean(row.get("assigned_member_label")) or "Unallocated"
    updated = str(row.get("updated_at") or "")[:16]
    return (
        f"{row.get('profile_name', 'Untitled')} · {status} · "
        f"{assignment} · {updated}"
    )


def render_setup(options) -> None:
    st.markdown(
        "<div class='hm-title'>Recommendation Profile Setup</div>"
        "<div class='hm-sub'>Create a new profile or load an existing Draft or Active profile for in-place editing.</div>",
        unsafe_allow_html=True,
    )

    member_labels, label_to_id, id_to_label, member_message = member_maps()

    st.markdown(
        "<div class='hm-preview'><b>Edit Existing Recommendation Profile</b><br>"
        "Use the scope filter to find allocated or unallocated profiles. Load Profile hydrates Setup, Meals, Exercise and Supplements together. "
        "Saving updates the same Profile ID. Use Clone Setup only when a new Draft/version is intended.</div>",
        unsafe_allow_html=True,
    )

    edit_columns = st.columns([0.26, 0.46, 0.14, 0.14], gap="medium")
    scope_options = _profile_scope_options(member_labels)
    selected_scope = edit_columns[0].selectbox(
        "Profile Scope",
        scope_options,
        key="pbm_setup_edit_scope",
        on_change=_clear_setup_edit_profile,
    )
    scope_value = _scope_value(selected_scope, label_to_id)
    ok_profiles, profiles, profile_message = list_profiles_for_editing(scope_value)

    profile_ids = [""] + [clean(row.get("id")) for row in profiles] if ok_profiles else [""]
    profile_by_id = {
        clean(row.get("id")): row
        for row in profiles
        if clean(row.get("id"))
    }

    selected_profile = edit_columns[1].selectbox(
        "Edit Existing Profile",
        profile_ids,
        format_func=lambda value: (
            SELECT_DRAFT if not value else _profile_option_label(profile_by_id[value])
        ),
        key="pbm_setup_edit_profile",
    )

    edit_columns[2].markdown(
        "<div class='hm-load-label' aria-hidden='true'>&nbsp;</div>",
        unsafe_allow_html=True,
    )
    if edit_columns[2].button(
        "Load Profile",
        use_container_width=True,
        disabled=not bool(selected_profile),
    ):
        ok, message = load_selected(selected_profile, shell_only=False)
        if ok:
            loaded = st.session_state["pbm_profile"]
            st.session_state["pbm_setup_message"] = (
                f"{clean(loaded.get('profile_name')) or 'Profile'} loaded with Setup, Meals, Exercise and Supplements. "
                "Future saves will update the same Profile ID."
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

    if ok_profiles and not profiles:
        st.caption("No editable Draft or Active profiles were found for this scope.")
    elif not ok_profiles:
        st.caption(profile_message)
    else:
        st.caption(
            f"{profile_message} Archived and replaced profiles remain historical and are intentionally not editable in place."
        )

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
                cloned["status"] = "draft"
                cloned["profile_name"] = f"Copy of {cloned['profile_name']}"
                cloned["clone_source_profile_id"] = clone_id
                cloned["clone_source_label"] = source_by_id[clone_id].get(
                    "profile_name",
                    "Selected profile",
                )
                st.session_state["pbm_profile"] = cloned
                st.session_state["pbm_items"] = []
                st.session_state["pbm_loaded_profile_id"] = ""
                st.session_state["pbm_loaded_member_id"] = ""
                bump_epoch()
                st.success(
                    "Profile Setup cloned as a new Draft. Recommendation rows were not copied."
                )
                st.rerun()
            st.error(clone_message)

        profile["change_note"] = st.text_input(
            "Change Note",
            value=profile.get("change_note", ""),
            key=f"pbm_profile_change_note_{epoch}",
        )
        profile_status = clean(profile.get("status"), "draft").title()
        st.text_input("Profile Status", value=profile_status, disabled=True)

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
        active_existing = bool(profile.get("id")) and clean(profile.get("status")).lower() == "active"
        member_label = st.selectbox(
            "Member Assignment",
            member_labels,
            index=member_labels.index(current_member),
            key=f"pbm_profile_member_{epoch}",
            disabled=active_existing,
            help=(
                "Active profile allocation is protected while content is edited. Use Publish Control to replace the active profile."
                if active_existing
                else "Draft profiles may remain unallocated or be assigned to a member."
            ),
        )
        profile["assigned_member_label"] = member_label
        profile["assigned_member_id"] = label_to_id.get(member_label, "")
        if active_existing:
            st.caption(
                "Active allocation is locked here so editing cannot detach or reassign the member."
            )
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
            value="Existing profile editing and module-specific saves enabled.",
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
            profile["status"] = clean(profile.get("status"), "draft").lower()
            st.session_state["pbm_loaded_profile_id"] = profile_id
            st.session_state["pbm_loaded_member_id"] = profile.get(
                "assigned_member_id",
                "",
            )
            st.success(save_message)
        else:
            st.error(save_message)

    st.markdown(
        "<div class='hm-preview'><b>Editing boundary</b><br>"
        "Saving Setup updates the loaded Profile ID and preserves its status and allocation. It does not create, replace or delete Meal, Exercise or Supplement rows. "
        "Clone Setup is the explicit action for creating a new Draft/version.</div>",
        unsafe_allow_html=True,
    )
