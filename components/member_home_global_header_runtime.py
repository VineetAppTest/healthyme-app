from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v3"
_MEMBER_HOME_TITLE = "Member Home"

_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v3">
/* Member Home keeps its profile action, but the utility row must occupy only the
   visible control height. Hidden Streamlit anchor wrappers previously enlarged the
   row and left a blank band before the hero. */
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) {
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

/* Remove the complete Streamlit element wrapper, not only the zero-height span. */
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

/* The injected stylesheet itself must not create a Streamlit element band. */
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v3),
div.element-container:has(style#hm-member-home-global-header-v3) {
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}

/* Streamlit's root vertical block keeps a standard inter-element gap. Pull only the
   Member Home hero back by that residual amount after the compact utility row. */
div[data-testid="stElementContainer"]:has(.hero-shell),
div.element-container:has(.hero-shell) {
  margin-top:-.72rem!important;
  padding-top:0!important;
}
.hero-shell {
  margin-top:0!important;
}
</style>
"""


def install_member_home_global_header_runtime() -> None:
    """Apply the compact global header spacing contract to Member Home."""

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
