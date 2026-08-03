from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "users_workflow_authority_trace_batch2_2026-08-03.md"
STORAGE = ROOT / "components" / "storage_backend.py"
NORMALIZED = ROOT / "components" / "normalized_store.py"
DB = ROOT / "components" / "db.py"
APP = ROOT / "app.py"
AUTH_UI = ROOT / "native_bridge" / "root_authorization_ui.py"
AUTH_UI_PRODUCTION = ROOT / "native_bridge" / "root_authorization_ui_h13r7e.py"


class UsersWorkflowAuthorityTraceBatch2Tests(unittest.TestCase):
    def test_document_freezes_read_only_boundary_and_baseline(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "This batch is a read-only authority trace",
            "Users | 15 | 15 | 0 | 0",
            "Workflow | 15 | 15 | 0 | 0",
            "The table currently has 4 rows: 1 active, 3 expired and 0 revoked",
            "No authority cutover is approved by this trace",
            "No authentication, workflow, session or data migration is included",
        ):
            self.assertIn(required, source)

    def test_storage_backend_exposes_current_overlay_and_dual_write_order(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("def _overlay_normalized_users_workflow", source)
        self.assertIn("load_users_workflow_from_normalized", source)
        self.assertIn('db["users"] = users', source)
        self.assertIn('db["workflow"] = workflow', source)
        self.assertIn("def save_state", source)
        self.assertLess(
            source.index("ok, msg = _save_to_supabase(db)"),
            source.index("sync_users_workflow_to_normalized(db)"),
        )
        self.assertIn("LOCAL_DB_PATH.write_text", source)
        self.assertIn("def push_local_data_to_supabase", source)

    def test_normalized_store_owns_dedicated_table_adapter(self) -> None:
        source = NORMALIZED.read_text(encoding="utf-8")
        for required in (
            '.table("hm_users")',
            '.table("hm_workflow")',
            "def load_users_workflow_from_normalized",
            "def sync_users_workflow_to_normalized",
            "def upsert_user_to_normalized",
            "def find_user_by_email_fast",
            "caller should fallback",
            '"workflow_status": "not_started"',
        ):
            self.assertIn(required, source)

    def test_compatibility_db_still_owns_user_workflow_and_login_session_writes(self) -> None:
        source = DB.read_text(encoding="utf-8")
        for required in (
            "def ensure_default_admin",
            "def create_login_session",
            'db.setdefault("login_sessions", {})',
            "def clear_login_session",
            "def ensure_oidc_user_record",
            "def change_password",
            "def create_user",
            "def normalize_workflow",
            "def update_workflow",
            "def submit_member_for_review_once",
            "save_db(db)",
        ):
            self.assertIn(required, source)

    def test_native_identity_and_authorization_routes_are_frozen(self) -> None:
        app_source = APP.read_text(encoding="utf-8")
        self.assertIn("st.user", app_source)
        self.assertIn("native_bridge", app_source)
        for path in (AUTH_UI, AUTH_UI_PRODUCTION):
            source = path.read_text(encoding="utf-8")
            self.assertIn("SUPABASE_URL", source)
            self.assertIn("SUPABASE_ANON_KEY", source)
            self.assertIn("render_root_authorization_ui", source)
            self.assertIn("st.user", source)

    def test_flutter_direct_read_boundary_is_recorded(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "VineetAppTest/healthyme-flutter-member",
            "a2de87cb37bea2dfecacbbb04cf03069f505077a",
            "lib/repositories/member_repository.dart",
            "MemberRepository.fetchCurrentMemberByEmail()",
            "directly reads",
            "`hm_users`",
            "`hm_workflow`",
        ):
            self.assertIn(required, source)

    def test_every_runtime_authority_path_is_classified_in_document(self) -> None:
        tokens = (
            "hm_users",
            "hm_workflow",
            "hm_streamlit_auth_sessions",
            'get("users"',
            "get('users'",
            '["users"]',
            "['users']",
            'setdefault("users"',
            "setdefault('users'",
            'get("workflow"',
            "get('workflow'",
            '["workflow"]',
            "['workflow']",
            'setdefault("workflow"',
            "setdefault('workflow'",
            'get("auth_sessions"',
            "get('auth_sessions'",
            '["auth_sessions"]',
            "['auth_sessions']",
            'setdefault("auth_sessions"',
            "setdefault('auth_sessions'",
            'get("login_sessions"',
            "get('login_sessions'",
            '["login_sessions"]',
            "['login_sessions']",
            'setdefault("login_sessions"',
            "setdefault('login_sessions'",
        )
        paths: list[pathlib.Path] = [APP]
        for folder_name in ("components", "pages", "native_bridge", "production_cutover"):
            folder = ROOT / folder_name
            if folder.exists():
                paths.extend(folder.rglob("*.py"))

        hits: list[str] = []
        for path in paths:
            source = path.read_text(encoding="utf-8", errors="ignore")
            if any(token in source for token in tokens):
                hits.append(str(path.relative_to(ROOT)))

        document = DOC.read_text(encoding="utf-8")
        missing = [path for path in sorted(set(hits)) if f"`{path}`" not in document]
        self.assertEqual(
            missing,
            [],
            "Unclassified Users/Workflow/session runtime paths: " + ", ".join(missing),
        )

    def test_trace_does_not_claim_session_or_auth_cutover(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        self.assertIn("Session migration scopes", source)
        self.assertIn("must not silently retire or reinterpret any session store", source)
        self.assertIn("Do not remove either shared collection immediately", source)


if __name__ == "__main__":
    unittest.main()
