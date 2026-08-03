from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content, encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    return source.replace(old, new, 1)


def regex_once(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {count}")
    return updated


def patch_member_page(
    path: str,
    *,
    repository_import: str,
    columns_name: str,
    list_function: str,
    loader_name: str,
    data_filename: str,
) -> None:
    source = read(path)
    source = replace_once(source, "import pathlib\n", "", f"{path} pathlib import")
    source = replace_once(
        source,
        "from components.guards import require_member\n",
        f"from components.guards import require_member\n{repository_import}\n",
        f"{path} repository import",
    )
    source = regex_once(
        source,
        rf'DATA_PATH = pathlib\.Path\(__file__\)\.resolve\(\)\.parents\[1\] / "data" / "{re.escape(data_filename)}"\n\n{columns_name} = \[.*?\]\n\n',
        "",
        f"{path} legacy path and columns",
    )
    loader = f'''def {loader_name}():\n    rows = {list_function}(active_only=False)\n    frame = pd.DataFrame(\n        [{{column: row.get(column, "") for column in {columns_name}}} for row in rows],\n        columns={columns_name},\n    )\n    if rows:\n        identities = []\n        for index, row in enumerate(rows):\n            source_id = str(row.get("id", index)).strip()\n            identities.append(int(source_id) if source_id.isdigit() else source_id)\n        frame.index = identities\n    return frame\n'''
    source = regex_once(
        source,
        rf'@st\.cache_data\(show_spinner=False\)\ndef {loader_name}\(_mtime=0\):\n.*?    return df\[{columns_name}\]\n',
        loader,
        f"{path} canonical loader",
    )
    source = regex_once(
        source,
        rf'{re.escape(loader_name)}\(DATA_PATH\.stat\(\)\.st_mtime if DATA_PATH\.exists\(\) else 0\)',
        f"{loader_name}()",
        f"{path} loader call",
    )
    write(path, source)


def patch_bootstrap() -> None:
    path = "components/__init__.py"
    source = read(path)
    for line in (
        "from components.exercise_repository_runtime import install_exercise_repository_runtime\n",
        "from components.recipe_repository_runtime import install_recipe_repository_runtime\n",
        "install_exercise_repository_runtime()\n",
        "install_recipe_repository_runtime()\n",
    ):
        source = replace_once(source, line, "", f"{path} remove {line.strip()}")
    write(path, source)


def patch_recommendation_contract() -> None:
    path = "components/recommendation_contract.py"
    source = read(path)
    source = replace_once(
        source,
        "from components.storage_backend import load_state, save_state\n",
        "from components.storage_backend import load_state, save_state\n"
        "from components.exercise_repository import list_exercise_repository\n"
        "from components.recipe_repository import list_recipe_repository\n",
        f"{path} canonical imports",
    )
    list_impl = '''def list_repository_items(resource_type: str, active_only: bool = True) -> list[dict[str, Any]]:\n    resource_type = _resource_type(resource_type)\n    if resource_type == "recipes":\n        return list_recipe_repository(active_only=active_only)\n    return list_exercise_repository(active_only=active_only)\n\n\n'''
    source = regex_once(
        source,
        r'def list_repository_items\(resource_type: str, active_only: bool = True\) -> list\[dict\[str, Any\]\]:\n.*?\n\ndef _repo_lookup',
        list_impl + "def _repo_lookup",
        f"{path} list repository dispatch",
    )
    sync_impl = '''def sync_repository_to_state(resource_type: str) -> list[dict[str, Any]]:\n    """Return a read-only canonical snapshot for legacy callers."""\n    return list_repository_items(resource_type, active_only=False)\n\n\n'''
    source = regex_once(
        source,
        r'def sync_repository_to_state\(resource_type: str\) -> list\[dict\[str, Any\]\]:\n.*?\n\ndef sync_all_repositories_to_state',
        sync_impl + "def sync_all_repositories_to_state",
        f"{path} read-only sync",
    )
    source = source.replace("CSV repository files remain the admin catalogue for recipes/exercises for now.\n- App state mirrors those catalogues under `recipes` and `exercises` so Supabase-backed\n  readers can see them.\n", "Recipe and Exercise definitions are read from the canonical Supabase Content Repository.\n")
    write(path, source)


def patch_recipe_tests() -> None:
    path = "tests/test_recipe_repository_canonical_cutover.py"
    source = read(path)
    source = source.replace("import components.recipe_repository_runtime as runtime\n", "")
    source = source.replace('RUNTIME = ROOT / "components" / "recipe_repository_runtime.py"\n', "")
    direct_tests = '''    def test_member_page_reads_canonical_repository_directly(self) -> None:\n        source = MEMBER_PAGE.read_text(encoding="utf-8")\n        self.assertIn("list_recipe_repository", source)\n        self.assertIn("def load_recipes():", source)\n        self.assertIn("frame.index = identities", source)\n        self.assertNotIn("pd.read_csv", source)\n        self.assertNotIn("DATA_PATH", source)\n\n'''
    source = regex_once(
        source,
        r'    def test_legacy_dataframe_preserves_numeric_source_ids\(self\) -> None:\n.*?\n    def test_admin_page_has_no_csv_write_path',
        direct_tests + "    def test_admin_page_has_no_csv_write_path",
        f"{path} runtime tests",
    )
    source = regex_once(
        source,
        r'    def test_member_page_remains_compatible_through_runtime\(self\) -> None:\n.*?\n\nif __name__',
        '''    def test_member_page_preserves_assignment_identity_contract(self) -> None:\n        source = MEMBER_PAGE.read_text(encoding="utf-8")\n        self.assertIn("df.index.astype(str).isin(assigned_ids)", source)\n        self.assertIn("int(selected_id) in df.index", source)\n        self.assertNotIn("recipe_repository_runtime", source)\n\n\nif __name__''',
        f"{path} member compatibility test",
    )
    write(path, source)


def patch_exercise_tests() -> None:
    path = "tests/test_exercise_journal_repository_fix_contract.py"
    source = read(path)
    source = regex_once(
        source,
        r'    def test_member_repository_and_profile_builder_read_persistent_exercises\(self\):\n.*?\n    def test_exercise_uses_standard_content_repository_without_new_table',
        '''    def test_member_repository_and_profile_builder_read_persistent_exercises(self):\n        page = source("pages/09_Exercise_Repository.py")\n        contract = source("components/recommendation_contract.py")\n        bootstrap = source("components/__init__.py")\n        self.assertIn("list_exercise_repository", page)\n        self.assertIn("def load_exercises():", page)\n        self.assertIn("frame.index = identities", page)\n        self.assertNotIn("pd.read_csv", page)\n        self.assertNotIn("DATA_PATH", page)\n        self.assertIn("list_exercise_repository(active_only=active_only)", contract)\n        self.assertNotIn("install_exercise_repository_runtime", bootstrap)\n\n    def test_exercise_uses_standard_content_repository_without_new_table''',
        f"{path} member direct read test",
    )
    write(path, source)


def patch_retirement_tests() -> None:
    path = "tests/test_content_repository_legacy_retirement.py"
    source = read(path)
    source = source.replace('EXERCISE_RUNTIME = ROOT / "components" / "exercise_repository_runtime.py"\n', '')
    source = source.replace('RECIPE_RUNTIME = ROOT / "components" / "recipe_repository_runtime.py"\n', '')
    source = replace_once(
        source,
        'ADMIN_RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"\n',
        'ADMIN_RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"\nMEMBER_RECIPE = ROOT / "pages" / "08_Recipe_Repository.py"\nMEMBER_EXERCISE = ROOT / "pages" / "09_Exercise_Repository.py"\nRECOMMENDATION_CONTRACT = ROOT / "components" / "recommendation_contract.py"\n',
        f"{path} member constants",
    )
    replacement = '''    def test_member_pages_read_canonical_modules_without_runtime_shims(self) -> None:\n        recipe = MEMBER_RECIPE.read_text(encoding="utf-8")\n        exercise = MEMBER_EXERCISE.read_text(encoding="utf-8")\n        bootstrap = COMPONENTS_INIT.read_text(encoding="utf-8")\n        contract = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")\n\n        self.assertIn("list_recipe_repository", recipe)\n        self.assertIn("list_exercise_repository", exercise)\n        self.assertNotIn("pd.read_csv", recipe)\n        self.assertNotIn("pd.read_csv", exercise)\n        self.assertNotIn("install_recipe_repository_runtime", bootstrap)\n        self.assertNotIn("install_exercise_repository_runtime", bootstrap)\n        self.assertIn("list_recipe_repository(active_only=active_only)", contract)\n        self.assertIn("list_exercise_repository(active_only=active_only)", contract)\n\n    def test_compatibility_sync_is_read_only_in_core_contract(self) -> None:\n        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")\n        sync_block = source.split("def sync_repository_to_state", 1)[1].split(\n            "def sync_all_repositories_to_state", 1\n        )[0]\n        self.assertIn("read-only canonical snapshot", sync_block)\n        self.assertIn("list_repository_items(resource_type, active_only=False)", sync_block)\n        self.assertNotIn("save_state", sync_block)\n\n'''
    source = regex_once(
        source,
        r'    def test_recipe_and_exercise_compatibility_syncs_are_read_only\(self\) -> None:\n.*?\n    def test_live_repository_modules_have_no_legacy_state_authority',
        replacement + "    def test_live_repository_modules_have_no_legacy_state_authority",
        f"{path} direct retirement tests",
    )
    write(path, source)


def remove_runtime_files() -> None:
    for relative in (
        "components/recipe_repository_runtime.py",
        "components/exercise_repository_runtime.py",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()


def main() -> None:
    patch_member_page(
        "pages/08_Recipe_Repository.py",
        repository_import="from components.recipe_repository import RECIPE_COLUMNS, list_recipe_repository",
        columns_name="RECIPE_COLUMNS",
        list_function="list_recipe_repository",
        loader_name="load_recipes",
        data_filename="recipes.csv",
    )
    patch_member_page(
        "pages/09_Exercise_Repository.py",
        repository_import="from components.exercise_repository import EXERCISE_COLUMNS, list_exercise_repository",
        columns_name="EXERCISE_COLUMNS",
        list_function="list_exercise_repository",
        loader_name="load_exercises",
        data_filename="exercises.csv",
    )
    patch_bootstrap()
    patch_recommendation_contract()
    patch_recipe_tests()
    patch_exercise_tests()
    patch_retirement_tests()
    remove_runtime_files()


if __name__ == "__main__":
    main()
