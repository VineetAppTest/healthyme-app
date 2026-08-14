from __future__ import annotations

import streamlit as st


APPLE_APPEARANCE_COMPAT_CSS = r"""
<style id="hm-apple-appearance-compat-v1">
:root{
  --hm-control-surface:#FFFFFF;
  --hm-control-text:#0F172A;
  --hm-control-muted:#64748B;
  --hm-control-disabled-surface:#F8F5EF;
  --hm-control-disabled-text:#475569;
  color-scheme:light!important;
}
html,
body,
html body [data-testid="stAppViewContainer"],
html body .stApp{
  color-scheme:light!important;
}

/*
 * Streamlit 1.59 uses BaseWeb wrappers around the native control. Apple dark
 * mode can colour either layer, so both the wrapper and the real field surface
 * must carry the accepted HealthyMe light palette.
 */
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"]
) :is([data-baseweb="input"],[data-baseweb="base-input"]),
html body [data-testid="stAppViewContainer"] div[data-testid="stTextArea"] :is(
  [data-baseweb="textarea"],
  textarea
),
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"]
) input,
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stDataFrame"],
  div[data-testid="stDataEditor"]
) input{
  background:var(--hm-control-surface)!important;
  background-color:var(--hm-control-surface)!important;
  background-image:none!important;
  color:var(--hm-control-text)!important;
  -webkit-text-fill-color:var(--hm-control-text)!important;
  caret-color:#064E3B!important;
  opacity:1!important;
  color-scheme:light!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"]
) [data-baseweb="select"]>div{
  background:var(--hm-control-surface)!important;
  background-color:var(--hm-control-surface)!important;
  color:var(--hm-control-text)!important;
  -webkit-text-fill-color:var(--hm-control-text)!important;
  opacity:1!important;
  color-scheme:light!important;
}
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"]
) [data-baseweb="select"] :is(input,span,div),
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"],
  div[data-testid="stTextArea"]
) svg{
  color:var(--hm-control-text)!important;
  fill:currentColor!important;
  opacity:1!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"],
  div[data-testid="stTextArea"]
) :is(input,textarea)::placeholder{
  color:var(--hm-control-muted)!important;
  -webkit-text-fill-color:var(--hm-control-muted)!important;
  opacity:1!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"],
  div[data-testid="stTextArea"]
) :is(input,textarea):is(:disabled,[readonly]),
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"]
) :is(
  [data-baseweb="select"][aria-disabled="true"],
  [aria-disabled="true"] [data-baseweb="select"]
)>div{
  background:var(--hm-control-disabled-surface)!important;
  background-color:var(--hm-control-disabled-surface)!important;
  color:var(--hm-control-disabled-text)!important;
  -webkit-text-fill-color:var(--hm-control-disabled-text)!important;
  opacity:1!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"],
  div[data-testid="stTextArea"]
) :is(input,textarea):-webkit-autofill,
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stTextInput"],
  div[data-testid="stNumberInput"],
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"],
  div[data-testid="stTextArea"]
) :is(input,textarea):-webkit-autofill:focus{
  -webkit-box-shadow:0 0 0 1000px var(--hm-control-surface) inset!important;
  -webkit-text-fill-color:var(--hm-control-text)!important;
  caret-color:#064E3B!important;
}

html body [data-baseweb="popover"],
html body [data-baseweb="popover"] [role="listbox"],
html body [data-baseweb="popover"] [role="option"],
html body [data-baseweb="calendar"]{
  background:var(--hm-control-surface)!important;
  background-color:var(--hm-control-surface)!important;
  color:var(--hm-control-text)!important;
  -webkit-text-fill-color:var(--hm-control-text)!important;
  color-scheme:light!important;
}
html body [data-baseweb="popover"] [role="option"][aria-selected="true"]{
  background:#E7F7EF!important;
  background-color:#E7F7EF!important;
}

html body [data-testid="stFileUploaderDropzone"]{
  background:#FFFDF8!important;
  background-color:#FFFDF8!important;
  color:var(--hm-control-text)!important;
  color-scheme:light!important;
}
html body [data-testid="stFileUploaderDropzone"] *{
  color:var(--hm-control-text)!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stCheckbox"],
  div[data-testid="stRadio"],
  div[data-testid="stToggle"],
  div[data-testid="stSlider"]
) :is(label,p,span){
  color:#334155!important;
}
html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stCheckbox"],
  div[data-testid="stRadio"],
  div[data-testid="stToggle"]
) input{
  accent-color:#0F766E!important;
}

html body [data-testid="stAppViewContainer"] :is(
  div[data-testid="stDateInput"],
  div[data-testid="stTimeInput"]
) input::-webkit-calendar-picker-indicator{
  opacity:1!important;
}

/*
 * Reassert only colour properties when Apple reports dark appearance. Layout,
 * dimensions and native date/time affordances intentionally remain untouched.
 */
@media (prefers-color-scheme: dark){
  :root,
  html,
  body,
  html body [data-testid="stAppViewContainer"],
  html body .stApp{
    color-scheme:light!important;
  }
  html body [data-testid="stAppViewContainer"] :is(
    div[data-testid="stTextInput"],
    div[data-testid="stNumberInput"],
    div[data-testid="stDateInput"],
    div[data-testid="stTimeInput"]
  ) :is([data-baseweb="input"],[data-baseweb="base-input"],input),
  html body [data-testid="stAppViewContainer"] div[data-testid="stTextArea"] :is(
    [data-baseweb="textarea"],
    textarea
  ),
  html body [data-testid="stAppViewContainer"] :is(
    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"]
  ) input{
    background:var(--hm-control-surface)!important;
    background-color:var(--hm-control-surface)!important;
    color:var(--hm-control-text)!important;
    -webkit-text-fill-color:var(--hm-control-text)!important;
    caret-color:#064E3B!important;
    opacity:1!important;
    color-scheme:light!important;
    box-shadow:inset 0 0 0 1000px var(--hm-control-surface)!important;
  }
  html body [data-testid="stAppViewContainer"] :is(
    div[data-testid="stSelectbox"],
    div[data-testid="stMultiSelect"]
  ) [data-baseweb="select"]>div{
    background:var(--hm-control-surface)!important;
    background-color:var(--hm-control-surface)!important;
    color:var(--hm-control-text)!important;
    -webkit-text-fill-color:var(--hm-control-text)!important;
    opacity:1!important;
    color-scheme:light!important;
  }
}
</style>
"""


def render_apple_appearance_compat() -> None:
    """Keep HealthyMe controls readable across Apple light and dark modes."""

    st.markdown(APPLE_APPEARANCE_COMPAT_CSS, unsafe_allow_html=True)
