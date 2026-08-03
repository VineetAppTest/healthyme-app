"""Canonical Supabase persistence for HealthyMe Content Repositories.

Recipe, Exercise and Supplement share this read/write contract. Repository-specific
modules translate the common envelope into the legacy row shapes expected by the
current Streamlit and member-facing consumers.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, List, Mapping, Tuple


CONTENT_TABLE = "hm_content_repository_items"
EVENT_TABLE = "hm_content_repository_events"
NUMERIC_CREATE_RPC = "hm_create_numeric_content_repository_item"
VALID_REPOSITORY_TYPES = {"recipe", "exercise", "supplement"}
VALID_STATUSES = {"active", "inactive"}
NUMERIC_REPOSITORY_TYPES = {"recipe", "exercise"}

_COMMON_LEGACY_FIELDS = {
    "id",
    "source_id",
    "resource_type",
    "status",
    "source",
    "source_system",
    "legacy_reference",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "content_version",
}


class RepositoryPersistenceError(RuntimeError):
    """Raised when canonical repository persistence cannot be verified."""


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _normalise_repository_type(value: object) -> str:
    repository_type = _clean(value).lower()
    if repository_type not in VALID_REPOSITORY_TYPES:
        raise ValueError(
            f"Unsupported Content Repository type: {repository_type or '<blank>'}."
        )
    return repository_type


def _normalise_status(value: object) -> str:
    status = _clean(value, "active").lower()
    if status in {"stopped", "archived", "disabled"}:
        status = "inactive"
    if status not in VALID_STATUSES:
        status = "active"
    return status


def _normalise_payload(value: object) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("Content Repository payload must be an object.")
    return copy.deepcopy(dict(value))


def _client():
    # Reuse the established server-side Supabase secret resolution. The canonical
    # tables are deliberately inaccessible to anon/authenticated browser clients.
    from components.recommendation_profile_store import _client as profile_client

    return profile_client()


def _rows(response: object) -> List[dict]:
    data = getattr(response, "data", None)
    if isinstance(data, Mapping):
        return [dict(data)]
    return [dict(row) for row in list(data or [])]


def _display_name(repository_type: str, row: Mapping[str, Any]) -> str:
    if repository_type == "supplement":
        return _clean(
            row.get("supplement_name") or row.get("title") or row.get("name")
        )
    return _clean(row.get("title") or row.get("name"))


def normalise_legacy_item(
    repository_type: str,
    row: Mapping[str, Any],
    *,
    fallback_source_id: object = "",
) -> Dict[str, Any]:
    """Translate one legacy repository row into the canonical table envelope.

    Legacy identity is retained exactly. Display names are presentation fields and
    never become identity. Type-specific fields stay in ``payload`` so all three
    repositories share one persistence pattern without forcing identical content
    columns.
    """
    kind = _normalise_repository_type(repository_type)
    source = dict(row or {})
    source_id = _clean(
        source.get("source_id") or source.get("id") or fallback_source_id
    )
    if not source_id:
        raise ValueError(
            f"{kind.title()} repository item is missing a stable source ID."
        )

    display_name = _display_name(kind, source)
    if not display_name:
        raise ValueError(
            f"{kind.title()} repository item {source_id} has no display name."
        )

    payload = {
        key: copy.deepcopy(value)
        for key, value in source.items()
        if key not in _COMMON_LEGACY_FIELDS
    }

    return {
        "repository_type": kind,
        "source_id": source_id,
        "display_name": display_name,
        "status": _normalise_status(source.get("status")),
        "payload": payload,
        "source_system": _clean(
            source.get("source_system") or source.get("source"), "legacy"
        ),
        "legacy_reference": _clean(source.get("legacy_reference")),
        "created_at": _clean(source.get("created_at")),
        "created_by": _clean(source.get("created_by")),
        "updated_at": _clean(source.get("updated_at")),
        "updated_by": _clean(source.get("updated_by")),
    }


def repository_identity(item: Mapping[str, Any]) -> Tuple[str, str]:
    return (
        _normalise_repository_type(item.get("repository_type")),
        _clean(item.get("source_id")),
    )


def validate_unique_identities(items: Iterable[Mapping[str, Any]]) -> None:
    seen: set[Tuple[str, str]] = set()
    for item in items:
        identity = repository_identity(item)
        if not identity[1]:
            raise ValueError(
                f"{identity[0].title()} repository item has a blank source ID."
            )
        if identity in seen:
            raise ValueError(
                f"Duplicate Content Repository identity: {identity[0]}:{identity[1]}."
            )
        seen.add(identity)


def check_content_repository_store() -> Dict[str, Any]:
    """Confirm both canonical tables are available through the server client."""
    try:
        client = _client()
        client.table(CONTENT_TABLE).select("id", count="exact").limit(1).execute()
        client.table(EVENT_TABLE).select("id", count="exact").limit(1).execute()
        return {
            "ok": True,
            "message": "Standard Content Repository tables are ready.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Standard Content Repository tables are not ready: {exc}",
        }


def list_repository_items(
    repository_type: str,
    *,
    active_only: bool = True,
) -> List[dict]:
    kind = _normalise_repository_type(repository_type)
    try:
        query = (
            _client()
            .table(CONTENT_TABLE)
            .select(
                "id,repository_type,source_id,display_name,status,payload,"
                "content_version,source_system,legacy_reference,created_at,"
                "created_by,updated_at,updated_by"
            )
            .eq("repository_type", kind)
        )
        if active_only:
            query = query.eq("status", "active")
        result = query.order("display_name").order("source_id").execute()
        return _rows(result)
    except Exception as exc:
        raise RepositoryPersistenceError(
            f"Could not read the {kind.title()} Repository from Supabase: {exc}"
        ) from exc


def get_repository_item(
    repository_type: str,
    source_id: object,
) -> Dict[str, Any] | None:
    kind = _normalise_repository_type(repository_type)
    clean_source_id = _clean(source_id)
    if not clean_source_id:
        raise ValueError("Content Repository source ID is required.")
    try:
        result = (
            _client()
            .table(CONTENT_TABLE)
            .select(
                "id,repository_type,source_id,display_name,status,payload,"
                "content_version,source_system,legacy_reference,created_at,"
                "created_by,updated_at,updated_by"
            )
            .eq("repository_type", kind)
            .eq("source_id", clean_source_id)
            .limit(1)
            .execute()
        )
        rows = _rows(result)
        return dict(rows[0]) if rows else None
    except Exception as exc:
        raise RepositoryPersistenceError(
            f"Could not read {kind}:{clean_source_id} from Supabase: {exc}"
        ) from exc


def _verified_item(
    repository_type: str,
    source_id: str,
    expected: Mapping[str, Any],
) -> Dict[str, Any]:
    # This is deliberately a fresh query after every create/update/status write.
    stored = get_repository_item(repository_type, source_id)
    if not stored:
        raise RepositoryPersistenceError(
            f"Supabase did not return {repository_type}:{source_id} after the write."
        )

    comparisons = {
        "display_name": _clean(stored.get("display_name"))
        == _clean(expected.get("display_name")),
        "status": _normalise_status(stored.get("status"))
        == _normalise_status(expected.get("status")),
        "payload": dict(stored.get("payload") or {})
        == dict(expected.get("payload") or {}),
        "source_system": _clean(stored.get("source_system"))
        == _clean(expected.get("source_system"), "healthyme"),
        "legacy_reference": _clean(stored.get("legacy_reference"))
        == _clean(expected.get("legacy_reference")),
    }
    failed = [field for field, matched in comparisons.items() if not matched]
    if failed:
        raise RepositoryPersistenceError(
            f"Supabase verification failed for {repository_type}:{source_id}; "
            f"mismatched fields: {', '.join(failed)}."
        )
    return stored


def create_numeric_repository_item(
    repository_type: str,
    display_name: object,
    payload: Mapping[str, Any],
    *,
    status: object = "active",
    actor_id: object = "admin",
    source_system: object = "healthyme",
) -> Dict[str, Any]:
    """Atomically create one numeric-ID Recipe or Exercise definition.

    PostgreSQL serializes ID allocation per repository type through an advisory
    transaction lock. The returned ID is confirmed through a separate fresh read.
    """
    kind = _normalise_repository_type(repository_type)
    if kind not in NUMERIC_REPOSITORY_TYPES:
        raise ValueError(
            f"Numeric Content Repository creation is not supported for {kind}."
        )

    clean_display_name = _clean(display_name)
    clean_actor = _clean(actor_id, "admin")
    if not clean_display_name:
        raise ValueError("Content Repository display name is required.")

    expected = {
        "repository_type": kind,
        "display_name": clean_display_name,
        "status": _normalise_status(status),
        "payload": _normalise_payload(payload),
        "source_system": _clean(source_system, "healthyme"),
        "legacy_reference": "",
    }

    try:
        result = (
            _client()
            .rpc(
                NUMERIC_CREATE_RPC,
                {
                    "p_repository_type": kind,
                    "p_display_name": expected["display_name"],
                    "p_payload": expected["payload"],
                    "p_status": expected["status"],
                    "p_actor_id": clean_actor,
                    "p_source_system": expected["source_system"],
                },
            )
            .execute()
        )
        rows = _rows(result)
        if len(rows) != 1 or not _clean(rows[0].get("source_id")):
            raise RepositoryPersistenceError(
                "Supabase did not return one allocated Content Repository ID."
            )
        source_id = _clean(rows[0].get("source_id"))
        return _verified_item(kind, source_id, expected)
    except RepositoryPersistenceError:
        raise
    except Exception as exc:
        raise RepositoryPersistenceError(
            f"Could not create a numeric {kind.title()} Repository item in Supabase: {exc}"
        ) from exc


def save_repository_item(
    repository_type: str,
    source_id: object,
    display_name: object,
    payload: Mapping[str, Any],
    *,
    status: object = "active",
    actor_id: object = "admin",
    source_system: object = "healthyme",
    legacy_reference: object = "",
) -> Dict[str, Any]:
    """Create or update one item and confirm it through a fresh Supabase read.

    Identity is immutable. Existing items are updated by the composite
    ``repository_type`` + ``source_id`` key; no title-based lookup or fallback is
    allowed. The database trigger owns timestamps, version increments and audit
    events.
    """
    kind = _normalise_repository_type(repository_type)
    clean_source_id = _clean(source_id)
    clean_display_name = _clean(display_name)
    clean_actor = _clean(actor_id, "admin")
    if not clean_source_id:
        raise ValueError("Content Repository source ID is required.")
    if not clean_display_name:
        raise ValueError("Content Repository display name is required.")

    expected = {
        "repository_type": kind,
        "source_id": clean_source_id,
        "display_name": clean_display_name,
        "status": _normalise_status(status),
        "payload": _normalise_payload(payload),
        "source_system": _clean(source_system, "healthyme"),
        "legacy_reference": _clean(legacy_reference),
    }

    try:
        client = _client()
        existing = get_repository_item(kind, clean_source_id)
        if existing:
            (
                client.table(CONTENT_TABLE)
                .update(
                    {
                        "display_name": expected["display_name"],
                        "status": expected["status"],
                        "payload": expected["payload"],
                        "source_system": expected["source_system"],
                        "legacy_reference": expected["legacy_reference"] or None,
                        "updated_by": clean_actor,
                    }
                )
                .eq("repository_type", kind)
                .eq("source_id", clean_source_id)
                .execute()
            )
        else:
            client.table(CONTENT_TABLE).insert(
                {
                    **expected,
                    "legacy_reference": expected["legacy_reference"] or None,
                    "created_by": clean_actor,
                    "updated_by": clean_actor,
                }
            ).execute()
        return _verified_item(kind, clean_source_id, expected)
    except RepositoryPersistenceError:
        raise
    except Exception as exc:
        raise RepositoryPersistenceError(
            f"Could not persist {kind}:{clean_source_id} in Supabase: {exc}"
        ) from exc


def set_repository_item_status(
    repository_type: str,
    source_id: object,
    *,
    active: bool,
    actor_id: object = "admin",
) -> Dict[str, Any]:
    kind = _normalise_repository_type(repository_type)
    clean_source_id = _clean(source_id)
    existing = get_repository_item(kind, clean_source_id)
    if not existing:
        raise ValueError(
            f"Content Repository item {kind}:{clean_source_id} was not found."
        )
    return save_repository_item(
        kind,
        clean_source_id,
        existing.get("display_name"),
        dict(existing.get("payload") or {}),
        status="active" if active else "inactive",
        actor_id=actor_id,
        source_system=existing.get("source_system") or "healthyme",
        legacy_reference=existing.get("legacy_reference") or "",
    )
