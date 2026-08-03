from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "components" / "recommendation_contract.py"
LEGACY_TEST = ROOT / "tests" / "test_content_repository_legacy_retirement.py"
CSV_TEST = ROOT / "tests" / "test_recommendation_contract_legacy_csv_cleanup.py"
DOC = ROOT / "docs" / "content_repository_legacy_retirement_2026-08-03.md"


text = CONTRACT.read_text(encoding="utf-8")
text = text.replace('        "repo_key": "recipes",\n', "")
text = text.replace('        "repo_key": "exercises",\n', "")
text = text.replace(
    '''def sync_repository_to_state(resource_type: str) -> list[dict[str, Any]]:\n    """Return a read-only canonical snapshot for legacy callers."""\n    return list_repository_items(resource_type, active_only=False)\n\n\ndef sync_all_repositories_to_state() -> dict[str, int]:\n    recipes = sync_repository_to_state("recipes")\n    exercises = sync_repository_to_state("exercises")\n    return {"recipes": len(recipes), "exercises": len(exercises)}\n\n\n''',
    "",
)
text = text.replace("    sync_all_repositories_to_state()\n", "")
text = text.replace(
    '    recipe_repo = list(db.get("recipes", []) or [])\n'
    '    exercise_repo = list(db.get("exercises", []) or [])\n',
    '    recipe_repo = list_recipe_repository(active_only=False)\n'
    '    exercise_repo = list_exercise_repository(active_only=False)\n',
)
text = text.replace(
    'result["issues"].append("recipes repository mirror is empty")',
    'result["issues"].append("canonical Recipe repository is empty")',
)
text = text.replace(
    'result["issues"].append("exercises repository mirror is empty")',
    'result["issues"].append("canonical Exercise repository is empty")',
)

for forbidden in (
    "def sync_repository_to_state(",
    "def sync_all_repositories_to_state(",
    "sync_all_repositories_to_state()",
    '"repo_key":',
    'db.get("recipes", [])',
    'db.get("exercises", [])',
    "repository mirror is empty",
):
    if forbidden in text:
        raise SystemExit(f"legacy repository authority remains: {forbidden}")

for required in (
    "list_recipe_repository(active_only=False)",
    "list_exercise_repository(active_only=False)",
    "canonical Recipe repository is empty",
    "canonical Exercise repository is empty",
):
    if required not in text:
        raise SystemExit(f"canonical diagnostic contract missing: {required}")

CONTRACT.write_text(text, encoding="utf-8")

legacy = LEGACY_TEST.read_text(encoding="utf-8")
old_block = '''    def test_compatibility_sync_is_read_only_in_core_contract(self) -> None:\n        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")\n        sync_block = source.split("def sync_repository_to_state", 1)[1].split(\n            "def sync_all_repositories_to_state", 1\n        )[0]\n        self.assertIn("read-only canonical snapshot", sync_block)\n        self.assertIn("list_repository_items(resource_type, active_only=False)", sync_block)\n        self.assertNotIn("save_state", sync_block)\n\n'''
new_block = '''    def test_legacy_sync_api_is_removed_from_live_code(self) -> None:\n        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")\n        self.assertNotIn("def sync_repository_to_state(", source)\n        self.assertNotIn("def sync_all_repositories_to_state(", source)\n        self.assertNotIn("sync_all_repositories_to_state()", source)\n\n        for folder in (ROOT / "components", ROOT / "pages"):\n            for path in folder.rglob("*.py"):\n                live_source = path.read_text(encoding="utf-8")\n                self.assertNotIn("sync_repository_to_state(", live_source, str(path))\n                self.assertNotIn("sync_all_repositories_to_state(", live_source, str(path))\n\n    def test_repository_diagnostics_use_canonical_sources(self) -> None:\n        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")\n        self.assertIn("recipe_repo = list_recipe_repository(active_only=False)", source)\n        self.assertIn("exercise_repo = list_exercise_repository(active_only=False)", source)\n        self.assertNotIn('recipe_repo = list(db.get("recipes", [])', source)\n        self.assertNotIn('exercise_repo = list(db.get("exercises", [])', source)\n        self.assertNotIn("repository mirror is empty", source)\n\n'''
if old_block not in legacy:
    raise SystemExit("legacy retirement test block changed unexpectedly")
legacy = legacy.replace(old_block, new_block)
LEGACY_TEST.write_text(legacy, encoding="utf-8")

csv_test = CSV_TEST.read_text(encoding="utf-8")
csv_test = csv_test.replace(
    '            "def sync_repository_to_state(",\n',
    '            "def list_repository_items(",\n',
)
csv_test = csv_test.replace(
    '''    def test_rollback_evidence_files_are_not_deleted(self) -> None:\n''',
    '''    def test_obsolete_sync_and_mirror_contracts_are_removed(self) -> None:\n        source = CONTRACT.read_text(encoding="utf-8")\n        for forbidden in (\n            "def sync_repository_to_state(",\n            "def sync_all_repositories_to_state(",\n            "sync_all_repositories_to_state()",\n            '\"repo_key\":',\n            "repository mirror is empty",\n        ):\n            self.assertNotIn(forbidden, source)\n        self.assertIn("recipe_repo = list_recipe_repository(active_only=False)", source)\n        self.assertIn("exercise_repo = list_exercise_repository(active_only=False)", source)\n\n    def test_rollback_evidence_files_are_not_deleted(self) -> None:\n''',
)
CSV_TEST.write_text(csv_test, encoding="utf-8")

doc = DOC.read_text(encoding="utf-8")
section = '''\n## Phase C checkpoint — legacy sync API removal\n\n- Removed `sync_repository_to_state` and `sync_all_repositories_to_state`; neither function persisted data after canonical cutover.\n- Removed the discarded sync call from recommendation-share enrichment.\n- Recommendation diagnostics now count Recipe and Exercise records directly from the canonical repository modules.\n- Legacy CSV files and app-state repository arrays remain retained as rollback evidence; this checkpoint does not delete or mutate them.\n'''
if "## Phase C checkpoint — legacy sync API removal" not in doc:
    doc += section
DOC.write_text(doc, encoding="utf-8")
