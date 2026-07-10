import datetime as dt
import os
import uuid
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

PROFILE_TABLE = "hm_recommendation_profiles"
ITEM_TABLE = "hm_recommendation_profile_items"
EVENT_TABLE = "hm_recommendation_profile_events"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _display(value: object, default: str = "NA") -> str:
    text = _clean(value)
    return text if text else default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _safe_dataframe(rows: List[Dict[str, Any]], empty_message: str = "No rows found.") -> None:
    """Render Streamlit tables using string-normalised values.

    Streamlit/PyArrow can hard-fail the whole app when a list-of-dicts has mixed
    value types in the same column. Publish Control should never crash the page
    just because one draft row has an unexpected numeric/null/object shape.
    """
    if not rows:
        st.info(empty_message)
        return
    cleaned_rows = [{key: _display(value) for key, value in row.items()} for row in rows]
    st.dataframe(pd.DataFrame(cleaned_rows), use_container_width=True, hide_index=True)


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean(value, default)
    try:
        value = st.secrets.get(name)
        if value is not None:
            return _clean(value, default)
        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean(value, default)
        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return _clean(value, default)
            except Exception:
                continue
    except Exception:
        pass
    return default


def _client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Supabase URL/key is not configured.")
    return create_client(url, key)


def _rows(response) -> List[dict]:
    return list(getattr(response, "data", None) or [])


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


@st.cache_data(ttl=90, show_spinner=False)
def load_publish_candidates() -> Tuple[bool, List[dict], str]:
    try:
        c = _client()
        result = (
            c.table(PROFILE_TABLE)
            .select("id,profile_name,status,assigned_member_id,assigned_member_label,start_date,updated_at")
            .eq("status", "draft")
            .order("updated_at", desc=True)
            .limit(75)
            .execute()
        )
        return True, _rows(result), "Loaded draft profiles ready for publish review."
    except Exception as exc:
        return False, [], f"Could not load draft profiles: {exc}"


@st.cache_data(ttl=90, show_spinner=False)
def load_active_profiles() -> Tuple[bool, List[dict], str]:
    try:
        c = _client()
        result = (
            c.table(PROFILE_TABLE)
            .select("id,profile_name,status,assigned_member_id,assigned_member_label,start_date,updated_at")
            .eq("status", "active")
            .order("updated_at", desc=True)
            .limit(100)
            .execute()
        )
        return True, _rows(result), "Loaded active profiles."
    except Exception as exc:
        return False, [], f"Could not load active profiles: {exc}"


@st.cache_data(ttl=90, show_spinner=False)
def load_profile_detail(profile_id: str) -> Tuple[bool, Dict[str, Any], List[dict], str]:
    clean_id = _clean(profile_id)
    if not clean_id:
        return False, {}, [], "Select a draft profile first."
    try:
        c = _client()
        profile_result = c.table(PROFILE_TABLE).select("*").eq("id", clean_id).limit(1).execute()
        profiles = _rows(profile_result)
        if not profiles:
            return False, {}, [], "Selected profile was not found."
        item_result = (
            c.table(ITEM_TABLE)
            .select("item_type,day_number,slot_name,item_order,reference_label,portion,instruction,scheduled_time,intensity,dosage_frequency")
            .eq("profile_id", clean_id)
            .order("item_type")
            .order("day_number")
            .order("item_order")
            .execute()
        )
        return True, profiles[0], _rows(item_result), "Loaded profile detail."
    except Exception as exc:
        return False, {}, [], f"Could not load profile detail: {exc}"


def clear_publish_cache() -> None:
    load_publish_candidates.clear()
    load_active_profiles.clear()
    load_profile_detail.clear()


