from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "streamlit_toolbar_cleanup.py"
INIT = ROOT / "components" / "__init__.py"
ROOT_AUTHORIZER = ROOT / "native_bridge" / "root_authorization_ui_h13r7e.py"


def test_toolbar_cleanup_component_compiles():
    compile(COMPONENT.read_text(encoding="utf-8"), str(COMPONENT), "exec")


def test_owner_toolbar_controls_are_hidden_globally():
    source = COMPONENT.read_text(encoding="utf-8")
    for selector in (
        '#MainMenu',
        'header[data-testid="stHeader"]',
        '[data-testid="stToolbar"]',
        '[data-testid="stToolbarActions"]',
        '[data-testid="stHeaderActionElements"]',
        '[data-testid="stAppToolbar"]',
        'button[kind="header"]',
    ):
        assert selector in source
    assert "display: none !important" in source
    assert "height: 0 !important" in source


def test_cleanup_runs_after_each_page_configuration():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "result = base(*args, **kwargs)" in source
    assert "st.markdown(_TOOLBAR_CSS, unsafe_allow_html=True)" in source
    assert source.index("result = base(*args, **kwargs)") < source.index(
        "st.markdown(_TOOLBAR_CSS, unsafe_allow_html=True)"
    )


def test_cleanup_is_installed_before_route_and_login_wrappers():
    source = INIT.read_text(encoding="utf-8")
    assert "install_streamlit_toolbar_cleanup" in source
    assert source.index("install_streamlit_toolbar_cleanup()") < source.index(
        "install_login_expiry_recovery()"
    )


def test_root_oauth_callback_uses_wrapped_page_configuration():
    source = ROOT_AUTHORIZER.read_text(encoding="utf-8")
    assert "st.set_page_config(" in source
    assert "render_root_authorization_ui" in source


def test_toolbar_cleanup_does_not_modify_auth_or_routing():
    source = COMPONENT.read_text(encoding="utf-8")
    for forbidden in (
        "authorization_id",
        "st.login",
        "st.logout",
        "st.navigation",
        "st.switch_page",
        "require_member",
        "require_admin",
        "st.query_params",
    ):
        assert forbidden not in source
