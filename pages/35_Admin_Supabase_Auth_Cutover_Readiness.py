import pandas as pd
import streamlit as st

import components.ui_common as ui_common
from components.current_build import apply_current_build
from components.guards import require_admin
from components.supabase_auth_cutover_h11 import (
    cutover_decision,
    cutover_readiness_rows,
    cutover_summary,
    session_guardrail_rows,
)
from components.supabase_provisioning_h6 import service_role_client
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
    page_title="Supabase Auth Cutover Readiness",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supabase Auth Cutover Readiness",
    "H11 admin-only readiness gate for member-auth cutover, rollback and session guardrails.",
    "Admin authentication governance",
)

client = service_role_client()
rows = cutover_readiness_rows(client)
summary = cutover_summary(rows)
decision = cutover_decision(summary)

st.warning(
    "H11 is admin-only. It does not touch Flutter, Food Journal, LAF/NSP, reports, or Auth0 admin login. "
    "Use this page as a readiness gate before declaring Supabase Auth as the member-auth source."
)

card_start()
st.subheader("Cutover decision")
cols = st.columns(4)
for col, label in zip(cols, ["PASS", "WARN", "BLOCKED", "INFO"]):
    with col:
        st.metric(label, summary.get(label, 0))
if summary.get("BLOCKED", 0):
    st.error(decision)
elif summary.get("WARN", 0):
    st.warning(decision)
else:
    st.success(decision)
card_end()

card_start()
st.subheader("H11 readiness checklist")
st.caption("Blocked rows must be resolved before broad member-auth cutover. Warning rows require explicit admin review.")
readiness_df = pd.DataFrame(rows)
st.dataframe(readiness_df, use_container_width=True, hide_index=True)
st.download_button(
    "Download H11 readiness CSV",
    data=readiness_df.to_csv(index=False).encode("utf-8"),
    file_name="healthyme_h11_supabase_auth_cutover_readiness.csv",
    mime="text/csv",
    use_container_width=True,
)
card_end()

card_start()
st.subheader("Session guardrail test matrix")
st.caption("These checks are intentionally listed here while Flutter APK smoke testing continues separately.")
session_df = pd.DataFrame(session_guardrail_rows())
st.dataframe(session_df, use_container_width=True, hide_index=True)
card_end()

card_start()
st.subheader("Rollback playbook")
st.markdown(
    """
**If Supabase member login has an issue during pilot or cutover:**

1. Stop sending onboarding/password-reset emails from the provisioning workbench.
2. Do not deactivate Auth0 or Streamlit admin access.
3. Keep Streamlit Full Admin as the operational control plane.
4. Use H10 Lifecycle Audit to identify affected member rows.
5. Fix `hm_users.email`, `hm_users.auth_user_id`, inactive status, or duplicate records as needed.
6. Re-test with one member before restarting rollout.
7. Do not expose the Supabase service-role key to Flutter or any client-side code.

**Rollback boundary:** member Flutter login rollout can be paused without changing Streamlit admin/Auth0.
"""
)
card_end()

card_start()
st.subheader("H11 acceptance")
st.markdown(
    """
H11 can be accepted when:

- H10 provisioning/lifecycle workbench is smoke-tested.
- All BLOCKED rows on this page are resolved.
- WARN rows are reviewed and either accepted or corrected.
- Flutter APK confirms login/logout/member-switch guardrails.
- Auth0 admin login remains unaffected.
- Rollback playbook is understood before wider member rollout.
"""
)
card_end()

render_page_nav(
    "Supabase Auth Cutover Readiness",
    back_page="pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
