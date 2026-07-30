import html

import streamlit as st

from components.db import (
    get_member_messages,
    list_members,
    load_db,
    queue_member_message,
    save_db,
)
from components.guards import require_admin
from components.member_email import email_delivery_configuration_status
from components.member_email_retry import (
    list_member_email_deliveries,
    retry_failed_member_emails,
    retry_member_email_delivery,
)
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)
from components.ui_common import (
    apply_luxe_theme,
    compact_topbar,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)


MESSAGE_MEMBER_KEY = "hm_admin_message_member"
MESSAGE_SUBJECT_KEY = "hm_admin_message_subject"
MESSAGE_BODY_KEY = "hm_admin_message_body"
MESSAGE_FLASH_KEY = "hm_admin_message_flash"


def _set_message_flash(kind, message):
    st.session_state[MESSAGE_FLASH_KEY] = {
        "kind": str(kind or "info"),
        "message": str(message or "").strip(),
    }


def _render_message_flash():
    flash = st.session_state.pop(MESSAGE_FLASH_KEY, None)
    if not isinstance(flash, dict):
        return
    message = str(flash.get("message") or "").strip()
    if not message:
        return
    kind = str(flash.get("kind") or "info")
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    else:
        st.error(message)


def _send_member_message(member_options):
    selected_label = st.session_state.get(MESSAGE_MEMBER_KEY)
    member_id = member_options.get(selected_label, "")
    subject = str(st.session_state.get(MESSAGE_SUBJECT_KEY) or "").strip()
    message = str(st.session_state.get(MESSAGE_BODY_KEY) or "").strip()

    if not member_id:
        _set_message_flash("error", "Select a member before sending the message.")
        return
    if not subject or not message:
        _set_message_flash("error", "Subject and message are required.")
        return

    try:
        result = queue_member_message(
            member_id,
            "admin",
            subject,
            message,
            actor_id=st.session_state.get("user_id", "admin"),
        )
    except Exception as exc:
        _set_message_flash(
            "error",
            f"Message could not be saved. Your entered text has been retained: {exc}",
        )
        return

    if not isinstance(result, dict) or not str(result.get("id") or "").strip():
        _set_message_flash(
            "error",
            "Message saving could not be confirmed. Your entered text has been retained.",
        )
        return

    delivery = str(result.get("email_delivery_status") or "")
    if delivery == "sent":
        kind = "success"
        flash_message = "Message saved in HealthyMe and email sent to the member."
    elif delivery == "configuration_missing":
        kind = "warning"
        flash_message = (
            "Message saved in HealthyMe. Email delivery is waiting for Resend configuration."
        )
    elif delivery == "recipient_missing":
        kind = "warning"
        flash_message = (
            "Message saved in HealthyMe, but the member does not have a valid email address."
        )
    else:
        error = str(
            result.get("email_delivery_error")
            or "Email delivery could not be confirmed."
        )
        kind = "warning"
        flash_message = (
            f"Message saved in HealthyMe. Email delivery needs attention: {error}"
        )

    # The callback runs before Streamlit renders the next page cycle. Clear only the
    # transaction fields after the message record is confirmed; preserve the member.
    st.session_state[MESSAGE_SUBJECT_KEY] = ""
    st.session_state[MESSAGE_BODY_KEY] = ""
    _set_message_flash(kind, flash_message)


