from __future__ import annotations

import streamlit as st


DAILY_LOG_FIELD_CONTRAST_CSS = r"""
<style id="hm-daily-log-field-contrast-v1">
html body [data-testid="stAppViewContainer"]{
  color-scheme:light!important;
}
div[data-testid="stElementContainer"]:has(style#hm-daily-log-field-contrast-v1),
div.element-container:has(style#hm-daily-log-field-contrast-v1){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}

/*
 * Streamlit 1.59 can render either the input itself or a BaseWeb wrapper as the
 * visible field surface. Colour both layers so iOS WebKit/device dark mode cannot
 * expose a dark theme beneath a transparent control.
 */
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stTextArea"],
  div[data-testid="stTimeInput"],
  div[data-testid="stDateInput"],
  [class*="st-key-hm_daily_"],
  [class*="st-key-hm_h9a4c_"],
  [class*="st-key-hm_food_journal_"]
) :is([data-baseweb="input"],[data-baseweb="base-input"],input,textarea){
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0F172A!important;
  -webkit-text-fill-color:#0F172A!important;
  caret-color:#064E3B!important;
  opacity:1!important;
  color-scheme:light!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stTextArea"],
  div[data-testid="stTimeInput"],
  div[data-testid="stDateInput"],
  [class*="st-key-hm_daily_"],
  [class*="st-key-hm_h9a4c_"],
  [class*="st-key-hm_food_journal_"]
) :is(input,textarea)::placeholder{
  color:#64748B!important;
  -webkit-text-fill-color:#64748B!important;
  opacity:1!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stTextArea"],
  div[data-testid="stTimeInput"],
  div[data-testid="stDateInput"],
  [class*="st-key-hm_daily_"],
  [class*="st-key-hm_h9a4c_"],
  [class*="st-key-hm_food_journal_"]
):focus-within :is([data-baseweb="input"],[data-baseweb="base-input"]){
  border-color:#0F766E!important;
  box-shadow:0 0 0 2px rgba(15,118,110,.18)!important;
}

html body [data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] [data-baseweb="select"]>div,
html body [data-testid="stAppViewContainer"] :is(
  [class*="st-key-hm_daily_"],
  [class*="st-key-hm_h9a4c_"],
  [class*="st-key-hm_food_journal_"]
) [data-baseweb="select"]>div{
  background:#FFFFFF!important;
  background-color:#FFFFFF!important;
  color:#0F172A!important;
  -webkit-text-fill-color:#0F172A!important;
  opacity:1!important;
  color-scheme:light!important;
}

html body [data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] [data-baseweb="select"] :is(input,span,div),
html body [data-testid="stAppViewContainer"] :is(
  [class*="st-key-hm_daily_"],
  [class*="st-key-hm_h9a4c_"],
  [class*="st-key-hm_food_journal_"]
) [data-baseweb="select"] :is(input,span,div){
  color:#0F172A!important;
  -webkit-text-fill-color:#0F172A!important;
  opacity:1!important;
}

html body [data-testid="stAppViewContainer"] div[data-testid="stSelectbox"]:focus-within [data-baseweb="select"]>div{
  border-color:#0F766E!important;
  box-shadow:0 0 0 2px rgba(15,118,110,.18)!important;
}

html body [data-testid="stAppViewContainer"] :is(input,textarea):-webkit-autofill,
html body [data-testid="stAppViewContainer"] :is(input,textarea):-webkit-autofill:focus{
  -webkit-box-shadow:0 0 0 1000px #FFFFFF inset!important;
  -webkit-text-fill-color:#0F172A!important;
  caret-color:#064E3B!important;
}

html body [data-baseweb="popover"] [role="listbox"],
html body [data-baseweb="popover"] [role="option"]{
  background:#FFFFFF!important;
  color:#0F172A!important;
  -webkit-text-fill-color:#0F172A!important;
  color-scheme:light!important;
}
</style>
"""


def render_daily_log_field_contrast() -> None:
    """Keep Daily Log field values readable across Streamlit and iOS themes."""

    st.markdown(DAILY_LOG_FIELD_CONTRAST_CSS, unsafe_allow_html=True)
