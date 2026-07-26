from __future__ import annotations

from pathlib import Path


BUILD = "H13R2-production-cutover-v1"
ROLLBACK_BUILD = "H13R1-production-native-full-app-v1"
SOURCE = Path(__file__).resolve().with_name("production_native_full_app.py")

source_text = SOURCE.read_text(encoding="utf-8")

expected_build = 'BUILD = "H13R1-production-native-full-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13R0-production-native-member-auth-only-v1"'

if expected_build not in source_text:
    raise RuntimeError("H13R2 source-integrity check failed: accepted H13R1 build marker missing.")
if expected_rollback not in source_text:
    raise RuntimeError("H13R2 source-integrity check failed: accepted H13R1 rollback marker missing.")

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
    'page_title="HealthyMe H13R2 Production Native Full App"',
    1,
)
source_text = source_text.replace(
    '"Step 4 integration: the accepted native identity and role router now "\n'
    '        "registers the real Member and Admin applications."',
    '"Production cutover: the accepted native identity and role router now "\n'
    '        "runs the real HealthyMe Member and Admin applications."',
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
    "        '                \"production_entry\": \"app.py\",',\n"
)
if diagnostic_source_marker not in source_text:
    raise RuntimeError(
        "H13R2 source-integrity check failed: H13R1 diagnostic marker missing."
    )
source_text = source_text.replace(
    diagnostic_source_marker,
    diagnostic_source_replacement,
    1,
)

source_text = source_text.replace(
    '__hm_h13r1_native_full_app__',
    '__hm_h13r2_production_cutover__',
    1,
)

compiled_source = compile(source_text, str(SOURCE), "exec")
exec(
    compiled_source,
    {
        "__name__": "__hm_h13r2_production_cutover__",
        "__file__": str(SOURCE),
        "__package__": None,
    },
)
