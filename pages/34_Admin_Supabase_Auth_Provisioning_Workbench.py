import pandas as pd
import streamlit as st

import components.ui_common as ui_common
from components.current_build import apply_current_build
from components.guards import require_admin
from components.supabase_provisioning_h6 import (
    config_status,
    load_audit_rows,
    member_review_rows,
    password_reset_redirect_to,
    provision_batch_members,
    provision_single_member,
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
    page_title="Supabase Auth Provisioning",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supabase Auth Provisioning",
    "H6 hardening: readiness summary, member review, duplicate prevention, controlled single and batch provisioning.",
    "Admin provisioning bridge",
)


def _actor_email() -> str:
    return (
        st.session_state.get("oidc_email")
        or st.session_state.get("supabase_auth_email")
        or st.session_state.get("user_email")
        or st.session_state.get("user_name")
        or ""
    )


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _result_dataframe(rows):
    if not rows:
        return pd.DataFrame()
    preferred = [
        "email",
        "member_name",
        "member_id",
        "active",
        "role",
        "auth_status",
        "auth_user_id",
        "hm_link_status",
        "password_reset_status",
        "status",
        "message",
        "audit",
    ]
    df = pd.DataFrame(rows)
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    return df[cols]


def _summary_cards(summary: dict) -> None:
    labels = list(summary.items())
    for start in range(0, len(labels), 4):
        cols = st.columns(min(4, len(labels) - start))
        for col, (label, value) in zip(cols, labels[start : start + 4]):
            with col:
                st.metric(label, value)


client = service_role_client()
config = config_status()
snapshot = readiness_snapshot(client)

st.warning(
    "Admin/server-side only. This page may use the Supabase service-role key from Streamlit secrets. "
    "Never copy the service-role key into Flutter or member-side code. Auth0 admin login is not retired in this branch."
)

card_start()
st.subheader("Configuration and readiness")
config_rows = [
    {"Config": "SUPABASE_URL", "Configured": _yes_no(config["SUPABASE_URL"])},
    {"Config": "SUPABASE_ANON_KEY", "Configured": _yes_no(config["SUPABASE_ANON_KEY"])},
    {"Config": "SUPABASE_SERVICE_ROLE_KEY", "Configured": _yes_no(config["SUPABASE_SERVICE_ROLE_KEY"])},
    {"Config": "Password reset redirect", "Configured": password_reset_redirect_to()},
]
st.dataframe(pd.DataFrame(config_rows), use_container_width=True, hide_index=True)
if client is None:
    st.error("Supabase service role key is not configured or the admin client could not be created.")
else:
    st.success("Service-role admin client initialized for this admin-only page.")
st.caption("Secret values are never displayed. Only configured/not configured status is shown.")
card_end()

card_start()
st.subheader("Provisioning summary")
_summary_cards(snapshot.get("summary", {}))
st.dataframe(pd.DataFrame(snapshot.get("checks", [])), use_container_width=True, hide_index=True)
card_end()

review_tab, single_tab, batch_tab, audit_tab, setup_tab = st.tabs(
    ["Member Review", "Single Member", "Batch Existing Members", "Audit Log", "Setup / UAT"]
)

with review_tab:
    card_start()
    st.subheader("Member provisioning review")
    st.caption("Review active, inactive, missing-email, duplicate-email, and already-provisioned member records before execution.")
    rows = member_review_rows(client)
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button(
            "Download member review CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="healthyme_supabase_member_provisioning_review_h6.csv",
            mime="text/csv",
            use_container_width=True,
        )
    card_end()

