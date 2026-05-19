
import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_build_text_v14, render_back_to_top
from components.db import list_members, queue_member_message, get_member_messages

st.set_page_config(page_title="Admin-Member Communication", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()
render_build_text_v14()

topbar("Admin-Member Communication", "Send app messages to members and queue email notifications.", "Admin communication")

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
selected_label = st.selectbox("Select member", list(member_options.keys()))
member_id = member_options[selected_label]

st.markdown(
    """
    <div class='hm-comm-card'>
      <b>How this works</b><br>
      The message is saved inside the app and marked for email notification. Actual email delivery requires the production email service/SMTP to be connected.
    </div>
    """,
    unsafe_allow_html=True,
)

subject = st.text_input("Subject", placeholder="Example: Please review your daily log")
message = st.text_area("Message", placeholder="Write the message that should be visible to the member and queued for email.")

if st.button("Send Message / Queue Email", type="primary", use_container_width=True):
    if not subject.strip() or not message.strip():
        st.error("Subject and message are required.")
    else:
        queue_member_message(member_id, "admin", subject.strip(), message.strip(), actor_id=st.session_state.get("user_id","admin"))
        st.success("Message saved in app and queued for email notification.")

st.subheader("Recent messages for selected member")
rows = get_member_messages(member_id, limit=10)
if not rows:
    st.info("No messages yet.")
else:
    for row in rows:
        st.markdown(
            f"""
            <div class='hm-comm-card'>
              <b>{row.get('subject','')}</b><br>
              <span style='color:#64748B;font-size:.85rem;'>{row.get('ts','')} · {row.get('sender_role','')}</span>
              <p>{row.get('message','')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.page_link("pages/10_Admin_Dashboard.py", label="Back to Dashboard", icon=":material/arrow_back:")
