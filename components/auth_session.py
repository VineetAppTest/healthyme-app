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

def restore_login_from_token():
    """Restore login after browser refresh.

    Optimized behavior:
    - If session_state already has logged_in, do nothing.
    - If this page already tried restoration and failed, do not keep retrying.
    - Only one database lookup is done on the first refreshed page load.
    """
    if st.session_state.get("logged_in"):
        return True

    if st.session_state.get("_hm_restore_attempted"):
        return False

    token = _get_query_token()
    if not token:
        st.session_state["_hm_restore_attempted"] = True
        return False

    user = get_user_by_session_token(token)
    st.session_state["_hm_restore_attempted"] = True

    if not user:
        return False

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_role"] = user["role"]
    st.session_state["user_name"] = user["name"]
    st.session_state["must_reset_password"] = user.get("must_reset_password", False)
    st.session_state["hm_token"] = token
    return True

def persist_token_in_url(token):
    try:
        # Only update if different. This avoids unnecessary rerun-like URL churn.
        if st.query_params.get("hm_token", "") != token:
            st.query_params["hm_token"] = token
    except Exception:
        pass

def logout_current_user():
    token = st.session_state.get("hm_token") or _get_query_token()
    clear_login_session(token)
    try:
        st.query_params.clear()
    except Exception:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]