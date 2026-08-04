from __future__ import annotations


_MARKER = "_hm_member_saved_days_dispatch_runtime_v3_retired"


def install_member_saved_days_dispatch_runtime() -> None:
    """Retired compatibility hook.

    Saved Days is now rendered directly by ``pages/18_Daily_Log.py``. The former
    runtime wrapper reset the date range to seven days, injected a second Meal
    Section and intercepted the Open saved day button. Older bootstraps still call
    this installer, so the public function remains as an intentional no-op.
    """

    return None
