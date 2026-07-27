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

# Replace only the production Login presentation after H13R1 has changed the
# accepted Member-router title. Authentication and routing code remain unchanged.
title_patch_marker = (
    "    source_text = source_text.replace(\n"
    "        'st.title(\"HealthyMe native full-member router\")',\n"
    "        'st.title(\"HealthyMe native full application router\")',\n"
    "    )\n"
)
if title_patch_marker not in source_text:
    raise RuntimeError(
        "H13R2 source-integrity check failed: H13R1 Login title transform missing."
    )

production_login_ui = '    st.markdown(\n        """\n        <style>\n        .hm-login-shell{margin-top:-1.1rem;}\n        .hm-login-brand-row{\n            display:flex;align-items:center;justify-content:space-between;\n            gap:1rem;margin:.15rem 0 1.15rem 0;padding:.35rem .1rem;\n        }\n        .hm-login-brand-name{font-size:2rem;font-weight:800;color:#123f32;line-height:1.05;}\n        .hm-login-brand-sub{font-size:.92rem;color:#63756f;margin-top:.3rem;}\n        .hm-login-secure-pill{\n            border:1px solid #cfe0da;background:#eef7f3;color:#245a48;\n            border-radius:999px;padding:.48rem .85rem;font-size:.8rem;font-weight:700;\n            white-space:nowrap;\n        }\n        .hm-login-card-title{font-size:1.55rem;font-weight:800;color:#173d33;margin-bottom:.25rem;}\n        .hm-login-card-copy{color:#64746f;font-size:.92rem;line-height:1.5;margin-bottom:.75rem;}\n        .hm-login-info{\n            background:#edf7f4;border:1px solid #d2e7df;border-radius:12px;\n            padding:.78rem .85rem;margin-top:.9rem;color:#315e50;font-size:.84rem;line-height:1.45;\n        }\n        .hm-journey-card{\n            min-height:100%;border:1px solid #dde7e3;border-radius:16px;\n            padding:1.35rem 1.35rem 1.2rem 1.35rem;background:linear-gradient(145deg,#fbfdfc,#f2f8f5);\n            box-shadow:0 8px 22px rgba(21,61,49,.06);\n        }\n        .hm-journey-card h3{color:#173d33;margin:0 0 .35rem 0;font-size:1.35rem;}\n        .hm-journey-card p{color:#667771;font-size:.9rem;line-height:1.5;margin:0 0 .95rem 0;}\n        .hm-journey-grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem;}\n        .hm-journey-item{\n            background:white;border:1px solid #e0e9e5;border-radius:11px;\n            padding:.7rem .75rem;color:#34594c;font-size:.84rem;font-weight:650;\n        }\n        .hm-login-feature-strip{\n            display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-top:1.05rem;\n        }\n        .hm-login-feature{\n            border:1px solid #e0e8e5;border-radius:12px;background:#fff;\n            padding:.72rem .82rem;display:flex;flex-direction:column;gap:.1rem;\n        }\n        .hm-login-feature b{color:#234b3e;font-size:.84rem;}\n        .hm-login-feature span{color:#74817d;font-size:.76rem;}\n        @media (max-width: 720px){\n            .hm-login-brand-row{align-items:flex-start;flex-direction:column;}\n            .hm-journey-grid,.hm-login-feature-strip{grid-template-columns:1fr;}\n        }\n        </style>\n        <div class="hm-login-shell">\n          <div class="hm-login-brand-row">\n            <div>\n              <div class="hm-login-brand-name">HealthyMe</div>\n              <div class="hm-login-brand-sub">Guided wellness assessment platform</div>\n            </div>\n            <div class="hm-login-secure-pill">Supabase OIDC · Secure access</div>\n          </div>\n        </div>\n        """,\n        unsafe_allow_html=True,\n    )\n\n    login_col, journey_col = st.columns([0.96, 1.04], gap="large")\n\n    with login_col:\n        try:\n            login_box = st.container(border=True)\n        except TypeError:\n            login_box = st.container()\n\n        with login_box:\n            st.markdown(\n                """\n                <div class="hm-login-card-title">Secure Login</div>\n                <div class="hm-login-card-copy">\n                  Sign in with your authorised HealthyMe account. Access is granted\n                  only after HealthyMe verifies your active Member or Admin role.\n                </div>\n                """,\n                unsafe_allow_html=True,\n            )\n            if st.button(\n                "Continue with Supabase OIDC",\n                key="h13q7_continue_oidc",\n                type="primary",\n                use_container_width=True,\n            ):\n                st.login(provider)\n                st.stop()\n\n            st.markdown(\n                """\n                <div class="hm-login-info">\n                  <b>No public sign-up</b><br>\n                  Supabase confirms your identity. HealthyMe then checks your active\n                  Member or Admin authorisation before opening the application.\n                </div>\n                """,\n                unsafe_allow_html=True,\n            )\n\n    with journey_col:\n        st.markdown(\n            """\n            <div class="hm-journey-card">\n              <h3>Your wellness journey</h3>\n              <p>A secure, expert-led path from assessment to practical wellness guidance.</p>\n              <div class="hm-journey-grid">\n                <div class="hm-journey-item">✓ Secure Supabase Login</div>\n                <div class="hm-journey-item">✓ Lifestyle Assessment</div>\n                <div class="hm-journey-item">✓ NSP Assessment</div>\n                <div class="hm-journey-item">🔒 Expert Review</div>\n              </div>\n            </div>\n            """,\n            unsafe_allow_html=True,\n        )\n\n    st.markdown(\n        """\n        <div class="hm-login-feature-strip">\n          <div class="hm-login-feature"><b>Secure</b><span>Supabase OIDC</span></div>\n          <div class="hm-login-feature"><b>Role-based</b><span>Member / Admin</span></div>\n          <div class="hm-login-feature"><b>Private</b><span>Native Streamlit session</span></div>\n        </div>\n        """,\n        unsafe_allow_html=True,\n    )\n\n    with st.expander("Technical diagnostics", expanded=False):\n        st.code(BUILD)\n        st.metric("Native Streamlit identity", "Absent")\n        st.code(\n            json.dumps(\n                {\n                    "build": BUILD,\n                    "rollback_build": ROLLBACK_BUILD,\n                    "native_identity_present": False,\n                    "full_member_route_count": len(_ROUTE_SPECS) + 2,\n                    "route_groups": route_counts,\n                    "real_admin_dashboard_loaded": False,\n                    "application_session_state_auth_source": False,\n                    "legacy_page_guard_used": False,\n                    "custom_browser_marker_used": False,\n                    "durable_auth_session_used": False,\n                    "local_storage_used": False,\n                    **_safe_cookie_snapshot(),\n                },\n                indent=2,\n                sort_keys=True,\n            ),\n            language="json",\n        )\n'
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
