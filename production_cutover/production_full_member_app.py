from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "native_bridge" / "native_bridge_full_member_app.py"

source_text = SOURCE.read_text(encoding="utf-8")
expected_build = 'BUILD = "H13Q7-native-full-member-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13Q6-native-gate4-real-todays-plan-v1"'

if expected_build not in source_text or expected_rollback not in source_text:
    raise RuntimeError(
        "The accepted H13Q7 Member runtime changed unexpectedly. "
        "Stop deployment and compare against PR #183."
    )

source_text = source_text.replace(
    expected_build,
    'BUILD = "H13Q9-production-parity-full-member-v1"',
    1,
)
source_text = source_text.replace(
    expected_rollback,
    'ROLLBACK_BUILD = "H13Q8-production-parity-native-router-v1"',
    1,
)
source_text = source_text.replace(
    "Consolidated Gate 5–7 integration: the accepted Gate 4 identity and role "
    '"router now registers the current read, write and remaining Member pages."',
    "H13Q9 Step 2: the accepted H13Q8 native identity and role router now "
    '"connects the complete enabled HealthyMe Member application."',
    1,
)

exec(
    compile(source_text, str(SOURCE), "exec"),
    {
        "__name__": "__hm_h13q9_production_full_member__",
        "__file__": str(SOURCE),
        "__package__": None,
    },
)