with single_tab:
    card_start()
    st.subheader("Single-member provisioning")
    st.caption("Use this first for one known test member before any batch execution. Dry run is enabled by default.")
    with st.form("hm_h6_single_supabase_provisioning_form"):
        email = st.text_input("Member email")
        temp_password = st.text_input(
            "Temporary password for new Auth user",
            type="password",
            help="Admin testing only. Leave blank to generate a strong password that is not displayed or logged. Prefer reset email for rollout.",
        )
        send_reset = st.checkbox("Send Supabase password reset email after successful link/create", value=True)
        dry_run = st.checkbox("Dry run only", value=True)
        confirmation = st.text_input("To execute, untick Dry run and type PROVISION")
        submitted = st.form_submit_button("Run single-member provisioning", type="primary", use_container_width=True)

    if submitted:
        execute_allowed = dry_run or confirmation.strip() == "PROVISION"
        if not execute_allowed:
            st.error("Action not executed. Type PROVISION exactly, or keep Dry run enabled.")
        else:
            result = provision_single_member(
                client,
                email=email,
                temp_password=temp_password,
                send_reset=send_reset,
                actor_email=_actor_email(),
                dry_run=dry_run,
            )
            df = _result_dataframe([result])
            st.dataframe(df, use_container_width=True, hide_index=True)
            status = result.get("status")
            if status in {"ok", "dry_run"}:
                st.success(result.get("message") or "Provisioning check completed.")
            elif status == "partial":
                st.warning(result.get("message") or "Provisioning partially completed. Review the result row.")
            else:
                st.error(result.get("message") or "Provisioning failed or was blocked.")
    card_end()

with batch_tab:
    card_start()
    st.subheader("Batch existing-member provisioning")
    st.caption("Batch skips inactive, missing-email, invalid-email and duplicate-email records. It continues even if one row fails.")
    with st.form("hm_h6_batch_supabase_provisioning_form"):
        temp_password = st.text_input(
            "Temporary password for newly created Auth users",
            type="password",
            help="Admin testing only. Leave blank to generate a unique strong password per created user. Prefer reset emails for rollout.",
        )
        send_reset = st.checkbox("Send password reset email for successfully linked/created users", value=True)
        limit = st.number_input("Batch limit", min_value=1, max_value=1000, value=250, step=25)
        dry_run = st.checkbox("Dry run only", value=True, key="h6_batch_dry_run")
        confirmation = st.text_input("To execute batch, untick Dry run and type BATCH PROVISION")
        submitted = st.form_submit_button("Run batch provisioning", type="primary", use_container_width=True)

    if submitted:
        execute_allowed = dry_run or confirmation.strip() == "BATCH PROVISION"
        if not execute_allowed:
            st.error("Batch not executed. Type BATCH PROVISION exactly, or keep Dry run enabled.")
        else:
            rows = provision_batch_members(
                client,
                temp_password=temp_password,
                send_reset=send_reset,
                actor_email=_actor_email(),
                dry_run=dry_run,
                include_inactive=False,
                limit=int(limit),
            )
            df = _result_dataframe(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if not df.empty:
                counts = df.get("status", pd.Series(dtype=str)).value_counts().reset_index()
                counts.columns = ["Status", "Count"]
                st.markdown("**Batch summary**")
                st.dataframe(counts, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download batch result CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="healthyme_supabase_batch_provisioning_result_h6.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            if dry_run:
                st.info("Dry run completed. No users were created, no hm_users rows were updated, and no audit rows were written.")
            else:
                st.success("Batch execution completed. Review the result table and audit tab.")
    card_end()

with audit_tab:
    card_start()
    st.subheader("Provisioning audit log")
    st.caption("Shows latest rows from hm_supabase_auth_provisioning_audit if the audit table exists.")
    limit = st.slider("Rows to load", min_value=25, max_value=500, value=100, step=25)
    ok, rows, message = load_audit_rows(client, limit=limit)
    if ok:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning(message)
    card_end()

with setup_tab:
    card_start()
    st.subheader("Setup and smoke test")
    st.markdown(
        """
**Safety rules**

- Auth0 Streamlit admin login remains active.
- This branch provisions member-role users only.
- Inactive members, missing emails, invalid emails and duplicate member emails are skipped.
- Supabase service-role key remains server-side only.
- Prefer dry run first, then single-member execution, then batch dry run, then batch execution.

**Smoke test sequence**

1. Open this page as admin.
2. Confirm readiness summary renders without crash.
3. Open Member Review and confirm the table renders.
4. Run single-member dry run for one existing active member.
5. Execute single-member provisioning only after dry run looks correct.
6. Re-run same member and confirm duplicate is marked already provisioned / linked.
7. Run batch dry run.
8. Execute batch only after dry run result looks correct.
9. Confirm Auth0 admin login still works.
"""
    )
    card_end()

render_page_nav(
    "Supabase Auth Provisioning",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
