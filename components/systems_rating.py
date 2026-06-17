import json
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]

SYSTEM_ORDER = [
    "Digestive",
    "Intestinal",
    "Immune/Lymphatic",
    "Nervous",
    "Circulatory/Cardiovascular",
    "Respiratory",
    "Glandular/Endocrine",
    "Reproductive",
    "Urinary",
    "Musculoskeletal",
]

def map_answer(value):
    if value in [None, "", "Select", "NA"]:
        return 0
    try:
        return int(value)
    except Exception:
        return 0

def load_systems_rating_map():
    path = BASE_DIR / "config" / "systems_rating_map.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {system: [] for system in SYSTEM_ORDER}

def calculate_systems_rating(nsp1_answers, nsp2_answers):
    """Calculate systems rating table from NSP Page 1 + NSP Page 2 answers.

    v101.3 source of truth:
    - NSP Excel non-grey cells in Pg1 E6:N45 and Pg2 E7:N33 define question-to-system mapping.
    - Answer values 1/2/3 are summed into every mapped system.
    - NA/blank/Select are treated as 0.
    """
    answers = {}
    answers.update(nsp1_answers or {})
    answers.update(nsp2_answers or {})

    mapping = load_systems_rating_map()
    rows = []
    for idx, system in enumerate(SYSTEM_ORDER, start=1):
        codes = mapping.get(system, [])
        total = sum(map_answer(answers.get(code, "Select")) for code in codes)
        rows.append({
            "No.": idx,
            "System": system,
            "Score": total,
        })
    return rows