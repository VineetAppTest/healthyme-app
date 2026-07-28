from __future__ import annotations

from pathlib import Path


BUILD = "H13R5A-production-scoped-profile-builder-staff-v1"
ROLLBACK_BUILD = "H13R5-production-direct-login-v1"
SOURCE = Path(__file__).resolve().with_name("production_native_full_app.py")

source_text = SOURCE.read_text(encoding="utf-8")

expected_build = 'BUILD = "H13R1-production-native-full-app-v1"'
expected_rollback = 'ROLLBACK_BUILD = "H13R0-production-native-member-auth-only-v1"'

if expected_build not in source_text:
    raise RuntimeError("H13R5A source-integrity check failed: accepted H13R1 build marker missing.")
if expected_rollback not in source_text:
    raise RuntimeError("H13R5A source-integrity check failed: accepted H13R1 rollback marker missing.")

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

# Remove the visible launcher and handoff presentation. Streamlit initiates the
# existing native OIDC flow immediately, so the first visible page is the HealthyMe
# email/password screen rendered by the root authorizer.
title_patch_marker = (
    "    source_text = source_text.replace(\n"
    "        'st.title(\"HealthyMe native full-member router\")',\n"
    "        'st.title(\"HealthyMe native full application router\")',\n"
    "    )\n"
)
if title_patch_marker not in source_text:
    raise RuntimeError(
        "H13R5A source-integrity check failed: H13R1 Login title transform missing."
    )

production_login_ui = '''    st.login(provider)
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

# Permit the Nutritionist role only on the Recommendation Profile Builder route.
# The general Admin role model and all other Admin routes remain unchanged.
admin_route_marker = '''def _render_admin_route(spec: AdminRouteSpec) -> None:
    context = _gate4_context()
    if str(context.get("role_category") or "") != "Admin":
'''
admin_route_replacement = '''def _render_admin_route(spec: AdminRouteSpec) -> None:
    context = _gate4_context()
    role_category = str(context.get("role_category") or "")
    nutritionist_profile_builder = (
        role_category == "Nutritionist"
        and spec.url_path == "Admin_Recommendation_Profile_Builder"
    )
    if role_category != "Admin" and not nutritionist_profile_builder:
'''
if admin_route_marker not in source_text:
    raise RuntimeError(
        "H13R5A source-integrity check failed: Admin route role marker missing."
    )
source_text = source_text.replace(
    admin_route_marker,
    admin_route_replacement,
    1,
)

# Production Native Full App reads and compiles the accepted Gate 4 source. Add a
# narrow Nutritionist role category during that compile without promoting the role
# to Admin in the shared role model.
gate4_read_marker = '    gate4_text = path.read_text(encoding="utf-8")\n'
gate4_role_old = '''def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    return "Unsupported"
'''
gate4_role_new = '''def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    if str(role or "").strip().lower() == "nutritionist":
        return "Nutritionist"
    return "Unsupported"
'''
gate4_role_patch = (
    gate4_read_marker
    + "    gate4_role_old = " + repr(gate4_role_old) + "\n"
    + "    gate4_role_new = " + repr(gate4_role_new) + "\n"
    + "    if gate4_role_old not in gate4_text:\n"
    + "        raise RuntimeError(\"H13R5A Gate 4 role category marker is missing.\")\n"
    + "    gate4_text = gate4_text.replace(gate4_role_old, gate4_role_new, 1)\n"
)
if gate4_read_marker not in source_text:
    raise RuntimeError(
        "H13R5A source-integrity check failed: Gate 4 source-read marker missing."
    )
source_text = source_text.replace(
    gate4_read_marker,
    gate4_role_patch,
    1,
)

admin_routing_marker = '''    new_admin_block = '''if role_category == "Admin":
    _clear_derived_application_context()
    ROUTER_CONTEXT["derived_application_context_applied"] = False
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False
    allowed_admin_paths = set(
        ROUTER_CONTEXT.get("allowed_admin_paths") or {admin_page.url_path}
    )
    if selected_path not in allowed_admin_paths:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()
'''
'''
admin_routing_replacement = '''    new_admin_block = '''if role_category == "Admin":
    _clear_derived_application_context()
    ROUTER_CONTEXT["derived_application_context_applied"] = False
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False
    allowed_admin_paths = set(
        ROUTER_CONTEXT.get("allowed_admin_paths") or {admin_page.url_path}
    )
    if selected_path not in allowed_admin_paths:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()

if role_category == "Nutritionist":
    try:
        apply_app_user_to_session(
            app_user,
            email=email,
            auth_provider="supabase",
            auth_user_id=subject,
        )
    except Exception as exc:
        _show_role_resolution_failure(
            role_lookup_ok=True,
            lookup_message=(
                f"{type(exc).__name__}: Nutritionist compatibility context could not be built."
            ),
        )
    ROUTER_CONTEXT["derived_application_context_applied"] = True
    ROUTER_CONTEXT["nutritionist_profile_builder_access_active"] = True
    allowed_nutritionist_paths = {"Admin_Recommendation_Profile_Builder"}
    if selected_path not in allowed_nutritionist_paths:
        st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")
    selected_page.run()
    st.stop()
'''
'''
if admin_routing_marker not in source_text:
    raise RuntimeError(
        "H13R5A source-integrity check failed: Admin routing transform marker missing."
    )
source_text = source_text.replace(
    admin_routing_marker,
    admin_routing_replacement,
    1,
)

# H13R1 builds its final diagnostics through a quoted source-transformation string.
diagnostic_source_marker = (
    "        '                \"nutritionist_role_promoted_to_admin\": False,',\n"
)
diagnostic_source_replacement = (
    "        '                \"nutritionist_role_promoted_to_admin\": False,\\n'\n"
    "        '                \"nutritionist_profile_builder_access_active\": True,\\n'\n"
    "        '                \"nutritionist_publish_allowed\": False,\\n'\n"
    "        '                \"production_cutover_active\": True,\\n'\n"
    "        '                \"single_visible_login_active\": True,\\n'\n"
    "        '                \"direct_oidc_handoff_active\": True,\\n'\n"
    "        '                \"oauth_destination_query_cleanup_active\": True,\\n'\n"
    "        '                \"production_entry\": \"app.py\",',\n"
)
if diagnostic_source_marker not in source_text:
    raise RuntimeError(
        "H13R5A source-integrity check failed: H13R1 diagnostic marker missing."
    )
source_text = source_text.replace(
    diagnostic_source_marker,
    diagnostic_source_replacement,
    1,
)

source_text = source_text.replace(
    '__hm_h13r1_native_full_app__',
    '__hm_h13r5a_scoped_profile_builder_staff__',
    1,
)

compiled_source = compile(source_text, str(SOURCE), "exec")
exec(
    compiled_source,
    {
        "__name__": "__hm_h13r5a_scoped_profile_builder_staff__",
        "__file__": str(SOURCE),
        "__package__": None,
    },
)
