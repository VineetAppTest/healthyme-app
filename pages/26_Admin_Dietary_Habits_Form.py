import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_page_nav, render_back_to_top, compact_topbar

st.set_page_config(page_title="Dietary Habits Form", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()
# v101.6: top page navigation removed; bottom nav remains standard
# render_page_nav("Dietary Habits Form", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
compact_topbar("Dietary Habits Form", "", "Admin form")

card_start()
st.subheader("Dietary Habits Form - Coming Soon")
st.info("This section has been removed from Member LAF and reserved as a separate admin-side form. It is intentionally greyed out for now and will be opened later.")
st.button("Dietary Habits Form - Coming Soon", disabled=True, use_container_width=True)
card_end()

render_page_nav("Dietary Habits Form", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
