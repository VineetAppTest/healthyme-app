from __future__ import annotations

import datetime as dt
import html
from typing import Any

import streamlit as st

from components.db import list_members
from components.guards import require_admin
from components.package_hardening import (
    COMMERCIAL_SNAPSHOT_NOTE,
    INCLUSIONS_RULE,
    adjust_subscription_sessions,
    assign_or_replace_member_package,
    get_member_package_summary,
    list_member_subscriptions,
    list_packages,
    list_subscription_events,
    list_subscription_payments,
    list_usage_events,
    save_package,
    update_subscription,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


CURRENCIES = ["INR", "USD", "AED", "GBP", "EUR"]
INCLUSION_KEYS = [
    "Evaluation",
    "Meal plan",
    "Exercise plan",
    "Supplement plan",
    "Review sessions",
]
SECTION_KEY = "hm_package_hardening_section"
SECTIONS = [
    ("library", "Package Library"),
    ("assign", "Assign / Replace"),
    ("current", "Current Subscriptions"),
    ("history", "History & Audit"),
]


def _text(value: object) -> str:
    return str(value or "").strip()


def _esc(value: object) -> str:
    return html.escape(_text(value))


def _money(value: object, currency: object = "INR") -> str:
    try:
        amount = float(value or 0)
    except Exception:
        amount = 0.0
    return f"{_text(currency) or 'INR'} {amount:,.2f}"


def _date_value(value: object, fallback: dt.date | None = None) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(_text(value)[:10])
    except Exception:
        return fallback or dt.date.today()


def _inclusion_names(values: dict[str, Any] | None) -> list[str]:
    return [key for key, enabled in dict(values or {}).items() if bool(enabled)]


def _inclusion_fields(prefix: str, defaults: dict[str, Any] | None = None) -> dict[str, bool]:
    defaults = dict(defaults or {})
    left, right = st.columns(2, gap="medium")
    output: dict[str, bool] = {}
    with left:
        for key in INCLUSION_KEYS[:3]:
            output[key] = st.checkbox(
                key,
                value=bool(defaults.get(key, True)),
                key=f"{prefix}_{key.lower().replace(' ', '_')}",
            )
    with right:
        for key in INCLUSION_KEYS[3:]:
            output[key] = st.checkbox(
                key,
                value=bool(defaults.get(key, True)),
                key=f"{prefix}_{key.lower().replace(' ', '_')}",
            )
    return output


def _inject_styles() -> None:
    st.markdown(
        """
<style id="hm-package-hardening-123-v1">
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{max-width:1180px!important;padding-top:.72rem!important;}
.hm-pkg-nav{margin:.15rem 0 .85rem}.hm-pkg-nav [data-testid="stButton"]>button{min-height:2.7rem!important;font-weight:850!important}
.hm-pkg-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:19px;padding:1rem 1.05rem;margin:.45rem 0 .85rem;box-shadow:0 9px 23px rgba(15,23,42,.05)}
.hm-pkg-title{color:#064E3B;font-size:1.06rem;font-weight:950;margin:0 0 .22rem}.hm-pkg-sub{color:#64748B;font-size:.84rem;font-weight:690;line-height:1.45;margin:0 0 .75rem}
.hm-pkg-rule{border:1px solid #D8A84E;background:#FFF7E6;color:#72551A;border-radius:14px;padding:.72rem .82rem;margin:.35rem 0 .8rem;font-size:.84rem;font-weight:720;line-height:1.45}
.hm-pkg-snapshot{border:1px solid #B7DEC5;background:#EEF9F1;color:#14532D;border-radius:14px;padding:.68rem .82rem;margin:.35rem 0 .8rem;font-size:.82rem;font-weight:700}
.hm-pkg-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.6rem;margin:.55rem 0 .8rem}.hm-pkg-kpi{background:#fff;border:1px solid #E3C98E;border-radius:14px;padding:.65rem .72rem;color:#64748B;font-size:.73rem;font-weight:780}.hm-pkg-kpi b{display:block;color:#064E3B;font-size:1.15rem;margin-top:.16rem}
.hm-pkg-row{border:1px solid #E7D8BE;background:#fff;border-radius:16px;padding:.78rem .88rem;margin:.48rem 0}.hm-pkg-row-head{display:flex;justify-content:space-between;gap:.5rem;align-items:flex-start;flex-wrap:wrap;color:#064E3B;font-weight:920}.hm-pkg-row-line{color:#475569;font-size:.82rem;font-weight:620;margin:.12rem 0;line-height:1.4}.hm-pkg-pill{display:inline-flex;padding:.15rem .44rem;border-radius:999px;border:1px solid #D9C28F;background:#FFF7E6;color:#72551A;font-size:.69rem;font-weight:850;margin-left:.25rem}
.hm-pkg-inclusions{display:flex;gap:.35rem;flex-wrap:wrap;margin-top:.4rem}.hm-pkg-inclusion{display:inline-flex;border:1px solid #E3C98E;background:#FFF9EC;color:#72551A;border-radius:999px;padding:.18rem .45rem;font-size:.70rem;font-weight:780}
.hm-pkg-audit{border-left:3px solid #D8A84E;padding:.45rem .65rem;margin:.35rem 0;background:#FFFDF8;border-radius:0 10px 10px 0;color:#475569;font-size:.78rem;line-height:1.4}
@media(max-width:900px){.hm-pkg-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
""",
        unsafe_allow_html=True,
    )


def _section_navigation(package_count: int, subscription_count: int) -> str:
    current = st.session_state.get(SECTION_KEY, "library")
    valid = {key for key, _label in SECTIONS}
    if current not in valid:
        current = "library"
        st.session_state[SECTION_KEY] = current
    st.markdown("<div class='hm-pkg-nav'>", unsafe_allow_html=True)
    columns = st.columns(len(SECTIONS), gap="small")
    for column, (key, label) in zip(columns, SECTIONS):
        suffix = ""
        if key == "library":
            suffix = f" ({package_count})"
        elif key in {"current", "history"}:
            suffix = f" ({subscription_count})"
        with column:
            if st.button(
                label + suffix,
                key=f"hm_pkg_nav_{key}",
                type="primary" if current == key else "secondary",
                use_container_width=True,
            ):
                st.session_state[SECTION_KEY] = key
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    return current


def _render_rule_banners() -> None:
    st.markdown(
        f"<div class='hm-pkg-rule'><b>Accepted rule:</b> {_esc(INCLUSIONS_RULE)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='hm-pkg-snapshot'><b>Commercial snapshot protection:</b> {_esc(COMMERCIAL_SNAPSHOT_NOTE)}</div>",
        unsafe_allow_html=True,
    )


def _render_metrics(metrics: dict[str, Any]) -> None:
    st.markdown(
        "<div class='hm-pkg-kpis'>"
        f"<div class='hm-pkg-kpi'>Allowance<b>{int(metrics.get('package_sessions', 0) or 0)}</b></div>"
        f"<div class='hm-pkg-kpi'>Consumed<b>{int(metrics.get('sessions_consumed', 0) or 0)}</b></div>"
        f"<div class='hm-pkg-kpi'>Reserved<b>{int(metrics.get('sessions_reserved', 0) or 0)}</b></div>"
        f"<div class='hm-pkg-kpi'>Remaining<b>{int(metrics.get('sessions_remaining', 0) or 0)}</b></div>"
        f"<div class='hm-pkg-kpi'>Available to schedule<b>{int(metrics.get('sessions_available_to_schedule', 0) or 0)}</b></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if int(metrics.get("overbooked_sessions", 0) or 0) > 0:
        st.warning(
            f"This subscription currently has {int(metrics.get('overbooked_sessions', 0))} session(s) beyond its allowance. Review schedule-limit override history."
        )


def _render_inclusions(inclusions: dict[str, Any] | None) -> None:
    names = _inclusion_names(inclusions)
    if not names:
        st.caption("No informational inclusions selected.")
        return
    chips = "".join(
        f"<span class='hm-pkg-inclusion'>{_esc(name)}</span>" for name in names
    )
    st.markdown(
        f"<div class='hm-pkg-inclusions'>{chips}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Informational only — these labels do not control access to any module.")


def _render_package_library(packages: list[dict[str, Any]], actor_id: str) -> None:
    st.markdown("<div class='hm-pkg-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-pkg-title'>Package Library</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-pkg-sub'>Create package masters for future member subscriptions. Editing a master never rewrites an existing member's saved commercial terms.</div>",
        unsafe_allow_html=True,
    )

    option_map = {"Create new package": ""}
    for package in packages:
        option_map[
            f"{package.get('package_name','Package')} · {package.get('session_count',0)} sessions · {_money(package.get('total_value'), package.get('currency'))} · {str(package.get('status','active')).title()}"
        ] = package.get("id", "")
    selected_label = st.selectbox(
        "Create or edit package",
        list(option_map.keys()),
        key="hm_pkg_library_selection",
    )
    selected_id = option_map.get(selected_label, "")
    selected = next((row for row in packages if row.get("id") == selected_id), {})

    with st.form(f"hm_pkg_library_form_{selected_id or 'new'}", clear_on_submit=False):
        name = st.text_input(
            "Package name",
            value=_text(selected.get("package_name")),
            placeholder="Example: 8-session Wellness Package",
        )
        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            sessions = st.number_input(
                "Session allowance",
                min_value=1,
                value=max(int(selected.get("session_count", 1) or 1), 1),
                step=1,
            )
        with c2:
            cost = st.number_input(
                "Cost per session",
                min_value=0.0,
                value=float(selected.get("cost_per_session", 0) or 0),
                step=100.0,
                format="%.2f",
            )
        with c3:
            default_total = float(
                selected.get("total_value", float(sessions) * float(cost)) or 0
            )
            total = st.number_input(
                "Total package value",
                min_value=0.0,
                value=default_total,
                step=100.0,
                format="%.2f",
            )
        with c4:
            currency = st.selectbox(
                "Currency",
                CURRENCIES,
                index=CURRENCIES.index(selected.get("currency", "INR"))
                if selected.get("currency", "INR") in CURRENCIES
                else 0,
            )
        status = st.selectbox(
            "Package status",
            ["active", "inactive"],
            index=0 if selected.get("status", "active") == "active" else 1,
        )
        st.markdown("**Informational inclusions**")
        inclusions = _inclusion_fields(
            f"hm_pkg_library_inclusion_{selected_id or 'new'}",
            selected.get("inclusions", {}),
        )
        submitted = st.form_submit_button(
            "Update Package" if selected_id else "Create Package",
            type="primary",
            use_container_width=True,
        )
    if submitted:
        try:
            saved = save_package(
                package_id=selected_id,
                package_name=name,
                session_count=sessions,
                cost_per_session=cost,
                total_value=total,
                currency=currency,
                inclusions=inclusions,
                status=status,
                actor_id=actor_id,
            )
            st.success(f"Package saved: {saved.get('package_name', name)}")
            st.rerun()
        except Exception as exc:
            st.error(f"Package could not be saved: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    for package in packages:
        st.markdown(
            "<div class='hm-pkg-row'>"
            f"<div class='hm-pkg-row-head'><span>{_esc(package.get('package_name') or 'Package')}</span><span class='hm-pkg-pill'>{_esc(str(package.get('status','active')).title())}</span></div>"
            f"<div class='hm-pkg-row-line'>{int(package.get('session_count',0) or 0)} sessions · {_money(package.get('cost_per_session'), package.get('currency'))} per session · Total {_money(package.get('total_value'), package.get('currency'))}</div>"
            f"<div class='hm-pkg-row-line'>Updated {_esc(str(package.get('updated_at',''))[:19])} by {_esc(package.get('updated_by') or package.get('created_by'))}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        _render_inclusions(package.get("inclusions", {}))


def _member_options() -> tuple[list[dict[str, Any]], dict[str, str]]:
    members = list_members()
    mapping = {
        f"{member.get('name','Member')} — {member.get('email','')}": member.get("id", "")
        for member in members
    }
    return members, mapping


def _render_current_summary(summary: dict[str, Any]) -> None:
    package = dict(summary.get("package") or {})
    metrics = dict(summary.get("metrics") or {})
    if not summary.get("has_current_package") or not package:
        st.info("No active or paused package is currently assigned to this member.")
        return
    st.markdown(
        "<div class='hm-pkg-row'>"
        f"<div class='hm-pkg-row-head'><span>{_esc(package.get('package_name') or 'Package')}</span><span class='hm-pkg-pill'>{_esc(str(package.get('status','active')).title())}</span></div>"
        f"<div class='hm-pkg-row-line'>Start {_esc(package.get('start_date'))} · Expiry {_esc(package.get('expiry_date') or 'Not set')}</div>"
        f"<div class='hm-pkg-row-line'>Total {_money(package.get('total_value'), package.get('currency'))} · Paid {_money(package.get('amount_paid'), package.get('currency'))} · Outstanding {_money(package.get('outstanding_amount'), package.get('currency'))} · {_esc(str(package.get('payment_status','not_recorded')).replace('_',' ').title())}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _render_metrics(metrics)
    _render_inclusions(package.get("inclusions", {}))


def _render_assign_replace(
    packages: list[dict[str, Any]], actor_id: str
) -> None:
    st.markdown("<div class='hm-pkg-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-pkg-title'>Member-first Assignment Review</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-pkg-sub'>Review the member's current allowance, usage, reserved sessions and financial position before assigning, replacing or renewing a package.</div>",
        unsafe_allow_html=True,
    )
    _members, member_map = _member_options()
    active_packages = [row for row in packages if row.get("status") == "active"]
    if not member_map:
        st.info("No active members are available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    if not active_packages:
        st.info("Create an active Package Library record first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    selected_member_label = st.selectbox(
        "Select member",
        list(member_map.keys()),
        key="hm_pkg_assign_member",
    )
    member_id = member_map[selected_member_label]
    summary = get_member_package_summary(member_id)
    _render_current_summary(summary)
    has_current = bool(summary.get("has_current_package"))

    package_map = {
        f"{row.get('package_name','Package')} · {row.get('session_count',0)} sessions · {_money(row.get('total_value'), row.get('currency'))}": row.get("id", "")
        for row in active_packages
    }
    selected_package_label = st.selectbox(
        "Select active package",
        list(package_map.keys()),
        key="hm_pkg_assign_package",
    )
    package_id = package_map[selected_package_label]
    selected_package = next(
        (row for row in active_packages if row.get("id") == package_id), {}
    )
    st.caption(
        f"Selected commercial snapshot: {selected_package.get('session_count',0)} sessions · {_money(selected_package.get('cost_per_session'), selected_package.get('currency'))} per session · Total {_money(selected_package.get('total_value'), selected_package.get('currency'))}."
    )
    _render_inclusions(selected_package.get("inclusions", {}))

    with st.form(f"hm_pkg_assign_form_{member_id}_{package_id}", clear_on_submit=False):
        d1, d2, d3 = st.columns(3, gap="medium")
        with d1:
            start_date = st.date_input("Start date", value=dt.date.today())
        with d2:
            use_expiry = st.checkbox("Set expiry date", value=False)
        with d3:
            expiry_date = st.date_input(
                "Expiry date",
                value=dt.date.today() + dt.timedelta(days=90),
                disabled=not use_expiry,
            )

        p1, p2, p3 = st.columns(3, gap="medium")
        with p1:
            payment_status = st.selectbox(
                "Payment status",
                [
                    "not_recorded",
                    "unpaid",
                    "partially_paid",
                    "paid",
                    "complimentary",
                ],
            )
        with p2:
            amount_paid = st.number_input(
                "Amount paid",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
        with p3:
            payment_date = st.date_input(
                "Payment date",
                value=dt.date.today(),
                disabled=payment_status in {"not_recorded", "unpaid", "complimentary"},
            )
        payment_reference = st.text_input(
            "Payment reference",
            placeholder="Optional transaction/reference number",
        )

        assignment_type = "replacement"
        decision = ""
        replacement_reason = ""
        manual_sessions = 0
        if has_current:
            assignment_type = st.radio(
                "Assignment type",
                ["replacement", "renewal"],
                horizontal=True,
            )
            decision_label = st.selectbox(
                "Unused-session decision",
                [
                    "Expire unused sessions",
                    "Carry forward available sessions",
                    "Retain current package until exhausted",
                    "Manual adjustment",
                ],
            )
            decision = {
                "Expire unused sessions": "expire_unused",
                "Carry forward available sessions": "carry_forward",
                "Retain current package until exhausted": "retain_until_exhausted",
                "Manual adjustment": "manual_adjustment",
            }[decision_label]
            if decision == "manual_adjustment":
                manual_sessions = st.number_input(
                    "Sessions to add to the new package",
                    min_value=0,
                    value=0,
                    step=1,
                )
            replacement_reason = st.text_area(
                "Mandatory replacement / renewal reason",
                placeholder="Explain why the current package is being replaced or renewed.",
            )

        submitted = st.form_submit_button(
            "Assign Package" if not has_current else "Confirm Replacement / Renewal",
            type="primary",
            use_container_width=True,
        )
    if submitted:
        try:
            result = assign_or_replace_member_package(
                member_id=member_id,
                package_id=package_id,
                start_date=start_date,
                expiry_date=expiry_date if use_expiry else None,
                payment_status=payment_status,
                amount_paid=amount_paid,
                payment_date=payment_date
                if payment_status not in {"not_recorded", "unpaid", "complimentary"}
                else None,
                payment_reference=payment_reference,
                assignment_type=assignment_type,
                unused_sessions_decision=decision,
                replacement_reason=replacement_reason,
                manual_adjustment_sessions=manual_sessions,
                actor_id=actor_id,
            )
            if result.get("status") == "retained":
                st.info(result.get("message"))
            else:
                st.success("Package assignment saved with commercial snapshot and audit history.")
                st.rerun()
        except Exception as exc:
            st.error(f"Package assignment could not be completed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)


def _subscription_label(row: dict[str, Any]) -> str:
    return (
        f"{row.get('member_name') or row.get('member_email') or 'Member'} · "
        f"{row.get('package_name') or 'Package'} · {str(row.get('status','')).title()} · "
        f"{str(row.get('subscribed_at',''))[:10]}"
    )


def _filter_subscriptions(
    rows: list[dict[str, Any]], *, current_only: bool
) -> list[dict[str, Any]]:
    search, status, payment = st.columns([1.4, 1, 1], gap="medium")
    with search:
        query = st.text_input(
            "Search member or package",
            key=f"hm_pkg_search_{'current' if current_only else 'history'}",
        ).lower()
    with status:
        statuses = ["All"] + sorted({_text(row.get("status")) for row in rows if row.get("status")})
        selected_status = st.selectbox(
            "Status",
            statuses,
            key=f"hm_pkg_status_{'current' if current_only else 'history'}",
        )
    with payment:
        payments = ["All"] + sorted({_text(row.get("payment_status")) for row in rows if row.get("payment_status")})
        selected_payment = st.selectbox(
            "Payment",
            payments,
            key=f"hm_pkg_payment_{'current' if current_only else 'history'}",
        )
    output = []
    for row in rows:
        if current_only and row.get("status") not in {"active", "paused"}:
            continue
        haystack = " ".join(
            [
                _text(row.get("member_name")),
                _text(row.get("member_email")),
                _text(row.get("package_name")),
            ]
        ).lower()
        if query and query not in haystack:
            continue
        if selected_status != "All" and row.get("status") != selected_status:
            continue
        if selected_payment != "All" and row.get("payment_status") != selected_payment:
            continue
        output.append(row)
    return output


def _render_subscription_card(row: dict[str, Any]) -> None:
    metrics = dict(row.get("metrics") or {})
    st.markdown(
        "<div class='hm-pkg-row'>"
        f"<div class='hm-pkg-row-head'><span>{_esc(row.get('member_name') or row.get('member_email') or 'Member')} · {_esc(row.get('package_name') or 'Package')}</span><span class='hm-pkg-pill'>{_esc(str(row.get('status','')).title())}</span></div>"
        f"<div class='hm-pkg-row-line'>Start {_esc(row.get('start_date'))} · Expiry {_esc(row.get('expiry_date') or 'Not set')} · Assigned {_esc(str(row.get('subscribed_at',''))[:19])}</div>"
        f"<div class='hm-pkg-row-line'>Snapshot: {int(row.get('session_count',0) or 0)} sessions · {_money(row.get('cost_per_session'), row.get('currency'))}/session · Total {_money(row.get('total_value'), row.get('currency'))}</div>"
        f"<div class='hm-pkg-row-line'>Payment: {_esc(str(row.get('payment_status','not_recorded')).replace('_',' ').title())} · Paid {_money(row.get('amount_paid'), row.get('currency'))} · Outstanding {_money(row.get('outstanding_amount'), row.get('currency'))}</div>"
        f"<div class='hm-pkg-row-line'>Audit: assigned by {_esc(row.get('assigned_by') or row.get('created_by'))} · updated by {_esc(row.get('updated_by'))} at {_esc(str(row.get('updated_at',''))[:19])}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _render_metrics(metrics)


def _render_subscription_management(
    subscriptions: list[dict[str, Any]], actor_id: str
) -> None:
    st.markdown("<div class='hm-pkg-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-pkg-title'>Current Subscriptions</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-pkg-sub'>Manage payment, extension, pause/resume, cancellation, completion, refund and audited session adjustments.</div>",
        unsafe_allow_html=True,
    )
    filtered = _filter_subscriptions(subscriptions, current_only=True)
    if not filtered:
        st.info("No current subscriptions match the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    labels = {_subscription_label(row): row.get("id", "") for row in filtered}
    selected_label = st.selectbox(
        "Select current subscription",
        list(labels.keys()),
        key="hm_pkg_current_selected",
    )
    selected_id = labels[selected_label]
    selected = next(row for row in filtered if row.get("id") == selected_id)
    _render_subscription_card(selected)
    _render_inclusions(selected.get("inclusions", {}))

    action = st.selectbox(
        "Subscription action",
        [
            "Update payment",
            "Extend expiry",
            "Pause",
            "Resume",
            "Cancel",
            "Mark completed",
            "Record refund",
            "Add complimentary sessions",
            "Manual allowance adjustment",
            "Manual consumption adjustment",
        ],
        key="hm_pkg_current_action",
    )
    action_key = {
        "Update payment": "payment_update",
        "Extend expiry": "extend",
        "Pause": "pause",
        "Resume": "resume",
        "Cancel": "cancel",
        "Mark completed": "complete",
        "Record refund": "refund",
    }.get(action, "")

    with st.form(f"hm_pkg_action_form_{selected_id}_{action}", clear_on_submit=False):
        reason = st.text_area(
            "Reason / note",
            placeholder="Mandatory for lifecycle and session adjustments; optional for payment update.",
        )
        expiry_date = None
        payment_status = ""
        amount = 0.0
        payment_date = None
        reference = ""
        session_delta = 0
        if action == "Update payment":
            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                payment_status = st.selectbox(
                    "Payment status",
                    [
                        "not_recorded",
                        "unpaid",
                        "partially_paid",
                        "paid",
                        "complimentary",
                    ],
                    index=[
                        "not_recorded",
                        "unpaid",
                        "partially_paid",
                        "paid",
                        "complimentary",
                    ].index(selected.get("payment_status", "not_recorded"))
                    if selected.get("payment_status", "not_recorded")
                    in {
                        "not_recorded",
                        "unpaid",
                        "partially_paid",
                        "paid",
                        "complimentary",
                    }
                    else 0,
                )
            with c2:
                amount = st.number_input(
                    "Total amount paid",
                    min_value=0.0,
                    value=float(selected.get("amount_paid", 0) or 0),
                    step=100.0,
                    format="%.2f",
                )
            with c3:
                payment_date = st.date_input("Payment date", value=dt.date.today())
            reference = st.text_input("Payment reference")
        elif action == "Extend expiry":
            expiry_date = st.date_input(
                "New expiry date",
                value=_date_value(
                    selected.get("expiry_date"), dt.date.today()
                )
                + dt.timedelta(days=30),
            )
        elif action == "Record refund":
            amount = st.number_input(
                "Refund amount",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
            payment_date = st.date_input("Refund date", value=dt.date.today())
            reference = st.text_input("Refund reference")
        elif action in {
            "Add complimentary sessions",
            "Manual allowance adjustment",
            "Manual consumption adjustment",
        }:
            min_value = 1 if action == "Add complimentary sessions" else -100
            session_delta = st.number_input(
                "Session adjustment",
                min_value=min_value,
                max_value=100,
                value=1,
                step=1,
            )
        submitted = st.form_submit_button(
            "Apply audited action",
            type="primary",
            use_container_width=True,
        )
    if submitted:
        try:
            if action_key:
                update_subscription(
                    subscription_id=selected_id,
                    action=action_key,
                    reason=reason,
                    expiry_date=expiry_date,
                    payment_status=payment_status,
                    amount=amount,
                    payment_date=payment_date,
                    reference=reference,
                    actor_id=actor_id,
                )
            else:
                adjustment_type = {
                    "Add complimentary sessions": "complimentary",
                    "Manual allowance adjustment": "manual_allowance",
                    "Manual consumption adjustment": "manual_consumption",
                }[action]
                adjust_subscription_sessions(
                    subscription_id=selected_id,
                    adjustment_type=adjustment_type,
                    session_delta=session_delta,
                    reason=reason,
                    actor_id=actor_id,
                )
            st.success("Subscription action saved with audit history.")
            st.rerun()
        except Exception as exc:
            st.error(f"Subscription action could not be completed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_history(subscriptions: list[dict[str, Any]]) -> None:
    st.markdown("<div class='hm-pkg-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-pkg-title'>Subscription History & Audit</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-pkg-sub'>Review current and historical commercial snapshots, replacement outcomes, unused-session decisions, usage adjustments and payments.</div>",
        unsafe_allow_html=True,
    )
    filtered = _filter_subscriptions(subscriptions, current_only=False)
    if not filtered:
        st.info("No subscription records match the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    labels = {_subscription_label(row): row.get("id", "") for row in filtered}
    selected_label = st.selectbox(
        "Select subscription history record",
        list(labels.keys()),
        key="hm_pkg_history_selected",
    )
    selected_id = labels[selected_label]
    selected = next(row for row in filtered if row.get("id") == selected_id)
    _render_subscription_card(selected)
    _render_inclusions(selected.get("inclusions", {}))
    if selected.get("replacement_reason") or selected.get("unused_sessions_decision"):
        st.markdown(
            "<div class='hm-pkg-audit'>"
            f"<b>Replacement reason:</b> {_esc(selected.get('replacement_reason') or 'Not recorded')}<br>"
            f"<b>Unused-session decision:</b> {_esc(str(selected.get('unused_sessions_decision') or 'Not applicable').replace('_',' ').title())}<br>"
            f"<b>Unused at end:</b> {int(selected.get('unused_sessions_at_end',0) or 0)} · <b>Carried/adjusted:</b> {int(selected.get('carry_forward_sessions',0) or 0)}"
            "</div>",
            unsafe_allow_html=True,
        )

    events = list_subscription_events(selected_id)
    usage = list_usage_events(selected_id)
    payments = list_subscription_payments(selected_id)
    event_tab, usage_tab, payment_tab = st.tabs(
        [f"Lifecycle ({len(events)})", f"Usage ({len(usage)})", f"Payments ({len(payments)})"]
    )
    with event_tab:
        if not events:
            st.info("No lifecycle events recorded.")
        for row in events:
            st.markdown(
                f"<div class='hm-pkg-audit'><b>{_esc(str(row.get('event_type','')).replace('_',' ').title())}</b> · {_esc(str(row.get('created_at',''))[:19])} · {_esc(row.get('created_by'))}<br>{_esc(row.get('reason'))}</div>",
                unsafe_allow_html=True,
            )
    with usage_tab:
        if not usage:
            st.info("No package usage or adjustment events recorded.")
        for row in usage:
            st.markdown(
                f"<div class='hm-pkg-audit'><b>{_esc(str(row.get('event_type','')).replace('_',' ').title())}</b> · Allowance {int(row.get('allowance_delta',0) or 0):+d} · Consumption {int(row.get('consumption_delta',0) or 0):+d}<br>{_esc(row.get('reason'))} · {_esc(str(row.get('created_at',''))[:19])}</div>",
                unsafe_allow_html=True,
            )
    with payment_tab:
        if not payments:
            st.info("No payment or refund entries recorded.")
        for row in payments:
            st.markdown(
                f"<div class='hm-pkg-audit'><b>{_esc(str(row.get('payment_type','')).replace('_',' ').title())}</b> · {_money(row.get('amount'), row.get('currency'))} · {_esc(str(row.get('payment_status','')).title())}<br>{_esc(row.get('reference'))} · {_esc(str(row.get('payment_date') or row.get('created_at',''))[:19])}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_package_hardening_admin_page() -> None:
    st.set_page_config(
        page_title="Packages",
        page_icon="💚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_styles()
    apply_luxe_theme()
    require_admin()
    utility_logout_bar()
    topbar(
        "Packages",
        "Hardened package masters, member subscriptions, usage governance and financial visibility.",
        "Admin workflow",
    )
    _inject_styles()
    _render_rule_banners()

    actor_id = _text(st.session_state.get("user_id")) or "admin"
    try:
        packages = list_packages(active_only=False)
        subscriptions = list_member_subscriptions()
    except Exception as exc:
        st.error(f"Package workspace could not load normalized Supabase data: {exc}")
        st.stop()

    section = _section_navigation(len(packages), len(subscriptions))
    if section == "library":
        _render_package_library(packages, actor_id)
    elif section == "assign":
        _render_assign_replace(packages, actor_id)
    elif section == "current":
        _render_subscription_management(subscriptions, actor_id)
    else:
        _render_history(subscriptions)

    render_page_nav(
        "Packages",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()
