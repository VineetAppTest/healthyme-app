from __future__ import annotations

from pathlib import Path


BUILD = "H13R4-production-single-visible-login-v1"
ROLLBACK_BUILD = "H13R2-production-cutover-v1"
SOURCE = Path(__file__).resolve().with_name("production_native_full_app.py")

source_text = SOURCE.read_text(encoding="utf-8")

expected_build = 'BUILD = "H13R1-production-native-full-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13R0-production-native-member-auth-only-v1"'

if expected_build not in source_text:
    raise RuntimeError("H13R4 source-integrity check failed: accepted H13R1 build marker missing.")
if expected_rollback not in source_text:
    raise RuntimeError("H13R4 source-integrity check failed: accepted H13R1 rollback marker missing.")

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
source_text = source_text.replace(
    'page_title="HealthyMe H13R1 Native Full App"',
    'page_title="HealthyMe Login"',
    1,
)
source_text = source_text.replace(
    '"Step 4 integration: the accepted native identity and role router now "\n'
    '        "registers the real Member and Admin applications."',
    '"Production cutover: the accepted native identity and role router now "\n'
    '        "runs the real HealthyMe Member and Admin applications."',
    1,
)

# Replace the visible launcher page with an immediate native OIDC handoff.
# The user sees only the HealthyMe credential screen rendered by the root authorizer.
title_patch_marker = (
    "    source_text = source_text.replace(\n"
    "        'st.title(\"HealthyMe native full-member router\")',\n"
    "        'st.title(\"HealthyMe native full application router\")',\n"
    "    )\n"
)
if title_patch_marker not in source_text:
    raise RuntimeError(
        "H13R4 source-integrity check failed: H13R1 Login title transform missing."
    )

production_login_ui = '''    st.markdown(
        """
        <style>
        .hm-login-handoff{
            min-height:58vh;display:flex;align-items:center;justify-content:center;
            color:#315e50;font-size:.95rem;font-weight:650;
        }
        </style>
        <div class="hm-login-handoff">Opening secure HealthyMe login…</div>
        """,
        unsafe_allow_html=True,
    )
    st.login(provider)
    st.stop()
'''
login_ui_transform = (
    title_patch_marker
    + "\n"
    + "    login_ui_start = source_text.index(\n"
    + "        '    st.title(\"HealthyMe native full application router\")'\n"
    + "    )\n"
    + "    login_ui_end = source_text.index(\n"
    + "        \"\\n\\n\\ndef _admin_page() -> None:\",\n"
    + "        login_ui_start,\n"
    + "    )\n"
    + "    source_text = (\n"
    + "        source_text[:login_ui_start]\n"
    + "        + " + repr(production_login_ui) + "\n"
    + "        + source_text[login_ui_end:]\n"
    + "    )\n"
)
source_text = source_text.replace(
    title_patch_marker,
    login_ui_transform,
    1,
)

# H13R1 builds its final diagnostics through a quoted source-transformation
# string. Patch that source-code string with escaped newlines so the H13R1
# wrapper remains syntactically valid before it performs its own transform.
diagnostic_source_marker = (
    "        '                \"nutritionist_role_promoted_to_admin\": False,',\n"
)
diagnostic_source_replacement = (
    "        '                \"nutritionist_role_promoted_to_admin\": False,\\n'\n"
    "        '                \"production_cutover_active\": True,\\n'\n"
    "        '                \"single_visible_login_active\": True,\\n'\n"
    "        '                \"production_entry\": \"app.py\",',\n"
)
if diagnostic_source_marker not in source_text:
    raise RuntimeError(
        "H13R4 source-integrity check failed: H13R1 diagnostic marker missing."
    )
source_text = source_text.replace(
    diagnostic_source_marker,
    diagnostic_source_replacement,
    1,
)

source_text = source_text.replace(
    '__hm_h13r1_native_full_app__',
    '__hm_h13r4_production_single_visible_login__',
    1,
)

compiled_source = compile(source_text, str(SOURCE), "exec")
exec(
    compiled_source,
    {
        "__name__": "__hm_h13r4_production_single_visible_login__",
        "__file__": str(SOURCE),
        "__package__": None,
    },
)
