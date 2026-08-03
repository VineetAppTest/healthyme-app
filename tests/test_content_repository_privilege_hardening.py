from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260803101500_harden_content_repository_service_role.sql"
)


class ContentRepositoryPrivilegeHardeningTests(unittest.TestCase):
    def test_service_role_is_reset_before_narrow_grants(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8").lower()

        item_revoke = (
            "revoke all on table public.hm_content_repository_items "
            "from service_role"
        )
        event_revoke = (
            "revoke all on table public.hm_content_repository_events "
            "from service_role"
        )
        item_grant = (
            "grant select, insert, update on table "
            "public.hm_content_repository_items to service_role"
        )
        event_grant = (
            "grant select, insert on table "
            "public.hm_content_repository_events to service_role"
        )

        self.assertIn(item_revoke, sql)
        self.assertIn(event_revoke, sql)
        self.assertIn(item_grant, sql)
        self.assertIn(event_grant, sql)
        self.assertLess(sql.index(item_revoke), sql.index(item_grant))
        self.assertLess(sql.index(event_revoke), sql.index(event_grant))
        self.assertNotIn("grant delete", sql)
        self.assertNotIn("grant truncate", sql)


if __name__ == "__main__":
    unittest.main()
