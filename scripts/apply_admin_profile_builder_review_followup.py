from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {path}, found {count}: {old[:140]!r}")
    file_path.write_text(text.replace(old, new, 1))


def insert_before(path: str, anchor: str, block: str) -> None:
    replace_once(path, anchor, block + anchor)


# SS1: keep Setup details horizontal while space is available, then wrap safely.
replace_once(
    "components/member_plan_builder_setup.py",
    '''def render_member_plan_setup(options: Dict[str, List[str]]) -> None:
    st.markdown("<div class='hm-title'>Setup</div>", unsafe_allow_html=True)
''',
    '''def render_member_plan_setup(options: Dict[str, List[str]]) -> None:
    st.markdown("<div class='hm-title'>Setup</div>", unsafe_allow_html=True)
    st.markdown(
        """
<style id="hm-member-plan-setup-responsive-details-v1">
.mpb-setup-details-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stExpander"]:has(.mpb-setup-details-anchor) div[data-testid="stHorizontalBlock"]{
  display:grid!important;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr))!important;
  gap:.52rem!important;
  width:100%!important;
  align-items:start!important;
}
div[data-testid="stExpander"]:has(.mpb-setup-details-anchor) div[data-testid="stHorizontalBlock"]>div[data-testid="column"]{
  width:auto!important;
  min-width:0!important;
  max-width:none!important;
  flex:none!important;
}
@media(max-width:640px){
  div[data-testid="stExpander"]:has(.mpb-setup-details-anchor) div[data-testid="stHorizontalBlock"]{
    grid-template-columns:1fr!important;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )
''',
)
replace_once(
    "components/member_plan_builder_setup.py",
    '''    with st.expander("More setup details", expanded=False):
        row2 = st.columns(3, gap="small")
''',
    '''    with st.expander("More setup details", expanded=False):
        st.markdown(
            "<span class='mpb-setup-details-anchor'></span>",
            unsafe_allow_html=True,
        )
        row2 = st.columns(3, gap="small")
''',
)

# SS3: retain useful recipe metadata but present it as a responsive horizontal grid.
replace_once(
    "components/member_plan_builder_meals_compact.py",
    '''from components.member_plan_builder_export import (
    load_member_plan_events,
    meal_review_rows,
    render_publish_log_and_download,
)
''',
    '''from components.member_plan_builder_export import (
    load_profile_plan_events,
    meal_review_rows,
    render_publish_log_and_download,
)
''',
)
replace_once(
    "components/member_plan_builder_meals_compact.py",
    '''def _render_more_details(snapshot: Dict[str, Any]) -> None:
    with st.expander("More details", expanded=False):
        details = _source_detail_lines(snapshot)
        if not details:
            st.caption("No additional repository information is available.")
            return
        for label, value in details:
            st.markdown(f"**{label}:** {safe(value)}")
''',
    '''def _render_more_details(snapshot: Dict[str, Any]) -> None:
    with st.expander("More details", expanded=False):
        details = _source_detail_lines(snapshot)
        if not details:
            st.caption("No additional repository information is available.")
            return
        tiles = "".join(
            "<div class='mpb-recipe-detail-tile'>"
            f"<span>{safe(label)}</span><strong>{safe(value)}</strong>"
            "</div>"
            for label, value in details
        )
        st.markdown(
            f"<div class='mpb-recipe-detail-grid'>{tiles}</div>",
            unsafe_allow_html=True,
        )
''',
)
replace_once(
    "components/member_plan_builder_meals_compact.py",
    '''def render_member_plan_meals_compact(recipes: List[str], can_publish: bool) -> None:
    profile = st.session_state.get("pbm_profile") or {}
''',
    '''def render_member_plan_meals_compact(recipes: List[str], can_publish: bool) -> None:
    st.markdown(
        """
<style id="hm-member-plan-recipe-detail-grid-v1">
.mpb-recipe-detail-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:.46rem;
  width:100%;
  align-items:stretch;
}
.mpb-recipe-detail-tile{
  min-width:0;
  border:1px solid #E7D8BE;
  border-radius:10px;
  background:#FFFFFF;
  padding:.44rem .52rem;
}
.mpb-recipe-detail-tile span{
  display:block;
  color:#7A5A16;
  font-size:.68rem;
  font-weight:900;
  line-height:1.2;
  margin-bottom:.14rem;
}
.mpb-recipe-detail-tile strong{
  display:block;
  color:#334155;
  font-size:.76rem;
  font-weight:720;
  line-height:1.34;
  overflow-wrap:anywhere;
}
@media(max-width:640px){.mpb-recipe-detail-grid{grid-template-columns:1fr;}}
</style>
""",
        unsafe_allow_html=True,
    )
    profile = st.session_state.get("pbm_profile") or {}
''',
)
meals_path = Path("components/member_plan_builder_meals_compact.py")
meals_text = meals_path.read_text()
if meals_text.count("load_member_plan_events.clear()") != 2:
    raise RuntimeError("Expected two member-wide event cache clears in Meals")
