from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {count}")
    return updated


# 1. Setup: keep the core plan identity visible; move all member-plan metadata into More setup details.
path = "components/member_plan_builder_setup.py"
text = read(path)
pattern = r'''    row2 = st\.columns\(3, gap="small"\)\n.*?        st\.caption\(\n            "Clone Complete Plan copies Setup and all seven-day Meal rows into a new Draft\. Exercise and Supplement allocations retain their independent IDs and history\."\n        \)\n'''
replacement = '''    with st.expander("More setup details", expanded=False):
        row2 = st.columns(3, gap="small")
        profile["region"] = row2[0].text_input(
            "Region / Food Culture",
            value=clean(profile.get("region")),
            key=f"mpb_region_{epoch}",
        )
        diet_options = with_placeholder(list(options.get("diet_type") or []), SELECT_DIET)
        current_diet = clean(profile.get("diet_type")) or SELECT_DIET
        if current_diet not in diet_options:
            diet_options.append(current_diet)
        profile["diet_type"] = row2[1].selectbox(
            "Diet Type",
            diet_options,
            index=diet_options.index(current_diet),
            key=f"mpb_diet_{epoch}",
        )
        age_options = with_placeholder(list(options.get("age_band") or []), SELECT_AGE)
        current_age = clean(profile.get("age_band")) or SELECT_AGE
        if current_age not in age_options:
            age_options.append(current_age)
        profile["age_band"] = row2[2].selectbox(
            "Age Band",
            age_options,
            index=age_options.index(current_age),
            key=f"mpb_age_{epoch}",
        )

        concerns = list(options.get("health_concern") or [])
        for concern in profile.get("health_concerns") or []:
            if concern not in concerns:
                concerns.append(concern)
        profile["health_concerns"] = st.multiselect(
            "Health Concerns",
            concerns,
            default=list(profile.get("health_concerns") or []),
            key=f"mpb_concerns_{epoch}",
        )

        note_col, change_col = st.columns(2, gap="small")
        profile["profile_note"] = note_col.text_area(
            "Nutritionist Note",
            value=clean(profile.get("profile_note")),
            height=72,
            key=f"mpb_note_{epoch}",
        )
        profile["change_note"] = change_col.text_area(
            "Change Note",
            value=clean(profile.get("change_note")),
            height=72,
            key=f"mpb_change_note_{epoch}",
        )
'''
text = regex_once(text, pattern, replacement, "setup details block")
write(path, text)

# 2. Meals: remove the redundant guide row.
path = "components/member_plan_builder_meals_compact.py"
text = read(path)
old = '''    st.markdown(
        "<div class='mpb-meal-guide'><b>Recipe</b><b>Portion guidance</b>"
        "<b>Member instruction</b><b>Add</b></div>",
        unsafe_allow_html=True,
    )
'''
text = replace_once(text, old, "", "meal guide")
write(path, text)

# 3. Member Plan disclosures: suppress native text/icon markers and retain one custom +/- marker.
path = "components/profile_builder_modular.py"
text = read(path)
text = replace_once(
    text,
    'div[data-testid="stExpander"] details summary{list-style:none!important;min-height:2.42rem!important;padding:.42rem .58rem!important;display:flex!important;align-items:center!important;gap:.48rem!important;border-radius:9px!important}',
    'div[data-testid="stExpander"] details summary{list-style:none!important;min-height:2.42rem!important;padding:.42rem .58rem!important;display:flex!important;align-items:center!important;gap:.48rem!important;border-radius:9px!important;font-size:0!important}',
    "profile expander summary",
)
text = replace_once(
    text,
    'div[data-testid="stExpander"] details summary svg,div[data-testid="stExpander"] details summary [data-testid="stExpanderToggleIcon"]{display:none!important;width:0!important;min-width:0!important}',
    'div[data-testid="stExpander"] details summary svg,div[data-testid="stExpander"] details summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"] details summary [data-testid="stIconMaterial"],div[data-testid="stExpander"] details summary [class*="material-symbol"],div[data-testid="stExpander"] details summary span[aria-hidden="true"]{display:none!important;width:0!important;min-width:0!important;font-size:0!important}',
    "profile expander native marker",
)
write(path, text)

