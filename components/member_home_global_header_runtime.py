from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v2"
_MEMBER_HOME_TITLE = "Member Home"

_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v2">
/* Keep Member Home's profile action, but enforce the same compact global header
   height and spacing used across HealthyMe pages. */
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) {
  min-height:2.84rem!important;
  height:2.84rem!important;
  margin-top:0!important;
  margin-bottom:.34rem!important;
  padding:0!important;
  align-items:center!important;
  gap:.72rem!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"] {
  min-height:2.84rem!important;
  height:2.84rem!important;
  display:flex!important;
  align-items:center!important;
}
.hm-member-identity-pill {
  width:100%!important;
  min-height:2.84rem!important;
  height:2.84rem!important;
  padding:.42rem .72rem!important;
  margin:0!important;
  box-sizing:border-box!important;
}
.hm-top-profile-anchor + div,
.hm-top-logout-anchor + div {
  min-height:2.84rem!important;
  height:2.84rem!important;
  margin:0!important;
  padding:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.hm-top-profile-anchor + div [data-testid="stButton"] > button,
.hm-top-profile-anchor + div .stButton > button,
.hm-top-logout-anchor + div [data-testid="stButton"] > button,
.hm-top-logout-anchor + div .stButton > button {
  min-height:2.84rem!important;
  height:2.84rem!important;
  margin:0!important;
}

/* The injected style and any zero-height wrapper must not create a band between
   the identity row and the hero banner. */
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v2),
div.element-container:has(style#hm-member-home-global-header-v2) {
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.hero-shell {
  margin-top:0!important;
}
</style>
"""


def install_member_home_global_header_runtime() -> None:
    """Apply the global header spacing contract to Member Home."""

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
