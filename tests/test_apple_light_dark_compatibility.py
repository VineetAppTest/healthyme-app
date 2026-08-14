from __future__ import annotations

import math
from pathlib import Path
import sys
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_bridge.full_admin_route_registry import discover_admin_page_specs
from native_bridge.full_member_route_registry import discover_member_page_specs


CONFIG_PATH = ROOT / ".streamlit" / "config.toml"
COMPAT_PATH = ROOT / "components" / "apple_appearance_compat.py"
UI_COMMON_PATH = ROOT / "components" / "ui_common.py"

WIDGET_MARKERS = (
    "st.text_input(",
    "st.text_area(",
    "st.number_input(",
    "st.date_input(",
    "st.time_input(",
    "st.selectbox(",
    "st.multiselect(",
    "st.checkbox(",
    "st.radio(",
    "st.toggle(",
    "st.slider(",
    "st.file_uploader(",
    "st.data_editor(",
)


def _hex_rgb(value: str) -> tuple[int, int, int]:
    clean = value.removeprefix("#")
    return tuple(int(clean[index : index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(value: str) -> float:
    channels = []
    for channel in _hex_rgb(value):
        normalised = channel / 255
        channels.append(
            normalised / 12.92
            if normalised <= 0.04045
            else math.pow((normalised + 0.055) / 1.055, 2.4)
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


class AppleLightDarkCompatibilityTests(unittest.TestCase):
    def test_streamlit_theme_is_explicitly_light_and_matches_accepted_palette(self):
        with CONFIG_PATH.open("rb") as config_file:
            config = tomllib.load(config_file)

        self.assertEqual(
            config["theme"],
            {
                "base": "light",
                "primaryColor": "#0F766E",
                "backgroundColor": "#FFFDF8",
                "secondaryBackgroundColor": "#FFFFFF",
                "textColor": "#17211F",
            },
        )
        self.assertEqual(config["client"]["toolbarMode"], "minimal")
        self.assertFalse(config["client"]["showSidebarNavigation"])

    def test_shared_compatibility_layer_covers_apple_control_states(self):
        source = COMPAT_PATH.read_text(encoding="utf-8")

        required_contracts = (
            'id="hm-apple-appearance-compat-v1"',
            "prefers-color-scheme: dark",
            "color-scheme:light!important",
            '-webkit-text-fill-color:var(--hm-control-text)!important',
            '-webkit-text-fill-color:var(--hm-control-muted)!important',
            ":-webkit-autofill",
            'aria-disabled="true"',
            'data-baseweb="popover"',
            'data-baseweb="calendar"',
            'data-testid="stFileUploaderDropzone"',
            "input::-webkit-calendar-picker-indicator",
        )
        for contract in required_contracts:
            self.assertIn(contract, source)

        for test_id in (
            "stTextInput",
            "stTextArea",
            "stNumberInput",
            "stDateInput",
            "stTimeInput",
            "stSelectbox",
            "stMultiSelect",
            "stCheckbox",
            "stRadio",
            "stToggle",
            "stSlider",
            "stDataFrame",
            "stDataEditor",
        ):
            self.assertIn(f'data-testid="{test_id}"', source)

    def test_global_layer_does_not_remove_native_apple_control_affordances(self):
        source = COMPAT_PATH.read_text(encoding="utf-8")

        self.assertNotIn("appearance:none", source)
        self.assertNotIn("-webkit-appearance:none", source)
        for layout_property in (
            "min-height:",
            "max-height:",
            "min-width:",
            "max-width:",
            "border-radius:",
            "padding:",
        ):
            self.assertNotIn(layout_property, source)

    def test_global_style_injection_always_renders_apple_compatibility_after_luxe_css(self):
        source = UI_COMMON_PATH.read_text(encoding="utf-8")
        function_start = source.index("def inject_global_styles():")
        function_end = source.index("def apply_luxe_theme():", function_start)
        function_source = source[function_start:function_end]

        self.assertLess(
            function_source.index("st.markdown(LUXE_CSS"),
            function_source.index("render_apple_appearance_compat()"),
        )

    def test_every_registered_form_page_uses_shared_global_styles(self):
        page_paths = {
            ROOT / spec.source_path
            for spec in (
                discover_member_page_specs(ROOT) + discover_admin_page_specs(ROOT)
            )
            if spec.source_path.startswith("pages/")
        }
        page_paths.update(
            {
                ROOT / "pages" / "01_Login.py",
                ROOT / "pages" / "02_Member_Home.py",
                ROOT / "pages" / "10_Admin_Dashboard.py",
                ROOT / "pages" / "36_Todays_Journey.py",
            }
        )

        form_pages = []
        missing = []
        for path in sorted(page_paths):
            source = path.read_text(encoding="utf-8")
            if not any(marker in source for marker in WIDGET_MARKERS):
                continue
            form_pages.append(path.relative_to(ROOT).as_posix())
            if "inject_global_styles()" not in source:
                missing.append(path.relative_to(ROOT).as_posix())

        self.assertGreaterEqual(len(form_pages), 35)
        self.assertEqual(missing, [])

    def test_accepted_text_and_placeholder_colours_meet_contrast_target(self):
        self.assertGreaterEqual(_contrast_ratio("#0F172A", "#FFFFFF"), 4.5)
        self.assertGreaterEqual(_contrast_ratio("#64748B", "#FFFFFF"), 4.5)
        self.assertGreaterEqual(_contrast_ratio("#475569", "#F8F5EF"), 4.5)

    def test_daily_log_specific_protection_remains_during_global_rollout(self):
        page_source = (ROOT / "pages" / "18_Daily_Log.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("render_daily_log_field_contrast()", page_source)


if __name__ == "__main__":
    unittest.main()
