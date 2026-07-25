from __future__ import annotations

import json
import traceback
from pathlib import Path

import streamlit as st


BUILD = "H13Q9-production-parity-full-member-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "native_bridge" / "native_bridge_full_member_app.py"

st.set_page_config(
    page_title="HealthyMe H13Q9 Full Member",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
startup_status = st.empty()
startup_status.info(f"Starting {BUILD} — production entry loaded.")

try:
    source_text = SOURCE.read_text(encoding="utf-8")
except Exception as exc:
    startup_status.error("H13Q9 could not read the accepted full-Member runtime.")
    st.exception(exc)
    st.stop()

expected_build = 'BUILD = "H13Q7-native-full-member-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13Q6-native-gate4-real-todays-plan-v1"'

if expected_build not in source_text or expected_rollback not in source_text:
    startup_status.error("H13Q9 source-integrity check failed before runtime execution.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "source": str(SOURCE),
                "expected_build_marker_found": expected_build in source_text,
                "expected_rollback_marker_found": expected_rollback in source_text,
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.stop()

source_text = source_text.replace(
    expected_build,
    f'BUILD = "{BUILD}"',
    1,
)
source_text = source_text.replace(
    expected_rollback,
    'ROLLBACK_BUILD = "H13Q8-production-parity-native-router-v1"',
    1,
)

# This entry owns page configuration so the accepted nested runtime must not call
# st.set_page_config a second time. All other Streamlit behaviour remains intact.
original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
startup_status.info(f"Starting {BUILD} — loading accepted Member router.")

try:
    exec(
        compile(source_text, str(SOURCE), "exec"),
        {
            "__name__": "__hm_h13q9_production_full_member__",
            "__file__": str(SOURCE),
            "__package__": None,
        },
    )
except Exception as exc:
    startup_status.error("H13Q9 runtime startup failed before the requested page completed.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "source": str(SOURCE),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    st.stop()
finally:
    st.set_page_config = original_set_page_config