# 4. View Member Plan: remove internal integrity/build copy and use one weekly-table family.
path = "components/member_plan_builder_view_compact.py"
text = read(path)
text = replace_once(text, "from collections import defaultdict\n", "from collections import defaultdict\nfrom datetime import date, datetime, timedelta\n", "view date import")
start = text.index("def _plain_table_cell")
end = text.index("def _legacy_rows", start)
new_helpers = '''def _plain_table_cell(value: object) -> str:
    return html.unescape(str(value or "").replace("<br>", "\n"))


def _parse_date(value: object) -> date | None:
    raw = clean(value)
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            pass
    return None


def _html_cell(value: object) -> str:
    text = _plain_table_cell(value)
    return "<br>".join(html.escape(line) for line in text.splitlines())


def _render_weekly_table(
    start_date: str,
    section_type: str,
    headers: tuple[str, str, str, str],
    day_cells,
) -> None:
    rows = []
    for day_number in range(1, 8):
        cells = tuple(day_cells(day_number))
        prefix = ""
        if day_number == 1:
            prefix = (
                f"<td rowspan='7' class='mpb-weekly-fixed'>{_html_cell(start_date)}</td>"
                f"<td rowspan='7' class='mpb-weekly-fixed'>{html.escape(section_type)}</td>"
            )
        rows.append(
            "<tr>"
            f"{prefix}<td class='mpb-weekly-day'>Day {day_number}</td>"
            + "".join(f"<td>{_html_cell(value)}</td>" for value in cells)
            + "</tr>"
        )
    st.markdown(
        """
<style id="mpb-weekly-table-v1">
.mpb-weekly-wrap{overflow:auto;border:1px solid #D8A84E;border-radius:12px;background:#fff;margin:.34rem 0 .78rem}.mpb-weekly-table{width:100%;border-collapse:collapse;font-size:.75rem;line-height:1.28}.mpb-weekly-table th{background:#FFF4DE;color:#064E3B;font-weight:900;text-align:center;padding:.45rem .42rem;border:1px solid #D8A84E}.mpb-weekly-table td{color:#334155;font-weight:650;padding:.45rem .42rem;border:1px solid #E3C98E;vertical-align:top}.mpb-weekly-table .mpb-weekly-fixed,.mpb-weekly-table .mpb-weekly-day{text-align:center;vertical-align:middle;color:#064E3B;font-weight:900;white-space:nowrap}.mpb-weekly-title{color:#064E3B;font-size:.92rem;font-weight:950;margin:.72rem 0 .28rem}
</style>
""",
        unsafe_allow_html=True,
    )
    header_html = "".join(f"<th>{html.escape(value)}</th>" for value in headers)
    st.markdown(
        f"<div class='mpb-weekly-title'>{html.escape(section_type)}</div>"
        "<div class='mpb-weekly-wrap'><table class='mpb-weekly-table'>"
        "<thead><tr><th>Start Date</th><th>Type</th><th>Day</th>"
        f"{header_html}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _model_rows(model: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    partitions = dict(model.get(domain) or {})
    output: List[Dict[str, Any]] = []
    for state in ("current", "upcoming"):
        output.extend(dict(row or {}) for row in partitions.get(state) or [])
    return output


def _row_applies_to_date(row: Dict[str, Any], target: date | None) -> bool:
    if target is None:
        return True
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    if start and target < start:
        return False
    if end and target > end:
        return False
    return True


def _allocation_day_cells(
    model: Dict[str, Any],
    domain: str,
    plan_start: str,
    day_number: int,
) -> tuple[str, str, str, str]:
    parsed_start = _parse_date(plan_start)
    target = parsed_start + timedelta(days=day_number - 1) if parsed_start else None
    rows = [row for row in _model_rows(model, domain) if _row_applies_to_date(row, target)]
    timing: List[str] = []
    names: List[str] = []
    values: List[str] = []
    remarks: List[str] = []
    for row in rows:
        snapshot = dict(row.get("source_snapshot") or {})
        timing.append(clean(row.get("timing") or snapshot.get("timing")))
        if domain == "exercise":
            names.append(clean(row.get("exercise_name") or row.get("title") or snapshot.get("title")))
            values.append(clean(snapshot.get("duration_or_reps")))
        else:
            names.append(clean(row.get("supplement_name") or row.get("title") or snapshot.get("supplement_name") or snapshot.get("title")))
            dose = clean(row.get("dosage") or snapshot.get("dosage"))
            frequency = clean(row.get("frequency") or snapshot.get("frequency"))
            values.append(" · ".join(value for value in (dose, frequency) if value))
        remarks.append(clean(row.get("instructions") or snapshot.get("instructions")))
    joined = lambda items: "\n".join(value for value in items if value)
    return joined(timing), joined(names), joined(values), joined(remarks)


'''
text = text[:start] + new_helpers + text[end:]
text = regex_once(text, r'def _render_allocation_table\(.*?\n\n\ndef render_view_member_plan_compact', 'def render_view_member_plan_compact', "remove old allocation renderer")
text = regex_once(
    text,
    r'''        st\.markdown\(\n            "<div class='mpb-integrity-note'>Active-plan integrity verified: Meals, Exercise and Supplement are consolidated for the same member\.</div>",\n            unsafe_allow_html=True,\n        \)\n''',
    "",
    "remove integrity banner",
)
old_render = '''    _render_meal_plan_table(
        clean(profile.get("start_date")),
        items,
    )

    if model:
        _render_allocation_table(
            "Exercise Allocations",
            _allocation_rows(model, "exercise"),
            "No current or upcoming Exercise allocation.",
        )
        _render_allocation_table(
            "Supplement Allocations",
            _allocation_rows(model, "supplement"),
            "No current or upcoming Supplement allocation.",
        )
'''
new_render = '''    plan_start = clean(profile.get("start_date"))
    _render_weekly_table(
        plan_start,
        "Meal",
        ("Timing", "Meal", "Liquid", "Remarks"),
        lambda day_number: _meal_cells(items, day_number),
    )

    if model:
        _render_weekly_table(
            plan_start,
            "Exercise",
            ("Timing", "Activity", "Duration/Sets", "Remarks"),
            lambda day_number: _allocation_day_cells(
                model, "exercise", plan_start, day_number
            ),
        )
        _render_weekly_table(
            plan_start,
            "Supplement",
            ("Timing", "Supplement", "Dosage", "Remarks"),
            lambda day_number: _allocation_day_cells(
                model, "supplement", plan_start, day_number
            ),
        )
'''
text = replace_once(text, old_render, new_render, "weekly plan render")
write(path, text)

