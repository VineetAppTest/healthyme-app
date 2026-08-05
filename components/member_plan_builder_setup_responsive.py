from __future__ import annotations

import streamlit as st


def render_member_plan_setup_responsive_styles() -> None:
    """Let Setup detail fields use available width and wrap without changing widgets."""

    st.markdown(
        """
<style id="hm-member-plan-setup-responsive-v1">
/* Scope only to the Setup disclosure containing Region / Food Culture. */
div[data-testid="stExpander"]:has(input[aria-label="Region / Food Culture"])
  div[data-testid="stHorizontalBlock"] {
  display:grid!important;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr))!important;
  gap:.52rem!important;
  width:100%!important;
  align-items:start!important;
}
div[data-testid="stExpander"]:has(input[aria-label="Region / Food Culture"])
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
  width:auto!important;
  min-width:0!important;
  max-width:none!important;
  flex:none!important;
}
@media(max-width:640px) {
  div[data-testid="stExpander"]:has(input[aria-label="Region / Food Culture"])
    div[data-testid="stHorizontalBlock"] {
    grid-template-columns:1fr!important;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )
