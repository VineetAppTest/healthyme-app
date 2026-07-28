from __future__ import annotations

from typing import Any


_INSTALLED = False


def install_package_hardening() -> None:
    """Install normalized package reads and package-limit scheduling guards.

    This adapter intentionally leaves authentication, route registration and role guards
    unchanged. Package inclusions remain descriptive data only.
    """

    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    from components import db as db_api
    from components import package_hardening as hardening

    if getattr(db_api, "_hm_package_hardening_123_installed", False):
        return
    db_api._hm_package_hardening_123_installed = True

    base_create_schedule = db_api.create_member_schedule
    base_update_schedule_status = db_api.update_member_schedule_status

    def list_packages_v1024b14(active_only=True):
        return hardening.list_packages(active_only=bool(active_only))

    def create_package_v1024b14(
        package_name="",
        session_count=1,
        cost_per_session=0.0,
        currency="INR",
        number_of_people=1,
        inclusions=None,
        actor_id="admin",
    ):
        del number_of_people
        return hardening.save_package(
            package_name=package_name,
            session_count=session_count,
            cost_per_session=cost_per_session,
            total_value=float(session_count or 1) * float(cost_per_session or 0),
            currency=currency,
            inclusions=inclusions,
            status="active",
            actor_id=actor_id,
        )

    def update_package_v1024b14(
        package_id,
        package_name="",
        session_count=1,
        cost_per_session=0.0,
        currency="INR",
        number_of_people=1,
        inclusions=None,
        status="active",
        actor_id="admin",
    ):
        del number_of_people
        return hardening.save_package(
            package_id=package_id,
            package_name=package_name,
            session_count=session_count,
            cost_per_session=cost_per_session,
            total_value=float(session_count or 1) * float(cost_per_session or 0),
            currency=currency,
            inclusions=inclusions,
            status=status,
            actor_id=actor_id,
        )

    def get_member_active_package_v1024b14(member_id):
        summary = hardening.get_member_package_summary(member_id)
        package = dict(summary.get("package") or {})
        if not package:
            return None
        package["metrics"] = dict(summary.get("metrics") or {})
        package["number_of_people"] = 1
        package["inclusions_informational_only"] = True
        return package

    def list_member_packages_v1024b14(member_id=None):
        rows = hardening.list_member_subscriptions(member_id or "")
        for row in rows:
            row["number_of_people"] = 1
            row["inclusions_informational_only"] = True
        return rows

    def get_member_session_ledger_v1024b13(member_id=None):
        if not member_id:
            return {
                "rows": [],
                "consumed_count": 0,
                "reserved_count": 0,
                "consumed_cost": 0,
                "package": None,
                "package_sessions": 0,
                "remaining_sessions": 0,
                "available_to_schedule": 0,
                "overbooked_sessions": 0,
            }
        return hardening.member_session_ledger(member_id)

    def create_member_schedule(
        member_id,
        title,
        schedule_type,
        schedule_date,
        start_time,
        end_time="",
        mode="",
        location_or_link="",
        notes="",
        actor_id="admin",
        session_cost=None,
        **_kwargs,
    ):
        capacity = hardening.schedule_capacity(member_id, schedule_date)
        override = False
        override_reason = ""
        try:
            import streamlit as st

            override = bool(st.session_state.get("hm_package_schedule_limit_override"))
            override_reason = str(
                st.session_state.get("hm_package_schedule_limit_override_reason") or ""
            ).strip()
        except Exception:
            pass

        if capacity.get("requires_override") and not override:
            return {
                "error": capacity.get("message")
                or "No package session is available for this schedule.",
                "package_limit_reached": True,
                "package_capacity": capacity,
            }
        if capacity.get("requires_override") and not override_reason:
            return {
                "error": "A mandatory Admin/Super Admin override reason is required.",
                "package_limit_reached": True,
                "package_capacity": capacity,
            }

        result = base_create_schedule(
            member_id=member_id,
            title=title,
            schedule_type=schedule_type,
            schedule_date=schedule_date,
            start_time=start_time,
            end_time=end_time,
            mode=mode,
            location_or_link=location_or_link,
            notes=notes,
            actor_id=actor_id,
            session_cost=session_cost,
        )
        if not result or result.get("error"):
            return result

        result["package_capacity_before_creation"] = capacity
        result["package_limit_overridden"] = bool(capacity.get("requires_override"))
        if capacity.get("requires_override"):
            result["package_override"] = hardening.record_schedule_limit_override(
                member_id=member_id,
                schedule_id=result.get("id", ""),
                reason=override_reason,
                actor_id=actor_id,
            )
        try:
            import streamlit as st

            st.session_state.pop("hm_package_schedule_limit_override", None)
            st.session_state.pop("hm_package_schedule_limit_override_reason", None)
        except Exception:
            pass
        return result

    def update_member_schedule_status(schedule_id, status, actor_id="admin"):
        result = base_update_schedule_status(schedule_id, status, actor_id=actor_id)
        if result:
            hardening.record_schedule_consumption_event(result, actor_id=actor_id)
        return result

    db_api.list_packages_v1024b14 = list_packages_v1024b14
    db_api.create_package_v1024b14 = create_package_v1024b14
    db_api.update_package_v1024b14 = update_package_v1024b14
    db_api.get_member_active_package_v1024b14 = get_member_active_package_v1024b14
    db_api.list_member_packages_v1024b14 = list_member_packages_v1024b14
    db_api.get_member_session_ledger_v1024b13 = get_member_session_ledger_v1024b13
    db_api.create_member_schedule = create_member_schedule
    db_api.update_member_schedule_status = update_member_schedule_status

    try:
        from components import schedule_timezone as schedule_module

        base_decide = schedule_module.decide_timezone_aware_reschedule_request

        def decide_timezone_aware_reschedule_request(
            request_id,
            decision,
            *,
            admin_note="",
            actor_id="admin",
        ):
            result = base_decide(
                request_id,
                decision,
                admin_note=admin_note,
                actor_id=actor_id,
            )
            if result and not result.get("error"):
                request = dict(result.get("request") or {})
                if str(request.get("status") or decision).lower() == "approved":
                    try:
                        db = db_api.load_db()
                        original = next(
                            (
                                row
                                for row in db.get("schedules", []) or []
                                if row.get("id") == request.get("schedule_id")
                            ),
                            None,
                        )
                        if original:
                            hardening.record_schedule_consumption_event(
                                original,
                                actor_id=actor_id,
                            )
                    except Exception:
                        pass
            return result

        schedule_module.decide_timezone_aware_reschedule_request = (
            decide_timezone_aware_reschedule_request
        )
    except Exception:
        pass
