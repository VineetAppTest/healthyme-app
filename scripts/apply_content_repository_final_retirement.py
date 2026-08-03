from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "components" / "recommendation_contract.py"
MIGRATION_UTILITY = ROOT / "components" / "content_repository_migration.py"


def remove_exact_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[:start] + source[end:]


def retire_recommendation_contract() -> None:
    source = CONTRACT.read_text(encoding="utf-8")

    if "def sync_repository_to_state(" in source:
        source = remove_exact_block(
            source,
            "def sync_repository_to_state(",
            "def _member_lookup(",
        )

    source = source.replace("    sync_all_repositories_to_state()\n", "")
    source = source.replace(
        '    recipe_repo = list(db.get("recipes", []) or [])\n'
        '    exercise_repo = list(db.get("exercises", []) or [])\n',
        "    recipe_repo = list_recipe_repository(active_only=False)\n"
        "    exercise_repo = list_exercise_repository(active_only=False)\n",
    )
    source = source.replace(
        '        result["issues"].append("recipes repository mirror is empty")',
        '        result["issues"].append("canonical Recipe repository is empty")',
    )
    source = source.replace(
        '        result["issues"].append("exercises repository mirror is empty")',
        '        result["issues"].append("canonical Exercise repository is empty")',
    )

    forbidden = (
        "def sync_repository_to_state(",
        "def sync_all_repositories_to_state(",
        "sync_all_repositories_to_state()",
        'db.get("recipes", [])',
        'db.get("exercises", [])',
        "repository mirror is empty",
    )
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"Final legacy repository dependency remained: {token}")

    required = (
        "list_recipe_repository(active_only=False)",
        "list_exercise_repository(active_only=False)",
        "def save_member_resource_allocations(",
        "def enrich_recommendation_share_payload(",
        "def save_unified_recommendation_share(",
        "def recommendation_contract_diagnostics(",
        "canonical Recipe repository is empty",
        "canonical Exercise repository is empty",
    )
    for token in required:
        if token not in source:
            raise RuntimeError(f"Required final repository contract token was lost: {token}")

    CONTRACT.write_text(source, encoding="utf-8")


def point_historical_migration_to_archive() -> None:
    source = MIGRATION_UTILITY.read_text(encoding="utf-8")
    source = source.replace(
        'LEGACY_RECIPE_PATH = BASE_DIR / "data" / "recipes.csv"',
        'LEGACY_RECIPE_PATH = (\n'
        '    BASE_DIR / "docs" / "archive" / "content_repository_legacy" / "recipes.csv"\n'
        ')',
    )

    if 'BASE_DIR / "data" / "recipes.csv"' in source:
        raise RuntimeError("Historical migration utility still points at active Recipe CSV")
    if '"legacy_reference": f"data/recipes.csv:{index}"' not in source:
        raise RuntimeError("Original Recipe provenance reference was lost")
    if 'content_repository_legacy" / "recipes.csv"' not in source:
        raise RuntimeError("Archived Recipe evidence path was not installed")

    MIGRATION_UTILITY.write_text(source, encoding="utf-8")


def main() -> None:
    retire_recommendation_contract()
    point_historical_migration_to_archive()


if __name__ == "__main__":
    main()
