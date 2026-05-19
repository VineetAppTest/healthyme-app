import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, compact_topbar, utility_logout_bar, render_back_to_top
from components.db import list_members, queue_member_message, get_member_messages

st.set_page_config(page_title="Admin-Member Communication", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.markdown(
    """
    <style>
    .hm-comm-wrap{margin-top:.25rem;}
    .hm-comm-card{
      background:#F8FAFC;
      border:1px solid #E7D8BE;
      border-radius:16px;
      padding:.85rem 1rem;
      margin:.45rem 0;
      box-shadow:0 6px 18px rgba(15,23,42,.04);
    }
    .hm-comm-compact-label{
      font-size:.82rem;
      color:#64748B;
      margin-bottom:.15rem;
      font-weight:700;
    }
    .hm-comm-success-space [data-testid="stAlert"]{
      margin-top:.45rem;
      margin-bottom:.5rem;
      padding:.55rem .8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

compact_topbar("Admin-Member Communication", "Send app messages to members and queue email notifications.", "Admin communication")

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
selected_label = st.selectbox("Select member", list(member_options.keys()))
member_id = member_options[selected_label]

subject = st.text_input("Subject", placeholder="Example: Please review your daily log")
message = st.text_area(
    "Message",
    placeholder="Write the message that should be visible to the member and queued for email.",
    height=110,
)

st.markdown("<div class='hm-comm-success-space'>", unsafe_allow_html=True)
if st.button("Send Message / Queue Email", type="primary", use_container_width=True):
    if not subject.strip() or not message.strip():
        st.error("Subject and message are required.")
    else:
        queue_member_message(member_id, "admin", subject.strip(), message.strip(), actor_id=st.session_state.get("user_id", "admin"))
        st.success("Message saved in app and queued for email notification.")
st.markdown("</div>", unsafe_allow_html=True)

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
              <span style='color:#64748B;font-size:.82rem;'>{row.get('ts','')} · {row.get('sender_role','')}</span>
              <p style='margin:.35rem 0 0 0;'>{row.get('message','')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

back_col, _ = st.columns([1.2, 4])
with back_col:
    if st.button("Back to Dashboard", key="back_to_admin_dashboard"):
        st.switch_page("pages/10_Admin_Dashboard.py")
