import pandas as pd
import streamlit as st

from components.auth_mode import supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.supabase_provisioning import (
    config_status,
    load_audit_rows,
    password_reset_redirect_to,
    provision_batch_members,
    provision_single_member,
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


st.set_page_config(
    page_title="Supabase Auth Provisioning",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


if not st.session_state.get("logged_in"):
    try:
        if supabase_auth_enabled():
            restore_supabase_login_from_session()
    except Exception:
        pass

if not st.session_state.get("logged_in"):
    try:
        restore_login_from_token()
    except Exception:
        pass

if not st.session_state.get("logged_in"):
    st.info("Please sign in as an admin to view Supabase Auth provisioning.")
    st.stop()

if st.session_state.get("user_role") not in {"admin", "super_admin"}:
    st.warning("Admin access required")
    st.stop()

utility_logout_bar()
topbar(
    "Supabase Auth Provisioning",
    "Sprint 2A + 2B + 2C: single member provisioning, batch provisioning and audit log.",
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


client = service_role_client()
config = config_status()

st.warning(
    "This page uses Supabase service-role access from Streamlit secrets. It must remain admin/server-side only. "
    "The service-role key must never be copied into Flutter."
)

card_start()
st.subheader("Configuration check")
st.dataframe(
    pd.DataFrame(
        [
            {"Config": "SUPABASE_URL", "Configured": _yes_no(config["SUPABASE_URL"])},
            {"Config": "SUPABASE_ANON_KEY", "Configured": _yes_no(config["SUPABASE_ANON_KEY"])},
            {"Config": "SUPABASE_SERVICE_ROLE_KEY", "Configured": _yes_no(config["SUPABASE_SERVICE_ROLE_KEY"])},
            {"Config": "Password reset redirect", "Configured": password_reset_redirect_to()},
        ]
    ),
    use_container_width=True,
    hide_index=True,
)
if client is None:
    st.error("Service-role client is not available. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Streamlit secrets before provisioning.")
st.caption("Before executing provisioning, run RUN_ONCE_SUPABASE_AUTH_PROVISIONING_SPRINT2A_2B_2C.sql in Supabase SQL Editor.")
card_end()

single_tab, batch_tab, audit_tab, setup_tab = st.tabs(
    ["2A Single Member", "2B Batch Existing Members", "2C Audit Log", "Setup / UAT"]
)

with single_tab:
    card_start()
    st.subheader("2A — Single member provisioning")
    st.caption(
        "Creates a missing Supabase Auth user or links an existing Auth user to hm_users.auth_user_id. "
        "It does not create a HealthyMe member row."
    )
    with st.form("hm_single_supabase_provisioning_form"):
        email = st.text_input("Member email")
        temp_password = st.text_input(
            "Temporary password for new Auth user",
            type="password",
            help="Leave blank to generate a strong temporary password. The generated password is shown only in the result table for this run.",
        )
        send_reset = st.checkbox("Also send Supabase password reset email after successful link/create", value=False)
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
            if result.get("status") in {"ok", "dry_run"}:
                st.success(result.get("message") or "Provisioning check completed.")
            elif result.get("status") == "partial":
                st.warning(result.get("message") or "Provisioning partially completed. Review the result row.")
            else:
                st.error(result.get("message") or "Provisioning failed or was blocked.")
            if result.get("temp_password") and result.get("temp_password") != "admin_entered_password":
                st.warning("Generated temporary password is visible only in the table above. Copy it now if you need to share it securely.")
    card_end()

with batch_tab:
    card_start()
    st.subheader("2B — Batch existing member provisioning")
    st.caption(
        "Scans existing active member-role hm_users records, creates missing Supabase Auth users, links auth_user_id, and writes audit rows. "
        "Run dry-run first."
    )
    with st.form("hm_batch_supabase_provisioning_form"):
        temp_password = st.text_input(
            "Temporary password for newly created Auth users",
            type="password",
            help="Optional. Leave blank to generate a unique strong password per newly created user. For large batches, prefer sending reset emails.",
        )
        send_reset = st.checkbox("Send password reset email for successfully linked/created users", value=False)
        include_inactive = st.checkbox("Include inactive members", value=False, help="Usually keep this off. Inactive members are skipped unless included for review.")
        limit = st.number_input("Batch limit", min_value=1, max_value=1000, value=250, step=25)
        dry_run = st.checkbox("Dry run only", value=True, key="batch_dry_run")
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
                include_inactive=include_inactive,
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
                    file_name="healthyme_supabase_batch_provisioning_result.csv",
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
    st.subheader("2C — Provisioning audit log")
    st.caption("Shows the latest provisioning actions written to hm_supabase_auth_provisioning_audit.")
    limit = st.slider("Rows to load", min_value=25, max_value=500, value=100, step=25)
    if st.button("Refresh audit log", use_container_width=True):
        st.session_state["hm_refresh_supabase_audit"] = True
    ok, rows, message = load_audit_rows(client, limit=limit)
    if ok:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.error(message)
    card_end()

with setup_tab:
    card_start()
    st.subheader("Setup and smoke test")
    st.markdown(
        """
**Run once before UAT**

1. Open Supabase Dashboard.
2. Go to SQL Editor.
3. Run `RUN_ONCE_SUPABASE_AUTH_PROVISIONING_SPRINT2A_2B_2C.sql` from this build.
4. Confirm Streamlit secrets contain `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.
5. Keep `SUPABASE_SERVICE_ROLE_KEY` only in Streamlit/server-side secrets.

**Smoke test sequence**

1. Open this page as admin.
2. Run single-member dry-run for one existing member.
3. Execute single-member provisioning for that same member.
4. Confirm `hm_users.auth_user_id` is populated.
5. Confirm the audit row is visible in the Audit Log tab.
6. Run batch dry-run.
7. Execute batch only after dry-run result looks correct.
8. Confirm Flutter member login still works for the provisioned member.

**Safety rules**

- This sprint provisions member-role users only.
- Streamlit admin login is not cut over to Supabase Auth in this sprint.
- Auth0 is not removed in this sprint.
- Inactive members are skipped by default.
- Duplicate member emails are blocked.
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
