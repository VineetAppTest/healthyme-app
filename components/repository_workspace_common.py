from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


WORKSPACE_CSS = """
<style>
.block-container{padding-top:.45rem!important;max-width:1080px!important;}
.hero-shell{margin:.45rem 0 .7rem!important;padding:.95rem 1.1rem!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor){
  max-width:960px!important;
  margin:.15rem auto .65rem!important;
  border:1px solid #E3C98E!important;
  border-radius:16px!important;
  background:#FFFDF8!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor)>div{
  padding:.72rem .82rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) div[data-testid="stVerticalBlock"]{
  gap:.34rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) div[data-testid="stHorizontalBlock"]{
  gap:.55rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) h4{
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #D4A72C!important;
  border-radius:6px!important;
  font-size:.82rem!important;
  line-height:1.15!important;
  margin:.34rem 0 .08rem!important;
  padding:.22rem .42rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) [data-testid="stWidgetLabel"] p{
  font-size:.74rem!important;
  line-height:1.1!important;
  margin-bottom:.03rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) [data-baseweb="input"]>div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) [data-baseweb="select"]>div{
  min-height:2.12rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) input{
  min-height:2.12rem!important;
  padding:.28rem .5rem!important;
  font-size:.76rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) textarea{
  min-height:64px!important;
  height:64px!important;
  padding:.38rem .5rem!important;
  font-size:.76rem!important;
  line-height:1.22!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) [data-testid="stFileUploaderDropzone"]{
  min-height:2.9rem!important;
  padding:.38rem .5rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) div[data-testid="stButton"]>button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) div[data-testid="stFormSubmitButton"]>button{
  min-height:2.2rem!important;
  padding:.3rem .65rem!important;
  font-size:.76rem!important;
  white-space:nowrap!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-workspace-anchor) button p{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  color:inherit!important;
  margin:0!important;
}
</style>
"""


def inject_workspace_ui() -> None:
    st.markdown(WORKSPACE_CSS, unsafe_allow_html=True)


@contextmanager
def workspace_panel() -> Iterator[None]:
    with st.container(border=True):
        st.markdown("<span class='hm-workspace-anchor'></span>", unsafe_allow_html=True)
        yield


def actor_id() -> str:
    return (
        st.session_state.get("user_id")
        or st.session_state.get("oidc_email")
        or "admin"
    )


def clean(value) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def workspace_mode(prefix: str) -> tuple[str, object | None]:
    mode = str(st.session_state.get(f"hm_{prefix}_workspace_mode") or "add").lower()
    item_id = st.session_state.get(f"hm_{prefix}_workspace_id")
    return ("edit" if mode == "edit" else "add", item_id)


def clear_workspace(prefix: str) -> None:
    st.session_state.pop(f"hm_{prefix}_workspace_mode", None)
    st.session_state.pop(f"hm_{prefix}_workspace_id", None)


def clear_widget_prefix(prefix: str) -> None:
    for key in list(st.session_state):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)
