from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v4"
_MEMBER_HOME_TITLE = "Member Home"

_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v4">
/* Member Home has one root header sequence: identity row followed by the hero.
   Control the root vertical block gap directly instead of relying on a negative
   margin against Streamlit's generated hero wrapper. */
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill):has(> div[data-testid="stElementContainer"] .hero-shell),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill):has(> div.element-container .hero-shell) {
  gap:.28rem!important;
  padding-top:0!important;
  margin-top:0!important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill) > div[data-testid="stHorizontalBlock"] {
  min-height:2.46rem!important;
  height:auto!important;
  margin:0!important;
  padding:0!important;
  align-items:center!important;
  gap:.72rem!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"] {
  min-height:2.46rem!important;
  height:auto!important;
  display:flex!important;
  align-items:center!important;
  margin:0!important;
  padding:0!important;
}
div[data-testid="column"] > div[data-testid="stVerticalBlock"]:has(.hm-top-profile-anchor),
div[data-testid="column"] > div[data-testid="stVerticalBlock"]:has(.hm-top-logout-anchor) {
  gap:0!important;
  min-height:2.46rem!important;
  height:2.46rem!important;
  margin:0!important;
  padding:0!important;
}

/* Hidden anchor elements must not reserve a second row inside their columns. */
div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor),
div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor),
div.element-container:has(.hm-top-profile-anchor),
div.element-container:has(.hm-top-logout-anchor) {
  display:none!important;
  visibility:hidden!important;
  width:0!important;
  min-width:0!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.hm-member-identity-pill {
  width:100%!important;
  min-height:2.46rem!important;
  height:2.46rem!important;
  padding:.24rem .64rem!important;
  margin:0!important;
  box-sizing:border-box!important;
}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"],
div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"] {
  min-height:2.46rem!important;
  height:2.46rem!important;
  margin:0!important;
  padding:0!important;
  display:flex!important;
  align-items:center!important;
}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"] > button,
div[data-testid="column"]:has(.hm-top-profile-anchor) .stButton > button,
div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"] > button,
div[data-testid="column"]:has(.hm-top-logout-anchor) .stButton > button {
  min-height:2.46rem!important;
  height:2.46rem!important;
  max-height:2.46rem!important;
  margin:0!important;
}

/* The hero is the next visible item in the controlled root sequence. */
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill) > div[data-testid="stElementContainer"]:has(.hero-shell),
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill) > div.element-container:has(.hero-shell) {
  margin:0!important;
  padding:0!important;
  min-height:0!important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] .hm-member-identity-pill) .hero-shell {
  margin-top:0!important;
}

/* The injected stylesheet itself must not become another flex-gap item. */
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v4),
div.element-container:has(style#hm-member-home-global-header-v4) {
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
</style>
"""


def install_member_home_global_header_runtime() -> None:
    """Apply the controlled identity-row and hero spacing contract."""

    from components import ui_common

    current_topbar = ui_common.topbar
    if getattr(current_topbar, _MARKER, False):
        return

    @functools.wraps(current_topbar)
    def topbar_with_member_global_spacing(title, *args, **kwargs):
        if str(title or "").strip() == _MEMBER_HOME_TITLE:
            st.markdown(_GLOBAL_HEADER_CSS, unsafe_allow_html=True)
        return current_topbar(title, *args, **kwargs)

    setattr(topbar_with_member_global_spacing, _MARKER, True)
    topbar_with_member_global_spacing._hm_original = current_topbar
    ui_common.topbar = topbar_with_member_global_spacing
