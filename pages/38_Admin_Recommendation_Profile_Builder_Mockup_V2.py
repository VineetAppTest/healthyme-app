import streamlit as st

PB_SCHEDULE_SCHEMA_VERSION = "v100.26"

st.set_page_config(
    page_title="Recommendation Profile Builder Mock-up V2",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hard reset only when the Profile Builder schedule schema changes.
# This clears old Streamlit widget/session keys that can keep legacy Exercise/Supplement slots alive
# after deploy, while avoiding repeated resets on every rerun once the schema marker is current.
if st.session_state.get("pb_schedule_schema_version") != PB_SCHEDULE_SCHEMA_VERSION:
    stale_prefixes = (
        "pbw_exercise_",
        "pbw_supplement_",
        "pbw_meal_",
        "add_exercise_",
        "add_supplement_",
        "add_meal_",
    )
    stale_exact_keys = {
        "pb_items",
        "pb_row_counts",
        "v4_exercise_day",
        "v4_supp_day",
        "v4_meal_day",
        "v4_preview_day",
        "v4_profile_action_message",
        "v4_clone_action_message",
    }
    for key in list(st.session_state.keys()):
        if key in stale_exact_keys or str(key).startswith(stale_prefixes):
            st.session_state.pop(key, None)
    st.session_state["v4_active_section"] = "Profile Setup"
    st.session_state["pb_schedule_schema_version"] = PB_SCHEDULE_SCHEMA_VERSION
    st.session_state["pb_force_schedule_reset"] = True

st.switch_page("pages/41_Admin_Recommendation_Profile_Builder_Mockup_V5.py")
