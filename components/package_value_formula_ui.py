from __future__ import annotations

from typing import Any

import streamlit as st

from components.package_hardening import save_package
from components.package_hardening_ui import (
    CURRENCIES,
    _esc,
    _inclusion_fields,
    _money,
    _render_inclusions,
    _text,
)


def calculated_package_total(session_count: object, cost_per_session: object) -> float:
    try:
        sessions = max(int(session_count or 0), 0)
    except Exception:
        sessions = 0
    try:
        cost = max(float(cost_per_session or 0), 0.0)
    except Exception:
        cost = 0.0
    return float(sessions) * cost


def _render_package_library_with_formula(
    packages: list[dict[str, Any]], actor_id: str
) -> None:
    st.markdown("<div class='hm-pkg-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-pkg-title'>Package Library</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-pkg-sub'>Create package masters for future member subscriptions. Editing a master never rewrites an existing member's saved commercial terms.</div>",
        unsafe_allow_html=True,
    )

    option_map = {"Create new package": ""}
    for package in packages:
        total = calculated_package_total(
            package.get("session_count"), package.get("cost_per_session")
        )
        option_map[
            f"{package.get('package_name','Package')} · {package.get('session_count',0)} sessions · {_money(total, package.get('currency'))} · {str(package.get('status','active')).title()}"
        ] = package.get("id", "")

    selected_label = st.selectbox(
        "Create or edit package",
        list(option_map.keys()),
        key="hm_pkg_library_selection",
    )
    selected_id = option_map.get(selected_label, "")
    selected = next((row for row in packages if row.get("id") == selected_id), {})
    suffix = selected_id or "new"

    name = st.text_input(
        "Package name",
        value=_text(selected.get("package_name")),
        placeholder="Example: 8-session Wellness Package",
        key=f"hm_pkg_formula_name_{suffix}",
    )
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        sessions = st.number_input(
            "Session allowance",
            min_value=1,
            value=max(int(selected.get("session_count", 1) or 1), 1),
            step=1,
            key=f"hm_pkg_formula_sessions_{suffix}",
        )
    with c2:
        cost = st.number_input(
            "Cost per session",
            min_value=0.0,
            value=float(selected.get("cost_per_session", 0) or 0),
            step=100.0,
            format="%.2f",
            key=f"hm_pkg_formula_cost_{suffix}",
        )
    total = calculated_package_total(sessions, cost)
    with c3:
        st.number_input(
            "Total package value",
            min_value=0.0,
            value=total,
            step=100.0,
            format="%.2f",
            disabled=True,
            key=f"hm_pkg_formula_total_{suffix}_{sessions}_{cost}",
            help="Calculated automatically as Session allowance × Cost per session.",
        )
        st.caption("Calculated automatically: allowance × cost per session.")
    with c4:
        selected_currency = selected.get("currency", "INR")
        currency = st.selectbox(
            "Currency",
            CURRENCIES,
            index=CURRENCIES.index(selected_currency)
            if selected_currency in CURRENCIES
            else 0,
            key=f"hm_pkg_formula_currency_{suffix}",
        )

    status = st.selectbox(
        "Package status",
        ["active", "inactive"],
        index=0 if selected.get("status", "active") == "active" else 1,
        key=f"hm_pkg_formula_status_{suffix}",
    )
    st.markdown("**Informational inclusions**")
    inclusions = _inclusion_fields(
        f"hm_pkg_library_inclusion_{suffix}",
        selected.get("inclusions", {}),
    )
    submitted = st.button(
        "Update Package" if selected_id else "Create Package",
        type="primary",
        use_container_width=True,
        key=f"hm_pkg_formula_save_{suffix}",
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
        total = calculated_package_total(
            package.get("session_count"), package.get("cost_per_session")
        )
        st.markdown(
            "<div class='hm-pkg-row'>"
            f"<div class='hm-pkg-row-head'><span>{_esc(package.get('package_name') or 'Package')}</span><span class='hm-pkg-pill'>{_esc(str(package.get('status','active')).title())}</span></div>"
            f"<div class='hm-pkg-row-line'>{int(package.get('session_count',0) or 0)} sessions · {_money(package.get('cost_per_session'), package.get('currency'))} per session · Total {_money(total, package.get('currency'))}</div>"
            f"<div class='hm-pkg-row-line'>Updated {_esc(str(package.get('updated_at',''))[:19])} by {_esc(package.get('updated_by') or package.get('created_by'))}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        _render_inclusions(package.get("inclusions", {}))


def install_package_value_formula(package_ui_module) -> None:
    """Make package total a read-only multiplication in the active Admin UI."""

    package_ui_module._render_package_library = _render_package_library_with_formula
