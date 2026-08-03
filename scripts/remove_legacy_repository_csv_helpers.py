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

    source = source.replace("import pathlib\n", "")
    source = remove_exact_block(source, "BASE_DIR = pathlib.Path", "RESOURCE_KEYS = {")
    source = remove_exact_block(source, "RECIPE_COLUMNS = [", "MEAL_SLOT_ORDER =")
    source = remove_exact_block(source, "def _repo_path(", "def list_repository_items(")
    source = source.replace(
        "# Backward compatible fallback: read old resource_assignments and resolve from CSV.",
        "# Backward compatible fallback: resolve old assignment IDs from the canonical repository.",
    )

    forbidden = (
        "import pathlib",
        "BASE_DIR =",
        "RECIPES_PATH =",
        "EXERCISES_PATH =",
        "RECIPE_COLUMNS =",
        "EXERCISE_COLUMNS =",
        "def _repo_path(",
        "def _expected_columns(",
        "def _read_repository_df(",
        "pd.read_csv(",
        "resolve from CSV",
    )
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"Legacy CSV helper token remained: {token}")

    required = (
        "import pandas as pd",
        "pd.isna(value)",
        "list_recipe_repository(active_only=active_only)",
        "list_exercise_repository(active_only=active_only)",
        "def sync_repository_to_state(",
        "def save_member_resource_allocations(",
        "def save_unified_recommendation_share(",
    )
    for token in required:
        if token not in source:
            raise RuntimeError(f"Required recommendation contract token was lost: {token}")

    CONTRACT.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
