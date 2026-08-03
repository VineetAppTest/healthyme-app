from __future__ import annotations

import copy
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if "components" not in sys.modules:
    components_package = types.ModuleType("components")
    components_package.__path__ = [str(ROOT / "components")]
    sys.modules["components"] = components_package

from components import supplement_member_allocation as allocation


MAGNESIUM = {
    "id": "suprepo_mag",
    "source_id": "suprepo_mag",
    "supplement_name": "Magnesium",
    "title": "Magnesium",
    "dosage": "200 mg",
    "frequency": "Daily",
    "timing": "Night",
    "instructions": "Take after dinner.",
    "admin_notes": "Repository-only note",
    "legacy_source_id": "legacy-mag",
    "status": "Active",
    "content_version": 3,
}
POTASSIUM = {
    "id": "suprepo_pot",
    "source_id": "suprepo_pot",
    "supplement_name": "Potassium",
    "title": "Potassium",
    "dosage": "100 mg",
    "frequency": "Daily",
    "timing": "Morning",
    "instructions": "Take with water.",
    "admin_notes": "Hidden operational note",
    "legacy_source_id": "legacy-pot",
    "status": "Active",
    "content_version": 2,
}
INACTIVE_SOURCE = {
    **MAGNESIUM,
    "id": "suprepo_old",
    "source_id": "suprepo_old",
    "supplement_name": "Old Supplement",
    "title": "Old Supplement",
    "legacy_source_id": "legacy-old",
    "status": "Inactive",
}


class SupplementMemberAllocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = {
            "users": [
                {
                    "id": "member-1",
                    "name": "Member One",
                    "email": "member@example.com",
                    "role": "member",
                    "is_active": True,
                }
            ],
            "member_supplements": [],
            "supplement_audit_logs": [],
            "notifications": [],
        }

        self.load_patch = mock.patch.object(
            allocation,
            "load_state",
            side_effect=lambda: copy.deepcopy(self.db),
        )

        def save(next_state):
            self.db.clear()
            self.db.update(copy.deepcopy(next_state))

        self.save_patch = mock.patch.object(
            allocation,
            "save_state",
            side_effect=save,
        )
        self.repo_patch = mock.patch.object(
            allocation,
            "list_supplement_repository",
            side_effect=lambda active_only=True: (
                [copy.deepcopy(MAGNESIUM), copy.deepcopy(POTASSIUM)]
                if active_only
                else [
                    copy.deepcopy(MAGNESIUM),
                    copy.deepcopy(POTASSIUM),
                    copy.deepcopy(INACTIVE_SOURCE),
                ]
            ),
        )
        self.load_patch.start()
        self.save_patch.start()
        self.repo_patch.start()
        self.addCleanup(self.load_patch.stop)
        self.addCleanup(self.save_patch.stop)
        self.addCleanup(self.repo_patch.stop)

    def test_new_allocation_uses_canonical_source_and_safe_snapshot(self):
        saved = allocation.save_supplement_member_allocation(
            member_id="member-1",
            source_id="suprepo_mag",
            dosage="250 mg",
            frequency="Daily",
            timing="Night",
            instructions="Take after dinner.",
            start_date="2099-01-01",
            actor_id="admin-1",
        )

        self.assertEqual(saved["source_type"], "supplement_repository")
        self.assertEqual(saved["source_id"], "suprepo_mag")
        self.assertEqual(saved["source_mapping_status"], "canonical")
        self.assertEqual(saved["source_snapshot"]["title"], "Magnesium")
        self.assertNotIn("admin_notes", saved["source_snapshot"])
        self.assertEqual(len(self.db["member_supplements"]), 1)
        self.assertEqual(
            self.db["supplement_audit_logs"][-1]["action"], "created"
        )
        self.assertEqual(
            self.db["notifications"][-1]["kind"],
            "supplement_regimen_updated",
        )

    def test_inactive_source_cannot_be_newly_allocated(self):
        with self.assertRaisesRegex(ValueError, "Only active canonical"):
            allocation.save_supplement_member_allocation(
                member_id="member-1",
                source_id="suprepo_old",
            )

    def test_legacy_allocation_maps_by_repository_legacy_id(self):
        self.db["member_supplements"] = [
            {
                "id": "legacy-mag",
                "member_id": "member-1",
                "supplement_name": "Magnesium",
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        rows = allocation.list_member_supplement_allocations("member-1")

        self.assertEqual(rows[0]["id"], "legacy-mag")
        self.assertEqual(rows[0]["source_id"], "suprepo_mag")
        self.assertEqual(
            rows[0]["source_mapping_status"], "mapped_by_legacy_id"
        )
        self.assertFalse(rows[0]["source_reference_persisted"])

    def test_second_legacy_allocation_maps_by_unique_exact_name(self):
        self.db["member_supplements"] = [
            {
                "id": "another-potassium-id",
                "member_id": "member-1",
                "supplement_name": "Potassium",
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        rows = allocation.list_member_supplement_allocations("member-1")

        self.assertEqual(rows[0]["source_id"], "suprepo_pot")
        self.assertEqual(
            rows[0]["source_mapping_status"], "mapped_by_exact_name"
        )

    def test_unmatched_legacy_allocation_remains_readable(self):
        self.db["member_supplements"] = [
            {
                "id": "unknown-id",
                "member_id": "member-1",
                "supplement_name": "Unknown Supplement",
                "status": "Stopped",
            }
        ]

        rows = allocation.list_member_supplement_allocations("member-1")

        self.assertEqual(rows[0]["id"], "unknown-id")
        self.assertEqual(rows[0]["source_id"], "")
        self.assertEqual(rows[0]["source_mapping_status"], "unmapped_legacy")
        self.assertEqual(rows[0]["status"], "Stopped")

    def test_legacy_mapping_backfill_preserves_allocation_id(self):
        self.db["member_supplements"] = [
            {
                "id": "legacy-mag",
                "member_id": "member-1",
                "supplement_name": "Magnesium",
                "dosage": "200 mg",
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        saved = allocation.save_supplement_member_allocation(
            member_id="member-1",
            source_id="suprepo_mag",
            allocation_id="legacy-mag",
            dosage="250 mg",
            end_date="2099-01-01",
        )

        self.assertEqual(saved["id"], "legacy-mag")
        self.assertEqual(saved["source_id"], "suprepo_mag")
        self.assertEqual(
            self.db["member_supplements"][0]["id"], "legacy-mag"
        )
        self.assertEqual(
            self.db["member_supplements"][0]["source_id"], "suprepo_mag"
        )
        self.assertEqual(
            self.db["member_supplements"][0]["source_mapping_status"],
            "backfilled_mapped_by_legacy_id",
        )

    def test_unmatched_active_legacy_row_can_be_explicitly_mapped(self):
        self.db["member_supplements"] = [
            {
                "id": "unknown-active",
                "member_id": "member-1",
                "supplement_name": "Custom Potassium",
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        saved = allocation.save_supplement_member_allocation(
            member_id="member-1",
            source_id="suprepo_pot",
            allocation_id="unknown-active",
            dosage="100 mg",
            end_date="2099-01-01",
        )

        self.assertEqual(saved["id"], "unknown-active")
        self.assertEqual(saved["source_id"], "suprepo_pot")
        self.assertEqual(
            self.db["member_supplements"][0]["source_mapping_status"],
            "explicit_admin_mapping",
        )

    def test_persisted_source_identity_cannot_change(self):
        self.db["member_supplements"] = [
            {
                "id": "allocation-1",
                "member_id": "member-1",
                "supplement_name": "Magnesium",
                "source_type": "supplement_repository",
                "source_id": "suprepo_mag",
                "source_snapshot": {
                    "source_id": "suprepo_mag",
                    "title": "Magnesium",
                },
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        with self.assertRaisesRegex(
            ValueError, "source identity cannot be changed"
        ):
            allocation.save_supplement_member_allocation(
                member_id="member-1",
                source_id="suprepo_pot",
                allocation_id="allocation-1",
                end_date="2099-01-01",
            )

    def test_unknown_allocation_id_does_not_create_row(self):
        with self.assertRaisesRegex(ValueError, "allocation was not found"):
            allocation.save_supplement_member_allocation(
                member_id="member-1",
                source_id="suprepo_mag",
                allocation_id="missing-allocation",
            )
        self.assertEqual(self.db["member_supplements"], [])

    def test_stop_retains_row_and_backfills_safe_mapping(self):
        self.db["member_supplements"] = [
            {
                "id": "legacy-mag",
                "member_id": "member-1",
                "supplement_name": "Magnesium",
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]

        stopped = allocation.stop_supplement_member_allocation(
            member_id="member-1",
            allocation_id="legacy-mag",
            stop_date="2026-08-04",
            stop_reason="Completed",
        )

        self.assertEqual(stopped["id"], "legacy-mag")
        self.assertEqual(stopped["status"], "Stopped")
        self.assertEqual(stopped["source_id"], "suprepo_mag")
        self.assertEqual(len(self.db["member_supplements"]), 1)
        self.assertEqual(
            self.db["member_supplements"][0]["source_id"], "suprepo_mag"
        )

    def test_update_preserves_frozen_snapshot_title(self):
        self.db["member_supplements"] = [
            {
                "id": "allocation-1",
                "member_id": "member-1",
                "supplement_name": "Magnesium",
                "source_type": "supplement_repository",
                "source_id": "suprepo_mag",
                "source_snapshot": {
                    "source_type": "supplement_repository",
                    "source_id": "suprepo_mag",
                    "supplement_name": "Magnesium",
                    "title": "Magnesium",
                },
                "status": "Active",
                "end_date": "2099-01-01",
            }
        ]
        renamed = {**MAGNESIUM, "supplement_name": "Renamed Magnesium", "title": "Renamed Magnesium"}
        with mock.patch.object(
            allocation,
            "list_supplement_repository",
            side_effect=lambda active_only=True: [copy.deepcopy(renamed), copy.deepcopy(POTASSIUM)],
        ):
            saved = allocation.save_supplement_member_allocation(
                member_id="member-1",
                source_id="suprepo_mag",
                allocation_id="allocation-1",
                dosage="300 mg",
                end_date="2099-01-01",
            )

        self.assertEqual(saved["supplement_name"], "Magnesium")
        self.assertEqual(saved["source_snapshot"]["title"], "Magnesium")

    def test_end_date_cannot_precede_start_date(self):
        with self.assertRaisesRegex(ValueError, "End Date"):
            allocation.save_supplement_member_allocation(
                member_id="member-1",
                source_id="suprepo_mag",
                start_date="2099-02-01",
                end_date="2099-01-01",
            )

    def test_page_and_dashboard_keep_workflows_separate(self):
        page = Path(
            "pages/43_Admin_Supplement_Member_Allocation.py"
        ).read_text(encoding="utf-8")
        dashboard = Path("pages/10_Admin_Dashboard.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("member_supplements", page)
        self.assertIn("save_supplement_member_allocation", page)
        self.assertNotIn("recommendation_shares", page)
        self.assertNotIn("admin_notes", page)
        self.assertIn("_clear_add_form(member_id)", page)
        self.assertIn(
            "pages/42_Admin_Exercise_Member_Allocation.py", dashboard
        )
        self.assertIn(
            "pages/43_Admin_Supplement_Member_Allocation.py", dashboard
        )


if __name__ == "__main__":
    unittest.main()
