from __future__ import annotations

import functools
import inspect
from typing import Any

import streamlit as st


_MARKER = "_hm_repository_layout_correction_v1"
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

/* Retain the accepted custom + / minus control, but remove Streamlit's native marker. */
div[data-testid="stExpander"]{width:100%!important;max-width:100%!important;}
div[data-testid="stExpander"] summary{
  list-style:none!important;
  width:100%!important;
  max-width:100%!important;
}
div[data-testid="stExpander"] summary::-webkit-details-marker{display:none!important;}
div[data-testid="stExpander"] summary::marker{content:""!important;display:none!important;}
div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
div[data-testid="stExpander"] summary [data-testid*="ExpanderIcon"],
div[data-testid="stExpander"] summary>svg{
  display:none!important;
  width:0!important;
  min-width:0!important;
}
div[data-testid="stExpander"] summary p{
  white-space:nowrap!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
  width:auto!important;
  flex:1 1 auto!important;
}

/* Apply the same compact structure to Add and Edit content. */
div[data-baseweb="tab-panel"] div[data-testid="stVerticalBlock"]{gap:.38rem!important;}
div[data-baseweb="tab-panel"] h3{font-size:1rem!important;margin:.25rem 0 .35rem!important;}
div[data-baseweb="tab-panel"] h4{
  color:#064E3B!important;
  font-size:.82rem!important;
  line-height:1.2!important;
  margin:.34rem 0 .08rem!important;
}
div[data-baseweb="tab-panel"] textarea{min-height:64px!important;}
div[data-baseweb="tab-panel"] div[data-testid="stForm"]{
  padding:.65rem .75rem!important;
  border-radius:14px!important;
}
div[data-baseweb="tab-panel"] div[data-testid="stFileUploader"]{
  margin-top:.05rem!important;
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
