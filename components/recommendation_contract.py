"""HealthyMe H9A.5E unified recommendation allocation contract.

This module keeps Recipe, Exercise, Supplement and Recommendation Share aligned while
we are still using the existing JSON/app-state storage model.

Design intent:
- Recipe and Exercise definitions are read from the canonical Supabase Content Repository.
- Direct allocation and recommendation-share allocation converge into
  `member_recipe_allocations` and `member_exercise_allocations`.
- Published `recommendation_shares[member_id]` contains resolved names/details, not
  blank IDs only.
"""

from __future__ import annotations

import datetime as _dt
import re
import uuid
from typing import Any

import pandas as pd

from components.storage_backend import load_state, save_state
from components.exercise_repository import list_exercise_repository
from components.recipe_repository import list_recipe_repository


RESOURCE_KEYS = {
    "recipes": {
        "repo_key": "recipes",
        "allocation_key": "member_recipe_allocations",
        "legacy_assignment_key": "recipes",
        "id_field": "recipe_id",
        "name_field": "recipe_name",
        "title_fallback": "Untitled Recipe",
    },
    "exercises": {
        "repo_key": "exercises",
        "allocation_key": "member_exercise_allocations",
        "legacy_assignment_key": "exercises",
        "id_field": "exercise_id",
        "name_field": "exercise_name",
        "title_fallback": "Untitled Exercise",
    },
}


MEAL_SLOT_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner", "Bedtime"]


def _now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "select", "na", "n/a"}:
        return ""
    return text


def _json_safe(value: Any) -> Any:
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value


def _resource_type(value: str) -> str:
    value = str(value or "").strip().lower()
    if value in {"recipe", "recipes", "meal", "meals"}:
        return "recipes"
    if value in {"exercise", "exercises", "workout", "workouts"}:
        return "exercises"
    raise ValueError("resource_type must be recipes or exercises")


def list_repository_items(resource_type: str, active_only: bool = True) -> list[dict[str, Any]]:
    resource_type = _resource_type(resource_type)
    if resource_type == "recipes":
        return list_recipe_repository(active_only=active_only)
    return list_exercise_repository(active_only=active_only)


def _repo_lookup(resource_type: str) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in list_repository_items(resource_type, active_only=False)}


def sync_repository_to_state(resource_type: str) -> list[dict[str, Any]]:
    """Return a read-only canonical snapshot for legacy callers."""
    return list_repository_items(resource_type, active_only=False)


def sync_all_repositories_to_state() -> dict[str, int]:
    recipes = sync_repository_to_state("recipes")
    exercises = sync_repository_to_state("exercises")
    return {"recipes": len(recipes), "exercises": len(exercises)}


def _member_lookup(db: dict[str, Any], member_id: str) -> dict[str, Any]:
    member_id = str(member_id or "").strip()
    for user in db.get("users", []) or []:
        if str(user.get("id")) == member_id or str(user.get("email", "")).strip().lower() == member_id.lower():
            return dict(user)
    return {}


def _canonical_allocation_from_item(
    *,
    member_id: str,
    resource_type: str,
    item_id: str,
    item: dict[str, Any],
    actor_id: str = "admin",
    source: str = "direct_member_page",
    start_date: str = "",
    end_date: str = "",
    meal_slot: str = "",
    notes: str = "",
) -> dict[str, Any]:
    resource_type = _resource_type(resource_type)
    cfg = RESOURCE_KEYS[resource_type]
    title = _clean(item.get("title")) or cfg["title_fallback"]
    allocation = {
        "id": f"{resource_type[:3]}_{member_id}_{item_id}",
        "member_id": member_id,
        cfg["id_field"]: str(item_id),
        cfg["name_field"]: title,
        "title": title,
        "status": "active",
        "source": source,
        "start_date": _clean(start_date),
        "end_date": _clean(end_date),
        "notes": _clean(notes),
        "created_by": actor_id or "admin",
        "updated_by": actor_id or "admin",
        "updated_at": _now_iso(),
    }
    if resource_type == "recipes":
        allocation.update({
            "meal_slot": _clean(meal_slot) or _clean(item.get("meal_type")) or "Recipe",
            "meal_type": _clean(item.get("meal_type")),
            "description": _clean(item.get("description")),
            "portion_size": _clean(item.get("portion_size")),
            "prep_time": _clean(item.get("prep_time")),
            "ingredients": _clean(item.get("ingredients")),
            "instructions": _clean(item.get("steps")) or _clean(item.get("instructions")),
            "nutrition": _clean(item.get("nutrition")),
            "image_url": _clean(item.get("image_url")),
        })
    else:
        allocation.update({
            "category": _clean(item.get("category")),
            "duration": _clean(item.get("duration_or_reps")),
            "duration_or_reps": _clean(item.get("duration_or_reps")),
            "difficulty": _clean(item.get("difficulty")),
            "equipment": _clean(item.get("equipment")),
            "instructions": _clean(item.get("instructions")),
            "benefits": _clean(item.get("benefits")),
            "image_url": _clean(item.get("image_url")),
        })
    return allocation