st.set_page_config(
    page_title="Admin-Member Communication",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
begin_page_measurement("Admin Messages")
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
    .hm-email-error{color:#9A3412;font-size:.76rem;line-height:1.35;margin-top:.30rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

compact_topbar(
    "Admin-Member Communication",
    "Send app messages to members and review tracked email delivery.",
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
    with st.expander(
        "Where to obtain and configure the production secrets",
        expanded=True,
    ):
        st.markdown(
            """
**1. Obtain `RESEND_API_KEY`**

Open the Resend dashboard, go to **API Keys**, create a key with sending permission and copy it when shown.

**2. Decide `RESEND_FROM_EMAIL`**

In Resend, verify the HealthyMe sending domain under **Domains**. After verification, use an address on that domain, for example `HealthyMe <care@healthyme.in>`. `RESEND_FROM` is also accepted as an alternative secret name.

**3. Add the secrets to this Streamlit application**

From the Streamlit Community Cloud workspace, open the menu beside this app, then go to **Settings → Secrets**. Paste the values in TOML format and save.
"""
        )
        st.code(
            'RESEND_API_KEY = "re_your_production_key"\n'
            'RESEND_FROM_EMAIL = "HealthyMe <care@your-verified-domain.com>"',
            language="toml",
        )
        st.caption(
            "The API key is confidential. Keep it only in Streamlit Secrets and never commit it to GitHub or paste it into a member message."
        )

members = list_members()
if not members:
    st.info("No members available.")
    finish_and_render_page_diagnostics("Admin Messages")
    st.stop()

member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
selected_label = st.selectbox(
    "Select member",
    list(member_options.keys()),
    key=MESSAGE_MEMBER_KEY,
)
member_id = member_options[selected_label]

compose_tab, delivery_tab = st.tabs(["Send Message", "Email Delivery"])

with compose_tab:
    st.markdown("<div class='hm-comm-success-space'>", unsafe_allow_html=True)
    _render_message_flash()
    subject = st.text_input(
        "Subject",
        placeholder="Example: Please review your Daily Log",
        key=MESSAGE_SUBJECT_KEY,
    )
    message = st.text_area(
        "Message",
        placeholder="Write a friendly and professional message for the member.",
        height=110,
        key=MESSAGE_BODY_KEY,
    )

    st.button(
        "Send Message and Email",
        type="primary",
        use_container_width=True,
        on_click=_send_member_message,
        args=(member_options,),
        key="hm_admin_message_send",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Recent messages for selected member")
    rows = get_member_messages(member_id, limit=10)
    if not rows:
        st.info("No messages yet.")
    else:
        for row in rows:
            delivery = str(
                row.get("email_delivery_status") or "not attempted"
            ).replace("_", " ").title()
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

with delivery_tab:
    db = load_db()
    deliveries = list_member_email_deliveries(db, member_id=member_id, limit=50)
    retryable_count = len(
        [
            row
            for row in deliveries
            if str(row.get("status", "")) in {"failed", "configuration_missing"}
        ]
    )
    st.markdown(
        f"**Tracked events:** {len(deliveries)} &nbsp;&nbsp; **Ready for retry:** {retryable_count}"
    )
    if st.button(
        "Retry failed/configuration-pending emails",
        use_container_width=True,
        disabled=retryable_count == 0 or not email_status.get("configured"),
        key="retry_member_emails",
    ):
        summary = retry_failed_member_emails(db, member_id=member_id, limit=20)
        save_db(db)
        st.success(
            f"Retry complete: {summary['sent']} sent, {summary['failed']} still pending/failed."
        )
        st.rerun()

    if not deliveries:
        st.info("No tracked member email events are available yet.")
    else:
        for delivery in deliveries:
            status = str(delivery.get("status") or "unknown").replace("_", " ").title()
            error = str(delivery.get("error") or "").strip()
            st.markdown(
                f"""
                <div class='hm-comm-card'>
                  <b>{html.escape(str(delivery.get('subject','Member update')))}</b>
                  <span class='hm-email-status'>{html.escape(status)}</span><br>
                  <span style='color:#64748B;font-size:.82rem;'>{html.escape(str(delivery.get('ts','')))} · {html.escape(str(delivery.get('kind','')))}</span>
                  <p style='margin:.35rem 0 0 0;'>{html.escape(str(delivery.get('message','')))}</p>
                  {f"<div class='hm-email-error'>{html.escape(error)}</div>" if error else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if str(delivery.get("status", "")) in {"failed", "configuration_missing"}:
                if st.button(
                    "Retry this email",
                    key=f"retry_email_{delivery.get('id')}",
                    disabled=not email_status.get("configured"),
                ):
                    result = retry_member_email_delivery(db, delivery.get("id", ""))
                    save_db(db)
                    if result.get("status") == "sent":
                        st.success("Email sent successfully.")
                    else:
                        st.warning(
                            "Email could not be sent: "
                            + str(result.get("error") or result.get("status") or "Unknown error")
                        )
                    st.rerun()

render_page_nav(
    "Admin-Member Communication",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
finish_and_render_page_diagnostics("Admin Messages")
