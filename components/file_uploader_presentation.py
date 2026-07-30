from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_file_uploader_presentation_v1"

_UPLOADER_CSS = """
<style id="hm-file-uploader-presentation-v1">
[data-testid="stFileUploader"] [data-testid="stIconMaterial"],
[data-testid="stFileUploader"] .material-symbols-rounded,
[data-testid="stFileUploader"] .material-symbols-outlined {
  font-family:"Material Symbols Rounded","Material Symbols Outlined"!important;
  font-weight:normal!important;font-style:normal!important;font-size:1.12rem!important;
  line-height:1!important;letter-spacing:normal!important;text-transform:none!important;
  white-space:nowrap!important;word-wrap:normal!important;direction:ltr!important;
  -webkit-font-feature-settings:"liga"!important;font-feature-settings:"liga"!important;
  -webkit-font-smoothing:antialiased!important;overflow:visible!important;
}
[data-testid="stFileUploader"] button {
  display:inline-flex!important;align-items:center!important;justify-content:center!important;
  gap:.32rem!important;min-width:5.9rem!important;width:auto!important;min-height:2.45rem!important;
  padding:.48rem .78rem!important;white-space:nowrap!important;overflow:visible!important;
  text-overflow:clip!important;line-height:1.1!important;
}
[data-testid="stFileUploader"] button * {
  white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;
  word-break:keep-all!important;overflow-wrap:normal!important;line-height:1.1!important;
}
</style>
"""


def install_file_uploader_presentation() -> None:
    """Restore Streamlit's uploader icon font without changing upload behavior."""

    current = st.file_uploader
    if getattr(current, _MARKER, False):
        return

    @functools.wraps(current)
    def file_uploader_with_clean_icon(*args, **kwargs):
        st.markdown(_UPLOADER_CSS, unsafe_allow_html=True)
        return current(*args, **kwargs)

    setattr(file_uploader_with_clean_icon, _MARKER, True)
    st.file_uploader = file_uploader_with_clean_icon
