import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_page_nav, render_back_to_top
from components.db import get_meal_type_repository, save_meal_type_repository
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Log Settings", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()
render_page_nav("Daily Log Settings", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
topbar("Daily Log Settings", "", "Admin repository")
render_system_message()

rows = get_meal_type_repository()
card_start()
st.subheader("Meal section repository")

edited = st.data_editor(
    rows,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "key": st.column_config.TextColumn("Key", help="Stable internal key. Use lowercase words with underscores."),
        "label": st.column_config.TextColumn("Meal Section Label"),
        "active": st.column_config.CheckboxColumn("Active"),
        "sort_order": st.column_config.NumberColumn("Sort Order", min_value=1, step=1),
    },
    hide_index=True,
)

if st.button("Save Meal Repository", type="primary", use_container_width=True):
    save_meal_type_repository(edited)
    set_system_message("Meal repository saved. Member Daily Log will use the active sections.", "success")
    st.rerun()

if st.button("Reset to Recommended Client Format", use_container_width=True):
    save_meal_type_repository([
        {"key": "breakfast", "label": "Breakfast", "active": True, "sort_order": 1},
        {"key": "lunch", "label": "Lunch", "active": True, "sort_order": 2},
        {"key": "evening_snack", "label": "Evening Snack", "active": True, "sort_order": 3},
        {"key": "dinner", "label": "Dinner", "active": True, "sort_order": 4},
        {"key": "bedtime", "label": "Bedtime", "active": True, "sort_order": 5},
        {"key": "other", "label": "Other", "active": True, "sort_order": 6},
    ])
    set_system_message("Repository reset to Breakfast, Lunch, Evening Snack, Dinner, Bedtime and Other.", "success")
    st.rerun()
card_end()

render_page_nav("Daily Log Settings", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