def activate_profile(profile: Dict[str, Any], confirm_text: str) -> Tuple[bool, str]:
    profile_id = _clean(profile.get("id"))
    profile_name = _clean(profile.get("profile_name"))
    assigned_member_id = _clean(profile.get("assigned_member_id"))
    assigned_member_label = _clean(profile.get("assigned_member_label"))
    status = _clean(profile.get("status"))

    if not profile_id:
        return False, "Select a saved draft before activating."
    if status != "draft":
        return False, "Only draft profiles can be activated from publish control."
    if not assigned_member_id or not assigned_member_label:
        return False, "Member assignment is required before activation. Go back to Profile Setup, assign a member, save the draft, then publish."
    if confirm_text.strip().upper() != "ACTIVATE":
        return False, "Type ACTIVATE in the confirmation box before publishing this profile."

    ts = now_iso()
    c = _client()
    active_result = (
        c.table(PROFILE_TABLE)
        .select("id,profile_name")
        .eq("status", "active")
        .eq("assigned_member_id", assigned_member_id)
        .execute()
    )
    existing_active = _rows(active_result)
    replaced_ids = [row.get("id") for row in existing_active if row.get("id") and row.get("id") != profile_id]

    if replaced_ids:
        c.table(PROFILE_TABLE).update({"status": "replaced", "updated_at": ts}).in_("id", replaced_ids).execute()
        for old in existing_active:
            old_id = old.get("id")
            if old_id and old_id != profile_id:
                c.table(EVENT_TABLE).insert({
                    "id": str(uuid.uuid4()),
                    "profile_id": old_id,
                    "event_type": "profile_replaced",
                    "event_note": f"Replaced by active profile: {profile_name}.",
                    "created_by_user_id": _clean(st.session_state.get("user_id")),
                    "created_by_email": _clean(st.session_state.get("user_email")),
                    "created_at": ts,
                }).execute()

    update_payload = {"status": "active", "updated_at": ts}
    if not _clean(profile.get("start_date")):
        update_payload["start_date"] = dt.date.today().isoformat()
    c.table(PROFILE_TABLE).update(update_payload).eq("id", profile_id).execute()
    c.table(EVENT_TABLE).insert({
        "id": str(uuid.uuid4()),
        "profile_id": profile_id,
        "event_type": "profile_activated",
        "event_note": f"Activated for {assigned_member_label}. Replaced {len(replaced_ids)} previous active profile(s).",
        "created_by_user_id": _clean(st.session_state.get("user_id")),
        "created_by_email": _clean(st.session_state.get("user_email")),
        "created_at": ts,
    }).execute()
    return True, f"Profile activated for {assigned_member_label}. Replaced {len(replaced_ids)} previous active profile(s)."


def _active_profile_rows(active_profiles: List[dict]) -> List[Dict[str, Any]]:
    return [
        {
            "Member": row.get("assigned_member_label") or "NA",
            "Active Profile": row.get("profile_name") or "NA",
            "Start Date": row.get("start_date") or "NA",
            "Updated": str(row.get("updated_at") or "")[:19],
        }
        for row in active_profiles
    ]


def _review_rows(items: List[dict]) -> List[Dict[str, Any]]:
    rows = []
    for row in items:
        rows.append({
            "Type": row.get("item_type"),
            "Day": _safe_int(row.get("day_number")),
            "Slot / Timing": row.get("slot_name") or row.get("scheduled_time") or "NA",
            "Item": row.get("reference_label") or "NA",
            "Dose / Portion": row.get("dosage_frequency") or row.get("portion") or "NA",
            "Intensity": row.get("intensity") or "NA",
            "Instruction": row.get("instruction") or "NA",
        })
    return rows


