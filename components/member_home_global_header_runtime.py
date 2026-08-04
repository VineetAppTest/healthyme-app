from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v6"
_MEMBER_HOME_TITLE = "Member Home"

_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v6">
/* The page owns structural spacing. This runtime only preserves control sizing and
   the compact mobile row, avoiding another block-container or hero override. */
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){min-height:2.46rem!important;height:auto!important;margin:0!important;padding:0!important;align-items:center!important;gap:.72rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{min-height:2.46rem!important;height:auto!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
div[data-testid="column"]>div[data-testid="stVerticalBlock"]:has(.hm-top-profile-anchor),div[data-testid="column"]>div[data-testid="stVerticalBlock"]:has(.hm-top-logout-anchor){gap:0!important;min-height:2.46rem!important;height:2.46rem!important;margin:0!important;padding:0!important;}
div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor),div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor),div.element-container:has(.hm-top-profile-anchor),div.element-container:has(.hm-top-logout-anchor){display:none!important;visibility:hidden!important;width:0!important;min-width:0!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hm-member-identity-pill{width:100%!important;min-height:2.46rem!important;height:2.46rem!important;padding:.24rem .64rem!important;margin:0!important;box-sizing:border-box!important;min-width:0!important;}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]{min-height:2.46rem!important;height:2.46rem!important;margin:0!important;padding:0!important;display:flex!important;align-items:center!important;}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-profile-anchor) .stButton>button,div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-logout-anchor) .stButton>button{min-height:2.46rem!important;height:2.46rem!important;max-height:2.46rem!important;margin:0!important;}
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v6),div.element-container:has(style#hm-member-home-global-header-v6){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
@media(max-width:760px){
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){display:grid!important;grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important;gap:.30rem!important;align-items:center!important;width:100%!important;min-height:2.30rem!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(1){grid-column:1!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(2){grid-column:2!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(3){grid-column:3!important;}
  .hm-member-identity-pill{height:2.30rem!important;min-height:2.30rem!important;padding:.20rem .42rem!important;font-size:.66rem!important;display:flex!important;align-items:center!important;gap:.22rem!important;overflow:hidden!important;white-space:nowrap!important;}
  .hm-member-identity-pill>span:first-child{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;}
  .hm-member-role-inline{flex:0 0 auto!important;font-size:.58rem!important;padding:.10rem .22rem!important;margin-left:0!important;white-space:nowrap!important;}
  div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-profile-anchor) .stButton>button,div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-logout-anchor) .stButton>button{width:100%!important;min-width:0!important;height:2.30rem!important;min-height:2.30rem!important;max-height:2.30rem!important;padding:.16rem .24rem!important;margin:0!important;border-radius:12px!important;font-size:.70rem!important;line-height:1!important;white-space:nowrap!important;}
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
