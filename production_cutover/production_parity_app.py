from pathlib import Path
import runpy

# H13Q8 Step 1 production-parity entry. The accepted native router implementation
# is kept isolated under native_bridge so production app.py remains untouched.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(
    str(REPOSITORY_ROOT / "native_bridge" / "native_bridge_app.py"),
    run_name="__hm_h13q8_production_parity__",
)
