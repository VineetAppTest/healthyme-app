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
/* Keep repository rows compact, readable and aligned with Edit/Delete. */
div[data-baseweb="tab-panel"],
div[data-testid="stTabs"] [role="tabpanel"]{
  max-width:1040px!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row){
  align-items:center!important;
  gap:.42rem!important;
  width:100%!important;
  max-width:1020px!important;
  margin:.12rem 0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:first-child,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:first-child{
  flex:0 1 68%!important;
  width:68%!important;
  min-width:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(2),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(2){
  flex:0 0 74px!important;
  width:74px!important;
  min-width:74px!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]:nth-child(3),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]:nth-child(3){
  flex:0 0 84px!important;
  width:84px!important;
  min-width:84px!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]{
  display:flex!important;
  align-items:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-row,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-row{
  width:100%!important;
  min-height:2.45rem!important;
  margin:0!important;
  padding:.4rem .62rem!important;
  border-radius:11px!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-title,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-name{
  font-size:.88rem!important;
  line-height:1.14!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-meta,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-meta{
  font-size:.72rem!important;
  line-height:1.2!important;
  margin-top:.08rem!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]{
  width:100%!important;
  margin:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"]>button,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]>button{
  min-height:1.9rem!important;
  padding:.2rem .46rem!important;
  margin:0!important;
  font-size:.74rem!important;
}

/* Retain one inline custom + / minus control and the complete label text. */
div[data-testid="stExpander"]{
  width:100%!important;
  max-width:1020px!important;
}
div[data-testid="stExpander"] summary{
  display:flex!important;
  align-items:center!important;
  list-style:none!important;
  width:100%!important;
  max-width:100%!important;
  min-height:2.1rem!important;
  padding:.42rem .62rem!important;
  overflow:visible!important;
}
div[data-testid="stExpander"] summary::-webkit-details-marker{display:none!important;}
div[data-testid="stExpander"] summary::marker{content:""!important;}
div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
div[data-testid="stExpander"] summary [data-testid*="ExpanderIcon"],
div[data-testid="stExpander"] summary [data-baseweb="icon"],
div[data-testid="stExpander"] summary svg{
  display:none!important;
  width:0!important;
  min-width:0!important;
  margin:0!important;
  padding:0!important;
}
div[data-testid="stExpander"] summary:before{
  width:1.2rem!important;
  height:1.2rem!important;
  margin-right:.42rem!important;
  font-size:.76rem!important;
  flex:0 0 1.2rem!important;
}
div[data-testid="stExpander"] summary p{
  display:block!important;
  white-space:nowrap!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
  width:auto!important;
  flex:1 1 auto!important;
  font-size:.82rem!important;
  line-height:1.15!important;
  margin:0!important;
}
div[data-testid="stExpander"] details[open]>div{
  padding:.3rem .68rem .7rem!important;
}

/* Apply the same balanced, moderately compact treatment to Add and Edit. */
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stVerticalBlock"],
div[data-baseweb="tab-panel"] div[data-testid="stVerticalBlock"],
div[data-testid="stExpander"] div[data-testid="stVerticalBlock"]{
  gap:.34rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stHorizontalBlock"],
div[data-baseweb="tab-panel"] div[data-testid="stHorizontalBlock"],
div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"]{
  gap:.62rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] h3,
div[data-baseweb="tab-panel"] h3{
  font-size:.98rem!important;
  line-height:1.18!important;
  margin:.22rem 0 .3rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] h4,
div[data-baseweb="tab-panel"] h4,
div[data-testid="stExpander"] h4{
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #D4A72C!important;
  border-radius:7px!important;
  font-size:.82rem!important;
  line-height:1.15!important;
  margin:.32rem 0 .1rem!important;
  padding:.26rem .5rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] [data-testid="stWidgetLabel"] p,
div[data-baseweb="tab-panel"] [data-testid="stWidgetLabel"] p,
div[data-testid="stExpander"] [data-testid="stWidgetLabel"] p{
  font-size:.72rem!important;
  line-height:1.08!important;
  margin-bottom:.05rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] [data-baseweb="input"]>div,
div[data-baseweb="tab-panel"] [data-baseweb="input"]>div,
div[data-testid="stExpander"] [data-baseweb="input"]>div,
div[data-testid="stTabs"] [role="tabpanel"] [data-baseweb="select"]>div,
div[data-baseweb="tab-panel"] [data-baseweb="select"]>div,
div[data-testid="stExpander"] [data-baseweb="select"]>div{
  min-height:2.05rem!important;
  height:2.05rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] input,
div[data-baseweb="tab-panel"] input,
div[data-testid="stExpander"] input{
  min-height:2.05rem!important;
  height:2.05rem!important;
  padding:.28rem .5rem!important;
  font-size:.76rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] textarea,
div[data-baseweb="tab-panel"] textarea,
div[data-testid="stExpander"] textarea{
  min-height:64px!important;
  height:64px!important;
  padding:.4rem .5rem!important;
  font-size:.76rem!important;
  line-height:1.25!important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stForm"],
div[data-baseweb="tab-panel"] div[data-testid="stForm"]{
  padding:.66rem .78rem!important;
  border-radius:12px!important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stFileUploader"],
div[data-baseweb="tab-panel"] div[data-testid="stFileUploader"],
div[data-testid="stExpander"] div[data-testid="stFileUploader"]{
  margin-top:.04rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] [data-testid="stFileUploaderDropzone"],
div[data-baseweb="tab-panel"] [data-testid="stFileUploaderDropzone"],
div[data-testid="stExpander"] [data-testid="stFileUploaderDropzone"]{
  min-height:3rem!important;
  padding:.35rem .5rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] [data-testid="stFileUploaderDropzone"] small,
div[data-baseweb="tab-panel"] [data-testid="stFileUploaderDropzone"] small,
div[data-testid="stExpander"] [data-testid="stFileUploaderDropzone"] small{
  font-size:.66rem!important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stButton"]>button,
div[data-baseweb="tab-panel"] div[data-testid="stButton"]>button,
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stFormSubmitButton"]>button,
div[data-baseweb="tab-panel"] div[data-testid="stFormSubmitButton"]>button,
div[data-testid="stExpander"] div[data-testid="stButton"]>button{
  min-height:1.95rem!important;
  padding:.2rem .5rem!important;
  font-size:.74rem!important;
}

@media(max-width:760px){
  div[data-baseweb="tab-panel"],
  div[data-testid="stTabs"] [role="tabpanel"]{
    max-width:100%!important;
  }
  div[data-testid="stHorizontalBlock"]:has(.hm-repo-row),
  div[data-testid="stHorizontalBlock"]:has(.hm-sup-row){
    gap:.3rem!important;
    max-width:100%!important;
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
  div[data-testid="stExpander"]{max-width:100%!important;}
}
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
