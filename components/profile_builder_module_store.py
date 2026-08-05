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
EDITABLE_PROFILE_STATUSES = {"draft", "active"}
EDIT_SCOPE_ALL = "__all__"
EDIT_SCOPE_UNALLOCATED = "__unallocated__"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def list_profiles_for_editing(
    member_scope: str = EDIT_SCOPE_ALL,
    limit: int = 200,
) -> Tuple[bool, List[dict], str]:
    """Return Draft and Active profiles available for in-place editing.

    ``member_scope`` accepts a member id, ``EDIT_SCOPE_ALL`` or
    ``EDIT_SCOPE_UNALLOCATED``. Archived and replaced profiles are intentionally
    excluded because they are historical records rather than current edit targets.
    """
    if not check_profile_builder_store().get("ok"):
        return False, [], "Profile Builder tables are not ready."

    scope = _clean(member_scope) or EDIT_SCOPE_ALL
    try:
        result = (
            _client()
            .table(PROFILE_TABLE)
            .select(
                "id,profile_name,status,assigned_member_id,"
                "assigned_member_label,updated_at"
            )
            .in_("status", sorted(EDITABLE_PROFILE_STATUSES))
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        profiles = _rows(result)
        if scope == EDIT_SCOPE_UNALLOCATED:
            profiles = [
                row
                for row in profiles
                if not _clean(row.get("assigned_member_id"))
            ]
            message = "Loaded unallocated Draft and Active profiles."
        elif scope != EDIT_SCOPE_ALL:
            profiles = [
                row
                for row in profiles
                if _clean(row.get("assigned_member_id")) == scope
            ]
            message = "Loaded the selected member's Draft and Active profiles."
        else:
            message = "Loaded all editable Draft and Active profiles."
        return True, profiles, message
    except Exception as exc:
        return False, [], f"Could not load editable profiles: {exc}"


def list_profiles_for_repository(
    limit: int = 500,
) -> Tuple[bool, List[dict], str]:
    """Return every retained Meal Profile for repository selection.

    Setup must not hide allocated or historical records. Draft, unallocated
    profiles remain editable; every other status is loaded for read-only review
    and meal-only cloning so member-plan history cannot be overwritten.
    """
    if not check_profile_builder_store().get("ok"):
        return False, [], "Profile Builder tables are not ready."

    try:
        result = (
            _client()
            .table(PROFILE_TABLE)
            .select(
                "id,profile_name,status,assigned_member_id,"
                "assigned_member_label,start_date,updated_at"
            )
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded all retained Meal Profiles."
    except Exception as exc:
        return False, [], f"Could not load the Meal Profile repository: {exc}"


def list_draft_profiles_for_member(
    member_id: str,
    limit: int = 100,
) -> Tuple[bool, List[dict], str]:
    """Backward-compatible Draft-only member filter used by older call sites."""
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return False, [], "Select a member first."
    ok, profiles, message = list_profiles_for_editing(clean_member_id, limit=limit)
    if not ok:
        return ok, profiles, message
    drafts = [
        row
        for row in profiles
        if _clean(row.get("status")).lower() == "draft"
    ]
    return True, drafts, "Loaded member-specific draft profiles."


def _profile_shell_row(
    profile: Dict[str, Any],
    profile_id: str,
    now: str,
) -> Dict[str, Any]:
    status = _clean(profile.get("status"), "draft").lower()
    if status not in EDITABLE_PROFILE_STATUSES:
        status = "draft"
    member_id = _clean(profile.get("assigned_member_id"))
    member_label = _clean(profile.get("assigned_member_label")) if member_id else ""
    return {
        "id": profile_id,
        "profile_name": _clean(profile.get("profile_name")),
        "status": status,
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
        "assigned_member_id": member_id or None,
        "assigned_member_label": member_label,
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
    """Create or update Setup fields without touching recommendation items.

    Existing profiles are updated only when their id still exists. This prevents a
    stale browser session from accidentally recreating a missing profile. Active
    profile allocation is locked to its existing member so an in-place content edit
    cannot silently detach or reassign the live member contract.
    """
    store_status = check_profile_builder_store()
    if not store_status.get("ok"):
        return False, "", store_status.get(
            "message", "Profile Builder tables are not ready."
        )

    profile_name = _clean(profile.get("profile_name"))
    if not profile_name:
        return False, "", "Profile Name is required before saving Setup."

    profile_id = _clean(profile.get("id"))
    is_existing = bool(profile_id)
    profile_id = profile_id or str(uuid.uuid4())
    now = _now_iso()

    try:
        client = _client()
        if is_existing:
            existing_result = (
                client.table(PROFILE_TABLE)
                .select(
                    "id,status,assigned_member_id,assigned_member_label,profile_name"
                )
                .eq("id", profile_id)
                .limit(1)
                .execute()
            )
            existing_rows = _rows(existing_result)
            if not existing_rows:
                return (
                    False,
                    profile_id,
                    "The loaded profile no longer exists. Reload the Profile Builder before saving.",
                )
            existing = existing_rows[0]
            existing_status = _clean(existing.get("status")).lower()
            if existing_status not in EDITABLE_PROFILE_STATUSES:
                return (
                    False,
                    profile_id,
                    f"{existing_status.title() or 'This'} profile is historical and cannot be edited in place. Clone it to create a new Draft.",
                )
            profile["status"] = existing_status
            if existing_status == "active":
                existing_member_id = _clean(existing.get("assigned_member_id"))
                incoming_member_id = _clean(profile.get("assigned_member_id"))
                if incoming_member_id != existing_member_id:
                    return (
                        False,
                        profile_id,
                        "Active profile allocation is protected. Content can be edited, but its member assignment cannot be changed here.",
                    )
                profile["assigned_member_id"] = existing_member_id
                profile["assigned_member_label"] = _clean(
                    existing.get("assigned_member_label")
                )
        else:
            profile["status"] = "draft"

        row = _profile_shell_row(profile, profile_id, now)
        client.table(PROFILE_TABLE).upsert(row, on_conflict="id").execute()
        client.table(EVENT_TABLE).insert(
            {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "event_type": "profile_setup_saved",
                "event_note": (
                    f"Profile Setup saved in place with status {row.get('status')}. "
                    "Meal, Exercise and Supplement rows were not changed."
                ),
                "created_by_user_id": row.get("created_by_user_id"),
                "created_by_email": row.get("created_by_email"),
                "created_at": now,
            }
        ).execute()
        assignment_text = (
            f" for {row.get('assigned_member_label')}"
            if row.get("assigned_member_id")
            else " as unallocated"
        )
        action = "updated" if is_existing else "created"
        return (
            True,
            profile_id,
            f"Profile Setup {action} successfully{assignment_text}. Recommendation modules were not changed.",
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
    """Replace one module for a loaded Draft or Active profile."""
    clean_profile_id = _clean(profile_id)
    clean_member_id = _clean(member_id)
    if item_type not in VALID_MODULES:
        return False, "Unsupported Profile Builder module."
    if not clean_profile_id:
        return False, "Select and load an editable profile first."
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
        profile_status = _clean(profile.get("status")).lower()
        if profile_status not in EDITABLE_PROFILE_STATUSES:
            return (
                False,
                f"{profile_status.title() or 'This'} profile is historical and cannot be edited in place. Clone it to create a new Draft.",
            )
        stored_member_id = _clean(profile.get("assigned_member_id"))
        if clean_member_id and stored_member_id != clean_member_id:
            return False, "The loaded profile's member assignment changed. Reload before saving."

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
                    f"Saved {len(rows)} {item_type} row(s) in place on the "
                    f"{profile_status} profile with {snapshot_count} source snapshot(s). "
                    "Other modules and member allocation were not changed."
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
        return (
            True,
            f"{label} saved successfully with {len(rows)} row(s) on the same {profile_status.title()} profile.",
        )
    except Exception as exc:
        return False, f"Could not save {item_type} module: {exc}"
