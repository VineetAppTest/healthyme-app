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

# Checkpoint B: interactive and database-write routes.
WRITE_MEMBER_FILES = (
    "03_LAF_Form.py",
    "04_NSP_Page1.py",
    "05_NSP_Page2.py",
    "06_Submit_Status.py",
    "18_Daily_Log.py",
    "19_Body_Mind_Connection.py",
)


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


def _looks_like_member_page(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    # Current HealthyMe Member pages consistently import or call require_member.
    # The additional Admin-name exclusion prevents an accidentally mixed file
    # from being registered as a Member route.
    return "require_member" in text and "admin" not in path.name.lower()


def discover_member_page_specs(repository_root: Path) -> list[MemberRouteSpec]:
    pages_dir = repository_root / "pages"
    specs: list[MemberRouteSpec] = []
    seen: set[str] = set()

    for filename in READ_MEMBER_FILES:
        if (pages_dir / filename).is_file():
            specs.append(_spec(filename, "A-read"))
            seen.add(filename)

    for filename in WRITE_MEMBER_FILES:
        if (pages_dir / filename).is_file():
            specs.append(_spec(filename, "B-write"))
            seen.add(filename)

    # Checkpoint C: include any additional current Member page without requiring
    # a new deployment iteration. The route still runs through the same native
    # role gate and generic compatibility adapter.
    for path in sorted(pages_dir.glob("*.py")):
        filename = path.name
        if filename in seen or filename in CORE_GATE4_FILES:
            continue
        if filename.startswith("01_") or "login" in filename.lower():
            continue
        if not _looks_like_member_page(path):
            continue
        specs.append(_spec(filename, "C-remaining"))
        seen.add(filename)

    # Make URL paths unique without changing the underlying source filenames.
    used_paths: set[str] = {"Member_Home", "Todays_Plan", "Login", "Admin_Dashboard"}
    unique_specs: list[MemberRouteSpec] = []
    for spec in specs:
        candidate = spec.url_path
        suffix = 2
        while candidate in used_paths:
            candidate = f"{spec.url_path}_{suffix}"
            suffix += 1
        used_paths.add(candidate)
        unique_specs.append(
            MemberRouteSpec(
                filename=spec.filename,
                source_path=spec.source_path,
                title=spec.title,
                url_path=candidate,
                checkpoint=spec.checkpoint,
            )
        )

    return unique_specs
