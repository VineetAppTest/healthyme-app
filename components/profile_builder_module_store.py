"""Module-scoped persistence for the HealthyMe Recommendation Profile Builder.

Setup saves only profile-level fields. Meals, Exercise and Supplements replace
only their own item rows so one module can never erase another module.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List, Tuple

from components.recommendation_profile_store import (
    EVENT_TABLE,
    ITEM_TABLE,
    PROFILE_TABLE,
    _clean,
    _client,
    _none_if_blank,
    _optional_uuid,
    _rows,
    check_profile_builder_store,
    profile_source_snapshot_columns_ready,
)

VALID_MODULES = {"meal", "exercise", "supplement"}


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def list_draft_profiles_for_member(
    member_id: str,
    limit: int = 100,
) -> Tuple[bool, List[dict], str]:
    """Return editable draft profiles assigned to one selected member."""
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return False, [], "Select a member first."
    if not check_profile_builder_store().get("ok"):
        return False, [], "Profile Builder tables are not ready."
    try:
        result = (
            _client()
            .table(PROFILE_TABLE)
            .select(
                "id,profile_name,status,assigned_member_id,"
                "assigned_member_label,updated_at"
            )
            .eq("status", "draft")
            .eq("assigned_member_id", clean_member_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded member-specific draft profiles."
    except Exception as exc:
        return False, [], f"Could not load member-specific draft profiles: {exc}"


def _profile_shell_row(
    profile: Dict[str, Any],
    profile_id: str,
    now: str,
) -> Dict[str, Any]:
    return {
        "id": profile_id,
        "profile_name": _clean(profile.get("profile_name")),
        "status": "draft",
        "region": _clean(profile.get("region")),
        "age_band": _clean(profile.get("age_band")),
        "diet_type": _clean(profile.get("diet_type")),
        "health_concerns": list(profile.get("health_concerns") or []),
        "profile_note": _clean(profile.get("profile_note")),
        "change_note": _clean(profile.get("change_note")),
        "cycle_rule": _clean(
            profile.get("cycle_rule"),
            "Weekly cyclical until replaced or stopped",
        ),
        "assigned_member_id": _clean(profile.get("assigned_member_id")),
        "assigned_member_label": _clean(profile.get("assigned_member_label")),
        "start_date": _none_if_blank(profile.get("start_date")),
        "clone_source_profile_id": _optional_uuid(
            profile.get("clone_source_profile_id")
        ),
        "clone_source_label": _clean(profile.get("clone_source_label")),
        "updated_at": now,
        "created_by_user_id": _clean(profile.get("created_by_user_id")),
        "created_by_email": _clean(profile.get("created_by_email")),
    }


def save_profile_shell(profile: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Create/update Setup fields without touching any recommendation item."""
    status = check_profile_builder_store()
    if not status.get("ok"):
        return False, "", status.get(
            "message", "Profile Builder tables are not ready."
        )

    profile_name = _clean(profile.get("profile_name"))
    member_id = _clean(profile.get("assigned_member_id"))
    if not profile_name:
        return False, "", "Profile Name is required before saving Setup."
    if not member_id:
        return False, "", "Member Assignment is required before saving Setup."

    profile_id = _clean(profile.get("id")) or str(uuid.uuid4())
    now = _now_iso()
    row = _profile_shell_row(profile, profile_id, now)
    try:
        client = _client()
        client.table(PROFILE_TABLE).upsert(row, on_conflict="id").execute()
        client.table(EVENT_TABLE).insert(
            {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "event_type": "profile_setup_saved",
                "event_note": (
                    "Profile Setup saved. Meal, Exercise and Supplement rows "
                    "were not changed."
                ),
                "created_by_user_id": row.get("created_by_user_id"),
                "created_by_email": row.get("created_by_email"),
                "created_at": now,
            }
        ).execute()
        return (
            True,
            profile_id,
            "Profile Setup saved successfully. Recommendation modules were not changed.",
        )
    except Exception as exc:
        return False, profile_id, f"Could not save Profile Setup: {exc}"


def _source_payload(item_type: str, reference_label: str) -> Dict[str, Any]:
    try:
        from components.profile_builder_source_contract import source_storage_payload

        source_type = "recipe" if item_type == "meal" else item_type
        return dict(source_storage_payload(source_type, reference_label) or {})
    except Exception:
        return {}


