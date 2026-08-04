from __future__ import annotations

from pathlib import Path


PAGE = Path("pages/02_Member_Home.py")
RUNTIME = Path("components/member_home_global_header_runtime.py")
TEST = Path("tests/test_member_home_global_header_runtime.py")

page = PAGE.read_text()

old_page_head = '''<style id="hm-member-home-local-style-v2">
/* Member Home only: injected before page reads so the first visible row starts at the top. */
html,body,#root{margin-top:0!important;padding-top:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
html body [data-testid="stAppViewContainer"],html body [data-testid="stAppViewContainer"] > .main,html body [data-testid="stMain"],html body section.main{padding-top:0!important;padding-block-start:0!important;margin-top:0!important;top:0!important;}
html body [data-testid="stMainBlockContainer"],html body [data-testid="stAppViewBlockContainer"],html body section.main > div.block-container,html body .main .block-container,html body .stMainBlockContainer,html body .block-container{padding-top:0!important;padding-block-start:0!important;margin-top:0!important;}
'''
new_page_head = '''<style id="hm-member-home-local-style-v3">
/* Member Home owns one structural shell for the identity row and hero. Do not
   reset the complete Streamlit app/root to zero padding; that clipped the utility
   row and allowed later runtime CSS to fight the page layout. */
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
.hm-member-home-root-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stElementContainer"]:has(.hm-member-home-root-anchor),div.element-container:has(.hm-member-home-root-anchor),div[data-testid="stElementContainer"]:has(style#hm-member-home-local-style-v3),div.element-container:has(style#hm-member-home-local-style-v3){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stAppViewContainer"] .block-container:has(.hm-member-home-root-anchor){padding-top:.55rem!important;padding-block-start:.55rem!important;margin-top:0!important;}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .hm-member-home-root-anchor):has(.hm-member-identity-pill):has(.hero-shell),div[data-testid="stVerticalBlock"]:has(> div.element-container .hm-member-home-root-anchor):has(.hm-member-identity-pill):has(.hero-shell){gap:.28rem!important;margin:0!important;padding:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) > div[data-testid="stElementContainer"]:has(.hm-member-identity-pill),div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) > div.element-container:has(.hm-member-identity-pill),div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) > div[data-testid="stElementContainer"]:has(.hero-shell),div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) > div.element-container:has(.hero-shell){margin:0!important;padding:0!important;min-height:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) .hero-shell{margin-top:0!important;}
'''
if page.count(old_page_head) != 1:
    raise RuntimeError("Member Home root-spacing block was not found exactly once")
page = page.replace(old_page_head, new_page_head, 1)

old_row_rule = 'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){align-items:center!important;gap:.72rem!important;margin:0 0 .52rem 0!important;padding-top:0!important;}'
new_row_rule = 'div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){align-items:center!important;gap:.72rem!important;margin:0!important;padding:0!important;}'
if page.count(old_row_rule) != 1:
    raise RuntimeError("Member utility-row margin rule was not found exactly once")
page = page.replace(old_row_rule, new_row_rule, 1)

