from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


_REPOSITORY_PAGE_CSS = """
<style>
/* Give repository rows clear breathing space even when page-local CSS is loaded later. */
.hm-repo-row,.hm-sup-row{
  margin:.08rem 0 .48rem!important;
}

/* Page-owned disclosure controls: one symbol and one complete inline label. */
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor){
  gap:.08rem!important;
  max-width:880px!important;
  margin:.38rem 0 .5rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor) div[data-testid="stButton"]>button{
  justify-content:flex-start!important;
  min-height:2.05rem!important;
  padding:.28rem .62rem!important;
  border:1px solid #E3C98E!important;
  border-radius:12px!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-size:.78rem!important;
  font-weight:850!important;
  text-align:left!important;
  white-space:nowrap!important;
  overflow:visible!important;
}

/* Server-side section switch: only the selected repository body is rendered. */
div[data-testid="stVerticalBlock"]:has(.hm-repository-section-anchor){
  gap:.12rem!important;
  max-width:880px!important;
  margin:.08rem 0 .42rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-section-anchor) div[data-testid="stButton"]>button{
  min-height:2rem!important;
  padding:.28rem .58rem!important;
  border-radius:999px!important;
  font-size:.74rem!important;
  font-weight:850!important;
  white-space:nowrap!important;
}

/* Add and Edit use the same crisp bordered workspace. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor){
  max-width:880px!important;
  margin:.12rem 0 .46rem!important;
  border:1px solid #E3C98E!important;
  border-radius:12px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor)>div{
  padding:.5rem .62rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stVerticalBlock"]{
  gap:.2rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stHorizontalBlock"]{
  gap:.4rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) h3{
  font-size:.9rem!important;
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
  margin:.2rem 0 .03rem!important;
  padding:.14rem .34rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stWidgetLabel"] p{
  font-size:.64rem!important;
  line-height:1.05!important;
  margin-bottom:0!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="input"]>div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-baseweb="select"]>div{
  min-height:1.9rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) input{
  min-height:1.9rem!important;
  padding:.2rem .42rem!important;
  font-size:.71rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) textarea{
  min-height:52px!important;
  height:52px!important;
  padding:.28rem .42rem!important;
  font-size:.71rem!important;
  line-height:1.2!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) [data-testid="stFileUploaderDropzone"]{
  min-height:2.45rem!important;
  padding:.3rem .42rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stButton"]>button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) div[data-testid="stFormSubmitButton"]>button{
  min-height:1.9rem!important;
  padding:.22rem .5rem!important;
  font-size:.71rem!important;
  font-weight:850!important;
}
/* Keep primary action copy visible across theme variants. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) button[kind="primary"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) button[data-testid="baseButton-primary"]{
  background:#0F766E!important;
  border-color:#0F766E!important;
  color:#FFFFFF!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) button[kind="primary"] *,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-form-anchor) button[data-testid="baseButton-primary"] *{
  color:#FFFFFF!important;
  opacity:1!important;
}

/* Read-only inactive items use a separated compact panel. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-inactive-anchor){
  max-width:880px!important;
  margin:.08rem 0 .42rem!important;
  border:1px solid #E3C98E!important;
  border-radius:12px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-repository-inactive-anchor)>div{
  padding:.44rem .58rem!important;
}

@media(max-width:760px){
  div[data-testid="stVerticalBlock"]:has(.hm-repository-disclosure-anchor),
  div[data-testid="stVerticalBlock"]:has(.hm-repository-section-anchor),
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


def render_repository_section_switch(
    add_label: str,
    *,
    key: str,
) -> str:
    """Render a server-side two-section switch and return the selected section.

    Unlike ``st.tabs``, this renders only the selected body, reducing the widget count
    and avoiding construction of a hidden Add form while Current Repository is open.
    """

    state_key = f"{key}_section"
    current = st.session_state.get(state_key, "repository")
    if current not in {"repository", "add"}:
        current = "repository"
        st.session_state[state_key] = current

    with st.container():
        st.markdown(
            "<span class='hm-repository-section-anchor'></span>",
            unsafe_allow_html=True,
        )
        repository_col, add_col, _ = st.columns([1.35, 1.05, 5.6], gap="small")
        with repository_col:
            show_repository = st.button(
                "Current Repository",
                key=f"{key}_show_repository",
                type="primary" if current == "repository" else "secondary",
                use_container_width=True,
            )
        with add_col:
            show_add = st.button(
                add_label,
                key=f"{key}_show_add",
                type="primary" if current == "add" else "secondary",
                use_container_width=True,
            )

    target = "repository" if show_repository else "add" if show_add else current
    if target != current:
        st.session_state[state_key] = target
        st.rerun()
    return current


def render_repository_disclosure(
    label: str,
    *,
    is_open: bool,
    key: str,
) -> bool:
    """Render one page-owned inline disclosure control."""

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
