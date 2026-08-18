from __future__ import annotations

from pathlib import Path
import unittest

from components.runtime_navigation_safety import unwrap_stale_full_app_navigation


ROOT = Path(__file__).resolve().parents[1]


class RuntimeNavigationSafetyTests(unittest.TestCase):
    @staticmethod
    def _patched(previous):
        namespace = {"_ORIGINAL_NAVIGATION": previous}
        exec("def _patched_navigation(*args, **kwargs):\n    return None\n", namespace)
        return namespace["_patched_navigation"]

    def test_native_navigation_is_unchanged(self):
        def native_navigation(*args, **kwargs):
            return None

        self.assertIs(
            unwrap_stale_full_app_navigation(native_navigation),
            native_navigation,
        )

    def test_one_stale_full_app_wrapper_is_removed(self):
        def app_level_navigation(*args, **kwargs):
            return None

        stale = self._patched(app_level_navigation)
        self.assertIs(
            unwrap_stale_full_app_navigation(stale),
            app_level_navigation,
        )

    def test_nested_stale_full_app_wrappers_are_removed(self):
        def app_level_navigation(*args, **kwargs):
            return None

        stale_once = self._patched(app_level_navigation)
        stale_twice = self._patched(stale_once)
        self.assertIs(
            unwrap_stale_full_app_navigation(stale_twice),
            app_level_navigation,
        )

    def test_non_full_app_wrapper_is_preserved(self):
        def _navigation_with_authenticated_root_canonicalization(*args, **kwargs):
            return None

        self.assertIs(
            unwrap_stale_full_app_navigation(
                _navigation_with_authenticated_root_canonicalization
            ),
            _navigation_with_authenticated_root_canonicalization,
        )

    def test_production_cutover_applies_guard_before_compiling_runtime(self):
        source = (
            ROOT / "production_cutover" / "production_live_cutover_app.py"
        ).read_text(encoding="utf-8")
        guard_call = "st.navigation = unwrap_stale_full_app_navigation(st.navigation)"
        source_read = "source_text = SOURCE.read_text(encoding=\"utf-8\")"
        self.assertIn(
            "from components.runtime_navigation_safety import "
            "unwrap_stale_full_app_navigation",
            source,
        )
        self.assertIn(guard_call, source)
        self.assertIn(source_read, source)
        self.assertLess(source.index(guard_call), source.index(source_read))


if __name__ == "__main__":
    unittest.main()