meals_path.write_text(
    meals_text.replace("load_member_plan_events.clear()", "load_profile_plan_events.clear()")
)

# SS2: Publish & Change Log follows the exact profile currently open, not every profile for the member.
insert_before(
    "components/member_plan_builder_export.py",
    "\n\ndef build_member_plan_workbook(\n",
    '''

@st.cache_data(ttl=60, show_spinner=False)
def load_profile_plan_events(
    profile_id: str,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """Load change events for one opened profile only."""

    clean_profile_id = clean(profile_id)
    if not clean_profile_id:
        return False, [], "Save or select a profile to view its change history."
    try:
        client = _client()
        profile_result = (
            client.table(PROFILE_TABLE)
            .select("id,profile_name,status,start_date,updated_at")
            .eq("id", clean_profile_id)
            .limit(1)
            .execute()
        )
        profiles = _rows(profile_result)
        if not profiles:
            return False, [], "The selected profile could not be found."
        profile = profiles[0]
        profile_info = {
            "Plan": clean(profile.get("profile_name")) or "Untitled",
            "Current Status": clean(profile.get("status")).title(),
            "Plan Start": clean(profile.get("start_date")),
        }
        event_result = (
            client.table(EVENT_TABLE)
            .select(
                "profile_id,event_type,event_note,created_by_user_id,"
                "created_by_email,created_at"
            )
            .eq("profile_id", clean_profile_id)
            .order("created_at", desc=True)
            .limit(1000)
            .execute()
        )
        events: List[Dict[str, Any]] = []
        for row in _rows(event_result):
            events.append(
                {
                    "Changed At": clean(row.get("created_at"))[:19],
                    "Plan": profile_info["Plan"],
                    "Plan Status": profile_info["Current Status"],
                    "Plan Start": profile_info["Plan Start"],
                    "Action": clean(row.get("event_type")).replace("_", " ").title(),
                    "Change Detail": clean(row.get("event_note")),
                    "Changed By": clean(row.get("created_by_email"))
                    or clean(row.get("created_by_user_id"))
                    or "System",
                    "Profile ID": clean(row.get("profile_id")),
                }
            )
        return True, events, f"Loaded {len(events)} change event(s) for the selected profile."
    except Exception as exc:
        return False, [], f"Could not load selected profile history: {exc}"
''',
)
replace_once(
    "components/member_plan_builder_export.py",
    '''    member_id = clean(profile.get("assigned_member_id"))
    st.markdown(
''',
    '''    profile_id = clean(profile.get("id"))
    st.markdown(
''',
)
replace_once(
    "components/member_plan_builder_export.py",
    '''    ok, events, message = load_member_plan_events(member_id)
''',
    '''    ok, events, message = load_profile_plan_events(profile_id)
''',
)
replace_once(
    "components/member_plan_builder_export.py",
    '''    events_ok, events, _ = load_member_plan_events(
        clean(profile.get("assigned_member_id"))
    )
''',
    '''    events_ok, events, _ = load_profile_plan_events(selected_id)
''',
)

