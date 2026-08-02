from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v1"
_MEMBER_HOME_TITLE = "Member Home"

_HIDE_LOCAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v1">
/* Member Home previously rendered a page-specific identity/profile/logout strip.
   Hide that complete row and use the shared HealthyMe utility bar instead. */
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill),
div[data-testid="stHorizontalBlock"]:has(.hm-top-profile-anchor),
div[data-testid="stHorizontalBlock"]:has(.hm-top-logout-anchor) {
  display:none!important;
  visibility:hidden!important;
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}

div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v1),
div.element-container:has(style#hm-member-home-global-header-v1) {
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}

/* Keep the shared utility row and hero adjacent, matching the global page rhythm. */
div[data-testid="stHorizontalBlock"]:has(.utility-bar) {
  margin-top:0!important;
  margin-bottom:.34rem!important;
  align-items:center!important;
}
.hero-shell {
  margin-top:0!important;
}
</style>
"""


def install_member_home_global_header_runtime() -> None:
    """Replace Member Home's local header with the shared global utility bar."""

    from components import ui_common

    current_topbar = ui_common.topbar
    if getattr(current_topbar, _MARKER, False):
        return

    @functools.wraps(current_topbar)
    def topbar_with_shared_member_header(title, *args, **kwargs):
        if str(title or "").strip() == _MEMBER_HOME_TITLE:
            st.markdown(_HIDE_LOCAL_HEADER_CSS, unsafe_allow_html=True)
            ui_common.utility_logout_bar()
        return current_topbar(title, *args, **kwargs)

    setattr(topbar_with_shared_member_header, _MARKER, True)
    topbar_with_shared_member_header._hm_original = current_topbar
    ui_common.topbar = topbar_with_shared_member_header
