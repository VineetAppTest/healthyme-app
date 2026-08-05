import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZERS = (
    ROOT / "native_bridge" / "root_authorization_ui.py",
    ROOT / "native_bridge" / "root_authorization_ui_h13r7e.py",
)


def _source(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    ast.parse(source)
    return source


def test_each_authorizer_starts_a_fresh_bounded_login_attempt() -> None:
    for path in AUTHORIZERS:
        source = _source(path)
        assert "function createFreshSupabaseClient()" in source, path.name
        assert "const supabase = createFreshSupabaseClient();" in source, path.name
        assert "const authStepTimeoutMs = 45000;" in source, path.name
        assert "supabase.auth.signInWithPassword" in source, path.name
        assert '"Credential confirmation"' in source, path.name


def test_each_authorizer_clears_prior_callback_markers_before_login() -> None:
    for path in AUTHORIZERS:
        source = _source(path)
        assert 'const authorizationMarkerPrefix = "hm_h13r2_oauth_reload:";' in source
        assert "function resetPriorAuthorizationMarkers()" in source
        assert "storage.removeItem(key)" in source
        assert source.index("resetPriorAuthorizationMarkers();") < source.index(
            'document.getElementById("hm-form").addEventListener'
        )


def test_each_authorizer_restores_or_restarts_instead_of_failing_silently() -> None:
    for path in AUTHORIZERS:
        source = _source(path)
        submit_start = source.index(
            'document.getElementById("hm-form").addEventListener'
        )
        submit_source = source[submit_start:]
        assert "try {{" in submit_source
        assert "}} catch (error) {{" in submit_source
        assert 'supabase.auth.signOut({{scope:"local"}})' in submit_source
        assert "requireRestart(" in submit_source
        assert 'showMessage(\n            error?.message || "Unable to complete secure login.' in submit_source
        assert "busy = false;" in submit_source
        assert "signInButton.disabled = false;" in submit_source


def test_production_router_keeps_the_hardened_authorizer() -> None:
    app_source = _source(ROOT / "app.py")
    assert "root_authorization_ui_h13r7e as _root_authorization_ui" in app_source
    assert "_BASE_AUTHORIZER = _root_authorization_ui.render_root_authorization_ui" in app_source