# Hide page-internal diagnostics/build copy from the production Member Plan Builder.
path = "pages/38_Admin_Recommendation_Profile_Builder.py"
text = read(path)
text = regex_once(text, r'from components\.performance_diagnostics import \(\n.*?\n\)\n', '', "diagnostics import")
text = text.replace('begin_page_measurement("Recommendation Profile Builder")\n', '')
text = text.replace('finish_and_render_page_diagnostics("Recommendation Profile Builder")\n', '')
write(path, text)

# 5. Repository pages: sharp active/inactive tabs, centered actions, one aligned +/- marker.
repo_css = '''
/* Authenticated smoke repository correction. */
div[data-testid="stTabs"] [role="tablist"]{gap:.62rem!important;border:0!important;margin:.12rem 0 .65rem!important;}
div[data-testid="stTabs"] button[role="tab"]{min-width:10.5rem!important;min-height:2.35rem!important;border:1.3px solid #D8A84E!important;border-radius:10px!important;background:#FFFFFF!important;color:#064E3B!important;font-weight:900!important;box-shadow:0 4px 10px rgba(6,78,59,.04)!important;}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{background:linear-gradient(135deg,#064E3B,#0F766E)!important;color:#FFFFFF!important;border-color:#064E3B!important;}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *{color:#FFFFFF!important;}
div[data-testid="stExpander"] summary{display:flex!important;align-items:center!important;gap:.42rem!important;font-size:0!important;}
div[data-testid="stExpander"] summary p{display:block!important;margin:0!important;font-size:.82rem!important;line-height:1.2!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;text-align:left!important;}
div[data-testid="stExpander"] summary svg,div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"] summary [data-testid="stIconMaterial"],div[data-testid="stExpander"] summary [class*="material-symbol"],div[data-testid="stExpander"] summary span[aria-hidden="true"]{display:none!important;width:0!important;min-width:0!important;font-size:0!important;}
'''
for path in (
    "pages/15_Admin_Recipe_Manager.py",
    "pages/16_Admin_Exercise_Manager.py",
    "pages/39_Admin_Supplement_Manager.py",
):
    text = read(path)
    text = text.replace('</style>', repo_css + '\n</style>', 1)
    text = text.replace(
        'details_col, edit_col, delete_col = st.columns([5.8, 0.72, 0.82], gap="small")',
        'details_col, edit_col, delete_col = st.columns(\n            [5.8, 0.72, 0.82], gap="small", vertical_alignment="center"\n        )',
    )
    write(path, text)

