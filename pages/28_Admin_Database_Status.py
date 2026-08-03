from components.ui_common import render_page_nav, render_back_to_top
import datetime
import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_back_to_top
from components.storage_backend import (
    get_storage_status,
    export_current_state_bytes,
    push_local_data_to_supabase,
    pull_supabase_to_local_backup,
)
from components.flash import set_system_message, render_system_message
from components.normalized_store import check_normalized_tables
from components.identity_projection_observation import (
    get_identity_projection_snapshot,
    get_identity_observation_window_status,
    get_identity_fallback_closure_status,
    observe_identity_projection,
)

st.set_page_config(page_title="Database Status", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar("Database Status", "Check Supabase, canonical identity authority, projection drift, and backups.", "Admin database")
render_system_message()

status = get_storage_status(force_check=True)
mode = status.get("mode", "UNKNOWN")
connected = status.get("supabase_connected", False)
fallback = status.get("fallback_active", True)
identity_available = status.get("identity_authority_available", False)
projection_healthy = status.get("identity_projection_healthy", False)

stat_grid([
    {"label": "Database Mode", "value": mode, "note": "SUPABASE or LOCAL_FALLBACK"},
    {"label": "Connection", "value": "Connected" if connected else "Not Connected", "note": "Application state"},
    {"label": "Identity Authority", "value": "Canonical" if identity_available else "Unavailable", "note": "hm_users + hm_workflow"},
    {"label": "Projection", "value": "Aligned" if projection_healthy else "Check Required", "note": "Shared rollback copy"},
])

if mode == "SUPABASE" and identity_available:
    st.success("App state and canonical identity authority are available.")
elif connected:
    st.error("App state is connected, but canonical identity reads are unavailable. Identity access is fail-closed.")
else:
    st.warning("App is not running in live Supabase mode. Local Users and Workflow are not accepted as authority.")

card_start()
st.subheader("Connection and authority details")
st.json({
    "mode": mode,
    "supabase_configured": status.get("supabase_configured"),
    "supabase_connected": connected,
    "fallback_active": fallback,
    "identity_authority_available": identity_available,
    "identity_fail_closed": status.get("identity_fail_closed"),
    "users_count": status.get("users_count", "-"),
    "members_count": status.get("members_count", "-"),
    "identity_projection_checked": status.get("identity_projection_checked", "-"),
    "identity_projection_healthy": status.get("identity_projection_healthy", "-"),
    "identity_projection_message": status.get("identity_projection_message", "-"),
    "last_action": status.get("last_action", ""),
    "last_error": status.get("last_error", ""),
    "normalized_last_action": status.get("normalized_last_action", "-"),
})
card_end()

card_start()
st.subheader("Identity projection observation")
projection_ok, projection, projection_msg = get_identity_projection_snapshot()
if projection_ok and projection.get("healthy"):
    st.success(projection_msg)
elif projection_ok:
    st.warning(projection_msg)
else:
    st.error(projection_msg)
st.json(projection if projection_ok else {"error": projection_msg})

c1, c2 = st.columns(2)
with c1:
    if st.button("Record Projection Observation", use_container_width=True):
        ok, _, msg = observe_identity_projection(apply_repair=False)
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
with c2:
    confirm_repair = st.checkbox(
        "Confirm canonical projection repair",
        help="This rewrites only shared Users and Workflow from canonical rows. Canonical data is never changed.",
    )
    if st.button(
        "Repair Shared Projection from Canonical",
        type="primary",
        use_container_width=True,
        disabled=not confirm_repair,
    ):
        ok, _, msg = observe_identity_projection(apply_repair=True)
        set_system_message(msg, "success" if ok else "error")
        st.rerun()

st.caption(
    "Observation is read-only. Repair is explicit, service-role controlled, idempotent, and preserves shared-only fields for canonical identities."
)
card_end()

card_start()
st.subheader("Gate 6 observation window")
window_ok, window_status, window_msg = get_identity_observation_window_status(
    window_hours=24,
    minimum_observations=3,
    minimum_span_minutes=60,
)
if window_ok and window_status.get("automated_retirement_preconditions_ready"):
    st.success(window_msg)
elif window_ok:
    st.warning(window_msg)
else:
    st.error(window_msg)

if window_ok:
    stat_grid([
        {
            "label": "Observations",
            "value": str(window_status.get("observation_count", 0)),
            "note": f"Minimum {window_status.get('minimum_observations', 3)}",
        },
        {
            "label": "Window Span",
            "value": f"{float(window_status.get('span_minutes', 0) or 0):.1f} min",
            "note": f"Minimum {window_status.get('minimum_span_minutes', 60)} min",
        },
        {
            "label": "Auth-linked Members",
            "value": f"{window_status.get('active_members_with_auth_user_id', 0)}/{window_status.get('active_member_count', 0)}",
            "note": "Active members",
        },
        {
            "label": "Automated Readiness",
            "value": "Ready" if window_status.get("automated_retirement_preconditions_ready") else "Blocked",
            "note": "Manual route/device smoke still required",
        },
    ])
    st.json({
        "database_observation_ready": window_status.get("database_observation_ready"),
        "automated_retirement_preconditions_ready": window_status.get("automated_retirement_preconditions_ready"),
        "healthy_observation_count": window_status.get("healthy_observation_count"),
        "repair_count": window_status.get("repair_count"),
        "first_observed_at": window_status.get("first_observed_at"),
        "latest_observed_at": window_status.get("latest_observed_at"),
        "active_members_using_email_fallback": window_status.get("active_members_using_email_fallback"),
        "active_members_missing_workflow": window_status.get("active_members_missing_workflow"),
        "flutter_anon_executable_function_count": window_status.get("flutter_anon_executable_function_count"),
        "flutter_authenticated_missing_function_count": window_status.get("flutter_authenticated_missing_function_count"),
        "flutter_shared_workflow_fallback_functions": window_status.get("flutter_shared_workflow_fallback_functions", []),
        "blockers": window_status.get("blockers", []),
    })
else:
    st.json({"error": window_msg})

st.caption(
    "Automated readiness is evidence only. Projection retirement still requires signed-in Admin, Member and Flutter device smoke evidence and a separate approved retirement PR."
)
card_end()

card_start()
st.subheader("Gate 7 identity fallback closure")
closure_ok, closure_status, closure_msg = get_identity_fallback_closure_status()
if closure_ok and closure_status.get("closed"):
    st.success(closure_msg)
elif closure_ok:
    st.warning(closure_msg)
else:
    st.error(closure_msg)

if closure_ok:
    active_members = int(closure_status.get("active_member_count", 0) or 0)
    missing_auth = int(closure_status.get("active_members_missing_auth_user_id", 0) or 0)
    stat_grid([
        {
            "label": "Auth-ID Linked",
            "value": f"{max(active_members - missing_auth, 0)}/{active_members}",
            "note": "Active members",
        },
        {
            "label": "Workflow Coverage",
            "value": "Complete" if not closure_status.get("active_members_missing_workflow") else "Missing",
            "note": "Canonical member Workflow",
        },
        {
            "label": "Fallbacks",
            "value": "Closed" if not closure_status.get("blockers") else "Open",
            "note": "Email, RLS and RPC reads",
        },
        {
            "label": "Direct Writes",
            "value": "Blocked" if not closure_status.get("direct_workflow_write_policies") else "Present",
            "note": "Authenticated hm_workflow",
        },
    ])
    st.json({
        "closed": closure_status.get("closed"),
        "active_members_missing_auth_user_id": closure_status.get("active_members_missing_auth_user_id"),
        "active_members_missing_workflow": closure_status.get("active_members_missing_workflow"),
        "current_member_id_uses_email_fallback": closure_status.get("current_member_id_uses_email_fallback"),
        "flutter_shared_workflow_fallback_functions": closure_status.get("flutter_shared_workflow_fallback_functions", []),
        "email_fallback_policies": closure_status.get("email_fallback_policies", []),
        "direct_workflow_write_policies": closure_status.get("direct_workflow_write_policies", []),
        "anon_privilege_count": closure_status.get("anon_privilege_count"),
        "authenticated_nonselect_privilege_count": closure_status.get("authenticated_nonselect_privilege_count"),
        "blockers": closure_status.get("blockers", []),
    })
else:
    st.json({"error": closure_msg})

st.caption(
    "Gate 7 closes database and RPC fallback paths only. Signed-in Streamlit route checks and Flutter device smoke remain separate acceptance evidence."
)
card_end()

card_start()
st.subheader("Backup and non-identity transfer tools")
st.markdown(
    """
    <div class='warning-banner'>
      <b>Use carefully:</b><br>
      Local-to-Supabase push preserves canonical Users and Workflow. It may replace other local-compatible application data, so download a backup first.
    </div>
    """,
    unsafe_allow_html=True,
)

backup_name = f"healthyme_database_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
st.download_button(
    "Download Current Database Backup",
    data=export_current_state_bytes(),
    file_name=backup_name,
    mime="application/json",
    use_container_width=True,
)

b1, b2 = st.columns(2)
with b1:
    if st.button("Push Local Non-Identity Data", use_container_width=True):
        ok, msg = push_local_data_to_supabase()
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
with b2:
    if st.button("Pull Supabase to Local Backup", use_container_width=True):
        ok, msg = pull_supabase_to_local_backup()
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
card_end()

card_start()
st.subheader("Canonical Users + Workflow tables")
norm_status = check_normalized_tables()
st.json(norm_status)
if st.button("Recheck Canonical Tables", use_container_width=True):
    norm_status = check_normalized_tables()
    set_system_message(
        norm_status.get("message", "Checked canonical tables."),
        "success" if norm_status.get("ok") else "warning",
    )
    st.rerun()
st.caption("The former bulk migration action has been retired. Repair can only refresh the non-authoritative shared projection from canonical rows.")
card_end()

card_start()
st.subheader("Safe go-live checks")
st.markdown(
    """
    1. Confirm Database Mode is <b>SUPABASE</b>.<br>
    2. Confirm Identity Authority is <b>Canonical</b>.<br>
    3. Confirm Projection is <b>Aligned</b>.<br>
    4. Confirm Gate 7 identity fallback closure is <b>Closed</b>.<br>
    5. Confirm Admin and Member routes resolve the current role after refresh.<br>
    6. Confirm Flutter member dashboard, LAF and NSP on an authenticated device.<br>
    7. Record projection observations across the accepted observation window.
    """,
    unsafe_allow_html=True,
)
card_end()

pass
render_page_nav("Database Status", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
