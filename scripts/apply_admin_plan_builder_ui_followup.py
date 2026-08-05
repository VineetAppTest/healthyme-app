from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text()
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1))


# Meals: render repository details in a responsive horizontal flow that wraps.
replace_once(
    "components/member_plan_builder_meals_compact.py",
    '''def _render_more_details(snapshot: Dict[str, Any]) -> None:\n    with st.expander("More details", expanded=False):\n        details = _source_detail_lines(snapshot)\n        if not details:\n            st.caption("No additional repository information is available.")\n            return\n        for label, value in details:\n            st.markdown(f"**{label}:** {safe(value)}")\n''',
    '''def _render_more_details(snapshot: Dict[str, Any]) -> None:\n    with st.expander("More details", expanded=False):\n        details = _source_detail_lines(snapshot)\n        if not details:\n            st.caption("No additional repository information is available.")\n            return\n        long_labels = {"Ingredients", "Preparation", "Repository Instructions"}\n        detail_html = "".join(\n            f"<div class='mpb-responsive-detail{' mpb-responsive-detail-wide' if label in long_labels else ''}'>"\n            f"<b>{safe(label)}:</b><span>{safe(value)}</span></div>"\n            for label, value in details\n        )\n        st.markdown(\n            f"<div class='mpb-responsive-details'>{detail_html}</div>",\n            unsafe_allow_html=True,\n        )\n''',
)

replace_once(
    "components/member_plan_builder_meals_compact.py",
    '''def render_member_plan_meals_compact(recipes: List[str], can_publish: bool) -> None:\n    profile = st.session_state.get("pbm_profile") or {}\n''',
    '''def render_member_plan_meals_compact(recipes: List[str], can_publish: bool) -> None:\n    st.markdown(\n        """\n<style id="hm-admin-plan-builder-responsive-details-v1">\n.mpb-responsive-details{display:flex;flex-wrap:wrap;align-items:flex-start;gap:.48rem 1rem;width:100%;}\n.mpb-responsive-detail{display:inline-flex;align-items:flex-start;gap:.25rem;flex:0 1 auto;max-width:100%;font-size:.82rem;line-height:1.35;color:#334155;}\n.mpb-responsive-detail b{color:#064E3B;white-space:nowrap;}\n.mpb-responsive-detail span{min-width:0;overflow-wrap:anywhere;}\n.mpb-responsive-detail-wide{flex:1 1 22rem;}\n@media(max-width:720px){.mpb-responsive-detail,.mpb-responsive-detail-wide{flex:1 1 100%;}}\n</style>\n""",\n        unsafe_allow_html=True,\n    )\n    profile = st.session_state.get("pbm_profile") or {}\n''',
)

# Change Log: keep existing member-wide loader for compatibility, but use an
# exact-profile loader on the open/selected profile surfaces.
insert_marker = '''def build_member_plan_workbook(\n'''
export_path = ROOT / "components/member_plan_builder_export.py"
export_text = export_path.read_text()
profile_loader = '''@st.cache_data(ttl=60, show_spinner=False)\ndef load_profile_plan_events(profile_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:\n    clean_profile_id = clean(profile_id)\n    if not clean_profile_id:\n        return False, [], "Select a profile to view its change history."\n    try:\n        client = _client()\n        profile_result = (\n            client.table(PROFILE_TABLE)\n            .select("id,profile_name,status,start_date,updated_at")\n            .eq("id", clean_profile_id)\n            .limit(1)\n            .execute()\n        )\n        profiles = _rows(profile_result)\n        if not profiles:\n            return True, [], "No plan history exists for this profile."\n        profile = profiles[0]\n        event_result = (\n            client.table(EVENT_TABLE)\n            .select(\n                "profile_id,event_type,event_note,created_by_user_id,"\n                "created_by_email,created_at"\n            )\n            .eq("profile_id", clean_profile_id)\n            .order("created_at", desc=True)\n            .limit(1000)\n            .execute()\n        )\n        events = [\n            {\n                "Changed At": clean(row.get("created_at"))[:19],\n                "Plan": clean(profile.get("profile_name")) or "Untitled",\n                "Plan Status": clean(profile.get("status")).title(),\n                "Plan Start": clean(profile.get("start_date")),\n                "Action": clean(row.get("event_type")).replace("_", " ").title(),\n                "Change Detail": clean(row.get("event_note")),\n                "Changed By": clean(row.get("created_by_email"))\n                or clean(row.get("created_by_user_id"))\n                or "System",\n                "Profile ID": clean(row.get("profile_id")),\n            }\n            for row in _rows(event_result)\n        ]\n        return True, events, f"Loaded {len(events)} profile change event(s)."\n    except Exception as exc:\n        return False, [], f"Could not load profile change history: {exc}"\n\n\n'''
if profile_loader not in export_text:
    if insert_marker not in export_text:
        raise RuntimeError("Export insertion marker not found")
    export_text = export_text.replace(insert_marker, profile_loader + insert_marker, 1)
