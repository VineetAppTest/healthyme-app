import html

import streamlit as st

from components.db import get_member_messages, list_members, queue_member_message
from components.guards import require_admin
from components.member_email import email_delivery_configuration_status
from components.ui_common import (
    apply_luxe_theme,
    compact_topbar,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Admin-Member Communication",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

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
    .hm-email-status{
      display:inline-flex;
      align-items:center;
      padding:.16rem .44rem;
      border-radius:999px;
      border:1px solid #D9C28F;
      background:#FFF7E6;
      color:#72551A;
      font-size:.72rem;
      font-weight:800;
      margin-left:.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

compact_topbar(
    "Admin-Member Communication",
    "Send app messages to members with tracked email delivery.",
    "Admin communication",
)

email_status = email_delivery_configuration_status()
if email_status.get("configured"):
    st.success("Member email delivery is configured through Resend.")
else:
    missing = []
    if not email_status.get("api_key_configured"):
        missing.append("RESEND_API_KEY")
    if not email_status.get("sender_configured"):
        missing.append("RESEND_FROM_EMAIL or RESEND_FROM")
    st.warning(
        "Member updates will remain recorded in HealthyMe, but outbound email cannot be delivered until "
        + " and ".join(missing)
        + " is configured in Streamlit secrets."
    )

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
selected_label = st.selectbox("Select member", list(member_options.keys()))
member_id = member_options[selected_label]

subject = st.text_input("Subject", placeholder="Example: Please review your Daily Log")
message = st.text_area(
    "Message",
    placeholder="Write a friendly and professional message for the member.",
    height=110,
)

st.markdown("<div class='hm-comm-success-space'>", unsafe_allow_html=True)
if st.button("Send Message and Email", type="primary", use_container_width=True):
    if not subject.strip() or not message.strip():
        st.error("Subject and message are required.")
    else:
        result = queue_member_message(
            member_id,
            "admin",
            subject.strip(),
            message.strip(),
            actor_id=st.session_state.get("user_id", "admin"),
        )
        delivery = str((result or {}).get("email_delivery_status") or "")
        if delivery == "sent":
            st.success("Message saved in HealthyMe and email sent to the member.")
        elif delivery == "configuration_missing":
            st.warning("Message saved in HealthyMe. Email delivery is waiting for Resend configuration.")
        elif delivery == "recipient_missing":
            st.warning("Message saved in HealthyMe, but the member does not have a valid email address.")
        else:
            error = str((result or {}).get("email_delivery_error") or "Email delivery could not be confirmed.")
            st.warning(f"Message saved in HealthyMe. Email delivery needs attention: {error}")
st.markdown("</div>", unsafe_allow_html=True)

st.subheader("Recent messages for selected member")
rows = get_member_messages(member_id, limit=10)
if not rows:
    st.info("No messages yet.")
else:
    for row in rows:
        delivery = str(row.get("email_delivery_status") or "not attempted").replace("_", " ").title()
        st.markdown(
            f"""
            <div class='hm-comm-card'>
              <b>{html.escape(str(row.get('subject','')))}</b>
              <span class='hm-email-status'>Email: {html.escape(delivery)}</span><br>
              <span style='color:#64748B;font-size:.82rem;'>{html.escape(str(row.get('ts','')))} · {html.escape(str(row.get('sender_role','')))}</span>
              <p style='margin:.35rem 0 0 0;'>{html.escape(str(row.get('message','')))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

render_page_nav(
    "Admin-Member Communication",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