# SS4: remove duplicated Exercise details and add controlled Frequency/Timing dropdowns.
replace_once(
    "components/member_plan_builder_exercise.py",
    '''from components.exercise_member_allocation import (
    list_active_exercise_sources,
    list_member_exercise_allocations,
    save_exercise_member_allocation,
    stop_exercise_member_allocation,
)
''',
    '''from components.exercise_member_allocation import (
    EXERCISE_FREQUENCY_OPTIONS,
    EXERCISE_TIMING_OPTIONS,
    list_active_exercise_sources,
    list_member_exercise_allocations,
    save_exercise_member_allocation,
    stop_exercise_member_allocation,
)
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''def _render_source_details(source: Dict) -> None:
    source_summary(
        clean(source.get("title")) or "Exercise",
        (
            clean(source.get("duration_or_reps")),
            clean(source.get("difficulty")),
            clean(source.get("category")),
        ),
    )
    with st.expander("More details", expanded=False):
        st.markdown(
            "<span class='mpb-exercise-more-details-anchor'></span>",
            unsafe_allow_html=True,
        )
        details = (
            ("Category", source.get("category")),
            ("Difficulty", source.get("difficulty")),
            ("Duration / Reps", source.get("duration_or_reps")),
            ("Equipment", source.get("equipment")),
            ("Benefits", source.get("benefits")),
        )
        shown = False
        for label, value in details:
            if clean(value):
                shown = True
                st.markdown(f"**{label}:** {clean(value)}")
        if not shown:
            st.caption("No additional repository information is available.")
''',
    '''def _frequency_value(value: object) -> int:
    try:
        candidate = int(value or 1)
    except Exception:
        candidate = 1
    return candidate if candidate in EXERCISE_FREQUENCY_OPTIONS else 1


def _timing_value(value: object) -> str:
    candidate = clean(value)
    return candidate if candidate in EXERCISE_TIMING_OPTIONS else "As advised"


def _render_source_details(source: Dict) -> None:
    source_summary(
        clean(source.get("title")) or "Exercise",
        (
            clean(source.get("duration_or_reps")),
            clean(source.get("difficulty")),
            clean(source.get("category")),
        ),
    )
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''        end = date_cols[1].date_input(
            "End Date",
            dt.date.today() + dt.timedelta(days=6),
            key=f"mpb_ex_add_end_{member_id}",
        )
        note_cols = st.columns(2, gap="small")
''',
    '''        end = date_cols[1].date_input(
            "End Date",
            dt.date.today() + dt.timedelta(days=6),
            key=f"mpb_ex_add_end_{member_id}",
        )
        prescription_cols = st.columns(2, gap="small")
        default_frequency = _frequency_value(source.get("frequency_per_week"))
        frequency_per_week = prescription_cols[0].selectbox(
            "Frequency per week",
            EXERCISE_FREQUENCY_OPTIONS,
            index=EXERCISE_FREQUENCY_OPTIONS.index(default_frequency),
            key=f"mpb_ex_add_frequency_{member_id}",
        )
        default_timing = _timing_value(source.get("timing") or source.get("time_of_day"))
        timing = prescription_cols[1].selectbox(
            "Timing",
            EXERCISE_TIMING_OPTIONS,
            index=EXERCISE_TIMING_OPTIONS.index(default_timing),
            key=f"mpb_ex_add_timing_{member_id}",
        )
        note_cols = st.columns(2, gap="small")
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''                    end_date=end,
                    instructions=instructions,
''',
    '''                    end_date=end,
                    frequency_per_week=frequency_per_week,
                    timing=timing,
                    instructions=instructions,
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''                    "End": row.get("end_date") or "Open",
                    "Status": clean(row.get("status")).title(),
''',
    '''                    "End": row.get("end_date") or "Open",
                    "Frequency": row.get("frequency_per_week"),
                    "Timing": row.get("timing"),
                    "Status": clean(row.get("status")).title(),
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''        edit_end = date_cols[1].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_end_{allocation_id}",
        )
        note_cols = st.columns(2, gap="small")
''',
    '''        edit_end = date_cols[1].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_end_{allocation_id}",
        )
        prescription_cols = st.columns(2, gap="small")
        current_frequency = _frequency_value(selected.get("frequency_per_week"))
        edit_frequency_per_week = prescription_cols[0].selectbox(
            "Frequency per week",
            EXERCISE_FREQUENCY_OPTIONS,
            index=EXERCISE_FREQUENCY_OPTIONS.index(current_frequency),
            disabled=stopped,
            key=f"mpb_ex_edit_frequency_{allocation_id}",
        )
        current_timing = _timing_value(selected.get("timing"))
        edit_timing = prescription_cols[1].selectbox(
            "Timing",
            EXERCISE_TIMING_OPTIONS,
            index=EXERCISE_TIMING_OPTIONS.index(current_timing),
            disabled=stopped,
            key=f"mpb_ex_edit_timing_{allocation_id}",
        )
        note_cols = st.columns(2, gap="small")
''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''                    end_date=edit_end,
                    instructions=edit_instruction,
''',
    '''                    end_date=edit_end,
                    frequency_per_week=edit_frequency_per_week,
                    timing=edit_timing,
                    instructions=edit_instruction,
''',
)
exercise_path = Path("components/member_plan_builder_exercise.py")
exercise_text = exercise_path.read_text()
style_start = exercise_text.index("\ndef _render_exercise_polish_styles() -> None:\n")
style_end = exercise_text.index("\ndef render_member_plan_exercise() -> None:\n", style_start)
exercise_text = exercise_text[:style_start] + exercise_text[style_end:]
exercise_text = exercise_text.replace(
    "def render_member_plan_exercise() -> None:\n    _render_exercise_polish_styles()\n",
    "def render_member_plan_exercise() -> None:\n",
    1,
)
exercise_path.write_text(exercise_text)

