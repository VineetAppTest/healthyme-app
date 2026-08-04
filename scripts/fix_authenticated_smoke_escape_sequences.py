from __future__ import annotations

from pathlib import Path


path = Path("scripts/apply_authenticated_smoke_corrections.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    'return html.unescape(str(value or "").replace("<br>", "\\n"))',
    'return html.unescape(str(value or "").replace("<br>", "\\\\n"))',
)
text = text.replace(
    'joined = lambda items: "\\n".join(value for value in items if value)',
    'joined = lambda items: "\\\\n".join(value for value in items if value)',
)
path.write_text(text, encoding="utf-8")
print("Authenticated smoke generated newline literals corrected.")