# 6. Scheduling: strong empty-state differentiator and centrally aligned day table.
path = "components/admin_schedule_feedback_aug04.py"
text = read(path)
text = replace_once(text, "  border:1px solid #E3C98E;\n  border-radius:13px;\n  background:#FFFDF8;\n  color:#64748B;", "  border:1.4px solid #D8A84E;\n  border-radius:12px;\n  background:#FFF7E6;\n  color:#334155;", "schedule empty state")
text = text.replace("  text-align:left;\n  padding:.50rem .48rem;", "  text-align:center;\n  padding:.50rem .48rem;")
text = text.replace("  vertical-align:top;\n  overflow-wrap:anywhere;", "  vertical-align:middle;\n  text-align:center;\n  overflow-wrap:anywhere;")
write(path, text)

# 7. Member Home structural header shell from the validated superseded PR.
path = "pages/02_Member_Home.py"
text = read(path)
old_top = '''<style id="hm-member-home-local-style-v2">
/* Member Home only: injected before page reads so the first visible row starts at the top. */
html,body,#root{margin-top:0!important;padding-top:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
html body [data-testid="stAppViewContainer"],html body [data-testid="stAppViewContainer"] > .main,html body [data-testid="stMain"],html body section.main{padding-top:0!important;padding-block-start:0!important;margin-top:0!important;top:0!important;}
html body [data-testid="stMainBlockContainer"],html body [data-testid="stAppViewBlockContainer"],html body section.main > div.block-container,html body .main .block-container,html body .stMainBlockContainer,html body .block-container{padding-top:0!important;padding-block-start:0!important;margin-top:0!important;}
'''
new_top = '''<style id="hm-member-home-local-style-v3">
/* One structural shell owns the identity row and hero spacing. */
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
.hm-member-home-root-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stElementContainer"]:has(.hm-member-home-root-anchor),div.element-container:has(.hm-member-home-root-anchor),div[data-testid="stElementContainer"]:has(style#hm-member-home-local-style-v3),div.element-container:has(style#hm-member-home-local-style-v3){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stAppViewContainer"] .block-container:has(.hm-member-home-root-anchor){padding-top:.55rem!important;padding-block-start:.55rem!important;margin-top:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor):has(.hm-member-identity-pill):has(.hero-shell){gap:.28rem!important;margin:0!important;padding:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) .hero-shell{margin-top:0!important;}
'''
text = replace_once(text, old_top, new_top, "member home structural css")
text = replace_once(text, 'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){align-items:center!important;gap:.72rem!important;margin:0 0 .52rem 0!important;padding-top:0!important;}', 'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){align-items:center!important;gap:.72rem!important;margin:0!important;padding:0!important;}', "member utility row margin")
old_render = '''# Render the local spacing override and first visible controls before slower page reads.
_render_member_home_css()
_render_member_utility_bar()
topbar(
    "Member Home",
    "Continue your wellness assessment and access your tools.",
    "Member experience",
)
'''
new_render = '''# Render one structural header shell before slower page reads.
with st.container():
    st.markdown(
        "<span class='hm-member-home-root-anchor'></span>",
        unsafe_allow_html=True,
    )
    _render_member_home_css()
    _render_member_utility_bar()
    topbar(
        "Member Home",
        "Continue your wellness assessment and access your tools.",
        "Member experience",
    )
'''
text = replace_once(text, old_render, new_render, "member home header render")
text = text.replace('.hm-v101-schedule-title{font-size:.88rem!important;', '.hm-v101-schedule-title{font-size:.78rem!important;')
text = text.replace('.hm-v101-schedule-line{font-size:.76rem!important;', '.hm-v101-schedule-line{font-size:.70rem!important;')
write(path, text)

