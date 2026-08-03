from __future__ import annotations

import copy
from pathlib import Path

import pytest

from components import exercise_member_allocation as allocation


ACTIVE_SOURCE = {
    "id": "12",
    "source_id": "12",
    "title": "Chair Squat",
    "status": "active",
    "category": "Strength",
    "difficulty": "Beginner",
    "duration_or_reps": "3 x 10",
    "instructions": "Keep the knees aligned.",
    "content_version": 4,
}
INACTIVE_SOURCE = {
    **ACTIVE_SOURCE,
    "id": "13",
    "source_id": "13",
    "title": "Legacy Stretch",
    "status": "inactive",
}


@pytest.fixture()
def state(monkeypatch):
    db = {
        "member_exercise_allocations": {},
        "exercise_member_allocation_audit": [],
    }

    monkeypatch.setattr(allocation, "load_state", lambda: copy.deepcopy(db))

    def save(next_state):
        db.clear()
        db.update(copy.deepcopy(next_state))

    monkeypatch.setattr(allocation, "save_state", save)
    monkeypatch.setattr(
        allocation,
        "list_exercise_repository",
        lambda active_only=True: (
            [copy.deepcopy(ACTIVE_SOURCE)]
            if active_only
            else [copy.deepcopy(ACTIVE_SOURCE), copy.deepcopy(INACTIVE_SOURCE)]
        ),
    )
    return db


def test_new_allocation_uses_active_canonical_source_and_snapshot(state):
    saved = allocation.save_exercise_member_allocation(
        member_id="member-1",
        source_id="12",
        start_date="2026-08-04",
        end_date="2026-08-10",
        instructions="Do this after breakfast.",
        notes="Low-impact plan.",
        actor_id="admin-1",
    )

    assert saved["source_type"] == "exercise_repository"
    assert saved["source_id"] == "12"
    assert saved["exercise_id"] == "12"
    assert saved["exercise_name"] == "Chair Squat"
    assert saved["source_snapshot"]["title"] == "Chair Squat"
    assert len(state["member_exercise_allocations"]["member-1"]) == 1
    assert state["exercise_member_allocation_audit"][-1]["action"] == "create"


def test_inactive_source_cannot_be_newly_allocated(state):
    with pytest.raises(ValueError, match="Only active canonical"):
        allocation.save_exercise_member_allocation(
            member_id="member-1",
            source_id="13",
        )


def test_existing_allocation_identity_is_preserved_on_update(state):
    state["member_exercise_allocations"]["member-1"] = [
        {
            "id": "legacy-allocation-7",
            "member_id": "member-1",
            "exercise_id": "12",
            "exercise_name": "Chair Squat",
            "status": "active",
            "source_snapshot": {"source_id": "12", "title": "Chair Squat"},
        }
    ]

    saved = allocation.save_exercise_member_allocation(
        member_id="member-1",
        source_id="12",
        allocation_id="legacy-allocation-7",
        start_date="2026-08-05",
        end_date="2026-08-12",
        instructions="Updated",
        status="active",
    )

    assert saved["id"] == "legacy-allocation-7"
    assert len(state["member_exercise_allocations"]["member-1"]) == 1
    assert state["member_exercise_allocations"]["member-1"][0]["id"] == (
        "legacy-allocation-7"
    )


def test_existing_source_identity_cannot_be_changed(state):
    state["member_exercise_allocations"]["member-1"] = [
        {
            "id": "allocation-1",
            "member_id": "member-1",
            "exercise_id": "12",
            "status": "active",
        }
    ]
    with pytest.raises(ValueError, match="source identity cannot be changed"):
        allocation.save_exercise_member_allocation(
            member_id="member-1",
            source_id="13",
            allocation_id="allocation-1",
        )


def test_stop_retains_row_and_history(state):
    state["member_exercise_allocations"]["member-1"] = [
        {
            "id": "allocation-1",
            "member_id": "member-1",
            "exercise_id": "12",
            "status": "active",
            "start_date": "2026-08-04",
        }
    ]

    stopped = allocation.stop_exercise_member_allocation(
        member_id="member-1",
        allocation_id="allocation-1",
        stop_date="2026-08-06",
        stop_reason="Pain reported.",
    )

    assert stopped["id"] == "allocation-1"
    assert stopped["status"] == "stopped"
    assert stopped["end_date"] == "2026-08-06"
    assert len(state["member_exercise_allocations"]["member-1"]) == 1


def test_historical_inactive_source_remains_readable(state):
    state["member_exercise_allocations"]["member-1"] = [
        {
            "id": "historical-13",
            "member_id": "member-1",
            "exercise_id": "13",
            "exercise_name": "Legacy Stretch",
            "status": "stopped",
        }
    ]

    rows = allocation.list_member_exercise_allocations(
        "member-1", include_stopped=True
    )

    assert rows[0]["id"] == "historical-13"
    assert rows[0]["source_id"] == "13"
    assert rows[0]["status"] == "stopped"


def test_end_date_cannot_precede_start_date(state):
    with pytest.raises(ValueError, match="End date"):
        allocation.save_exercise_member_allocation(
            member_id="member-1",
            source_id="12",
            start_date="2026-08-10",
            end_date="2026-08-04",
        )


def test_page_boundary_is_exercise_only():
    page = Path("pages/42_Admin_Exercise_Member_Allocation.py").read_text(
        encoding="utf-8"
    )
    assert "member_exercise_allocations" in page
    assert "save_exercise_member_allocation" in page
    assert "recommendation_shares" not in page
    assert "member_supplements" not in page
    assert "save_unified_recommendation_share" not in page
    assert "_clear_add_form(member_id)" in page
    assert "st.session_state.pop" in page
