from __future__ import annotations

import streamlit as st

from components.pbm_core import (
    SELECT_AGE, SELECT_DIET, SELECT_DRAFT, SELECT_MEMBER,
    clean, clean_date, clear_widgets, load_selected, member_maps,
    profile_from_db, profile_payload, reset_profile, with_placeholder,
)
from components.profile_builder_module_store import save_profile_shell
from components.recommendation_profile_store import (
    check_profile_builder_store, list_draft_profiles, list_profile_sources,
    load_profile,
)


def render_setup(options) -> None:
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Create and save the profile shell only. Meals, Exercise and Supplements are selected and saved separately.</div>", unsafe_allow_html=True)
    member_labels, label_to_id, id_to_label, member_message = member_maps()
    ok_drafts, drafts, draft_message = list_draft_profiles(); draft_ids = [""] + [clean(row.get("id")) for row in drafts] if ok_drafts else [""]; draft_by_id = {clean(row.get("id")): row for row in drafts}
    load_columns = st.columns([.56, .20, .24], gap="medium")
    selected_draft = load_columns[0].selectbox("Load saved profile", draft_ids, format_func=lambda value: SELECT_DRAFT if not value else f"{draft_by_id[value].get('profile_name','Untitled')} · {str(draft_by_id[value].get('updated_at',''))[:16]}", key="pbm_setup_load_profile")
    if load_columns[1].button("Load Profile", use_container_width=True, disabled=not bool(selected_draft)):
        ok, message = load_selected(selected_draft, shell_only=True)
        if ok: st.session_state["pbm_setup_message"] = message; st.rerun()
        st.error(message)
    if load_columns[2].button("New Profile", use_container_width=True): reset_profile(); st.session_state["pbm_setup_message"] = "New blank profile started."; st.rerun()
    message = st.session_state.pop("pbm_setup_message", "")
    if message: st.success(message)
    if not ok_drafts: st.caption(draft_message)

    profile = st.session_state["pbm_profile"]
    profile["assigned_member_label"] = id_to_label.get(clean(profile.get("assigned_member_id")), profile.get("assigned_member_label") or SELECT_MEMBER)
    source_ok, sources, source_message = list_profile_sources(); source_ids = [""] + [clean(row.get("id")) for row in sources] if source_ok else [""]; source_by_id = {clean(row.get("id")): row for row in sources}
    left, right = st.columns(2, gap="large")
    with left:
        profile["profile_name"] = st.text_input("Profile Name", value=profile.get("profile_name", ""), key="pbm_profile_name")
        clone_columns = st.columns([.70, .30], gap="small")
        clone_id = clone_columns[0].selectbox("Clone Profile Setup From", source_ids, format_func=lambda value: "New profile" if not value else f"{source_by_id[value].get('profile_name','Untitled')} [{source_by_id[value].get('status','draft')}]", key="pbm_profile_clone_source")
        if clone_columns[1].button("Clone Setup", use_container_width=True, disabled=not bool(clone_id)):
            ok, source_profile, _items, clone_message = load_profile(clone_id)
            if ok:
                cloned = profile_from_db(source_profile); cloned["id"] = ""; cloned["profile_name"] = f"Copy of {cloned['profile_name']}"; cloned["clone_source_profile_id"] = clone_id; cloned["clone_source_label"] = source_by_id[clone_id].get("profile_name", "Selected profile")
                clear_widgets("pbm_profile_"); st.session_state["pbm_profile"] = cloned; st.session_state["pbm_items"] = []; st.success("Profile Setup cloned. Recommendation rows were not copied."); st.rerun()
            st.error(clone_message)
        profile["change_note"] = st.text_input("Change Note", value=profile.get("change_note", ""), key="pbm_profile_change_note")
        st.text_input("Profile Status", value="Draft", disabled=True)
    with right:
        profile["region"] = st.text_input("Region / Food Culture", value=profile.get("region", ""), key="pbm_profile_region")
        age_options = with_placeholder(options["age_band"], SELECT_AGE); current_age = profile.get("age_band")
        if current_age not in age_options: age_options.append(current_age)
        profile["age_band"] = st.selectbox("Age Band", age_options, index=age_options.index(current_age), key="pbm_profile_age_band")
        concerns = list(options["health_concern"])
        for concern in profile.get("health_concerns", []):
            if concern not in concerns: concerns.append(concern)
        profile["health_concerns"] = st.multiselect("Health Concerns", concerns, default=profile.get("health_concerns", []), key="pbm_profile_health_concerns")
        diet_options = with_placeholder(options["diet_type"], SELECT_DIET); current_diet = profile.get("diet_type")
        if current_diet not in diet_options: diet_options.append(current_diet)
        profile["diet_type"] = st.selectbox("Diet Type", diet_options, index=diet_options.index(current_diet), key="pbm_profile_diet_type")
    lower_left, lower_right = st.columns(2, gap="large")
    with lower_left:
        current_member = profile.get("assigned_member_label", SELECT_MEMBER)
        if current_member not in member_labels: current_member = SELECT_MEMBER
        member_label = st.selectbox("Member Assignment", member_labels, index=member_labels.index(current_member), key="pbm_profile_member"); profile["assigned_member_label"] = member_label; profile["assigned_member_id"] = label_to_id.get(member_label, "")
        profile["profile_note"] = st.text_area("Profile-level Nutritionist Note", value=profile.get("profile_note", ""), height=150, key="pbm_profile_note")
    with lower_right:
        profile["start_date"] = st.date_input("Plan Start Date", value=clean_date(profile.get("start_date")), key="pbm_profile_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True)
        st.text_input("Implementation Status", value="Setup shell and module-specific saves enabled.", disabled=True)
    st.caption(f"Member source: {member_message} Profile source: {source_message}")
    if st.button("Save Profile Setup", type="primary", use_container_width=True, disabled=not check_profile_builder_store().get("ok")):
        ok, profile_id, save_message = save_profile_shell(profile_payload())
        if ok: profile["id"] = profile_id; st.session_state["pbm_loaded_profile_id"] = profile_id; st.session_state["pbm_loaded_member_id"] = profile.get("assigned_member_id", ""); st.success(save_message)
        else: st.error(save_message)
    st.markdown("<div class='hm-preview'><b>Setup boundary</b><br>Saving Setup creates or updates the profile shell only. It does not create, replace or delete Meal, Exercise or Supplement rows.</div>", unsafe_allow_html=True)
