from __future__ import annotations

import json
import traceback
from pathlib import Path

import streamlit as st


BUILD = "H13R0-production-native-member-auth-only-v1"
ROLLBACK_BUILD = "H13Q9-production-parity-full-member-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "native_bridge" / "native_bridge_full_member_app.py"

st.set_page_config(
    page_title="HealthyMe H13R0 Native Member",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from components.native_member_auth import install_native_member_adapters

    adapter_status = install_native_member_adapters()
except Exception as exc:
    st.error("H13R0 could not install the native Member authentication adapters.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    st.stop()

try:
    source_text = SOURCE.read_text(encoding="utf-8")
except Exception as exc:
    st.error("H13R0 could not read the accepted H13Q9 full-Member runtime.")
    st.exception(exc)
    st.stop()

expected_build = 'BUILD = "H13Q7-native-full-member-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13Q6-native-gate4-real-todays-plan-v1"'

if expected_build not in source_text or expected_rollback not in source_text:
    st.error("H13R0 source-integrity check failed before runtime execution.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "source": str(SOURCE),
                "expected_build_marker_found": expected_build in source_text,
                "expected_rollback_marker_found": expected_rollback in source_text,
                "adapter_status": adapter_status,
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
    f'ROLLBACK_BUILD = "{ROLLBACK_BUILD}"',
    1,
)

# Surface the Step 3 retirement state in the existing diagnostics without
# changing the accepted Member page layouts.
source_text = source_text.replace(
    '"legacy_page_guard_used": False,',
    '"legacy_page_guard_used": False,\n'
    '                "legacy_member_auth_retired": True,\n'
    '                "native_member_guard_installed": True,\n'
    '                "member_password_restore_used": False,',
)
source_text = source_text.replace(
    '"durable_auth_session_used": False,',
    '"durable_auth_session_used": False,\n'
    '                "native_member_logout_installed": True,',
)

original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None

try:
    exec(
        compile(source_text, str(SOURCE), "exec"),
        {
            "__name__": "__hm_h13r0_native_member_retired__",
            "__file__": str(SOURCE),
            "__package__": None,
        },
    )
except Exception as exc:
    st.error("H13R0 runtime failed before the requested page completed.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "adapter_status": adapter_status,
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
