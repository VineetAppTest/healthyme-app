from __future__ import annotations

import unittest
from unittest.mock import patch

from components import profile_builder_module_store_canonical as store


class ProfileBuilderPhase2LegacySnapshotSaveTests(unittest.TestCase):
    def test_unresolved_legacy_snapshot_survives_module_normalisation(self):
        item = {
            "item_type": "exercise",
            "day_number": 1,
            "slot_name": "Exercise Regime",
            "item_order": 1,
            "reference_label": "Ambiguous Legacy Exercise",
            "instruction": "Continue carefully",
            "scheduled_time": "Morning",
            "source_id": "",
            "source_type": "exercise_repository",
            "source_snapshot": {
                "source_type": "exercise_repository",
                "title": "Ambiguous Legacy Exercise",
                "benefits": "Historical benefit",
                "status": "historical",
            },
            "source_admin_overrides": {
                "benefits": "Member-specific historical context"
            },
        }

        with (
            patch.object(
                store,
                "profile_source_snapshot_columns_ready",
                return_value=True,
            ),
            patch.object(
                store,
                "source_storage_payload_for_row",
                return_value={},
            ),
        ):
            rows, snapshot_count = store._normalise_item_rows(
                "profile-1",
                "exercise",
                [item],
                "2026-08-03T00:00:00+00:00",
            )

        self.assertEqual(snapshot_count, 1)
        self.assertEqual(len(rows), 1)
        saved = rows[0]
        self.assertEqual(saved["source_id"], "")
        self.assertEqual(saved["source_type"], "exercise_repository")
        self.assertEqual(saved["source_label"], "Ambiguous Legacy Exercise")
        self.assertEqual(
            saved["source_snapshot"]["benefits"],
            "Member-specific historical context",
        )
        self.assertEqual(
            saved["source_snapshot"]["source_original_snapshot"]["benefits"],
            "Historical benefit",
        )


if __name__ == "__main__":
    unittest.main()
