import streamlit as st

import components.admin_scheduling_consolidated as admin_scheduling
from components.admin_performance_optimization import admin_scheduling_render_scope
from components.admin_uiux_corrections import admin_scheduling_uiux_scope
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)


begin_page_measurement("Admin Scheduling")

# Keep Scheduling navigation consistent with the rest of HealthyMe: Back on the
# left edge and Dashboard on the right edge at both the top and bottom of the page.
st.markdown(
    """
    <style id="hm-admin-scheduling-edge-navigation-v1">
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top),
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom){
      display:grid!important;
      grid-template-columns:minmax(150px,220px) minmax(0,1fr) minmax(170px,240px)!important;
      gap:.75rem!important;
      width:100%!important;
      align-items:center!important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top) > div:nth-child(1),
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom) > div:nth-child(1){
      grid-column:1!important;
      width:100%!important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top) > div:nth-child(2),
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom) > div:nth-child(2){
      grid-column:3!important;
      width:100%!important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top) > div:nth-child(3),
    div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom) > div:nth-child(3){
      display:none!important;
    }
    @media(max-width:640px){
      div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top),
      div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom){
        grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
        gap:.55rem!important;
      }
      div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_top) > div:nth-child(2),
      div[data-testid="stHorizontalBlock"]:has(.st-key-hm_admin_schedule_back_bottom) > div:nth-child(2){
        grid-column:2!important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with admin_scheduling_render_scope(admin_scheduling):
    with admin_scheduling_uiux_scope(admin_scheduling):
        admin_scheduling.render_admin_scheduling_consolidated_page()
finish_and_render_page_diagnostics("Admin Scheduling")