def save_member_resource_allocations(
    member_id: str,
    resource_type: str,
    item_ids: list[str],
    actor_id: str = "admin",
    source: str = "direct_member_page",
    start_date: str = "",
    end_date: str = "",
) -> list[dict[str, Any]]:
    """Save direct/member-page allocation into the unified allocation layer."""
    resource_type = _resource_type(resource_type)
    cfg = RESOURCE_KEYS[resource_type]
    repo = _repo_lookup(resource_type)
    clean_ids = [str(x).strip() for x in (item_ids or []) if str(x).strip()]
    allocations = []
    for item_id in clean_ids:
        item = repo.get(item_id, {})
        if not item:
            item = {"id": item_id, "title": f"{cfg['title_fallback']} {item_id}", "status": "active"}
        allocations.append(_canonical_allocation_from_item(
            member_id=str(member_id),
            resource_type=resource_type,
            item_id=item_id,
            item=item,
            actor_id=actor_id,
            source=source,
            start_date=start_date,
            end_date=end_date,
        ))

    db = load_state()
    db.setdefault("resource_assignments", {}).setdefault(cfg["legacy_assignment_key"], {})[str(member_id)] = clean_ids
    db.setdefault(cfg["allocation_key"], {})[str(member_id)] = allocations
    db.setdefault("recommendation_contract_audit", []).append({
        "ts": _now_iso(),
        "action": f"save_{resource_type}_allocation",
        "member_id": str(member_id),
        "count": len(allocations),
        "source": source,
        "actor_id": actor_id or "admin",
    })
    member = _member_lookup(db, str(member_id))
    label = "recipes" if resource_type == "recipes" else "exercises"
    db.setdefault("notifications", []).append({
        "ts": _now_iso(),
        "kind": f"{resource_type}_allocated",
        "user_id": str(member_id),
        "member_id": str(member_id),
        "email_to": member.get("email", ""),
        "message": f"Your admin has allocated {len(allocations)} {label} to your HealthyMe plan.",
        "status": "queued",
        "email_required": True,
        "created_by": actor_id or "admin",
        "source": "unified_recommendation_allocation_contract",
    })
    save_state(db)
    return allocations


def migrate_legacy_resource_assignments(member_id: str | None = None, actor_id: str = "admin") -> dict[str, int]:
    """Convert existing resource_assignments into canonical member allocations."""
    db = load_state()
    migrated = {"recipes": 0, "exercises": 0}
    for resource_type in ["recipes", "exercises"]:
        cfg = RESOURCE_KEYS[resource_type]
        by_member = db.get("resource_assignments", {}).get(cfg["legacy_assignment_key"], {}) or {}
        for mid, ids in by_member.items():
            if member_id and str(mid) != str(member_id):
                continue
            rows = save_member_resource_allocations(str(mid), resource_type, [str(x) for x in ids or []], actor_id=actor_id, source="legacy_resource_assignments")
            migrated[resource_type] += len(rows)
    return migrated


