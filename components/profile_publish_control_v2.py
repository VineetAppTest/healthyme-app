from __future__ import annotations

import streamlit as st

from components.profile_builder_access import (
    current_profile_builder_user_can_publish,
)
from components.profile_publish_control import (
    _active_profile_rows,
    _clean,
    _escape,
    _review_rows,
    _rows,
    _safe_table,
    activate_profile,
    clear_publish_cache,
    load_active_profiles,
    load_profile_detail,
    load_publish_candidates,
)


def _render_publish_review_toggle_css() -> None:
    """Match the stable Food Journal Expand / Collapse button presentation."""
    st.markdown(
        """
<style id="hm-publish-review-food-journal-toggle-v1">
.hm-publish-toggle-anchor{display:block!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hm-publish-toggle-anchor + div [data-testid="stButton"] > button,
.hm-publish-toggle-anchor + div .stButton > button,
[class*="st-key-hm_publish_review_toggle_btn"] button,
[class*="st-key-hm_publish_review_toggle_btn"] [data-testid="stButton"] > button,
[class*="st-key-hm_publish_review_toggle_btn"] .stButton > button{
  display:flex!important;
  width:100%!important;
  justify-content:flex-start!important;
  align-items:center!important;
  text-align:left!important;
  min-height:2.72rem!important;
  background:linear-gradient(135deg,#FFFDF8 0%,#FFF6E5 100%)!important;
  border:1.45px solid #D8A84E!important;
  border-radius:16px!important;
  box-shadow:0 7px 16px rgba(15,23,42,.045)!important;
  color:#064E3B!important;
  font-weight:950!important;
  margin:.50rem 0 .34rem 0!important;
  padding:.58rem .78rem!important;
}
.hm-publish-toggle-anchor + div [data-testid="stButton"] > button *,
.hm-publish-toggle-anchor + div .stButton > button *,
[class*="st-key-hm_publish_review_toggle_btn"] button > div,
[class*="st-key-hm_publish_review_toggle_btn"] button p,
[class*="st-key-hm_publish_review_toggle_btn"] button span,
[class*="st-key-hm_publish_review_toggle_btn"] button *{
  width:100%!important;
  justify-content:flex-start!important;
  color:#064E3B!important;
  font-size:.90rem!important;
  font-weight:950!important;
  line-height:1.18!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  text-align:left!important;
}
.hm-publish-review-body{
  border:1px solid #E7D8BE;
  background:#FFFDF8;
  border-radius:16px;
  padding:1rem 1rem 1.18rem!important;
  margin:.16rem 0 .76rem 0;
  overflow:visible!important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_review_rows_toggle(items) -> None:
    state_key = "hm_publish_review_rows_open"
    st.session_state.setdefault(state_key, False)
    is_open = bool(st.session_state.get(state_key))
    prefix = "▾" if is_open else "▸"

    st.markdown(
        "<div class='hm-publish-toggle-anchor'></div>",
        unsafe_allow_html=True,
    )
    if st.button(
        f"{prefix} Review Recommendation Rows Before Activation",
        key="hm_publish_review_toggle_btn",
        use_container_width=True,
    ):
        st.session_state[state_key] = not is_open
        st.rerun()

    if st.session_state.get(state_key):
        st.markdown(
            "<div class='hm-publish-review-body'>",
            unsafe_allow_html=True,
        )
        _safe_table(
            _review_rows(items),
            "No recommendation rows found for this draft.",
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _activate_without_typed_confirmation(profile):
    # The Admin/Super Admin role gate is the authorization boundary. The legacy
    # ACTIVATE text entry is intentionally removed from the visible workflow.
    return activate_profile(profile, "ACTIVATE")


def _render_profile_publish_control_inner() -> None:
    if not current_profile_builder_user_can_publish():
        st.warning(
            "Publish / Activate is restricted to Admin and Super Admin. "
            "Nutritionists may create and edit Draft or Active profile content, "
            "but cannot activate or replace the member's live plan."
        )
        return

    _render_publish_review_toggle_css()
    ok_drafts, drafts, draft_message = load_publish_candidates()
    ok_active, active_profiles, active_message = load_active_profiles()

    st.markdown(
        "<div class='hm-title'>Publish Control</div>"
        "<div class='hm-sub'>Activate one saved recommendation profile per member. "
        "The previous active profile is replaced and event history is retained.</div>",
        unsafe_allow_html=True,
    )
    if not ok_drafts:
        st.error(draft_message)
    if not ok_active:
        st.warning(active_message)
    if st.button("Refresh Publish Control", use_container_width=True):
        clear_publish_cache()
        st.rerun()

    st.markdown(
        "<div class='hm-title'>Current Active Profiles</div>",
        unsafe_allow_html=True,
    )
    if active_profiles:
        _safe_table(
            _active_profile_rows(active_profiles),
            "No active recommendation profiles found yet.",
        )
    else:
        st.info("No active recommendation profiles found yet.")

    st.markdown(
        "<div class='hm-title'>Publish Saved Draft</div>"
        "<div class='hm-sub'>Select a saved draft that already has member assignment "
        "and recommendation rows.</div>",
        unsafe_allow_html=True,
    )
    label_to_id = {"-- Select draft profile --": ""}
    for draft in drafts:
        member_label = draft.get("assigned_member_label") or "No member assigned"
        label = (
            f"{draft.get('profile_name', 'Untitled draft')} · {member_label} · "
            f"{str(draft.get('updated_at', ''))[:16]}"
        )
        label_to_id[label] = draft.get("id", "")

    selected_label = st.selectbox(
        "Draft Profile",
        list(label_to_id.keys()),
        key="publish_draft_choice",
    )
    selected_id = label_to_id.get(selected_label, "")
    if not selected_id:
        st.info("Select a draft profile to review publish readiness.")
        return

    detail_ok, profile, items, detail_message = load_profile_detail(selected_id)
    if not detail_ok:
        st.error(detail_message)
        return

    meal_count = len([row for row in items if row.get("item_type") == "meal"])
    exercise_count = len(
        [row for row in items if row.get("item_type") == "exercise"]
    )
    supplement_count = len(
        [row for row in items if row.get("item_type") == "supplement"]
    )
    member_ready = bool(
        _clean(profile.get("assigned_member_id"))
        and _clean(profile.get("assigned_member_label"))
    )
    status_ready = _clean(profile.get("status")) == "draft"
    rows_ready = bool(items)
    can_activate = member_ready and status_ready and rows_ready
    status_pill = "hm-ok" if can_activate else "hm-pending"
    status_text = (
        "Ready for activation"
        if can_activate
        else "Needs attention before activation"
    )

    st.markdown(
        f"""
<div class='hm-preview'>
<b>Selected Draft Review</b><br>
<span class='hm-pill {status_pill}'>{status_text}</span><br>
<b>Profile:</b> {_escape(profile.get('profile_name'))}<br>
<b>Member:</b> {_escape(profile.get('assigned_member_label'), 'No member assigned')}<br>
<b>Status:</b> {_escape(profile.get('status'))}<br>
<b>Start Date:</b> {_escape(profile.get('start_date'))}
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class='hm-count-grid'>
  <div class='hm-count-card'><b>{meal_count}</b><span>Meal rows</span></div>
  <div class='hm-count-card'><b>{exercise_count}</b><span>Exercise rows</span></div>
  <div class='hm-count-card'><b>{supplement_count}</b><span>Supplement rows</span></div>
  <div class='hm-count-card'><b>{len(items)}</b><span>Total rows</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not member_ready:
        st.error(
            "Member assignment is required. Go to Profile Setup, assign a member, "
            "save the draft, then return here."
        )
    if not status_ready:
        st.error("Only draft profiles can be activated from this tab.")
    if not rows_ready:
        st.error("At least one recommendation row is required before activation.")

    if items:
        _render_review_rows_toggle(items)

    st.markdown(
        "<div class='hm-preview'><b>Activation Confirmation</b><br>"
        "Publishing will make this profile active for the selected member and mark "
        "any previous active profile for the same member as replaced. The Admin or "
        "Super Admin role is the authorization boundary for this action.</div>",
        unsafe_allow_html=True,
    )
    if st.button(
        "Publish / Activate Profile",
        type="primary",
        use_container_width=True,
        disabled=not can_activate,
    ):
        try:
            success, message = _activate_without_typed_confirmation(profile)
            if success:
                clear_publish_cache()
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        except Exception as exc:
            st.error(f"Could not activate profile: {exc}")


def render_profile_publish_control() -> None:
    try:
        _render_profile_publish_control_inner()
    except BaseException as exc:
        if exc.__class__.__name__ in {"RerunException", "StopException"}:
            raise
        st.error(f"Publish Control could not complete this action: {exc}")
        st.caption(
            "This error has been caught inside Publish Control. Use Refresh Publish "
            "Control once. If it repeats, share this displayed message."
        )
