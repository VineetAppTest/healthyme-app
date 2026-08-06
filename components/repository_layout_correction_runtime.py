from __future__ import annotations

import functools
import inspect
from typing import Any

import streamlit as st


_MARKER = "_hm_repository_layout_correction_v3"
_REPOSITORY_PAGES = {
    "pages/15_Admin_Recipe_Manager.py": "recipe",
    "pages/16_Admin_Exercise_Manager.py": "exercise",
    "pages/39_Admin_Supplement_Manager.py": "supplement",
}

_REPOSITORY_CSS = """
<style>
/* Keep repository rows compact and align the content card with Edit/Delete. */
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row){
  align-items:center!important;
  gap:.42rem!important;
  width:100%!important;
  margin:.14rem 0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:first-child,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:first-child{
  flex:0 1 68%!important;
  width:68%!important;
  min-width:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(2),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(2){
  flex:0 0 76px!important;
  width:76px!important;
  min-width:76px!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(3),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(3){
  flex:0 0 86px!important;
  width:86px!important;
  min-width:86px!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]{
  display:flex!important;
  align-items:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-row,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-row{
  width:100%!important;
  min-height:2.55rem!important;
  margin:0!important;
  padding:.42rem .62rem!important;
  border-radius:12px!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]{
  width:100%!important;
  margin:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"]>button,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]>button{
  min-height:1.9rem!important;
  padding:.2rem .48rem!important;
  margin:0!important;
}

/* Keep one custom inline + / minus marker and suppress every native indicator. */
div[data-testid="stExpander"]{width:100%!important;max-width:100%!important;}
div[data-testid="stExpander"] summary{
  list-style:none!important;
  width:100%!important;
  max-width:100%!important;
  display:flex!important;
  align-items:center!important;
  font-size:0!important;
}
div[data-testid="stExpander"] summary::-webkit-details-marker{display:none!important;}
div[data-testid="stExpander"] summary::marker{content:""!important;display:none!important;}
div[data-testid="stExpander"] summary:before{
  font-size:.82rem!important;
  line-height:1!important;
}
div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
div[data-testid="stExpander"] summary [data-testid*="ExpanderIcon"],
div[data-testid="stExpander"] summary [aria-hidden="true"],
div[data-testid="stExpander"] summary [class*="material-symbols"],
div[data-testid="stExpander"] summary>svg,
div[data-testid="stExpander"] summary svg{
  display:none!important;
  width:0!important;
  min-width:0!important;
}
div[data-testid="stExpander"] summary p{
  display:block!important;
  font-size:.82rem!important;
  line-height:1.25!important;
  white-space:nowrap!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
  width:auto!important;
  flex:1 1 auto!important;
}

/* Use the same moderately compact, clearly grouped treatment for Add and Edit. */
div[data-baseweb="tab-panel"] div[data-testid="stVerticalBlock"],
div[data-testid="stExpander"] details[open] div[data-testid="stVerticalBlock"]{
  gap:.46rem!important;
}
div[data-baseweb="tab-panel"] h3,
div[data-testid="stExpander"] h3{
  font-size:.96rem!important;
  line-height:1.2!important;
  margin:.22rem 0 .30rem!important;
}
div[data-baseweb="tab-panel"] h4,
div[data-testid="stExpander"] h4{
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #E3C98E!important;
  border-radius:6px!important;
  font-size:.80rem!important;
  line-height:1.2!important;
  margin:.44rem 0 .20rem!important;
  padding:.20rem .38rem!important;
}
div[data-baseweb="tab-panel"] label p,
div[data-testid="stExpander"] label p{
  display:block!important;
  font-size:.72rem!important;
  line-height:1.22!important;
  margin:.06rem 0 .18rem!important;
  padding-left:.02rem!important;
}
div[data-baseweb="tab-panel"] input,
div[data-testid="stExpander"] input,
div[data-baseweb="tab-panel"] div[data-baseweb="select"]>div,
div[data-testid="stExpander"] div[data-baseweb="select"]>div{
  min-height:2.10rem!important;
}
div[data-baseweb="tab-panel"] textarea,
div[data-testid="stExpander"] textarea{
  min-height:58px!important;
}
div[data-baseweb="tab-panel"] div[data-testid="stForm"]{
  padding:.58rem .68rem!important;
  border-radius:12px!important;
}
div[data-testid="stExpander"] details[open]>div{
  padding:.38rem .68rem .62rem!important;
}
div[data-baseweb="tab-panel"] div[data-testid="stFileUploader"],
div[data-testid="stExpander"] div[data-testid="stFileUploader"]{
  margin-top:0!important;
}
div[data-baseweb="tab-panel"] div[data-testid="stButton"]>button,
div[data-testid="stExpander"] div[data-testid="stButton"]>button,
div[data-baseweb="tab-panel"] div[data-testid="stFormSubmitButton"]>button,
div[data-testid="stExpander"] div[data-testid="stFormSubmitButton"]>button{
  min-height:1.95rem!important;
  padding:.20rem .52rem!important;
}
div[data-baseweb="tab-panel"] button p,
div[data-testid="stExpander"] button p{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  font-size:.74rem!important;
  line-height:1.15!important;
  white-space:nowrap!important;
}

@media(max-width:760px){
  div[data-testid="stHorizontalBlock"]:has(.hm-repo-row),
  div[data-testid="stHorizontalBlock"]:has(.hm-sup-row){
    gap:.3rem!important;
  }
  div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:first-child,
  div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:first-child{
    flex:1 1 auto!important;
    width:auto!important;
  }
  div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(2),
  div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(2){
    flex:0 0 62px!important;width:62px!important;min-width:62px!important;
  }
  div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(3),
  div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(3){
    flex:0 0 70px!important;width:70px!important;min-width:70px!important;
  }
}


/* v3: current Streamlit DOM + sharper repository controls. */
div[data-testid="stSegmentedControl"] [role="radiogroup"],
div[data-testid="stSegmentedControl"] [data-baseweb="button-group"]{
  border:1px solid #D8A84E!important;border-radius:9px!important;
  overflow:hidden!important;background:#FFFFFF!important;box-shadow:none!important;
}
div[data-testid="stSegmentedControl"] button,
div[data-testid="stSegmentedControl"] label{
  min-height:2.34rem!important;border-radius:0!important;box-shadow:none!important;
  font-weight:850!important;align-items:center!important;justify-content:center!important;
}
div[data-testid="stSegmentedControl"] button:first-child,
div[data-testid="stSegmentedControl"] label:first-child{border-radius:8px 0 0 8px!important;}
div[data-testid="stSegmentedControl"] button:last-child,
div[data-testid="stSegmentedControl"] label:last-child{border-radius:0 8px 8px 0!important;}

div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]{
  display:flex!important;align-items:center!important;align-self:stretch!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="column"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="column"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"]{
  width:100%!important;height:100%!important;min-height:2.68rem!important;
  display:flex!important;justify-content:center!important;gap:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stElementContainer"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stElementContainer"]{
  margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"]>button,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]>button{
  min-height:2.18rem!important;height:2.18rem!important;border-radius:9px!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-row,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-row{
  min-height:2.68rem!important;border-radius:10px!important;}

div[data-testid="stExpander"] details{
  border:1.2px solid #D8A84E!important;border-radius:10px!important;
  background:#FFFDF8!important;overflow:hidden!important;}
div[data-testid="stExpander"] summary{
  min-height:2.42rem!important;padding:.48rem .62rem!important;gap:.48rem!important;
  display:flex!important;align-items:center!important;border-radius:9px!important;}
div[data-testid="stExpander"] summary:before{
  content:"+"!important;display:inline-flex!important;align-items:center!important;
  justify-content:center!important;width:1.34rem!important;height:1.34rem!important;
  border-radius:6px!important;background:#DDF7F3!important;color:#006D6F!important;
  font-size:.82rem!important;font-weight:950!important;line-height:1!important;
  margin:0!important;flex:0 0 1.34rem!important;}
div[data-testid="stExpander"] summary:after{
  content:""!important;display:block!important;width:1.34rem!important;
  flex:0 0 1.34rem!important;}
div[data-testid="stExpander"] details[open] summary:before{content:"−"!important;}
div[data-testid="stExpander"] summary p{
  display:block!important;width:100%!important;max-width:none!important;
  margin:0!important;color:#064E3B!important;font-size:.82rem!important;
  font-weight:900!important;line-height:1.2!important;white-space:normal!important;
  overflow:visible!important;text-overflow:clip!important;text-align:center!important;}
</style>
"""


