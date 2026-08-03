from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "users_workflow_single_authority_target_design_batch2a_2026-08-03.md"
GATE3_DOC = ROOT / "docs" / "users_gate3_write_cutover_2026-08-03.md"
GATE4_DOC = ROOT / "docs" / "workflow_gate4_write_cutover_2026-08-03.md"
STORAGE = ROOT / "components" / "storage_backend.py"
NORMALIZED = ROOT / "components" / "normalized_store.py"
DB = ROOT / "components" / "db.py"
ROLE_MODEL = ROOT / "components" / "admin_role_model.py"


class UsersWorkflowTargetDesignBatch2ATests(unittest.TestCase):
    def test_design_only_boundary_is_explicit(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "Design only — no implementation",
            "No runtime, SQL, RLS, RPC, authentication or Flutter change is included",
            "The existing shared Users and Workflow collections remain untouched in this design PR",
            "This PR approves a design and implementation order only",
        ):
            self.assertIn(required, source)

    def test_single_authority_target_is_frozen(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "`hm_users` is the sole live User authority",
            "`hm_workflow` is the sole live Workflow authority",
            "Compatibility projection is non-authoritative and temporary",
            "No identity or Workflow write may fall back to shared JSON or `data/db.json`",
            "Session migration remains a separate batch",
        ):
            self.assertIn(required, source)

    def test_security_blocker_precedes_cutover(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "Mandatory security blocker",
            "hm_flutter_upsert_nsp_workflow",
            "SECURITY DEFINER",
            "executable by `anon` and `authenticated`",
            "First implementation gate: Flutter Workflow RPC permission hardening",
            "No broader authority cutover may begin",
            "reject arbitrary member IDs",
        ):
            self.assertIn(required, source)

    def test_user_workflow_and_session_scopes_are_separate(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "User target contract",
            "Workflow target contract",
            "Session migration scopes",
            "Password retirement",
            "Default-Admin recovery",
            "Demo Mode",
            "Later batch — Sessions",
        ):
            self.assertIn(required, source)

    def test_flutter_boundary_and_mobile_dual_write_are_recorded(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "VineetAppTest/healthyme-flutter-member",
            "a2de87cb37bea2dfecacbbb04cf03069f505077a",
            "falls back to shared-state Workflow",
            "updates shared-state Workflow during LAF saves",
            "preserve canonical direct reads",
            "Remove the shared-state Workflow fallback from `hm_flutter_get_laf()` only after",
        ):
            self.assertIn(required, source)

    def test_target_requires_fail_closed_verified_writes(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "execute transactionally in the database",
            "capture before/after event evidence",
            "fresh read-after-write verification",
            "Canonical write failure means the business operation fails visibly",
            "cannot report success after writing a different store",
        ):
            self.assertIn(required, source)

    def test_rollout_order_is_complete(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for gate in range(1, 9):
            self.assertIn(f"### Gate {gate} —", source)
        self.assertLess(
            source.index("### Gate 1 — Flutter Workflow RPC permission hardening"),
            source.index("### Gate 3 — User write cutover"),
        )
        self.assertLess(
            source.index("### Gate 4 — Workflow write cutover"),
            source.index("### Gate 7 — Projection retirement"),
        )

    def test_current_runtime_reflects_staged_gate4_cutover(self) -> None:
        storage = STORAGE.read_text(encoding="utf-8")
        normalized = NORMALIZED.read_text(encoding="utf-8")
        db_source = DB.read_text(encoding="utf-8")
        role_source = ROLE_MODEL.read_text(encoding="utf-8")
        gate3 = GATE3_DOC.read_text(encoding="utf-8")
        gate4 = GATE4_DOC.read_text(encoding="utf-8")

        self.assertIn("def _overlay_normalized_users_workflow", storage)
        self.assertIn("commit_identity_and_state", storage)
        self.assertIn("workflow_changed = _workflow_projection_changed(previous, db)", storage)
        self.assertNotIn("sync_workflow_to_normalized", storage)
        self.assertIn("if identity_changed and not configured:", storage)
        self.assertIn("raise RuntimeError", storage)
        self.assertIn("LOCAL_DB_PATH.write_text", storage)
        self.assertIn("def commit_users_and_state", normalized)
        self.assertIn("def commit_identity_and_state", normalized)
        self.assertIn("def sync_users_workflow_to_normalized", normalized)
        self.assertNotIn('.table("hm_workflow").upsert(', normalized)
        self.assertIn("def ensure_default_admin", db_source)
        self.assertIn("def create_login_session", db_source)
        self.assertIn("Loaded user from legacy local store", role_source)
        self.assertIn("Gate 3 cuts over the **User write authority only**", gate3)
        self.assertIn("Gate 4 cuts over the **Streamlit/shared-state Workflow write authority**", gate4)
        self.assertIn("Sessions, password retirement, default-Admin redesign", gate4)


if __name__ == "__main__":
    unittest.main()