def get_member_resource_allocations(member_id: str, resource_type: str) -> list[dict[str, Any]]:
    resource_type = _resource_type(resource_type)
    cfg = RESOURCE_KEYS[resource_type]
    db = load_state()
    rows = list(db.get(cfg["allocation_key"], {}).get(str(member_id), []) or [])
    if rows:
        return [dict(r) for r in rows if str(r.get("status", "active")).lower() == "active"]
    # Backward compatible fallback: resolve old assignment IDs from the canonical repository.
    legacy_ids = db.get("resource_assignments", {}).get(cfg["legacy_assignment_key"], {}).get(str(member_id), []) or []
    if legacy_ids:
        return save_member_resource_allocations(str(member_id), resource_type, [str(x) for x in legacy_ids], actor_id="system", source="legacy_resource_assignments")
    return []


def _has_real_plan_items(items: list[dict[str, Any]], id_field: str, name_field: str) -> bool:
    for item in items or []:
        if _clean(item.get(id_field)) or _clean(item.get(name_field)) or _clean(item.get("title")) or _clean(item.get("name")):
            return True
    return False


def _recipe_plan_from_allocations(member_id: str, start_date: str = "") -> list[dict[str, Any]]:
    rows = get_member_resource_allocations(member_id, "recipes")
    plan = []
    for idx, row in enumerate(rows, start=1):
        slot = _clean(row.get("meal_slot")) or _clean(row.get("meal_type")) or "Recipe"
        plan.append({
            "day_number": 1,
            "date": str(start_date or ""),
            "meal_slot": slot,
            "recipe_id": _clean(row.get("recipe_id")),
            "recipe_name": _clean(row.get("recipe_name")) or _clean(row.get("title")),
            "name": _clean(row.get("recipe_name")) or _clean(row.get("title")),
            "quantity": _clean(row.get("portion_size")),
            "portion_size": _clean(row.get("portion_size")),
            "timing": _clean(row.get("prep_time")),
            "instructions": _clean(row.get("instructions")),
            "notes": _clean(row.get("notes")),
            "source": _clean(row.get("source")) or "member_recipe_allocations",
            "allocation_id": _clean(row.get("id")) or f"recipe_alloc_{idx}",
        })
    return plan


def _exercise_plan_from_allocations(member_id: str, start_date: str = "") -> list[dict[str, Any]]:
    rows = get_member_resource_allocations(member_id, "exercises")
    plan = []
    for idx, row in enumerate(rows, start=1):
        plan.append({
            "day_number": idx,
            "date": str(start_date or ""),
            "exercise_id": _clean(row.get("exercise_id")),
            "exercise_name": _clean(row.get("exercise_name")) or _clean(row.get("title")),
            "name": _clean(row.get("exercise_name")) or _clean(row.get("title")),
            "title": _clean(row.get("exercise_name")) or _clean(row.get("title")),
            "duration": _clean(row.get("duration")) or _clean(row.get("duration_or_reps")),
            "frequency": _clean(row.get("frequency")),
            "timing": _clean(row.get("timing")),
            "instructions": _clean(row.get("instructions")),
            "notes": _clean(row.get("notes")),
            "source": _clean(row.get("source")) or "member_exercise_allocations",
            "allocation_id": _clean(row.get("id")) or f"exercise_alloc_{idx}",
        })
    return plan


