from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, List, Tuple

from components.profile_builder_repository_contract import (
    CONTRACT_VERSION,
    list_profile_builder_repository_sources,
    profile_builder_repository_source_by_id,
)
from components.recommendation_profile_store import (
    DEFAULT_SOURCES,
    MASTER_TABLE,
    SOURCE_BACKED_GROUPS,
    _client,
    _rows,
    check_profile_builder_store,
    profile_source_snapshot_columns_ready,
)


SUPPORTED_KINDS = ("recipe", "exercise", "supplement")


def _clean(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _kind(value: str) -> str:
    clean_kind = _clean(value).lower()
    if clean_kind in {"meal", "recipe"}:
        return "recipe"
    if clean_kind in {"exercise", "workout"}:
        return "exercise"
    if clean_kind == "supplement":
        return "supplement"
    raise ValueError("kind must be recipe, exercise or supplement")


def _as_dict(value: object) -> Dict[str, Any]:
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def _snapshot_title(snapshot: Dict[str, Any], fallback: str = "") -> str:
    return _clean(
        snapshot.get("title")
        or snapshot.get("supplement_name")
        or fallback
    )


def _base_saved_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = _as_dict(row.get("source_snapshot"))
    original = _as_dict(snapshot.get("source_original_snapshot"))
    return original or snapshot


def _saved_option_id(
    kind: str,
    label: str,
    source_id: str = "",
    source_type: str = "",
) -> str:
    digest = hashlib.sha1(
        f"{kind}|{source_type}|{source_id}|{label}".encode("utf-8")
    ).hexdigest()[:12]
    prefix = "saved" if source_id else "legacy"
    return f"{prefix}:{kind}:{digest}"


def _saved_option(kind: str, row: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = _base_saved_snapshot(row)
    label = _clean(row.get("reference_label")) or _snapshot_title(snapshot)
    source_id = _clean(row.get("source_id") or snapshot.get("source_id"))
    source_type = _clean(row.get("source_type") or snapshot.get("source_type"))
    status = _clean(snapshot.get("status")) or "historical"
    return {
        "contract_version": _clean(
            snapshot.get("contract_version")
            or row.get("source_contract_version")
        ),
        "kind": kind,
        "source_type": source_type,
        "source_id": source_id,
        "identity_key": (
            f"{source_type}:{source_id}" if source_type and source_id else ""
        ),
        "option_id": _saved_option_id(
            kind,
            label,
            source_id,
            source_type,
        ),
        "display_label": label or "Legacy saved source",
        "status": status,
        "selectable": False,
        "legacy": not bool(source_id),
        "saved": True,
        "snapshot": copy.deepcopy(snapshot),
    }


def _option_from_source(source: Dict[str, Any]) -> Dict[str, Any]:
    option = copy.deepcopy(source)
    option["option_id"] = _clean(source.get("source_id"))
    option["legacy"] = False
    option["saved"] = False
    return option


def load_profile_builder_repository_options() -> Dict[str, List[Dict[str, Any]]]:
    """Load active canonical repository options for the live Builder."""
    return {
        kind: [
            _option_from_source(source)
            for source in list_profile_builder_repository_sources(
                kind,
                active_only=True,
            )
        ]
        for kind in SUPPORTED_KINDS
    }


def _load_repository_options_safely() -> Tuple[
    Dict[str, List[Dict[str, Any]]],
    List[str],
]:
    options: Dict[str, List[Dict[str, Any]]] = {}
    messages: List[str] = []
    for kind in SUPPORTED_KINDS:
        try:
            options[kind] = [
                _option_from_source(source)
                for source in list_profile_builder_repository_sources(
                    kind,
                    active_only=True,
                )
            ]
            messages.append(f"{kind}={len(options[kind])}")
        except Exception as exc:
            # Repository-backed groups must never fall back to mock source values.
            options[kind] = []
            messages.append(f"{kind}=unavailable ({exc})")
    return options, messages


def load_profile_builder_phase2_sources() -> Tuple[
    Dict[str, List[str]],
    Dict[str, List[Dict[str, Any]]],
    str,
]:
    """Load non-repository master data plus canonical repository options.

    Recipe, Exercise and Supplement come only from the Phase 1 canonical contract.
    A repository read failure leaves that source group empty instead of exposing mock
    selections that could be saved as real recommendation data.
    """
    sources = {key: list(values) for key, values in DEFAULT_SOURCES.items()}
    repository_options, repository_messages = _load_repository_options_safely()
    for kind, options in repository_options.items():
        sources[kind] = [
            _clean(option.get("display_label"))
            for option in options
            if _clean(option.get("display_label"))
        ]

    messages = [
        "Canonical repository reads: "
        + ", ".join(repository_messages)
        + "."
    ]

    store_ready = check_profile_builder_store().get("ok")
    if store_ready:
        try:
            result = (
                _client()
                .table(MASTER_TABLE)
                .select("option_group,option_value,sort_order,is_active")
                .eq("is_active", True)
                .order("option_group")
                .order("sort_order")
                .execute()
            )
            grouped: Dict[str, List[str]] = {}
            for row in _rows(result):
                group = _clean(row.get("option_group"))
                value = _clean(row.get("option_value"))
                if group and value:
                    grouped.setdefault(group, []).append(value)
            for group, values in grouped.items():
                if group in SOURCE_BACKED_GROUPS or not values:
                    continue
                sources[group] = values
            messages.append("Profile Builder master options loaded.")
        except Exception as exc:
            messages.append(
                f"Fallback master options retained because master data could not be loaded: {exc}"
            )
    else:
        messages.append("Fallback non-repository master options retained.")

    if store_ready:
        messages.append(
            "Snapshot schema ready."
            if profile_source_snapshot_columns_ready()
            else "Source snapshot columns are unavailable; canonical source details remain read-only until the schema is available."
        )
    else:
        messages.append("Profile Builder store is not ready.")
    return sources, repository_options, " ".join(messages)


def _matches_by_label(
    kind: str,
    label: str,
    *,
    active_only: bool,
) -> List[Dict[str, Any]]:
    clean_label = _clean(label).casefold()
    if not clean_label:
        return []
    return [
        source
        for source in list_profile_builder_repository_sources(
            kind,
            active_only=active_only,
        )
        if _clean(source.get("display_label")).casefold() == clean_label
    ]


def prepare_row_source(kind: str, row: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare canonical identity without rewriting an existing saved snapshot."""
    source_kind = _kind(kind)
    row.setdefault("source_id", "")
    row.setdefault("source_type", "")
    row.setdefault("source_snapshot", {})
    row.setdefault("source_contract_version", "")
    row.setdefault("source_option_id", "")

    saved_snapshot = _base_saved_snapshot(row)
    source_id = _clean(
        row.get("source_id")
        or saved_snapshot.get("source_id")
    )
    source_type = _clean(
        row.get("source_type")
        or saved_snapshot.get("source_type")
    )
    label = _clean(row.get("reference_label")) or _snapshot_title(saved_snapshot)

    if source_id:
        resolved = None
        if not source_type or not saved_snapshot:
            resolved = profile_builder_repository_source_by_id(
                source_kind,
                source_id,
                active_only=False,
            )
        if resolved:
            source_type = source_type or _clean(resolved.get("source_type"))
            if not saved_snapshot:
                saved_snapshot = copy.deepcopy(resolved.get("snapshot") or {})
                row["source_snapshot"] = copy.deepcopy(saved_snapshot)
            label = label or _clean(resolved.get("display_label"))

        row["source_id"] = source_id
        row["source_type"] = source_type
        row["source_contract_version"] = _clean(
            saved_snapshot.get("contract_version")
            or row.get("source_contract_version")
        )
        if not row.get("reference_label"):
            row["reference_label"] = label
        if not row.get("source_option_id"):
            if saved_snapshot or label:
                row["source_option_id"] = _saved_option_id(
                    source_kind,
                    label,
                    source_id,
                    source_type,
                )
            else:
                row["source_option_id"] = source_id
        return row

    matches = _matches_by_label(source_kind, label, active_only=False)
    if len(matches) == 1:
        match = matches[0]
        row["source_id"] = _clean(match.get("source_id"))
        row["source_type"] = _clean(match.get("source_type"))
        row["source_contract_version"] = _clean(
            match.get("contract_version") or CONTRACT_VERSION
        )
        if not row.get("source_snapshot"):
            row["source_snapshot"] = copy.deepcopy(match.get("snapshot") or {})
        if not row.get("reference_label"):
            row["reference_label"] = _clean(match.get("display_label"))

    if (
        not row.get("source_option_id")
        and (
            _clean(row.get("reference_label"))
            or _base_saved_snapshot(row)
        )
    ):
        row["source_option_id"] = _saved_option_id(
            source_kind,
            _clean(row.get("reference_label")),
            _clean(row.get("source_id")),
            _clean(row.get("source_type")),
        )
    return row


def source_options_for_row(
    kind: str,
    row: Dict[str, Any],
    active_options: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return active options plus the row's immutable saved source option."""
    source_kind = _kind(kind)
    prepare_row_source(source_kind, row)
    options = [copy.deepcopy(option) for option in active_options]
    active_ids = {
        _clean(option.get("source_id"))
        for option in options
        if _clean(option.get("source_id"))
    }
    source_id = _clean(row.get("source_id"))
    current_option_id = _clean(row.get("source_option_id"))
    has_saved_value = bool(
        _clean(row.get("reference_label"))
        or _base_saved_snapshot(row)
    )

    if current_option_id.startswith(("saved:", "legacy:")) and has_saved_value:
        options.append(_saved_option(source_kind, row))
    elif source_id and source_id not in active_ids:
        options.append(_saved_option(source_kind, row))
    elif not source_id and has_saved_value:
        options.append(_saved_option(source_kind, row))

    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for option in options:
        option_id = _clean(option.get("option_id"))
        if not option_id or option_id in seen:
            continue
        seen.add(option_id)
        deduped.append(option)
    return deduped


def current_source_option_id(
    kind: str,
    row: Dict[str, Any],
    options: List[Dict[str, Any]],
) -> str:
    prepare_row_source(kind, row)
    option_ids = {
        _clean(option.get("option_id"))
        for option in options
    }
    current = _clean(row.get("source_option_id"))
    if current and current in option_ids:
        return current
    source_id = _clean(row.get("source_id"))
    if source_id and source_id in option_ids:
        row["source_option_id"] = source_id
        return source_id
    for option in options:
        if option.get("saved"):
            option_id = _clean(option.get("option_id"))
            row["source_option_id"] = option_id
            return option_id
    return ""


def source_option_labels(
    options: List[Dict[str, Any]],
) -> Dict[str, str]:
    counts: Dict[str, int] = {}
    for option in options:
        if option.get("saved"):
            continue
        label_key = _clean(option.get("display_label")).casefold()
        if label_key:
            counts[label_key] = counts.get(label_key, 0) + 1

    labels: Dict[str, str] = {}
    for option in options:
        option_id = _clean(option.get("option_id"))
        label = _clean(option.get("display_label")) or "Unnamed source"
        if option.get("legacy"):
            label = f"{label} · Legacy saved source"
        elif option.get("saved"):
            if _clean(option.get("status")).lower() == "inactive":
                label = f"{label} · Inactive saved source"
            else:
                label = f"{label} · Saved profile source"
        elif counts.get(label.casefold(), 0) > 1:
            label = f"{label} · ID {_clean(option.get('source_id'))}"
        labels[option_id] = label
    return labels


def apply_source_selection(
    kind: str,
    row: Dict[str, Any],
    selected_option_id: str,
    options: List[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    """Apply an ID-based selection without rewriting an unchanged saved source."""
    source_kind = _kind(kind)
    prepare_row_source(source_kind, row)
    selected_id = _clean(selected_option_id)
    previous_option_id = _clean(row.get("source_option_id"))
    previous_id = _clean(row.get("source_id"))
    previous_label = _clean(row.get("reference_label"))

    if selected_id == previous_option_id:
        return False, source_snapshot_for_row(source_kind, row)

    if not selected_id:
        changed = bool(previous_id or previous_label or previous_option_id)
        row.update(
            {
                "source_id": "",
                "source_type": "",
                "source_contract_version": "",
                "source_option_id": "",
                "source_snapshot": {},
                "reference_label": "",
                "source_admin_overrides": {},
            }
        )
        return changed, {}

    option = next(
        (
            candidate
            for candidate in options
            if _clean(candidate.get("option_id")) == selected_id
        ),
        None,
    )
    if not option:
        return False, source_snapshot_for_row(source_kind, row)

    if option.get("saved"):
        row["source_option_id"] = selected_id
        return False, copy.deepcopy(option.get("snapshot") or {})

    source_id = _clean(option.get("source_id"))
    label = _clean(option.get("display_label"))
    changed = (
        selected_id != previous_option_id
        or source_id != previous_id
        or label != previous_label
    )
    row.update(
        {
            "source_id": source_id,
            "source_type": _clean(option.get("source_type")),
            "source_contract_version": _clean(
                option.get("contract_version") or CONTRACT_VERSION
            ),
            "source_option_id": selected_id,
            "source_snapshot": copy.deepcopy(option.get("snapshot") or {}),
            "reference_label": label,
        }
    )
    if changed:
        row["source_admin_overrides"] = {}
    return changed, copy.deepcopy(row.get("source_snapshot") or {})


def source_snapshot_for_row(kind: str, row: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve source details by ID, preferring the row's saved historical snapshot."""
    source_kind = _kind(kind)
    prepare_row_source(source_kind, row)
    saved = _base_saved_snapshot(row)
    if saved:
        return copy.deepcopy(saved)

    source_id = _clean(row.get("source_id"))
    if source_id:
        resolved = profile_builder_repository_source_by_id(
            source_kind,
            source_id,
            active_only=False,
        )
        if resolved:
            return copy.deepcopy(resolved.get("snapshot") or {})

    label = _clean(row.get("reference_label"))
    matches = _matches_by_label(source_kind, label, active_only=False)
    if len(matches) == 1:
        return copy.deepcopy(matches[0].get("snapshot") or {})
    return {}


def source_snapshot_for_legacy_label(
    kind: str,
    label: str,
) -> Dict[str, Any]:
    """Compatibility lookup for older non-row call sites.

    A duplicate visible label is intentionally treated as ambiguous rather than
    silently binding to the wrong repository item.
    """
    source_kind = _kind(kind)
    matches = _matches_by_label(source_kind, label, active_only=False)
    if len(matches) == 1:
        return copy.deepcopy(matches[0].get("snapshot") or {})
    return {}


def source_storage_payload_for_row(
    kind: str,
    row: Dict[str, Any],
) -> Dict[str, Any]:
    """Create the existing database source payload from the row's canonical identity."""
    source_kind = _kind(kind)
    prepare_row_source(source_kind, row)
    snapshot = source_snapshot_for_row(source_kind, row)
    source_id = _clean(row.get("source_id") or snapshot.get("source_id"))
    source_type = _clean(row.get("source_type") or snapshot.get("source_type"))
    label = _clean(row.get("reference_label")) or _snapshot_title(snapshot)
    if not snapshot or not source_id or not source_type:
        return {}

    original = copy.deepcopy(snapshot)
    overrides = {
        _clean(field): value
        for field, value in dict(row.get("source_admin_overrides") or {}).items()
        if _clean(field) and _clean(value)
    }
    effective = copy.deepcopy(snapshot)
    for field, value in overrides.items():
        if field not in {"image_reference", "instructions"}:
            effective[field] = value
    effective["source_original_snapshot"] = original
    effective["admin_source_overrides"] = overrides
    effective["contract_version"] = _clean(
        snapshot.get("contract_version")
        or row.get("source_contract_version")
        or CONTRACT_VERSION
    )

    image = _as_dict(snapshot.get("image"))
    return {
        "source_type": source_type,
        "source_id": source_id,
        "source_label": label,
        "source_snapshot": effective,
        "source_image_url": _clean(image.get("image_url")),
        "source_image_bucket": _clean(image.get("image_bucket")),
        "source_image_path": _clean(image.get("image_path")),
        "source_image_access_type": _clean(image.get("image_access_type")),
    }
