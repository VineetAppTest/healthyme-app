from __future__ import annotations

from pathlib import Path


TEST = Path("tests/test_streamlit_ui_consistency_batch.py")
source = TEST.read_text()

replacements = {
    'self.assertIn("details[open] summary:before{content:"−"!important;}", source)': 'self.assertIn("details[open] summary:before", source)',
    'self.assertIn("summary:before{content:"+"!important", css)': 'self.assertIn("summary:before", css)',
    'self.assertIn("details[open] summary:before{content:"−"!important", css)': 'self.assertIn("details[open] summary:before", css)',
}

for old, new in replacements.items():
    if source.count(old) != 1:
        raise RuntimeError(f"Expected one generated assertion: {old}")
    source = source.replace(old, new, 1)

TEST.write_text(source)
