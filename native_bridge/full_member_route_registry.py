from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


CORE_GATE4_FILES = {
    "02_Member_Home.py",
    "36_Todays_Journey.py",
}

# Checkpoint A: read-oriented Member routes. Gate 4 already owns Member Home
# and Today's Plan, so they are intentionally excluded here.
READ_MEMBER_FILES = (
    "07_My_Profile.py",
    "08_Recipe_Repository.py",
    "09_Exercise_Repository.py",
    "33_My_Schedule.py",
    "37_Member_Plan.py",
    "40_Member_Supplements.py",
)

WRITE_MEMBER_FILES: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemberRouteSpec:
    filename: str
    source_path: str
    title: str
    url_path: str
    checkpoint: str


def _display_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").strip() or stem


def _url_path(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d+_", "", stem)
    return re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_") or "Member_Page"


def _spec(filename: str, checkpoint: str) -> MemberRouteSpec:
    return MemberRouteSpec(
        filename=filename,
        source_path=f"pages/{filename}",
        title=_display_title(filename),
        url_path=_url_path(filename),
        checkpoint=checkpoint,
    )


def discover_member_page_specs(repository_root: Path) -> list[MemberRouteSpec]:
    pages_dir = repository_root / "pages"
    specs: list[MemberRouteSpec] = []
    seen: set[str] = set()

    for filename in READ_MEMBER_FILES:
        if (pages_dir / filename).is_file():
            specs.append(_spec(filename, "A-read"))
            seen.add(filename)

    return specs
