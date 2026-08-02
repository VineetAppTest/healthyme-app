from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


_REPOSITORY_PAGE_CSS = """
<style>
/* Give every repository row its own breathing space and align actions vertically. */
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row),
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row){
  align-items:center!important;
  margin:0 0 .42rem!important;
}
.hm-repo-row,.hm-sup-row{
  margin:0!important;
}

/* Direct repository controls: no Streamlit expander marker can be rendered. */
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor){
  gap:.08rem!important;
  max-width:940px!important;
  margin:.34rem 0 .5rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor) div[data-testid="stButton"]>button{
  justify-content:flex-start!important;
  min-height:2.15rem!important;
  padding:.3rem .68rem!important;
  border:1px solid #E3C98E!important;
  border-radius:14px!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-size:.78rem!important;
  font-weight:850!important;
  line-height:1.15!important;
  text-align:left!important;
  white-space:nowrap!important;
  overflow:visible!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor) div[data-testid="stButton"]>button p{
  color:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  margin:0!important;
  visibility:visible!important;
}

/* Add and Edit use this exact same crisp bordered workspace. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor){
  max-width:900px!important;
  margin:.14rem 0 .48rem!important;
  border:1px solid #E3C98E!important;
  border-radius:13px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor)>div{
  padding:.5rem .62rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stVerticalBlock"]{
  gap:.2rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stHorizontalBlock"]{
  gap:.42rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) h3{
  font-size:.88rem!important;
  line-height:1.15!important;
  margin:.02rem 0 .12rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) h4{
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #D4A72C!important;
  border-radius:5px!important;
  font-size:.72rem!important;
  line-height:1.1!important;
  margin:.22rem 0 .04rem!important;
  padding:.16rem .34rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stWidgetLabel"]{
  min-height:auto!important;
  margin-bottom:0!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stWidgetLabel"] p{
  font-size:.64rem!important;
  line-height:1.05!important;
  margin:0!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="input"]>div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="select"]>div{
  min-height:1.86rem!important;
  height:1.86rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) input{
  min-height:1.86rem!important;
  height:1.86rem!important;
  padding:.2rem .42rem!important;
  font-size:.7rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) textarea{
  min-height:52px!important;
  height:52px!important;
  padding:.3rem .42rem!important;
  font-size:.7rem!important;
  line-height:1.18!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stFileUploaderDropzone"]{
  min-height:2.45rem!important;
  padding:.28rem .4rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stFileUploaderDropzone"] p,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stFileUploaderDropzone"] small{
  font-size:.62rem!important;
  line-height:1.05!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stButton"]>button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stFormSubmitButton"]>button{
  min-height:2.05rem!important;
  height:auto!important;
  padding:.28rem .5rem!important;
  font-size:.7rem!important;
  line-height:1.1!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stButton"]>button p,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stFormSubmitButton"]>button p{
  color:inherit!important;
  font-size:inherit!important;
  line-height:inherit!important;
  margin:0!important;
  visibility:visible!important;
}

/* Read-only inactive items use a compact bordered panel. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-inactive-anchor){
  max-width:940px!important;
  margin:.12rem 0 .45rem!important;
  border:1px solid #E3C98E!important;
  border-radius:14px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-inactive-anchor)>div{
  padding:.48rem .64rem!important;
}

@media(max-width:760px){
  div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor),
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor),
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-inactive-anchor){
    max-width:100%!important;
  }
  div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor) div[data-testid="stButton"]>button{
    white-space:normal!important;
  }
}
</style>
"""


def inject_repository_page_ui() -> None:
    st.markdown(_REPOSITORY_PAGE_CSS, unsafe_allow_html=True)


def render_repository_disclosure(
    label: str,
    *,
    is_open: bool,
    key: str,
) -> bool:
    """Render one page-owned inline disclosure control without a native marker."""

    symbol = "⊖" if is_open else "⊕"
    with st.container():
        st.markdown(
            "<span class='hm-repository-disclosure-anchor'></span>",
            unsafe_allow_html=True,
        )
        return st.button(
            f"{symbol}  {label}",
            key=key,
            use_container_width=True,
        )


@contextmanager
def repository_form_panel() -> Iterator[None]:
    with st.container(border=True):
        st.markdown(
            "<span class='hm-repository-form-anchor'></span>",
            unsafe_allow_html=True,
        )
        yield


@contextmanager
def repository_inactive_panel() -> Iterator[None]:
    with st.container(border=True):
        st.markdown(
            "<span class='hm-repository-inactive-anchor'></span>",
            unsafe_allow_html=True,
        )
        yield