export_text = export_text.replace(
    '''    member_id = clean(profile.get("assigned_member_id"))\n''',
    '''    profile_id = clean(profile.get("id"))\n''',
    1,
)
export_text = export_text.replace(
    '''    ok, events, message = load_member_plan_events(member_id)\n''',
    '''    ok, events, message = load_profile_plan_events(profile_id)\n''',
    1,
)
export_text = export_text.replace(
    '''    events_ok, events, _ = load_member_plan_events(\n        clean(profile.get("assigned_member_id"))\n    )\n''',
    '''    events_ok, events, _ = load_profile_plan_events(\n        clean(profile.get("id"))\n    )\n''',
    1,
)
export_path.write_text(export_text)

# Exercise: remove duplicate source summary and present More Details as a
# responsive horizontal flow with long Benefits content allowed to wrap.
replace_once(
    "components/member_plan_builder_exercise.py",
    '''def _render_source_details(source: Dict) -> None:\n    source_summary(\n        clean(source.get("title")) or "Exercise",\n        (\n            clean(source.get("duration_or_reps")),\n            clean(source.get("difficulty")),\n            clean(source.get("category")),\n        ),\n    )\n    with st.expander("More details", expanded=False):\n        st.markdown(\n            "<span class='mpb-exercise-more-details-anchor'></span>",\n            unsafe_allow_html=True,\n        )\n        details = (\n            ("Category", source.get("category")),\n            ("Difficulty", source.get("difficulty")),\n            ("Duration / Reps", source.get("duration_or_reps")),\n            ("Equipment", source.get("equipment")),\n            ("Benefits", source.get("benefits")),\n        )\n        shown = False\n        for label, value in details:\n            if clean(value):\n                shown = True\n                st.markdown(f"**{label}:** {clean(value)}")\n        if not shown:\n            st.caption("No additional repository information is available.")\n''',
    '''def _render_source_details(source: Dict) -> None:\n    with st.expander("More details", expanded=False):\n        st.markdown(\n            "<span class='mpb-exercise-more-details-anchor'></span>",\n            unsafe_allow_html=True,\n        )\n        details = [\n            (label, clean(value))\n            for label, value in (\n                ("Category", source.get("category")),\n                ("Difficulty", source.get("difficulty")),\n                ("Duration / Reps", source.get("duration_or_reps")),\n                ("Equipment", source.get("equipment")),\n                ("Benefits", source.get("benefits")),\n            )\n            if clean(value)\n        ]\n        if not details:\n            st.caption("No additional repository information is available.")\n            return\n        detail_html = "".join(\n            f"<div class='mpb-exercise-detail{' mpb-exercise-detail-wide' if label == 'Benefits' else ''}'>"\n            f"<b>{label}:</b><span>{value}</span></div>"\n            for label, value in details\n        )\n        st.markdown(\n            f"<div class='mpb-exercise-detail-wrap'>{detail_html}</div>",\n            unsafe_allow_html=True,\n        )\n''',
)
replace_once(
    "components/member_plan_builder_exercise.py",
    '''div[data-testid="stExpander"]:has(.mpb-exercise-more-details-anchor) [data-testid="stExpanderDetails"]{\n  padding:.42rem .58rem .52rem!important;\n}\n''',
    '''div[data-testid="stExpander"]:has(.mpb-exercise-more-details-anchor) [data-testid="stExpanderDetails"]{\n  padding:.42rem .58rem .52rem!important;\n}\n.mpb-exercise-detail-wrap{display:flex;flex-wrap:wrap;align-items:flex-start;gap:.45rem 1rem;width:100%;}\n.mpb-exercise-detail{display:inline-flex;align-items:flex-start;gap:.25rem;flex:0 1 auto;max-width:100%;font-size:.80rem;line-height:1.35;color:#334155;}\n.mpb-exercise-detail b{color:#064E3B;white-space:nowrap;}\n.mpb-exercise-detail span{min-width:0;overflow-wrap:anywhere;}\n.mpb-exercise-detail-wide{flex:1 1 22rem;}\n@media(max-width:720px){.mpb-exercise-detail,.mpb-exercise-detail-wide{flex:1 1 100%;}}\n''',
)

