from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


_REPOSITORY_PAGE_CSS = """
<style>
/* Direct repository controls: no Streamlit expander marker can be rendered. */
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor){
  gap:.14rem!important;
  max-width:940px!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor) div[data-testid="stButton"]>button{
  justify-content:flex-start!important;
  min-height:2.25rem!important;
  padding:.36rem .72rem!important;
  border:1px solid #E3C98E!important;
  border-radius:14px!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-size:.84rem!important;
  font-weight:900!important;
  text-align:left!important;
  white-space:nowrap!important;
  overflow:visible!important;
}

/* Add and Edit use this exact same bordered workspace. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor){
  max-width:940px!important;
  margin:.18rem 0 .55rem!important;
  border:1px solid #E3C98E!important;
  border-radius:14px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor)>div{
  padding:.72rem .82rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stVerticalBlock"]{
  gap:.34rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stHorizontalBlock"]{
  gap:.55rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) h3{
  font-size:1rem!important;
  line-height:1.2!important;
  margin:.08rem 0 .22rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) h4{
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #D4A72C!important;
  border-radius:6px!important;
  font-size:.8rem!important;
  line-height:1.15!important;
  margin:.35rem 0 .08rem!important;
  padding:.22rem .42rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stWidgetLabel"] p{
  font-size:.72rem!important;
  line-height:1.1!important;
  margin-bottom:.04rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="input"]>div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="select"]>div{
  min-height:2.18rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) input{
  min-height:2.18rem!important;
  padding:.28rem .5rem!important;
  font-size:.76rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) textarea{
  min-height:68px!important;
  height:68px!important;
  padding:.4rem .5rem!important;
  font-size:.76rem!important;
  line-height:1.25!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stFileUploaderDropzone"]{
  min-height:3rem!important;
  padding:.42rem .52rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stButton"]>button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stFormSubmitButton"]>button{
  min-height:2rem!important;
  padding:.26rem .55rem!important;
  font-size:.74rem!important;
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
  padding:.55rem .7rem!important;
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
    """Render one page-owned inline disclosure control.

    Circled Unicode symbols keep the accepted circular + / minus treatment while
    avoiding Streamlit's native expander marker entirely.
    """

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
