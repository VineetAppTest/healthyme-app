from __future__ import annotations

import streamlit as st

from components.member_timezone import member_local_today


_MEMBER_KEY = "_hm_daily_guidance_selected_member_id"


def install_daily_guidance_today_default() -> None:
    """Default new General Guidance entries to the selected member's local today."""

    if getattr(st, "_hm_daily_guidance_today_default_installed", False):
        return
    st._hm_daily_guidance_today_default_installed = True

    base_selectbox = st.selectbox
    base_date_input = st.date_input

    def selectbox_with_member_capture(label, options, *args, **kwargs):
        selected = base_selectbox(label, options, *args, **kwargs)
        if label == "Select member" and isinstance(selected, str) and " — " in selected:
            st.session_state[_MEMBER_KEY] = selected.split(" — ", 1)[0].strip()
        return selected

    def date_input_with_guidance_today(label, *args, **kwargs):
        if label == "Guidance Date":
            member_id = st.session_state.get(_MEMBER_KEY, "")
            kwargs["value"] = member_local_today(member_id)
            original_key = str(kwargs.get("key") or "h9a4_general_guidance_date")
            kwargs["key"] = f"{original_key}_{member_id or 'member'}"
        return base_date_input(label, *args, **kwargs)

    st.selectbox = selectbox_with_member_capture
    st.date_input = date_input_with_guidance_today
