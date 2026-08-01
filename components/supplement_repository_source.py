from __future__ import annotations

from typing import Any

from components.supplement_repository import list_supplement_repository


_MARKER = "_hm_supplement_repository_source_v1"


def _repository_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": "supplement_repository",
        "source_id": str(row.get("source_id") or row.get("id") or "").strip(),
        "title": str(row.get("supplement_name") or row.get("title") or "").strip(),
        "supplement_name": str(row.get("supplement_name") or row.get("title") or "").strip(),
        "dosage": str(row.get("dosage") or "").strip(),
        "frequency": str(row.get("frequency") or "").strip(),
        "timing": str(row.get("timing") or "").strip(),
        "instructions": str(row.get("instructions") or "").strip(),
        "start_date": "",
        "end_date": "",
        "admin_notes": str(row.get("admin_notes") or "").strip(),
        "status": str(row.get("status") or "Active").strip(),
    }


def install_profile_builder_supplement_repository_source() -> None:
    """Make Profile Builder consume the master repository, never member allocations."""
    from components import profile_builder_source_contract as contract

    if getattr(contract, _MARKER, False):
        return

    original_build = contract.build_profile_builder_source_contract

    def repository_rows(*, status: str | None = None, **_kwargs):
        active_only = not status or str(status).strip().lower() == "active"
        return list_supplement_repository(active_only=active_only)

    def build_with_repository_source():
        sources, snapshots, message = original_build()
        message = message.replace(
            "active regimen name(s)",
            "active repository item(s)",
        )
        return sources, snapshots, message

    contract.list_member_supplements = repository_rows
    contract.supplement_snapshot = _repository_snapshot
    contract.build_profile_builder_source_contract = build_with_repository_source
    setattr(contract, _MARKER, True)
