from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_member_home_global_header_v8"
_MEMBER_HOME_TITLE = "Member Home"

_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v8">
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor):has(.hm-member-identity-pill):has(.hero-shell){gap:.68rem!important;margin:0!important;padding:0!important;overflow:visible!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){min-height:2.46rem!important;height:auto!important;margin:0 0 .18rem 0!important;padding:0!important;align-items:center!important;gap:.72rem!important;overflow:visible!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>:is(div[data-testid="column"],div[data-testid="stColumn"]){min-height:2.46rem!important;height:2.46rem!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>:is(div[data-testid="column"],div[data-testid="stColumn"])>div[data-testid="stVerticalBlock"]{width:100%!important;height:2.46rem!important;min-height:2.46rem!important;display:flex!important;flex-direction:column!important;justify-content:center!important;gap:0!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) [data-testid="stButton"]{height:2.46rem!important;min-height:2.46rem!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) [data-testid="stButton"]>button{height:2.46rem!important;min-height:2.46rem!important;max-height:2.46rem!important;margin:0!important;align-self:center!important;}
div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor),div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor),div.element-container:has(.hm-top-profile-anchor),div.element-container:has(.hm-top-logout-anchor){display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hm-member-identity-pill{width:100%!important;min-height:2.46rem!important;height:2.46rem!important;padding:.24rem .64rem!important;margin:0!important;box-sizing:border-box!important;min-width:0!important;}
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v8),div.element-container:has(style#hm-member-home-global-header-v8){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) div[data-testid="stElementContainer"]:has(.hero-shell){height:auto!important;min-height:0!important;margin:.16rem 0 1rem 0!important;padding:0!important;overflow:visible!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) .hero-shell{margin:0!important;height:auto!important;min-height:0!important;position:relative!important;overflow:visible!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card){margin-top:.78rem!important;clear:both!important;position:relative!important;}
@media(max-width:760px){div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){display:grid!important;grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important;gap:.30rem!important;align-items:center!important;width:100%!important;min-height:2.30rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>:is(div[data-testid="column"],div[data-testid="stColumn"]){display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>:is(div[data-testid="column"],div[data-testid="stColumn"])>div[data-testid="stVerticalBlock"]{height:2.30rem!important;min-height:2.30rem!important;justify-content:center!important;}.hm-member-identity-pill{height:2.30rem!important;min-height:2.30rem!important;padding:.20rem .42rem!important;font-size:.66rem!important;display:flex!important;align-items:center!important;gap:.22rem!important;overflow:hidden!important;white-space:nowrap!important;}.hm-member-identity-pill>span:first-child{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;}}
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
