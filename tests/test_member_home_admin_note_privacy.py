from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MEMBER_HOME = ROOT / "pages" / "02_Member_Home.py"


class MemberHomeAdminNotePrivacyTests(unittest.TestCase):
    def test_member_home_does_not_read_or_render_internal_admin_note(self):
        source = MEMBER_HOME.read_text(encoding="utf-8")
        self.assertNotIn('current_instance.get("admin_note")', source)
        self.assertNotIn("Admin note:", source)
        self.assertNotIn("hm-v990-admin-note", source)

    def test_task_progress_and_due_date_remain_member_visible(self):
        source = MEMBER_HOME.read_text(encoding="utf-8")
        self.assertIn('current_instance.get("due_date")', source)
        self.assertIn("Task progress:", source)
        self.assertIn("hm-v990-task-chip", source)
        self.assertIn(
            "Use Submit / Status after completing all requested tasks to send this to admin for review.",
            source,
        )

    def test_admin_note_storage_contract_is_not_deleted(self):
        assessment_source = (ROOT / "components" / "assessment_instances.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("admin_note", assessment_source)


if __name__ == "__main__":
    unittest.main()