# Supplement: remove the duplicate summary/More Details section and restore the
# approved repository dropdown choices for Frequency and Timing.
supp_path = ROOT / "components/member_plan_builder_supplement.py"
supp = supp_path.read_text()
supp = supp.replace(
    '''from components.pbm_core import clean\n''',
    '''from components.pbm_core import clean\n\n\nTIMING_OPTIONS = [\n    "Morning",\n    "Midday",\n    "Evening",\n    "Before Bed",\n    "With Food",\n    "Empty Stomach",\n    "After Meals",\n]\nFREQUENCY_OPTIONS = [\n    "Once",\n    "Twice",\n    "Thrice",\n    "Four times",\n    "Five times",\n    "Six times",\n    "Seven times",\n    "Eight times",\n    "Nine times",\n    "Ten times",\n]\n\n\ndef _options_with_current(options: list[str], current: object) -> list[str]:\n    value = clean(current)\n    return options + [value] if value and value not in options else list(options)\n''',
    1,
)
start = supp.index("def _render_source_details(source: Dict) -> None:\n")
end = supp.index("\n\ndef _render_add_supplement", start)
supp = supp[:start] + supp[end + 2:]
supp = supp.replace("        _render_source_details(source)\n\n", "", 1)
supp = supp.replace(
    '''        frequency = fields[1].text_input(\n            "Frequency",\n            value=clean(source.get("frequency")),\n            key=f"mpb_su_add_frequency_{member_id}",\n        )\n        timing = fields[2].text_input(\n            "Timing",\n            value=clean(source.get("timing")),\n            key=f"mpb_su_add_timing_{member_id}",\n        )\n''',
    '''        frequency_options = _options_with_current(\n            FREQUENCY_OPTIONS, source.get("frequency")\n        )\n        current_frequency = clean(source.get("frequency")) or FREQUENCY_OPTIONS[0]\n        frequency = fields[1].selectbox(\n            "Frequency",\n            frequency_options,\n            index=frequency_options.index(current_frequency),\n            key=f"mpb_su_add_frequency_{member_id}",\n        )\n        timing_options = _options_with_current(TIMING_OPTIONS, source.get("timing"))\n        current_timing = clean(source.get("timing")) or TIMING_OPTIONS[0]\n        timing = fields[2].selectbox(\n            "Timing",\n            timing_options,\n            index=timing_options.index(current_timing),\n            key=f"mpb_su_add_timing_{member_id}",\n        )\n''',
    1,
)
supp = supp.replace(
    '''        frequency = fields[1].text_input(\n            "Frequency",\n            value=clean(selected.get("frequency")),\n            disabled=stopped,\n            key=f"mpb_su_edit_frequency_{allocation_id}",\n        )\n        timing = fields[2].text_input(\n            "Timing",\n            value=clean(selected.get("timing")),\n            disabled=stopped,\n            key=f"mpb_su_edit_timing_{allocation_id}",\n        )\n''',
    '''        edit_frequency_options = _options_with_current(\n            FREQUENCY_OPTIONS, selected.get("frequency")\n        )\n        current_edit_frequency = clean(selected.get("frequency")) or FREQUENCY_OPTIONS[0]\n        frequency = fields[1].selectbox(\n            "Frequency",\n            edit_frequency_options,\n            index=edit_frequency_options.index(current_edit_frequency),\n            disabled=stopped,\n            key=f"mpb_su_edit_frequency_{allocation_id}",\n        )\n        edit_timing_options = _options_with_current(\n            TIMING_OPTIONS, selected.get("timing")\n        )\n        current_edit_timing = clean(selected.get("timing")) or TIMING_OPTIONS[0]\n        timing = fields[2].selectbox(\n            "Timing",\n            edit_timing_options,\n            index=edit_timing_options.index(current_edit_timing),\n            disabled=stopped,\n            key=f"mpb_su_edit_timing_{allocation_id}",\n        )\n''',
    1,
)
if "_render_source_details" in supp:
    raise RuntimeError("Supplement More Details renderer was not fully removed")
supp_path.write_text(supp)

print("Admin Plan Builder UI follow-up applied")
