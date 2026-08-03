from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Tuple

from components.profile_builder_canonical_sources import (
    source_storage_payload_for_row,
)
from components.profile_builder_module_store import (
    EDITABLE_PROFILE_STATUSES,
    EVENT_TABLE,
    ITEM_TABLE,
    PROFILE_TABLE,
    VALID_MODULES,
    _clean,
    _client,
    _now_iso,
    _rows,
    check_profile_builder_store,
    profile_source_snapshot_columns_ready,
)


def _as_dict(value: object) -> Dict[str, Any]:
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def _legacy_snapshot_payload(
    item: Dict[str, Any],
    reference_label: str,
) -> Dict[str, Any]:
    """Preserve an unresolved legacy snapshot without inventing a source ID.

    Legacy label-only rows can remain ambiguous when duplicate repository names
    exist. Their historical snapshot must survive a module save even though Phase 2
    deliberately refuses to bind them to an uncertain canonical repository item.
    """
    stored = _as_dict(item.get("source_snapshot"))
    original = _as_dict(stored.get("source_original_snapshot")) or stored
    if not original:
        return {}

    overrides = {
        _clean(field): value
        for field, value in dict(item.get("source_admin_overrides") or {}).items()
        if _clean(field) and _clean(value)
    }
    effective = copy.deepcopy(original)
    for field, value in overrides.items():
        if field not in {"image_reference", "instructions"}:
            effective[field] = value
    effective["source_original_snapshot"] = copy.deepcopy(original)
    effective["admin_source_overrides"] = overrides

    image = _as_dict(original.get("image"))
    return {
        "source_type": _clean(
            item.get("source_type") or original.get("source_type")
        ),
        "source_id": _clean(item.get("source_id") or original.get("source_id")),
        "source_label": reference_label
        or _clean(original.get("title") or original.get("supplement_name")),
        "source_snapshot": effective,
        "source_image_url": _clean(image.get("image_url")),
        "source_image_bucket": _clean(image.get("image_bucket")),
        "source_image_path": _clean(image.get("image_path")),
        "source_image_access_type": _clean(image.get("image_access_type")),
    }


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
            source_payload = source_storage_payload_for_row(item_type, item)
            if not source_payload:
                source_payload = _legacy_snapshot_payload(item, reference_label)
            if source_payload:
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
    """Replace one module while preserving canonical source identity and snapshots."""
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
                "Add at least one completed row before saving this module. Existing saved rows were not changed.",
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
