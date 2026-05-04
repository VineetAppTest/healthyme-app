import streamlit as st
from components.db import get_user_by_session_token, clear_login_session

def _get_query_token():
    try:
        token = st.query_params.get("hm_token", "")
        if isinstance(token, list):
            token = token[0] if token else ""
        return str(token or "").strip()
    except Exception:
        return ""

def persist_token_in_url(token):
    """Keep login token in URL so browser refresh can restore session.

    This is intentionally lightweight. It only updates the URL if the token is missing/different.
    """
    token = (token or "").strip()
    if not token:
        return
    try:
        if str(st.query_params.get("hm_token", "") or "").strip() != token:
            st.query_params["hm_token"] = token
    except Exception:
        pass

def keep_logged_in_url_alive():
    """When Streamlit session is already logged in, keep token attached to current page URL.

    This fixes the issue where st.switch_page navigation can land on a page without hm_token,
    and then browser refresh loses the login.
    """
    if st.session_state.get("logged_in") and st.session_state.get("hm_token"):
        persist_token_in_url(st.session_state.get("hm_token"))

def restore_login_from_token():
    """Restore login after browser refresh.

    Behavior:
    - If already logged in, re-attach token to URL and return immediately.
    - If refreshed and token exists in URL, restore session once.
    - If no token exists, return False quickly.
    """
    if st.session_state.get("logged_in"):
        keep_logged_in_url_alive()
        return True

    token = _get_query_token()
    if not token:
        return False

    user = get_user_by_session_token(token)
    if not user:
        return False

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_role"] = user["role"]
    st.session_state["user_name"] = user["name"]
    st.session_state["must_reset_password"] = user.get("must_reset_password", False)
    st.session_state["hm_token"] = token
    keep_logged_in_url_alive()
    return True

def logout_current_user():
    token = st.session_state.get("hm_token") or _get_query_token()
    clear_login_session(token)
    try:
        st.query_params.clear()
    except Exception:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]