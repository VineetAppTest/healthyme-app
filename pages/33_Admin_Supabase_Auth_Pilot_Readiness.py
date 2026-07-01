import pandas as pd
import streamlit as st

import components.ui_common as ui_common
from components.auth_mode import auth0_enabled, get_auth_mode, supabase_auth_enabled
from components.current_build import apply_current_build
from components.guards import require_admin
from components.supabase_provisioning_h6 import (
    member_review_rows,
    readiness_snapshot,
    service_role_client,
)
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)

apply_current_build(ui_common)

st.set_page_config(
    page_title="Supabase Auth Readiness",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supabase Auth Readiness",
    "H6 readiness checks before controlled Supabase Auth member provisioning and Flutter login migration.",
    "Admin auth readiness",
)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _summary_cards(summary: dict) -> None:
    labels = list(summary.items())
    for start in range(0, len(labels), 4):
        cols = st.columns(min(4, len(labels) - start))
        for col, (label, value) in zip(cols, labels[start : start + 4]):
            with col:
                st.metric(label, value)


client = service_role_client()
snapshot = readiness_snapshot(client)

st.warning(
    "Readiness only. This page does not retire Auth0, does not change login mode, does not create users, and does not run SQL."
)

card_start()
st.subheader("Current Auth Mode")
mode = get_auth_mode()
auth_mode_rows = [
    {"Item": "Current AUTH_MODE", "Status": mode},
    {"Item": "Auth0 enabled", "Status": _yes_no(auth0_enabled())},
    {"Item": "Supabase pilot login enabled", "Status": _yes_no(supabase_auth_enabled())},
]
st.dataframe(pd.DataFrame(auth_mode_rows), use_container_width=True, hide_index=True)
if mode == "auth0":
    st.success("Default Auth0-only behavior is active. This is expected until controlled dual-mode testing.")
elif mode == "dual":
    st.info("Dual mode is enabled for controlled pilot testing.")
else:
    st.warning("Supabase-only mode is active. Confirm this was intentionally enabled for controlled testing.")
card_end()

card_start()
st.subheader("Readiness checklist")
checks = pd.DataFrame(snapshot.get("checks", []))
st.dataframe(checks, use_container_width=True, hide_index=True)
failed = [row for row in snapshot.get("checks", []) if row.get("Status") != "pass"]
if failed:
    st.warning("One or more readiness checks need attention before production provisioning.")
else:
    st.success("All available readiness checks passed.")
card_end()

card_start()
st.subheader("Provisioning summary")
_summary_cards(snapshot.get("summary", {}))
st.caption("Counts are generated through admin/server-side access. Secret values are never displayed.")
card_end()

card_start()
st.subheader("Member review preview")
st.caption("Preview of member eligibility before opening the provisioning workbench.")
rows = member_review_rows(client)
preview_df = pd.DataFrame(rows)
st.dataframe(preview_df, use_container_width=True, hide_index=True)
if not preview_df.empty:
    status_counts = preview_df.get("Supabase Auth status", pd.Series(dtype=str)).value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    st.markdown("**Eligibility summary**")
    st.dataframe(status_counts, use_container_width=True, hide_index=True)
card_end()

card_start()
st.subheader("RLS readiness review")
st.markdown(
    """
This branch does not automatically change production RLS policies. Before applying member-side RLS SQL, confirm:

1. `hm_users` RLS status.
2. `hm_workflow` RLS status.
3. Existing policies on both tables.
4. Whether the Supabase warning is performance-related, duplicate-policy-related, or security-related.
5. Streamlit admin/service-role reporting remains unaffected.

Use the SQL file in this branch only after review: `sql/supabase_auth_member_rls_readiness_h6.sql`.
"""
)
card_end()

card_start()
st.subheader("Controlled next step")
st.markdown(
    """
Proceed to **Supabase Provisioning** only after this page renders without crash and the member review table looks correct.

Recommended order:

1. Single-member dry run.
2. Single-member execute for one test member.
3. Re-run same member to confirm duplicate prevention.
4. Batch dry run.
5. Batch execute only after dry-run output looks correct.
"""
)
if st.button("Open Supabase Provisioning Workbench", use_container_width=True):
    st.switch_page("pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py")
card_end()

render_page_nav(
    "Supabase Auth Readiness",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
