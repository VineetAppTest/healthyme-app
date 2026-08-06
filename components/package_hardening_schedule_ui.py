from __future__ import annotations

import html

import streamlit as st

from components.admin_role_model import current_user_is_admin
from components.package_hardening import (
    INCLUSIONS_RULE,
    get_member_package_summary,
    member_session_ledger,
    schedule_capacity,
)


_OVERRIDE_KEY = "hm_package_schedule_limit_override"
_OVERRIDE_REASON_KEY = "hm_package_schedule_limit_override_reason"


def _text(value: object) -> str:
    return str(value or "").strip()


def _safe(value: object) -> str:
    return html.escape(_text(value))


def _money(value: object, currency: object) -> str:
    try:
        amount = float(value or 0)
    except Exception:
        amount = 0.0
    return f"{_text(currency) or 'INR'} {amount:,.2f}"


def _render_member_usage_status_table(
    member_id: object,
    metrics: dict,
    package: dict,
) -> None:
    try:
        ledger = member_session_ledger(member_id)
    except Exception as exc:
        st.error(f"Usage status could not be loaded: {exc}")
        return

    ledger_metrics = dict(ledger.get("metrics") or metrics or {})
    consumed = int(
        ledger_metrics.get("sessions_consumed", ledger.get("consumed_count", 0)) or 0
    )
    scheduled = int(
        ledger_metrics.get("sessions_reserved", ledger.get("reserved_count", 0)) or 0
    )
    total = int(
        ledger_metrics.get(
            "package_sessions",
            package.get("session_count", ledger.get("package_sessions", 0)),
        )
        or 0
    )
    remaining = int(
        ledger_metrics.get("sessions_remaining", ledger.get("remaining_sessions", 0))
        or 0
    )
    available = int(
        ledger_metrics.get(
            "sessions_available_to_schedule",
            ledger.get("available_to_schedule", 0),
        )
        or 0
    )
    status = _text(package.get("status") or "active").replace("_", " ").title()
    rows = list(ledger.get("rows") or [])
    scheduled_rows = [
        row
        for row in rows
        if not row.get("consumed")
        and _text(row.get("raw_status")).lower() in {"scheduled", "acknowledged"}
    ]
    consumed_rows = [row for row in rows if row.get("consumed")]
    st.markdown(
        """
<style id="hm-member-package-usage-status-v1">
.hm-usage-status-wrap{overflow-x:auto;border:1px solid #E3C98E;border-radius:14px;background:#FFFDF8;margin:.48rem 0 .10rem}
.hm-usage-status-table{width:100%;border-collapse:collapse;min-width:720px;font-size:.80rem;line-height:1.32}
.hm-usage-status-table th{background:#FFF7E6;color:#064E3B;text-align:center;font-weight:900;padding:.48rem .52rem;border:1px solid #E3C98E;white-space:nowrap}
.hm-usage-status-table td{color:#334155;text-align:center;font-weight:760;padding:.52rem .54rem;border:1px solid #F0E3C5;white-space:nowrap}
.hm-usage-status-caption{color:#64748B;font-size:.76rem;font-weight:700;margin:.32rem 0 0}
.hm-meeting-detail-title{color:#064E3B;font-size:.84rem;font-weight:950;margin:.58rem 0 .24rem}
.hm-meeting-detail-wrap{overflow-x:auto;border:1px solid #E3C98E;border-radius:12px;background:#FFFDF8;margin:.18rem 0 .58rem}
.hm-meeting-detail-table{width:100%;min-width:660px;border-collapse:collapse;font-size:.76rem;line-height:1.32}
.hm-meeting-detail-table th{background:#FFF7E6;color:#064E3B;text-align:left;font-weight:900;padding:.42rem .48rem;border:1px solid #E3C98E;white-space:nowrap}
.hm-meeting-detail-table td{color:#334155;font-weight:730;padding:.44rem .48rem;border:1px solid #F0E3C5;vertical-align:top}
.hm-meeting-detail-empty{border:1px dashed #D9C28F;border-radius:12px;background:#FFFDF8;color:#64748B;padding:.52rem .62rem;margin:.18rem 0 .58rem;font-size:.76rem;font-weight:720}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='hm-usage-status-wrap'><table class='hm-usage-status-table'>"
        "<thead><tr><th>Total Sessions</th><th>Consumed</th><th>Scheduled</th>"
        "<th>Remaining</th><th>Available to Schedule</th><th>Status</th></tr></thead>"
        "<tbody><tr>"
        f"<td>{total}</td><td>{consumed}</td><td>{scheduled}</td>"
        f"<td>{remaining}</td><td>{available}</td><td>{_safe(status)}</td>"
        "</tr></tbody></table></div>"
        "<div class='hm-usage-status-caption'>Usage status is based on completed sessions, open scheduled sessions and approved late-reschedule consumption.</div>",
        unsafe_allow_html=True,
    )
    _render_meeting_detail_table(
        "Scheduled Meeting Details",
        scheduled_rows,
        "No meeting is currently scheduled.",
    )
    _render_meeting_detail_table(
        "Consumed Meeting Details",
        consumed_rows,
        "No meeting has been consumed yet.",
    )


def _render_meeting_detail_table(
    title: str,
    rows: list[dict],
    empty_message: str,
) -> None:
    st.markdown(
        f"<div class='hm-meeting-detail-title'>{_safe(title)}</div>",
        unsafe_allow_html=True,
    )
    if not rows:
        st.markdown(
            f"<div class='hm-meeting-detail-empty'>{_safe(empty_message)}</div>",
            unsafe_allow_html=True,
        )
        return
    body = "".join(
        "<tr>"
        f"<td>{_safe(row.get('title') or 'Session')}</td>"
        f"<td>{_safe(row.get('date') or '-')}</td>"
        f"<td>{_safe(row.get('time') or '-')}</td>"
        f"<td>{_safe(row.get('status') or '-')}</td>"
        "</tr>"
        for row in rows
    )
    st.markdown(
        "<div class='hm-meeting-detail-wrap'><table class='hm-meeting-detail-table'>"
        "<thead><tr><th>Meeting</th><th>Date</th><th>Time</th><th>Status</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _selected_admin_member_id(schedule_timezone_ui) -> str:
    selected_label = st.session_state.get("hm_tz_schedule_member")
    if not selected_label:
        return ""
    member_options = {
        f"{member.get('name', '')} — {member.get('email', '')}": member.get("id", "")
        for member in schedule_timezone_ui.list_members()
    }
    return _text(member_options.get(selected_label))


def _render_hardened_package(member_id: object, member_view: bool = False) -> None:
    heading = "Package Subscribed" if member_view else "Current Member Package"
    st.markdown(
        f"<div class='hm-schedule-heading'>{heading}</div>",
        unsafe_allow_html=True,
    )
    try:
        summary = get_member_package_summary(member_id)
    except Exception as exc:
        st.error(f"Package summary could not be loaded: {exc}")
        return
    package = dict(summary.get("package") or {})
    metrics = dict(summary.get("metrics") or {})
    if not package:
        st.info(
            "No package has been subscribed for you yet."
            if member_view
            else "No active or paused package is assigned to this member."
        )
        return

    inclusions = [
        key
        for key, enabled in dict(package.get("inclusions") or {}).items()
        if bool(enabled)
    ]
    inclusions_text = ", ".join(inclusions) or "No informational inclusions selected"
    st.markdown(
        "<div class='hm-package-summary'>"
        f"<div class='hm-package-title'>{_safe(package.get('package_name') or 'Package')} <span class='hm-schedule-pill'>{_safe(str(package.get('status','active')).title())}</span></div>"
        f"<div class='hm-package-line'>Allowance: {int(metrics.get('package_sessions', package.get('session_count', 0)) or 0)} sessions · Cost/session: {_money(package.get('cost_per_session'), package.get('currency'))} · Total: {_money(package.get('total_value'), package.get('currency'))}</div>"
        f"<div class='hm-package-line'>Start: {_safe(package.get('start_date') or 'Not set')} · Expiry: {_safe(package.get('expiry_date') or 'Not set')}</div>"
        f"<div class='hm-package-line'>Payment: {_safe(str(package.get('payment_status','not_recorded')).replace('_',' ').title())} · Paid: {_money(package.get('amount_paid'), package.get('currency'))} · Outstanding: {_money(package.get('outstanding_amount'), package.get('currency'))}</div>"
        f"<div class='hm-package-line'><b>Informational inclusions:</b> {_safe(inclusions_text)}</div>"
        f"<div class='hm-package-line'><i>{_safe(INCLUSIONS_RULE)}</i></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if member_view:
        _render_member_usage_status_table(member_id, metrics, package)


def _render_hardened_ledger(member_id: object, member_timezone: str) -> None:
    st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-schedule-heading'>Session Usage</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='hm-schedule-sub'>Completed sessions and approved late-reschedule consumption follow one canonical rule in Streamlit and Flutter. Open scheduled sessions reserve capacity. Dates and times are shown in member local time: {_safe(member_timezone)}.</div>",
        unsafe_allow_html=True,
    )
    try:
        ledger = member_session_ledger(member_id)
    except Exception as exc:
        st.error(f"Session ledger could not be loaded: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    metrics = dict(ledger.get("metrics") or {})
    st.markdown(
        "<style>.hm-hardened-ledger-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.45rem 0 .8rem}.hm-hardened-ledger-grid .hm-ledger-kpi{min-width:0}@media(max-width:900px){.hm-hardened-ledger-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style>"
        "<div class='hm-hardened-ledger-grid'>"
        f"<div class='hm-ledger-kpi'>Allowance<b>{int(metrics.get('package_sessions', 0) or 0)}</b></div>"
        f"<div class='hm-ledger-kpi'>Consumed<b>{int(metrics.get('sessions_consumed', 0) or 0)}</b></div>"
        f"<div class='hm-ledger-kpi'>Reserved<b>{int(metrics.get('sessions_reserved', 0) or 0)}</b></div>"
        f"<div class='hm-ledger-kpi'>Remaining<b>{int(metrics.get('sessions_remaining', 0) or 0)}</b></div>"
        f"<div class='hm-ledger-kpi'>Available to schedule<b>{int(metrics.get('sessions_available_to_schedule', 0) or 0)}</b></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    package = dict(ledger.get("package") or {})
    st.markdown(
        f"<div class='hm-package-line'>Historical consumed value: {_money(ledger.get('consumed_cost'), package.get('currency','INR'))}. Each ledger row uses its saved historical subscription price, never the latest Package Library price.</div>",
        unsafe_allow_html=True,
    )
    if int(metrics.get("overbooked_sessions", 0) or 0) > 0:
        st.warning(
            f"{int(metrics.get('overbooked_sessions', 0))} session(s) are beyond the current allowance. This can occur only through an audited Admin/Super Admin override or legacy history."
        )
    rows = list(ledger.get("rows") or [])
    if not rows:
        st.info("No sessions have been scheduled yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    st.markdown("<div class='hm-ledger-table'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-ledger-row hm-ledger-head'><div>Session</div><div>Date</div><div>Time</div><div>Cost</div><div>Usage</div></div>",
        unsafe_allow_html=True,
    )
    for row in rows:
        usage = "Consumed" if row.get("consumed") else "Open / not consumed"
        st.markdown(
            "<div class='hm-ledger-row'>"
            f"<div>{_safe(row.get('title') or 'Session')}<br><small>{_safe(row.get('status'))}</small></div>"
            f"<div>{_safe(row.get('date'))}</div>"
            f"<div>{_safe(row.get('time'))}</div>"
            f"<div>{_money(row.get('cost'), row.get('currency'))}</div>"
            f"<div>{_safe(usage)}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)


def _install_admin_create_guard(schedule_timezone_ui) -> None:
    if getattr(st, "_hm_package_schedule_button_guard_installed", False):
        return
    st._hm_package_schedule_button_guard_installed = True
    base_button = getattr(st, "_hm_base_button_before_package_guard", st.button)
    st._hm_base_button_before_package_guard = base_button

    def button_with_package_capacity(label, *args, **kwargs):
        if str(label) != "Create Schedule / Notify Member":
            return base_button(label, *args, **kwargs)

        member_id = _selected_admin_member_id(schedule_timezone_ui)
        schedule_date = st.session_state.get("hm_tz_schedule_date")
        try:
            capacity = schedule_capacity(member_id, schedule_date)
        except Exception as exc:
            capacity = {
                "allowed": False,
                "requires_override": True,
                "message": f"Package capacity could not be verified: {exc}",
                "metrics": {},
                "package": {},
            }
        metrics = dict(capacity.get("metrics") or {})
        package = dict(capacity.get("package") or {})
        st.markdown(
            "<div class='hm-policy-box'>"
            f"<b>Package capacity check:</b> {_safe(package.get('package_name') or 'No current package')} · "
            f"Allowance {int(metrics.get('package_sessions',0) or 0)} · Consumed {int(metrics.get('sessions_consumed',0) or 0)} · "
            f"Reserved {int(metrics.get('sessions_reserved',0) or 0)} · Available to schedule {int(metrics.get('sessions_available_to_schedule',0) or 0)}"
            "</div>",
            unsafe_allow_html=True,
        )

        blocked = bool(capacity.get("requires_override"))
        override = False
        reason = ""
        if blocked:
            st.warning(capacity.get("message") or "A package-limit override is required.")
            if current_user_is_admin():
                override = st.checkbox(
                    "Admin/Super Admin override — allow this schedule despite the package limit",
                    key=_OVERRIDE_KEY,
                )
                if override:
                    reason = st.text_area(
                        "Mandatory package-limit override reason",
                        key=_OVERRIDE_REASON_KEY,
                        placeholder="Explain why this session must be scheduled beyond the current package allowance or lifecycle status.",
                    ).strip()
            else:
                st.error("Only Admin or Super Admin can override package scheduling limits.")
        else:
            st.session_state.pop(_OVERRIDE_KEY, None)
            st.session_state.pop(_OVERRIDE_REASON_KEY, None)

        original_disabled = bool(kwargs.get("disabled", False))
        kwargs["disabled"] = original_disabled or (
            blocked and (not override or not reason)
        )
        return base_button(label, *args, **kwargs)

    st.button = button_with_package_capacity
    schedule_timezone_ui.st.button = button_with_package_capacity


def install_package_hardening_schedule_ui(
    schedule_timezone_ui,
    *,
    admin_page: bool,
) -> None:
    """Replace only package/ledger presentation and the Admin create guard."""

    schedule_timezone_ui._render_package = _render_hardened_package
    schedule_timezone_ui._render_member_ledger = _render_hardened_ledger
    if admin_page:
        _install_admin_create_guard(schedule_timezone_ui)