from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "components" / "recommendation_contract.py"


def remove_exact_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[:start] + source[end:]


def main() -> None:
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


if __name__ == "__main__":
    main()
