from __future__ import annotations

from pathlib import Path


TEST = Path("tests/test_meal_profile_builder_phase_b.py")
source = TEST.read_text()

old = '''    def test_expanders_are_standardised_to_one_line_more_details(self) -> None:
        source = EXPANDER_FILE.read_text(encoding="utf-8")
        self.assertIn('text == "More setup details"', source)
        self.assertIn('text.startswith("More details —")', source)
        self.assertIn('label = "More details"', source)
        modular = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("white-space:nowrap", modular)
        self.assertIn("stVerticalBlockBorderWrapper", modular)
'''
new = '''    def test_expanders_use_full_visible_more_details_labels(self) -> None:
        source = EXPANDER_FILE.read_text(encoding="utf-8")
        self.assertIn('text == "More setup details"', source)
        self.assertIn('text.startswith("More details —")', source)
        self.assertIn('label = "More details"', source)
        modular = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("white-space:normal", modular)
        self.assertIn("overflow:visible", modular)
        self.assertIn("text-overflow:clip", modular)
        self.assertNotIn("text-overflow:ellipsis", modular)
        self.assertIn("stVerticalBlockBorderWrapper", modular)
'''

if source.count(old) != 1:
    raise RuntimeError("Expected one stale one-line expander acceptance contract")

TEST.write_text(source.replace(old, new, 1))