# Replace the global-header runtime with the validated structural-shell version.
path = "components/member_home_global_header_runtime.py"
text = read(path)
text = text.replace('_hm_member_home_global_header_v5', '_hm_member_home_global_header_v6')
start = text.index('_GLOBAL_HEADER_CSS = """')
end = text.index('\n\n\ndef install_member_home_global_header_runtime', start)
new_css = '''_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v6">
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){min-height:2.46rem!important;height:auto!important;margin:0!important;padding:0!important;align-items:center!important;gap:.72rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{min-height:2.46rem!important;height:auto!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor),div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor),div.element-container:has(.hm-top-profile-anchor),div.element-container:has(.hm-top-logout-anchor){display:none!important;visibility:hidden!important;width:0!important;height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hm-member-identity-pill{width:100%!important;min-height:2.46rem!important;height:2.46rem!important;padding:.24rem .64rem!important;margin:0!important;box-sizing:border-box!important;min-width:0!important;}
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v6),div.element-container:has(style#hm-member-home-global-header-v6){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
@media(max-width:760px){div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){display:grid!important;grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important;gap:.30rem!important;align-items:center!important;width:100%!important;min-height:2.30rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}.hm-member-identity-pill{height:2.30rem!important;min-height:2.30rem!important;padding:.20rem .42rem!important;font-size:.66rem!important;display:flex!important;align-items:center!important;gap:.22rem!important;overflow:hidden!important;white-space:nowrap!important;}.hm-member-identity-pill>span:first-child{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;}}
</style>
"""'''
text = text[:start] + new_css + text[end:]
write(path, text)

# Upcoming Schedule: use the new style marker, remove negative positioning and show full labels/actions.
path = "components/member_home_schedule_presentation.py"
text = read(path)
text = text.replace('_MEMBER_HOME_STYLE_MARKER = \'id="hm-member-home-local-style-v2"\'', '_MEMBER_HOME_STYLE_MARKER = \'id="hm-member-home-local-style-v3"\'')
text = regex_once(text, r'div\[data-testid="stElementContainer"\]:has\(#hm-member-home-local-style-v2\)\{.*?\}\ndiv\[data-testid="stHorizontalBlock"\]:has\(\.hm-member-identity-pill\)\{.*?\}\n', '', "remove negative member header polish")
text = text.replace('  width:285px!important;max-width:calc(100vw - 2rem)!important;', '  width:min(420px,100%)!important;max-width:100%!important;')
text = text.replace('  overflow:hidden!important;\n}', '  overflow:visible!important;\n}', 1)
text = text.replace('  margin:0!important;font-size:.88rem!important;font-weight:900!important;', '  margin:0!important;font-size:.78rem!important;font-weight:900!important;flex:1 1 auto!important;max-width:none!important;overflow:visible!important;text-overflow:clip!important;')
text = text.replace('  font-size:.78rem!important;font-weight:900!important;', '  font-size:.66rem!important;font-weight:900!important;', 1)
write(path, text)

