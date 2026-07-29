from __future__ import annotations

import streamlit as st


def install_member_schedule_package_copy_cleanup(schedule_ui) -> None:
    """Hide only the informational-inclusions rule on the Member package tab."""

    base_render_package = schedule_ui._render_package
    if getattr(base_render_package, "_hm_member_package_copy_cleanup", False):
        return

    def render_member_package(member_id, member_view=False):
        if member_view:
            st.markdown(
                """
<style id="hm-member-package-copy-cleanup-v1">
.hm-package-summary .hm-package-line:has(> i){display:none!important;}
</style>
""",
                unsafe_allow_html=True,
            )
        return base_render_package(member_id, member_view=member_view)

    render_member_package._hm_member_package_copy_cleanup = True
    schedule_ui._render_package = render_member_package
