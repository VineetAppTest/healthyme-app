from __future__ import annotations

from collections.abc import Iterable

import streamlit as st


def clear_widget_state(keys: Iterable[str]) -> None:
    """Remove submitted widget state without disturbing page context controls."""

    for key in keys:
        if key:
            st.session_state.pop(str(key), None)


def clear_prefixed_widget_state(prefixes: Iterable[str]) -> None:
    """Clear all widget values whose keys start with an approved form prefix."""

    normalized = tuple(str(prefix) for prefix in prefixes if str(prefix))
    if not normalized:
        return
    for key in list(st.session_state.keys()):
        if str(key).startswith(normalized):
            st.session_state.pop(key, None)
