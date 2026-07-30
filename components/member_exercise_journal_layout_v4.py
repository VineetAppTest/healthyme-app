from __future__ import annotations

import streamlit as st

from components import member_exercise_journal_table as base


def _inject_layout_styles() -> None:
    st.markdown(
        """
<style id="hm-exercise-journal-layout-v4">
.hm-exercise-actions-anchor{
  display:block;height:0;min-height:0;margin:0;padding:0;overflow:hidden;
}
.hm-exercise-actions-anchor + div[data-testid="stHorizontalBlock"]{
  margin:.18rem 0 .62rem 0!important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_member_exercise_journal_layout_v4(
    member_id: str,
    member_email: str = "",
    *,
    heading: str = "Exercise Journal",
    key_prefix: str = "hm_member_exercise_table",
    show_build_note: bool = True,
) -> None:
    """Render the existing Exercise Journal contract with the accepted Daily Log layout."""

    base._inject_styles()
    _inject_layout_styles()
    if heading:
        st.markdown(f"### {base._esc(heading)}")

    date_key = f"{key_prefix}_date"
    pending_key = f"{key_prefix}_pending_date"
    if pending_key in st.session_state:
        st.session_state[date_key] = st.session_state.pop(pending_key)
    st.session_state.setdefault(date_key, base.dt.date.today())

    with st.container(border=True):
        st.markdown("### Exercise Journal Date")
        selected_date = st.date_input(
            "Select the date for this exercise journal entry",
            key=date_key,
        )
    log_date = selected_date.isoformat()

    contract = base.exercise_contract_for_date(member_id, member_email, selected_date)
    if not contract.get("ok"):
        st.error(
            contract.get("message")
            or "Exercise recommendations could not be loaded."
        )

    profile = dict(contract.get("profile") or {})
    assigned = list(contract.get("exercises") or [])
    profile_items = list(contract.get("catalog") or [])
    existing_rows = base.list_member_exercise_logs(member_id, log_date)
    existing = {
        int(row.get("item_order") or index): dict(row)
        for index, row in enumerate(existing_rows, 1)
    }

    catalog = base.repository_activity_catalog()
    catalog.update(
        {
            base._clean(item.get("name")): dict(item)
            for item in profile_items
            if base._clean(item.get("name"))
        }
    )
    for row in existing_rows:
        name = base._clean(row.get("exercise_name"))
        if name and name not in catalog:
            catalog[name] = dict(row)

    base_count = max(1, len(assigned), len(existing_rows))
    count_key = f"{key_prefix}_row_count_{log_date}"
    st.session_state.setdefault(count_key, base_count)
    row_count = max(
        base_count,
        min(base.MAX_EXERCISE_ROWS, int(st.session_state[count_key])),
    )
    st.session_state[count_key] = row_count

    if show_build_note:
        st.markdown(
            f"<div class='hm-exercise-date-caption'>{base._esc(contract.get('day_label'))}</div>",
            unsafe_allow_html=True,
        )

    if not profile.get("id"):
        st.warning(
            "An active recommendation profile is required before a new Exercise "
            "Journal entry can be saved. Existing saved days remain viewable."
        )

    timings = base._unique(
        [item.get("timing_or_slot") for item in profile_items]
        + [row.get("scheduled_time") for row in existing_rows]
        + list(base.STANDARD_TIMING_OPTIONS)
    )
    activities = list(catalog.keys())
    profile_id = base._clean(profile.get("id")) or "profile"

    for index in range(1, row_count + 1):
        prescribed = dict(assigned[index - 1]) if index <= len(assigned) else {}
        prior = dict(existing.get(index) or {})
        item_order = int(
            prior.get("item_order") or prescribed.get("item_order") or index
        )
        current_activity = (
            base._clean(prior.get("exercise_name"))
            or base._clean(prescribed.get("name"))
            or "Select activity"
        )
        current_timing = (
            base._clean(prior.get("scheduled_time"))
            or base._clean(prescribed.get("timing_or_slot"))
            or "Morning"
        )
        widget = (
            f"{key_prefix}_{profile_id}_{contract.get('day_number')}_"
            f"{log_date}_{item_order}"
        )

        with st.container(border=True):
            st.markdown(
                f"<div class='hm-exercise-row-number'>Exercise {index}</div>",
                unsafe_allow_html=True,
            )
            timing_col, activity_col, duration_col, remarks_col = st.columns(
                [1, 1.65, 1.45, 2],
                gap="small",
            )
            with timing_col:
                selected_timing = st.selectbox(
                    "Timing",
                    base._options(current_timing, timings),
                    key=f"{widget}_timing",
                )
            with activity_col:
                activity_options = base._unique([current_activity, *activities])
                selected_activity = st.selectbox(
                    "Activity",
                    activity_options,
                    key=f"{widget}_activity",
                )

            definition = dict(
                catalog.get(selected_activity) or prescribed or prior
            )
            with duration_col:
                selected_duration = st.text_input(
                    "Duration / Sets",
                    value=(
                        base._clean(prior.get("duration_or_reps"))
                        or base._clean(definition.get("duration_or_reps"))
                    ),
                    key=f"{widget}_{base._slug(selected_activity)}_duration",
                    placeholder="Example: 30 min / 2 sets of 10",
                )
            with remarks_col:
                remarks = st.text_input(
                    "Remarks",
                    value=base._clean(prior.get("member_notes")),
                    key=f"{widget}_remarks",
                    placeholder="Optional remarks",
                )

            status_col, time_col, save_col = st.columns(
                [1.1, 1.5, 1.35],
                gap="small",
            )
            with status_col:
                prior_status = (
                    prior.get("status")
                    if prior.get("status") in base.STATUS_OPTIONS
                    else "Not Started"
                )
                status = st.selectbox(
                    "Status",
                    base.STATUS_OPTIONS,
                    index=base.STATUS_OPTIONS.index(prior_status),
                    key=f"{widget}_status",
                )
            with time_col:
                completion_time = st.text_input(
                    "Completion time (optional)",
                    value=base._display_time(prior.get("completion_time")),
                    key=f"{widget}_completion_time",
                    placeholder="Example: 10:30 PM",
                )
            with save_col:
                st.markdown(
                    "<div style='height:1.55rem'></div>",
                    unsafe_allow_html=True,
                )
                save_clicked = st.button(
                    "Save Exercise Entry",
                    key=f"{widget}_save",
                    use_container_width=True,
                    disabled=(
                        selected_activity == "Select activity"
                        or not bool(profile.get("id"))
                    ),
                )

            if save_clicked:
                try:
                    base.save_member_exercise_log(
                        base.build_exercise_log_payload(
                            member_id=member_id,
                            log_date=log_date,
                            profile=profile,
                            day_number=int(contract.get("day_number") or 1),
                            item_order=item_order,
                            selected_activity=selected_activity,
                            selected_timing=selected_timing,
                            selected_duration=selected_duration,
                            remarks=remarks,
                            status=status,
                            completion_time=completion_time,
                            selected_definition=definition,
                        )
                    )
                    base.set_system_message(
                        "Exercise Journal entry saved for "
                        f"{selected_activity} on "
                        f"{selected_date.strftime('%d %b %Y')}.",
                        "success",
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Exercise Journal entry could not be saved: {exc}")

    st.markdown(
        "<span class='hm-exercise-actions-anchor'></span>",
        unsafe_allow_html=True,
    )
    add_col, remove_col = st.columns(2)
    with add_col:
        if st.button(
            "+ Add Exercise",
            key=f"{key_prefix}_add_{log_date}",
            disabled=row_count >= base.MAX_EXERCISE_ROWS,
            use_container_width=True,
        ):
            st.session_state[count_key] = min(
                base.MAX_EXERCISE_ROWS,
                row_count + 1,
            )
            st.rerun()
    with remove_col:
        if st.button(
            "Remove Exercise",
            key=f"{key_prefix}_remove_{log_date}",
            disabled=row_count <= base_count,
            use_container_width=True,
        ):
            st.session_state[count_key] = max(base_count, row_count - 1)
            st.rerun()

    base._render_saved_days(member_id, key_prefix, date_key, pending_key)