# 8. Food Journal: return to a two-row meal entry and keep Add Food Item on Daily Log.
path = "pages/18_Daily_Log.py"
text = read(path)
css_start = text.index('        .hm-meal-entry-grid-anchor')
css_end = text.index('        .hm-toggle-body:empty', css_start)
new_grid_css = '''        .hm-meal-time-grid-anchor,.hm-meal-food-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-time-grid-anchor){display:grid!important;grid-template-columns:minmax(5rem,1fr) minmax(5rem,1fr) minmax(6rem,1.15fr) minmax(0,3fr)!important;gap:.48rem!important;align-items:end!important;width:100%!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-food-grid-anchor){display:grid!important;grid-template-columns:minmax(14rem,2.2fr) minmax(8rem,1.25fr)!important;gap:.48rem!important;align-items:end!important;width:100%!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-time-grid-anchor)>div,div[data-testid="stHorizontalBlock"]:has(.hm-meal-food-grid-anchor)>div{width:100%!important;min-width:0!important;max-width:none!important;flex:none!important;overflow:visible!important;}
        @media(max-width:760px){div[data-testid="stHorizontalBlock"]:has(.hm-meal-time-grid-anchor){grid-template-columns:repeat(3,minmax(0,1fr))!important;}div[data-testid="stHorizontalBlock"]:has(.hm-meal-time-grid-anchor)>div:nth-child(4){display:none!important;}div[data-testid="stHorizontalBlock"]:has(.hm-meal-food-grid-anchor){grid-template-columns:1fr!important;}}
'''
text = text[:css_start] + new_grid_css + text[css_end:]
start = text.index('def _render_meal_fields')
end = text.index('\n\ndef _render_meal_toggle', start)
new_function = '''def _render_meal_fields(label, key, prior, date_key):
    prior = _as_dict(prior)
    parsed_time = _parse_time(prior.get("time", ""))
    prior_hour = f"{((parsed_time.hour - 1) % 12) + 1:02d}" if parsed_time else "HH"
    prior_minute = f"{parsed_time.minute:02d}" if parsed_time else "MM"
    prior_period = ("AM" if parsed_time.hour < 12 else "PM") if parsed_time else "AM/PM"
    hour_options = ["HH"] + [f"{value:02d}" for value in range(1, 13)]
    minute_options = ["MM"] + [f"{value:02d}" for value in range(60)]
    period_options = ["AM/PM", "AM", "PM"]

    time_cols = st.columns([1, 1, 1.15, 3], gap="small")
    with time_cols[0]:
        st.markdown("<span class='hm-meal-time-grid-anchor'></span>", unsafe_allow_html=True)
        selected_hour = st.selectbox("Hour", hour_options, index=hour_options.index(prior_hour), key=f"hm_daily_hour_v13_{date_key}_{key}")
    with time_cols[1]:
        selected_minute = st.selectbox("Minutes", minute_options, index=minute_options.index(prior_minute), key=f"hm_daily_minute_v13_{date_key}_{key}")
    with time_cols[2]:
        selected_period = st.selectbox("AM/PM", period_options, index=period_options.index(prior_period), key=f"hm_daily_ampm_v13_{date_key}_{key}")

    existing_items = _normalise_food_items(prior)
    count_key = f"hm_meal_item_count_{date_key}_{key}"
    if count_key not in st.session_state:
        st.session_state[count_key] = max(1, len(existing_items))
    item_count = max(1, min(MAX_MEAL_ITEMS, int(st.session_state.get(count_key, 1) or 1)))
    food_items = []
    for idx in range(item_count):
        prior_item = existing_items[idx] if idx < len(existing_items) else {}
        food_col, portion_col = st.columns([2.2, 1.25], gap="small")
        with food_col:
            st.markdown("<span class='hm-meal-food-grid-anchor'></span>", unsafe_allow_html=True)
            food = st.text_input(f"Food Item {idx + 1}", value=prior_item.get("food", ""), key=f"{date_key}_{key}_food_{idx}", placeholder="Enter food item")
        with portion_col:
            portion = st.text_input(f"Portion {idx + 1}", value=prior_item.get("portion_size", ""), key=f"{date_key}_{key}_portion_{idx}", placeholder="Enter portion")
        row = {"food": _clean(food), "portion_size": _clean(portion)}
        if _food_item_has_data(row):
            food_items.append(row)

    st.markdown("<span class='hm-add-food-anchor'></span>", unsafe_allow_html=True)
    if st.button("+ Add food item", key=f"hm_daily_log_add_food_item_{date_key}_{key}", disabled=item_count >= MAX_MEAL_ITEMS):
        st.session_state[count_key] = min(MAX_MEAL_ITEMS, item_count + 1)
        st.session_state["_hm_h13r9e_pending_rerun_path"] = "Daily_Log"
        st.rerun()

    time_value = None
    if selected_hour != "HH" and selected_minute != "MM" and selected_period != "AM/PM":
        time_value = datetime.strptime(f"{selected_hour}:{selected_minute} {selected_period}", "%I:%M %p").time()

    prior_mood, prior_energy = _legacy_mood_and_energy(prior)
    mood_col, energy_col = st.columns(2, gap="medium")
    with mood_col:
        mood = st.text_input(f"Mood after {label.lower()}", value=prior_mood, key=f"{date_key}_{key}_mood", placeholder="How did you feel?")
    with energy_col:
        energy = st.text_input(f"Energy after {label.lower()}", value=prior_energy, key=f"{date_key}_{key}_energy", placeholder="How was your energy?")
    clean_mood = _clean(mood)
    clean_energy = _clean(energy)
    legacy_food = "; ".join(item.get("food", "") for item in food_items if item.get("food"))
    legacy_portion = "; ".join(item.get("portion_size", "") for item in food_items if item.get("portion_size"))
    combined_mood_energy = " | ".join(value for value in [f"Mood: {clean_mood}" if clean_mood else "", f"Energy: {clean_energy}" if clean_energy else ""] if value)
    return {"label": label, "time": _time_text(time_value), "food_items": food_items, "food": legacy_food, "portion_size": legacy_portion, "mood": clean_mood, "energy": clean_energy, "mood_energy": combined_mood_energy}
'''
text = text[:start] + new_function + text[end:]
write(path, text)

print("Authenticated smoke corrections applied.")