def _enrich_meal_plan(member_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    repo = _repo_lookup("recipes")
    start_date = _clean(payload.get("start_date"))
    incoming = [dict(x) for x in (payload.get("meal_plan") or []) if isinstance(x, dict)]
    enriched = []
    for row in incoming:
        recipe_id = _clean(row.get("recipe_id"))
        recipe = repo.get(recipe_id, {}) if recipe_id else {}
        name = _clean(row.get("recipe_name")) or _clean(row.get("name")) or _clean(recipe.get("title"))
        out = dict(row)
        out["recipe_id"] = recipe_id
        out["recipe_name"] = name
        out["name"] = name
        out.setdefault("meal_slot", _clean(recipe.get("meal_type")) or "Recipe")
        out.setdefault("quantity", _clean(recipe.get("portion_size")))
        out.setdefault("portion_size", _clean(recipe.get("portion_size")))
        out.setdefault("timing", _clean(recipe.get("prep_time")))
        out.setdefault("instructions", _clean(recipe.get("steps")) or _clean(recipe.get("instructions")))
        enriched.append(out)
    if _has_real_plan_items(enriched, "recipe_id", "recipe_name"):
        return enriched
    return _recipe_plan_from_allocations(member_id, start_date=start_date)


def _enrich_exercise_plan(member_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    repo = _repo_lookup("exercises")
    start_date = _clean(payload.get("start_date"))
    incoming = [dict(x) for x in (payload.get("exercise_plan") or []) if isinstance(x, dict)]
    enriched = []
    for row in incoming:
        exercise_id = _clean(row.get("exercise_id"))
        exercise = repo.get(exercise_id, {}) if exercise_id else {}
        name = _clean(row.get("exercise_name")) or _clean(row.get("name")) or _clean(row.get("title")) or _clean(exercise.get("title"))
        out = dict(row)
        out["exercise_id"] = exercise_id
        out["exercise_name"] = name
        out["name"] = name
        out["title"] = name
        out.setdefault("duration", _clean(exercise.get("duration_or_reps")))
        out.setdefault("instructions", _clean(exercise.get("instructions")))
        enriched.append(out)
    if _has_real_plan_items(enriched, "exercise_id", "exercise_name"):
        return enriched
    return _exercise_plan_from_allocations(member_id, start_date=start_date)


def enrich_recommendation_share_payload(member_id: str, payload: dict[str, Any], actor_id: str = "admin") -> dict[str, Any]:
    sync_all_repositories_to_state()
    out = _json_safe(dict(payload or {}))
    out["member_id"] = str(member_id)
    out["meal_plan"] = _enrich_meal_plan(str(member_id), out)
    out["exercise_plan"] = _enrich_exercise_plan(str(member_id), out)
    out.setdefault("supplement_plan", [])
    out["updated_at"] = _now_iso()
    out["updated_by"] = actor_id or "admin"
    return out


def save_unified_recommendation_share(member_id: str, payload: dict[str, Any], actor_id: str = "admin", publish: bool = False) -> dict[str, Any]:
    """Save/publish a recommendation share with resolved recipe/exercise details."""
    member_id = str(member_id or "").strip()
    if not member_id:
        raise ValueError("Member is required before saving recommendations.")
    enriched = enrich_recommendation_share_payload(member_id, payload or {}, actor_id=actor_id)
    share_id = _clean(enriched.get("id")) or str(uuid.uuid4())[:8]
    now = _now_iso()
    enriched["id"] = share_id
    enriched["status"] = "Published" if publish else "Draft"
    enriched.setdefault("created_at", now)
    enriched.setdefault("created_by", actor_id or "admin")
    enriched["updated_at"] = now
    enriched["updated_by"] = actor_id or "admin"
    if publish:
        enriched["published_at"] = now
        enriched["published_by"] = actor_id or "admin"

    db = load_state()
    member = _member_lookup(db, member_id)
    shares = db.setdefault("recommendation_shares", {}).setdefault(member_id, [])
    replaced = False
    for idx, existing in enumerate(shares):
        if str(existing.get("id", "")) == share_id:
            prior_created_at = existing.get("created_at") or enriched.get("created_at") or now
            prior_created_by = existing.get("created_by") or enriched.get("created_by") or actor_id or "admin"
            shares[idx] = dict(enriched)
            shares[idx]["created_at"] = prior_created_at
            shares[idx]["created_by"] = prior_created_by
            replaced = True
            break
    if not replaced:
        shares.append(dict(enriched))

    db.setdefault("recommendation_share_audit", []).append({
        "ts": now,
        "action": "published" if publish else "saved_draft",
        "actor_id": actor_id or "admin",
        "member_id": member_id,
        "member_email": member.get("email", ""),
        "share_id": share_id,
        "start_date": _clean(enriched.get("start_date")),
        "end_date": _clean(enriched.get("end_date")),
        "meal_items": len(enriched.get("meal_plan") or []),
        "exercise_items": len(enriched.get("exercise_plan") or []),
        "real_recipe_items": sum(1 for r in enriched.get("meal_plan", []) if _clean(r.get("recipe_id")) or _clean(r.get("recipe_name"))),
        "real_exercise_items": sum(1 for r in enriched.get("exercise_plan", []) if _clean(r.get("exercise_id")) or _clean(r.get("exercise_name"))),
        "source": "unified_recommendation_allocation_contract",
    })

    if publish:
        db.setdefault("notifications", []).append({
            "ts": now,
            "kind": "recommendations_published",
            "user_id": member_id,
            "member_id": member_id,
            "email_to": member.get("email", ""),
            "message": "Your HealthyMe recommendations have been published.",
            "status": "queued",
            "email_required": True,
            "created_by": actor_id or "admin",
            "share_id": share_id,
        })
        db.setdefault("messages", []).append({
            "id": str(uuid.uuid4())[:8],
            "ts": now,
            "member_id": member_id,
            "sender_role": "admin",
            "actor_id": actor_id or "admin",
            "subject": "Recommendations published",
            "message": "Your latest HealthyMe recommendations are now available.",
            "status": "queued",
            "email_required": True,
            "source": "recommendation_share",
            "share_id": share_id,
            "read": False,
            "archived": False,
        })

    save_state(db)
    return dict(enriched)


def get_latest_unified_recommendation_share(member_id: str, include_draft: bool = True) -> dict[str, Any]:
    db = load_state()
    rows = list(db.get("recommendation_shares", {}).get(str(member_id), []) or [])
    if not include_draft:
        rows = [r for r in rows if str(r.get("status", "")).lower() == "published"]
    rows.sort(key=lambda r: str(r.get("published_at") or r.get("updated_at") or r.get("created_at") or ""), reverse=True)
    return dict(rows[0]) if rows else {}


def recommendation_contract_diagnostics(member_id: str | None = None) -> dict[str, Any]:
    db = load_state()
    recipe_repo = list(db.get("recipes", []) or [])
    exercise_repo = list(db.get("exercises", []) or [])
    result: dict[str, Any] = {
        "recipes_repository_count": len(recipe_repo),
        "exercises_repository_count": len(exercise_repo),
        "member_recipe_allocations_count": 0,
        "member_exercise_allocations_count": 0,
        "published_shares_count": 0,
        "published_recipe_items": 0,
        "published_exercise_items": 0,
        "issues": [],
    }
    member_ids = [str(member_id)] if member_id else list({
        *[str(k) for k in db.get("member_recipe_allocations", {}).keys()],
        *[str(k) for k in db.get("member_exercise_allocations", {}).keys()],
        *[str(k) for k in db.get("recommendation_shares", {}).keys()],
    })
    for mid in member_ids:
        recipe_allocs = list(db.get("member_recipe_allocations", {}).get(mid, []) or [])
        exercise_allocs = list(db.get("member_exercise_allocations", {}).get(mid, []) or [])
        result["member_recipe_allocations_count"] += len(recipe_allocs)
        result["member_exercise_allocations_count"] += len(exercise_allocs)
        for share in db.get("recommendation_shares", {}).get(mid, []) or []:
            if str(share.get("status", "")).lower() != "published":
                continue
            result["published_shares_count"] += 1
            meal_real = sum(1 for r in share.get("meal_plan", []) or [] if _clean(r.get("recipe_id")) or _clean(r.get("recipe_name")))
            exercise_real = sum(1 for r in share.get("exercise_plan", []) or [] if _clean(r.get("exercise_id")) or _clean(r.get("exercise_name")))
            result["published_recipe_items"] += meal_real
            result["published_exercise_items"] += exercise_real
            if not meal_real:
                result["issues"].append(f"{mid}: published share {share.get('id', '')} has no real recipe item")
            if not exercise_real:
                result["issues"].append(f"{mid}: published share {share.get('id', '')} has no real exercise item")
    if not recipe_repo:
        result["issues"].append("recipes repository mirror is empty")
    if not exercise_repo:
        result["issues"].append("exercises repository mirror is empty")
    return result