def _normalise_item_rows(
    profile_id: str,
    item_type: str,
    items: List[Dict[str, Any]],
    now: str,
) -> Tuple[List[dict], int]:
    snapshot_ready = profile_source_snapshot_columns_ready()
    rows: List[dict] = []
    snapshot_count = 0

    for item in items:
        if _clean(item.get("item_type")) != item_type:
            continue
        try:
            day_number = int(item.get("day_number") or 0)
            item_order = int(item.get("item_order") or 1)
        except (TypeError, ValueError):
            continue
        slot_name = _clean(item.get("slot_name"))
        reference_label = _clean(item.get("reference_label"))
        if reference_label.startswith("-- Select"):
            reference_label = ""
        instruction = _clean(item.get("instruction"))
        portion = _clean(item.get("portion"))
        scheduled_time = _clean(item.get("scheduled_time"))
        intensity = _clean(item.get("intensity"))
        dosage_frequency = _clean(item.get("dosage_frequency"))
        if not (1 <= day_number <= 7) or not slot_name:
            continue
        if not any(
            [
                reference_label,
                portion,
                instruction,
                scheduled_time,
                intensity,
                dosage_frequency,
            ]
        ):
            continue

        row: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "item_type": item_type,
            "day_number": day_number,
            "slot_name": slot_name,
            "item_order": item_order,
            "reference_label": reference_label,
            "portion": portion,
            "instruction": instruction,
            "scheduled_time": scheduled_time,
            "intensity": intensity,
            "dosage_frequency": dosage_frequency,
            "updated_at": now,
        }
        if snapshot_ready and reference_label:
            source_payload = _source_payload(item_type, reference_label)
            if source_payload:
                overrides = dict(item.get("source_admin_overrides") or {})
                if overrides:
                    snapshot = dict(source_payload.get("source_snapshot") or {})
                    snapshot["admin_source_overrides"] = overrides
                    source_payload["source_snapshot"] = snapshot
                row.update(source_payload)
                snapshot_count += 1
        rows.append(row)
    return rows, snapshot_count


def save_profile_module(
    profile_id: str,
    member_id: str,
    item_type: str,
    items: List[Dict[str, Any]],
    *,
    created_by_user_id: str = "",
    created_by_email: str = "",
) -> Tuple[bool, str]:
    """Replace only one module for a member-owned draft profile."""
    clean_profile_id = _clean(profile_id)
    clean_member_id = _clean(member_id)
    if item_type not in VALID_MODULES:
        return False, "Unsupported Profile Builder module."
    if not clean_profile_id or not clean_member_id:
        return False, "Select and load a member-specific Draft Profile first."
    if not check_profile_builder_store().get("ok"):
        return False, "Profile Builder tables are not ready."

    try:
        client = _client()
        profile_result = (
            client.table(PROFILE_TABLE)
            .select("id,status,assigned_member_id,profile_name")
            .eq("id", clean_profile_id)
            .limit(1)
            .execute()
        )
        profiles = _rows(profile_result)
        if not profiles:
            return False, "Selected profile was not found."
        profile = profiles[0]
        if _clean(profile.get("status")).lower() != "draft":
            return False, "Only Draft profiles can be edited."
        if _clean(profile.get("assigned_member_id")) != clean_member_id:
            return False, "Selected profile does not belong to the selected member."

        now = _now_iso()
        rows, snapshot_count = _normalise_item_rows(
            clean_profile_id,
            item_type,
            items,
            now,
        )
        if not rows:
            return (
                False,
                "Add at least one completed row before saving this module. "
                "Existing saved rows were not changed.",
            )

        (
            client.table(ITEM_TABLE)
            .delete()
            .eq("profile_id", clean_profile_id)
            .eq("item_type", item_type)
            .execute()
        )
        client.table(ITEM_TABLE).insert(rows).execute()
        client.table(PROFILE_TABLE).update({"updated_at": now}).eq(
            "id", clean_profile_id
        ).execute()
        client.table(EVENT_TABLE).insert(
            {
                "id": str(uuid.uuid4()),
                "profile_id": clean_profile_id,
                "event_type": f"{item_type}_module_saved",
                "event_note": (
                    f"Saved {len(rows)} {item_type} row(s) with "
                    f"{snapshot_count} source snapshot(s). Other modules were not changed."
                ),
                "created_by_user_id": _clean(created_by_user_id),
                "created_by_email": _clean(created_by_email),
                "created_at": now,
            }
        ).execute()
        label = {
            "meal": "Meals",
            "exercise": "Exercise",
            "supplement": "Supplements",
        }[item_type]
        return True, f"{label} saved successfully with {len(rows)} row(s)."
    except Exception as exc:
        return False, f"Could not save {item_type} module: {exc}"
