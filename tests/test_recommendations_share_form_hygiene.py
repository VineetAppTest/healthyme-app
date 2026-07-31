from pathlib import Path
import py_compile


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "recommendations_share_form_hygiene.py"
PAGE = ROOT / "pages" / "35_Admin_Recommendations_Share.py"


def test_runtime_and_page_compile():
    py_compile.compile(str(COMPONENT), doraise=True)
    py_compile.compile(str(PAGE), doraise=True)