old_render = '''# Render the local spacing override and first visible controls before slower page reads.
_render_member_home_css()
_render_member_utility_bar()
topbar(
    "Member Home",
    "Continue your wellness assessment and access your tools.",
    "Member experience",
)
'''
new_render = '''# Render one structural header shell before slower page reads. The local marker,
# signed-in utility row and hero now share one Streamlit container and spacing rule.
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
if page.count(old_render) != 1:
    raise RuntimeError("Member Home header render sequence was not found exactly once")
page = page.replace(old_render, new_render, 1)
PAGE.write_text(page)

runtime = RUNTIME.read_text()
runtime = runtime.replace(
    '_MARKER = "_hm_member_home_global_header_v5"',
    '_MARKER = "_hm_member_home_global_header_v6"',
    1,
)
css_start = runtime.find('_GLOBAL_HEADER_CSS = """\n')
css_end_marker = '\n"""\n\n\ndef install_member_home_global_header_runtime()'
css_end = runtime.find(css_end_marker, css_start)
if css_start < 0 or css_end < 0:
    raise RuntimeError("Global Member Home header CSS boundaries were not found")
new_runtime_css = '''_GLOBAL_HEADER_CSS = """
<style id="hm-member-home-global-header-v6">
/* The page owns structural spacing. This runtime only preserves control sizing and
   the compact mobile row, avoiding another block-container or hero override. */
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){min-height:2.46rem!important;height:auto!important;margin:0!important;padding:0!important;align-items:center!important;gap:.72rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{min-height:2.46rem!important;height:auto!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
div[data-testid="column"]>div[data-testid="stVerticalBlock"]:has(.hm-top-profile-anchor),div[data-testid="column"]>div[data-testid="stVerticalBlock"]:has(.hm-top-logout-anchor){gap:0!important;min-height:2.46rem!important;height:2.46rem!important;margin:0!important;padding:0!important;}
div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor),div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor),div.element-container:has(.hm-top-profile-anchor),div.element-container:has(.hm-top-logout-anchor){display:none!important;visibility:hidden!important;width:0!important;min-width:0!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hm-member-identity-pill{width:100%!important;min-height:2.46rem!important;height:2.46rem!important;padding:.24rem .64rem!important;margin:0!important;box-sizing:border-box!important;min-width:0!important;}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]{min-height:2.46rem!important;height:2.46rem!important;margin:0!important;padding:0!important;display:flex!important;align-items:center!important;}
div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-profile-anchor) .stButton>button,div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-logout-anchor) .stButton>button{min-height:2.46rem!important;height:2.46rem!important;max-height:2.46rem!important;margin:0!important;}
div[data-testid="stElementContainer"]:has(style#hm-member-home-global-header-v6),div.element-container:has(style#hm-member-home-global-header-v6){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
@media(max-width:760px){
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){display:grid!important;grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important;gap:.30rem!important;align-items:center!important;width:100%!important;min-height:2.30rem!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]{display:block!important;width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;height:2.30rem!important;min-height:2.30rem!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(1){grid-column:1!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(2){grid-column:2!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill)>div[data-testid="column"]:nth-child(3){grid-column:3!important;}
  .hm-member-identity-pill{height:2.30rem!important;min-height:2.30rem!important;padding:.20rem .42rem!important;font-size:.66rem!important;display:flex!important;align-items:center!important;gap:.22rem!important;overflow:hidden!important;white-space:nowrap!important;}
  .hm-member-identity-pill>span:first-child{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;}
  .hm-member-role-inline{flex:0 0 auto!important;font-size:.58rem!important;padding:.10rem .22rem!important;margin-left:0!important;white-space:nowrap!important;}
  div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"],div[data-testid="column"]:has(.hm-top-profile-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-profile-anchor) .stButton>button,div[data-testid="column"]:has(.hm-top-logout-anchor) [data-testid="stButton"]>button,div[data-testid="column"]:has(.hm-top-logout-anchor) .stButton>button{width:100%!important;min-width:0!important;height:2.30rem!important;min-height:2.30rem!important;max-height:2.30rem!important;padding:.16rem .24rem!important;margin:0!important;border-radius:12px!important;font-size:.70rem!important;line-height:1!important;white-space:nowrap!important;}
}
</style>
"""'''
runtime = runtime[:css_start] + new_runtime_css + runtime[css_end + len('\n"""'):]
RUNTIME.write_text(runtime)

test = TEST.read_text()
test = test.replace("import unittest\n", "import unittest\nfrom pathlib import Path\n", 1)
start = test.find("    def test_member_home_controls_root_header_sequence_and_mobile_row(self):\n")
end = test.find("\n    def test_other_pages_keep_their_existing_header_sequence", start)
if start < 0 or end < 0:
    raise RuntimeError("Existing Member Home runtime test boundaries were not found")
replacement_test = '''    def test_member_home_runtime_only_sizes_controls_and_mobile_row(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Member Home", "Member subtitle", "Member experience")

        self.assertEqual(calls, ["Member Home"])
        rendered_css = "\\n".join(self.fake_st.markdown_calls)
        self.assertIn("hm-member-home-global-header-v6", rendered_css)
        self.assertIn("hm-member-identity-pill", rendered_css)
        self.assertIn("hm-top-profile-anchor", rendered_css)
        self.assertIn("hm-top-logout-anchor", rendered_css)
        self.assertIn("@media(max-width:760px)", rendered_css)
        self.assertIn(
            "grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important",
            rendered_css,
        )
        self.assertIn("text-overflow:ellipsis!important", rendered_css)
        self.assertNotIn("block-container:has", rendered_css)
        self.assertNotIn(".hero-shell", rendered_css)
        self.assertNotIn("margin-top:-", rendered_css)

    def test_member_home_page_uses_one_structural_header_shell(self):
        source = Path("pages/02_Member_Home.py").read_text()

        self.assertIn("hm-member-home-local-style-v3", source)
        self.assertIn("hm-member-home-root-anchor", source)
        self.assertIn("with st.container():", source)
        self.assertIn("padding-top:.55rem!important", source)
        self.assertIn("gap:.28rem!important", source)
        self.assertNotIn("html body .block-container{padding-top:0", source)
        self.assertNotIn("margin:0 0 .52rem 0!important", source)
'''
test = test[:start] + replacement_test + test[end:]
TEST.write_text(test)
