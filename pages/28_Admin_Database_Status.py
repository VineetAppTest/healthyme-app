import datetime
import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.storage_backend import (
    get_storage_status,
    export_current_state_bytes,
    push_local_data_to_supabase,
    pull_supabase_to_local_backup,
)
from components.flash import set_system_message, render_system_message
from components.normalized_store import check_normalized_tables, sync_users_workflow_to_normalized

st.set_page_config(page_title="Database Status", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar("Database Status", "Check Supabase connection, fallback mode, migration, and backups.", "Admin database")
render_system_message()

status = get_storage_status(force_check=True)
mode = status.get("mode", "UNKNOWN")
connected = status.get("supabase_connected", False)
fallback = status.get("fallback_active", True)

stat_grid([
    {"label": "Database Mode", "value": mode, "note": "SUPABASE or LOCAL_FALLBACK"},
    {"label": "Supabase Secrets", "value": "Present" if status.get("supabase_configured") else "Missing", "note": "Streamlit Secrets / env"},
    {"label": "Connection", "value": "Connected" if connected else "Not Connected", "note": "Health check"},
    {"label": "Fallback", "value": "Active" if fallback else "Inactive", "note": "Local JSON mode"},
])

if mode != "SUPABASE":
    st.warning("App is currently not running in LIVE Supabase mode. Data may not persist on Streamlit Cloud.")
else:
    st.success("App is running in LIVE Supabase mode.")

card_start()
st.subheader("Connection details")
st.json({
    "mode": mode,
    "supabase_configured": status.get("supabase_configured"),
    "supabase_connected": connected,
    "fallback_active": fallback,
    "users_count": status.get("users_count", "-"),
    "members_count": status.get("members_count", "-"),
    "last_action": status.get("last_action", ""),
    "last_error": status.get("last_error", ""),
    "normalized_users_workflow": status.get("normalized_users_workflow", "-"),
    "normalized_last_action": status.get("normalized_last_action", "-"),
})
card_end()

card_start()
st.subheader("Manual migration and backup tools")
st.markdown(
    """
    <div class='warning-banner'>
      <b>Use carefully:</b><br>
      Push local data to Supabase only when you intentionally want the current local/demo database to become the Supabase database. Always download a backup first.
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

c1, c2 = st.columns(2)
with c1:
    if st.button("Push Local Data to Supabase", type="primary", use_container_width=True):
        ok, msg = push_local_data_to_supabase()
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
with c2:
    if st.button("Pull Supabase to Local Backup", use_container_width=True):
        ok, msg = pull_supabase_to_local_backup()
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
card_end()


card_start()
st.subheader("Normalized Users + Workflow Tables")
norm_status = check_normalized_tables()
st.json(norm_status)

n1, n2 = st.columns(2)
with n1:
    if st.button("Check Normalized Tables", use_container_width=True):
        norm_status = check_normalized_tables()
        set_system_message(norm_status.get("message", "Checked normalized tables."), "success" if norm_status.get("ok") else "warning")
        st.rerun()
with n2:
    if st.button("Migrate Users + Workflow to Normalized Tables", type="primary", use_container_width=True):
        # Uses current active database state and upserts users/workflow to hm_users/hm_workflow.
        from components.storage_backend import load_state
        current_db = load_state(force_refresh=True)
        ok, msg = sync_users_workflow_to_normalized(current_db)
        set_system_message(msg, "success" if ok else "error")
        st.rerun()

st.caption("Safe migration: only users and workflow are migrated. LAF/NSP/reports remain on current storage for now.")
card_end()

card_start()
st.subheader("Layman setup guide")
st.markdown("""
A step-by-step guide has been included in the package:

```text
SUPABASE_LAYMAN_CONNECTION_GUIDE.md
```

Use it for connecting Supabase and checking whether the connection is live.
""")
card_end()

card_start()
st.subheader("Safe go-live test")
st.markdown(
    """
    1. Confirm this page says <b>Database Mode: SUPABASE</b>.<br>
    2. Create a test member from Admin User Manager.<br>
    3. Reboot Streamlit app.<br>
    4. Confirm the test member is still visible.<br>
    5. If yes, Supabase persistence is working.
    """,
    unsafe_allow_html=True,
)
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")