def _page_kind() -> str:
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        for suffix, kind in _REPOSITORY_PAGES.items():
            if path.endswith(suffix):
                return kind
        frame = frame.f_back
    return ""


def _label(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    return str(args[0] if args else kwargs.get("label", ""))


def install_repository_layout_correction_runtime() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    current_markdown = st.markdown
    current_text_input = st.text_input
    current_text_area = st.text_area
    current_multiselect = st.multiselect

    @functools.wraps(current_tabs)
    def tabs_with_repository_layout(*args, **kwargs):
        if _page_kind():
            current_markdown(_REPOSITORY_CSS, unsafe_allow_html=True)
        return current_tabs(*args, **kwargs)

    @functools.wraps(current_markdown)
    def markdown_with_repository_sections(body, *args, **kwargs):
        kind = _page_kind()
        text = str(body or "")
        if kind == "recipe" and text == "#### Core details":
            body = "#### Core Details"
        elif kind == "exercise" and text == "#### Core display fields":
            body = "#### Core Fields"
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_text_input)
    def text_input_with_repository_sections(*args, **kwargs):
        kind = _page_kind()
        label = _label(args, kwargs)
        if kind == "exercise" and label == "Goal tags":
            current_markdown("#### Tags")
        elif kind == "supplement" and label == "Supplement Name":
            current_markdown("#### Basic Details")
        return current_text_input(*args, **kwargs)

    @functools.wraps(current_text_area)
    def text_area_with_repository_sections(*args, **kwargs):
        kind = _page_kind()
        label = _label(args, kwargs)
        if kind == "exercise" and label == "Short description":
            current_markdown("#### Guidance / Benefits")
        elif kind == "supplement" and label == "Default Instructions":
            current_markdown("#### Instructions")
        return current_text_area(*args, **kwargs)

    @functools.wraps(current_multiselect)
    def multiselect_with_repository_sections(*args, **kwargs):
        if _page_kind() == "supplement" and _label(args, kwargs) == "Default Timing":
            current_markdown("#### Timing")
        return current_multiselect(*args, **kwargs)

    for wrapped in (
        tabs_with_repository_layout,
        markdown_with_repository_sections,
        text_input_with_repository_sections,
        text_area_with_repository_sections,
        multiselect_with_repository_sections,
    ):
        setattr(wrapped, _MARKER, True)

    st.tabs = tabs_with_repository_layout
    st.markdown = markdown_with_repository_sections
    st.text_input = text_input_with_repository_sections
    st.text_area = text_area_with_repository_sections
    st.multiselect = multiselect_with_repository_sections