def _render_profile_publish_control_inner() -> None:
    ok_drafts, drafts, draft_message = load_publish_candidates()
    ok_active, active_profiles, active_message = load_active_profiles()

    st.markdown("<div class='hm-title'>Publish Control</div><div class='hm-sub'>Activate one saved recommendation profile per member. Previous active profile is replaced and event history is retained.</div>", unsafe_allow_html=True)
    if not ok_drafts:
        st.error(draft_message)
    if not ok_active:
        st.warning(active_message)
    if st.button("Refresh Publish Control", use_container_width=True):
        clear_publish_cache()
        st.rerun()

    st.markdown("<div class='hm-title'>Current Active Profiles</div>", unsafe_allow_html=True)
    if active_profiles:
        _safe_dataframe(_active_profile_rows(active_profiles), "No active recommendation profiles found yet.")
    else:
        st.info("No active recommendation profiles found yet.")

    st.markdown("<div class='hm-title'>Publish Saved Draft</div><div class='hm-sub'>Select a saved draft that already has member assignment and recommendation rows.</div>", unsafe_allow_html=True)
    label_to_id = {"-- Select draft profile --": ""}
    for draft in drafts:
        member_label = draft.get("assigned_member_label") or "No member assigned"
        label = f"{draft.get('profile_name', 'Untitled draft')} · {member_label} · {str(draft.get('updated_at', ''))[:16]}"
        label_to_id[label] = draft.get("id", "")

    selected_label = st.selectbox("Draft Profile", list(label_to_id.keys()), key="publish_draft_choice")
    selected_id = label_to_id.get(selected_label, "")
    if not selected_id:
        st.info("Select a draft profile to review publish readiness.")
        return

    detail_ok, profile, items, detail_message = load_profile_detail(selected_id)
    if not detail_ok:
        st.error(detail_message)
        return

    meal_count = len([row for row in items if row.get("item_type") == "meal"])
    exercise_count = len([row for row in items if row.get("item_type") == "exercise"])
    supplement_count = len([row for row in items if row.get("item_type") == "supplement"])
    member_ready = bool(_clean(profile.get("assigned_member_id")) and _clean(profile.get("assigned_member_label")))
    status_ready = _clean(profile.get("status")) == "draft"
    rows_ready = bool(items)
    can_activate = member_ready and status_ready and rows_ready

    st.markdown(f"""
<div class='hm-preview'>
<b>Selected Draft Review</b><br>
<span class='hm-pill {'hm-ok' if can_activate else 'hm-pending'}'>{'Ready for activation' if can_activate else 'Needs attention before activation'}</span><br>
<b>Profile:</b> {_display(profile.get('profile_name'))}<br>
<b>Member:</b> {_display(profile.get('assigned_member_label'), 'No member assigned')}<br>
<b>Status:</b> {_display(profile.get('status'))}<br>
<b>Start Date:</b> {_display(profile.get('start_date'))}
</div>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-count-grid'>
  <div class='hm-count-card'><b>{meal_count}</b><span>Meal rows</span></div>
  <div class='hm-count-card'><b>{exercise_count}</b><span>Exercise rows</span></div>
  <div class='hm-count-card'><b>{supplement_count}</b><span>Supplement rows</span></div>
  <div class='hm-count-card'><b>{len(items)}</b><span>Total rows</span></div>
</div>
""", unsafe_allow_html=True)

    if not member_ready:
        st.error("Member assignment is required. Go to Profile Setup, assign a member, save the draft, then return here.")
    if not status_ready:
        st.error("Only draft profiles can be activated from this tab.")
    if not rows_ready:
        st.error("At least one recommendation row is required before activation.")

    if items:
        with st.expander("Review recommendation rows before activation", expanded=False):
            _safe_dataframe(_review_rows(items), "No recommendation rows found for this draft.")

    st.markdown("<div class='hm-preview'><b>Activation Confirmation</b><br>This will make this profile active for the selected member and mark any previous active profile for the same member as replaced. Member-facing display is not wired in this sprint.</div>", unsafe_allow_html=True)
    confirm_text = st.text_input("Type ACTIVATE to confirm", key="publish_confirm_text")
    if st.button("Publish / Activate Profile", type="primary", use_container_width=True, disabled=not can_activate):
        try:
            success, message = activate_profile(profile, confirm_text)
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
    except Exception as exc:
        st.error(f"Publish Control could not complete this action: {exc}")
        st.caption("Use Refresh Publish Control once. If this repeats, share the displayed message instead of the generic Streamlit error page.")