# Persist Exercise prescription metadata without changing allocation authority.
replace_once(
    "components/exercise_member_allocation.py",
    '''INACTIVE_STATUSES = {"inactive", "stopped", "archived"}
''',
    '''INACTIVE_STATUSES = {"inactive", "stopped", "archived"}
EXERCISE_FREQUENCY_OPTIONS = tuple(range(1, 8))
EXERCISE_TIMING_OPTIONS = (
    "Morning",
    "Afternoon",
    "Evening",
    "Night",
    "As advised",
)
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''def _normalise_status(value: Any) -> str:
    return "stopped" if _clean(value).lower() in INACTIVE_STATUSES else ACTIVE_STATUS
''',
    '''def _normalise_status(value: Any) -> str:
    return "stopped" if _clean(value).lower() in INACTIVE_STATUSES else ACTIVE_STATUS


def _normalise_frequency(value: Any, *, strict: bool = False) -> int:
    try:
        frequency = int(value or 1)
    except Exception:
        frequency = 0
    if frequency in EXERCISE_FREQUENCY_OPTIONS:
        return frequency
    if strict and _clean(value):
        raise ValueError("Frequency per week must be between 1 and 7.")
    return 1


def _normalise_timing(value: Any, *, strict: bool = False) -> str:
    timing = _clean(value)
    if timing in EXERCISE_TIMING_OPTIONS:
        return timing
    if strict and timing:
        raise ValueError("Timing must use an approved Exercise timing option.")
    return "As advised"
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''        "end_date": _clean(source.get("end_date")),
        "instructions": _clean(source.get("instructions")),
''',
    '''        "end_date": _clean(source.get("end_date")),
        "frequency_per_week": _normalise_frequency(source.get("frequency_per_week")),
        "timing": _normalise_timing(source.get("timing")),
        "instructions": _clean(source.get("instructions")),
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''    start_date: Any = "",
    end_date: Any = "",
    instructions: Any = "",
''',
    '''    start_date: Any = "",
    end_date: Any = "",
    frequency_per_week: Any = None,
    timing: Any = None,
    instructions: Any = "",
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''    if not source:
        raise ValueError("Exercise repository source was not found.")

    display_title = (
''',
    '''    if not source:
        raise ValueError("Exercise repository source was not found.")

    frequency_value = (
        existing.get("frequency_per_week")
        if existing and frequency_per_week is None
        else frequency_per_week
    )
    timing_value = existing.get("timing") if existing and timing is None else timing
    frequency = _normalise_frequency(
        frequency_value,
        strict=frequency_per_week is not None,
    )
    allocation_timing = _normalise_timing(
        timing_value,
        strict=timing is not None,
    )

    display_title = (
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''        "end_date": end,
        "instructions": _clean(instructions),
''',
    '''        "end_date": end,
        "frequency_per_week": frequency,
        "timing": allocation_timing,
        "instructions": _clean(instructions),
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''            "status": saved["status"],
            "actor_id": _clean(actor_id) or "admin",
''',
    '''            "status": saved["status"],
            "frequency_per_week": saved["frequency_per_week"],
            "timing": saved["timing"],
            "actor_id": _clean(actor_id) or "admin",
''',
)
replace_once(
    "components/exercise_member_allocation.py",
    '''        start_date=allocation.get("start_date", ""),
        end_date=end_date,
        instructions=allocation.get("instructions", ""),
''',
    '''        start_date=allocation.get("start_date", ""),
        end_date=end_date,
        frequency_per_week=allocation.get("frequency_per_week"),
        timing=allocation.get("timing"),
        instructions=allocation.get("instructions", ""),
''',
)

# Surface the new prescription metadata in the read-only Current Member Plan.
insert_before(
    "components/current_member_plan_view.py",
    "\n\ndef _render_allocation_card(row: dict[str, Any], domain: str) -> None:\n",
    '''

def _frequency_label(value: Any) -> str:
    text = _clean(value)
    return f"{text}x/week" if text else ""
''',
)
replace_once(
    "components/current_member_plan_view.py",
    '''            _chip("Duration/Reps", snapshot.get("duration_or_reps")),
            _chip("Equipment", snapshot.get("equipment")),
''',
    '''            _chip("Duration/Reps", snapshot.get("duration_or_reps")),
            _chip("Frequency", _frequency_label(row.get("frequency_per_week"))),
            _chip("Timing", row.get("timing")),
            _chip("Equipment", snapshot.get("equipment")),
''',
)
