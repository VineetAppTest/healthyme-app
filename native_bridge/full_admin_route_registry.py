from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from native_bridge.full_member_route_registry import discover_member_page_specs


CORE_ADMIN_FILES = {"10_Admin_Dashboard.py"}

# Current Admin Dashboard destinations. Additional protected Admin pages are
# discovered from the production codebase so nested workflows remain reachable.
DASHBOARD_ADMIN_FILES = (
    "11_Evaluation_Status.py",
    "15_Admin_Recipe_Manager.py",
    "16_Admin_Exercise_Manager.py",
    "17_Admin_User_Manager.py",
    "20_Admin_Question_Manager.py",
    "21_Admin_Response_Editor.py",
    "22_Admin_Daily_Log_Report.py",
    "25_Admin_Reassessment_Manager.py",
    "26_Admin_Review_Queue.py",
    "27_Comparative_NSP_Report.py",
    "28_Admin_Database_Status.py",
    "30_Admin_User_Access_Manager.py",
    "31_Admin_Member_Communication.py",
    "32_Admin_Scheduling.py",
    "33_Admin_Supabase_Auth_Pilot_Readiness.py",
    "34_Admin_NSP_Score_Recalculation.py",
    "34_Admin_Supabase_Auth_Provisioning_Workbench.py",
    "35_Admin_Recommendations_Share.py",
    "36_Admin_Unified_Recommendations.py",
    "38_Admin_Recommendation_Profile_Builder.py",
    "39_Admin_Supplement_Manager.py",
    "41_Admin_Packages.py",
    "45_Admin_Active_Profile_Contract_Diagnostics.py",
    "46_Admin_Profile_Source_Alignment.py",
)


@dataclass(frozen=True)
class AdminRouteSpec:
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
    return re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_") or "Admin_Page"


def _spec(filename: str, checkpoint: str) -> AdminRouteSpec:
    return AdminRouteSpec(
        filename=filename,
        source_path=f"pages/{filename}",
        title=_display_title(filename),
        url_path=_url_path(filename),
        checkpoint=checkpoint,
    )


def _looks_like_admin_page(path: Path) -> bool:
    filename = path.name
    lowered = filename.lower()
    if filename in CORE_ADMIN_FILES:
        return False
    if filename.startswith("01_") or "login" in lowered:
        return False
    if lowered in {"02_member_home.py"}:
        return False

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    # Current HealthyMe Admin pages either call/import require_admin or carry the
    # Admin filename contract. This intentionally preserves direct nested routes
    # that are not linked from the Dashboard but are reachable from Admin flows.
    return "require_admin" in text or "admin_" in lowered


def discover_admin_page_specs(repository_root: Path) -> list[AdminRouteSpec]:
    pages_dir = repository_root / "pages"
    specs: list[AdminRouteSpec] = []
    seen: set[str] = set()

    # Member ownership is authoritative. A file or URL already registered by the
    # Member router must never be rediscovered as an Admin route.
    member_specs = discover_member_page_specs(repository_root)
    member_filenames = {spec.filename for spec in member_specs}
    member_url_paths = {spec.url_path for spec in member_specs}

    for filename in DASHBOARD_ADMIN_FILES:
        if filename in member_filenames:
            continue
        if (pages_dir / filename).is_file():
            specs.append(_spec(filename, "A-dashboard-linked"))
            seen.add(filename)

    for path in sorted(pages_dir.glob("*.py")):
        filename = path.name
        if (
            filename in seen
            or filename in CORE_ADMIN_FILES
            or filename in member_filenames
        ):
            continue
        if not _looks_like_admin_page(path):
            continue
        specs.append(_spec(filename, "B-discovered-protected"))
        seen.add(filename)

    used_paths: set[str] = {
        "Login",
        "Admin_Dashboard",
        "Member_Home",
        "Todays_Plan",
        "Daily_Log",
        "My_Schedule",
        "Member_Plan",
    }
    used_paths.update(member_url_paths)

    unique_specs: list[AdminRouteSpec] = []
    for spec in specs:
        candidate = spec.url_path
        suffix = 2
        while candidate in used_paths:
            candidate = f"{spec.url_path}_{suffix}"
            suffix += 1
        used_paths.add(candidate)
        unique_specs.append(
            AdminRouteSpec(
                filename=spec.filename,
                source_path=spec.source_path,
                title=spec.title,
                url_path=candidate,
                checkpoint=spec.checkpoint,
            )
        )

    return unique_specs
