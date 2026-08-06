from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from components import member_allocation_notifications as notifications


ROOT = Path(__file__).resolve().parents[1]


def _delivery(status: str = "sent") -> dict[str, str]:
    return {
        "status": status,
        "provider": "Resend",
        "provider_id": "email-1",
        "error": "",
        "attempted_at": "2026-08-05T18:00:00+00:00",
    }


def _state(*, supplement_placeholder: bool = False) -> dict:
    rows = []
    if supplement_placeholder:
        rows.append(
            {
                "kind": "supplement_regimen_updated",
                "user_id": "member-1",
                "message": "Legacy placeholder",
            }
        )
    return {
        "users": [
            {
                "id": "member-1",
                "name": "Test Member",
                "email": "member@example.com",
                "role": "member",
                "is_active": True,
            }
        ],
        "messages": [],
        "notifications": rows,
        "email_delivery_logs": [],
    }


def test_admin_profile_filters_and_setup_retain_all_profiles() -> None:
    setup = (ROOT / "components/member_plan_builder_setup.py").read_text(encoding="utf-8")
    meals = (ROOT / "components/member_plan_builder_meals_compact.py").read_text(encoding="utf-8")
    store = (ROOT / "components/profile_builder_module_store.py").read_text(encoding="utf-8")
    view = (ROOT / "components/member_plan_builder_view_compact.py").read_text(encoding="utf-8")
    allocation = (ROOT / "components/member_plan_builder_allocation_common.py").read_text(encoding="utf-8")

    assert "list_profiles_for_repository()" in setup
    assert "list_profiles_for_repository()" in meals
    assert '"Health Concerns"' in meals
    assert "def _profile_is_editable" in meals
    assert "This allocated or historical Meal Profile is visible for review only." in meals
    assert 'st.session_state[_MEAL_PROFILE_SELECTOR] = SELECT_PROFILE' in meals
    assert 'clean(row.get("status")).lower() == "draft"' not in setup
    assert '"This allocated or historical Meal Profile is retained read-only.' in setup
    assert "def list_profiles_for_repository(" in store
    assert "health_concerns" in store[store.index("def list_profiles_for_repository(") :]
    assert '.in_("status"' not in store[store.index("def list_profiles_for_repository(") :]
    assert 'profiles = [row for row in profiles if clean(row.get("assigned_member_id"))]' not in view
    assert '"Meal Profile"' in view
    assert '"All Meal Profiles"' in view
    assert '"Member"' in allocation
    assert '"Member Plan"' not in allocation


def test_exercise_more_details_uses_auto_height_grid_without_inner_border_overlap() -> None:
    source = (ROOT / "components/member_plan_builder_exercise.py").read_text(encoding="utf-8")
    assert "height:auto!important" in source
    assert "max-height:none!important" in source
    assert "position:static!important" in source
    assert "grid-template-columns:repeat(auto-fit,minmax(185px,1fr))" in source
    assert "border-top:1px solid #F0DFC0!important" in source
    assert "border:0!important" in source


def test_exercise_allocation_email_is_idempotent_across_duplicate_save_ids() -> None:
    state = _state()
    first = {
        "id": "exercise-1",
        "member_id": "member-1",
        "source_id": "walk",
        "exercise_name": "Brisk Walk",
        "start_date": "2026-08-05",
        "end_date": "2026-08-11",
        "instructions": "Walk briskly",
        "notes": "",
        "status": "active",
    }
    duplicate = {**first, "id": "exercise-2"}

    with (
        patch.object(notifications, "load_state", return_value=state),
        patch.object(notifications, "save_state") as save_state,
        patch("components.member_email._send_resend_email", return_value=_delivery()) as send,
    ):
        result_one = notifications._queue_allocated_delivery(
            "exercise", first, actor_id="admin-1"
        )
        result_two = notifications._queue_allocated_delivery(
            "exercise", duplicate, actor_id="admin-1"
        )

    assert result_one["status"] == "sent"
    assert result_two["dedupe_key"] == result_one["dedupe_key"]
    assert send.call_count == 1
    assert save_state.call_count == 2
    assert len(state["messages"]) == 1
    assert len(state["notifications"]) == 1
    assert len(state["email_delivery_logs"]) == 1


def test_supplement_allocation_reuses_core_placeholder_notification() -> None:
    state = _state(supplement_placeholder=True)
    saved = {
        "id": "supplement-1",
        "member_id": "member-1",
        "member_email": "member@example.com",
        "source_id": "magnesium",
        "supplement_name": "Magnesium",
        "dosage": "400 mg",
        "frequency": "Once",
        "timing": "Evening",
        "start_date": "2026-08-05",
        "end_date": "",
        "instructions": "After dinner",
        "status": "Active",
    }

    with (
        patch.object(notifications, "load_state", return_value=state),
        patch.object(notifications, "save_state"),
        patch("components.member_email._send_resend_email", return_value=_delivery()),
    ):
        result = notifications._queue_allocated_delivery(
            "supplement", saved, actor_id="admin-1"
        )

    assert result["status"] == "sent"
    assert len(state["messages"]) == 1
    assert len(state["notifications"]) == 1
    assert state["notifications"][0]["kind"] == "supplement_allocated"
    assert state["notifications"][0]["email_delivery_status"] == "sent"


def test_meal_plan_publish_queues_one_email_and_in_app_event() -> None:
    state = _state()
    plan = {
        "id": "plan-copy-1",
        "profile_name": "Balanced Plan",
        "assigned_member_id": "member-1",
        "start_date": "2026-08-05",
    }
    duplicate_plan = {**plan, "id": "plan-copy-2"}
    meals = [
        {
            "item_type": "meal",
            "day_number": 1,
            "slot_name": "Lunch",
            "item_order": 1,
            "reference_label": "Moong Chilla",
            "portion": "2",
            "instruction": "Serve warm",
        }
    ]

    with (
        patch.object(notifications, "load_state", return_value=state),
        patch.object(notifications, "save_state") as save_state,
        patch("components.member_email._send_resend_email", return_value=_delivery()) as send,
    ):
        first = notifications.queue_meal_plan_allocation(
            plan,
            source_profile_id="source-profile",
            meal_rows=meals,
            actor_id="admin-1",
        )
        duplicate = notifications.queue_meal_plan_allocation(
            duplicate_plan,
            source_profile_id="source-profile",
            meal_rows=meals,
            actor_id="admin-1",
        )

    assert first["status"] == "sent"
    assert duplicate["dedupe_key"] == first["dedupe_key"]
    assert send.call_count == 1
    assert save_state.call_count == 2
    assert len(state["messages"]) == 1
    assert len(state["notifications"]) == 1
    assert state["notifications"][0]["kind"] == "meal_plan_allocated"
    assert state["messages"][0]["subject"] == "Meal added"
    assert 'Please review it in "My Weekly Plan".' in state["messages"][0]["message"]
    assert "Benefits:" in state["messages"][0]["message"]
    assert "Member instructions:" in state["messages"][0]["message"]
    assert 'Please review it in "My Weekly Plan".' in state["notifications"][0]["message"]
