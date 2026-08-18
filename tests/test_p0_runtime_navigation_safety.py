from __future__ import annotations

import unittest

from components.runtime_navigation_safety import unwrap_stale_full_app_navigation


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


if __name__ == "__main__":
    unittest.main()
