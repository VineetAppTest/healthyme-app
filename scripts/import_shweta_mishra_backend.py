"""
One-time backend import for Shweta Mishra.

Creates/updates the member login authorization record and populates:
- LAF responses
- NSP Page 1 responses
- NSP Page 2 responses
- Digestive, Intestinal, Immune, Glandular, Musculoskeletal admin subforms
- Initial assessment instance / review queue state

Safe to run more than once: it upserts the same member_id and overwrites only this member's records.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Dict, Any

import sys

_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ROOT_FOR_IMPORT))

MEMBER_ID = "shweta01"
INSTANCE_ID = f"{MEMBER_ID}_inst_1"
MEMBER_EMAIL = "shwemish@gmail.com"
MEMBER_NAME = "Shweta Mishra"
TEMP_PASSWORD = "Password@123"
NSP_ASSESSMENT_DATE = "2026-04-19"
LAF_SIGNED_DATE = "2026-04-12"
LAF_PAGE1_DATE = "2026-04-13"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _today_iso() -> str:
    return datetime.date.today().isoformat()


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_templates() -> Dict[str, Any]:
    path = _repo_root() / "config" / "admin_templates.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _map_answer(v: Any) -> int:
    if v in (None, "", "Select", "NA"):
        return 0
    try:
        return int(v)
    except Exception:
        return 0


LAF_RESPONSES: Dict[str, Any] = {
    "full_name": MEMBER_NAME,
    "gender": "Female",
    "age": "49",
    "height_cm": "152",
    "weight_kg": "74",
    "country": "India",
    "mobile_number": "+91 502942947",
    "email_id": MEMBER_EMAIL,
    "relationship_status": "Married",
    "purpose_guidance": "To get help with menopausal symptoms and weight management.",
    "main_health_concerns": "Menopausal symptoms, high blood pressure, fatty liver, and high insulin resistance.",
    "exercise_details": "Strength training 3-4 days/week; 35-40 minute walk 2-3 days/week.",
    "energy_level": "5",
    "energy_lulls_highs": "Lull after lunch.",
    "sleep_hours": "6-8 hours",
    "sleep_time": "11:20 PM",
    "wake_time": "8-9 AM",
    "trouble_falling_asleep": "Yes",
    "trouble_staying_asleep": "Yes",
    "awaken_rested": "No",
    "snore": "Yes",
    "occupation": "Housewife",
    "enjoy_work": "Sometimes",
    "work_hours": "NA",
    "work_start_end": "NA",
    "work_shifts_regular": "NA",
    "changed_employment_12_months": "No",
    "smoke_tobacco": "No",
    "household_smoke": "Yes",
    "medicinal_marijuana": "No",
    "recreational_drugs": "No",
    "dependency_treatment": "No",
    "interests_hobbies": "Music, reading.",
    "prescription_medication": "No",
    "otc_medication": "Yes",
    "otc_medication_list": "Omega 3, Magnesium Glycinate, Vitamin D3.",
    "supplements_list": "Omega 3, Magnesium Glycinate, Vitamin D3. Same as above mentioned.",
    "birth_control": "None",
    "antibiotics_5_years": "Yes",
    "antibiotics_details": "Post spine surgery.",
    "allergies_sensitivities": "Yes",
    "allergies_sensitivities_list": "Shrimp allergy.",
    "anaphylaxis": "",
    "silver_mercury_fillings": "No",
    "diagnosed_illness": "No",
    "hospitalized": "Yes",
    "hospitalized_reason": "Spine surgery in 2024.",
    "surgery_gall_bladder": "No",
    "surgery_tonsils": "No",
    "surgery_appendix": "No",
    "bowel_movement_frequency": "1-2 times daily",
    "strain_bowel_movement": "Occasionally",
    "strain_related_food_circumstances": "Not clearly specified in scanned LAF.",
    "loose_bowel_movements": "Occasionally",
    "loose_related_food_circumstances": "Yes; details not clearly specified in scanned LAF.",
    "undigested_food_stools": "Occasionally",
    "family_cardiovascular": "M",
    "family_kidney": "M",
    "family_type2_diabetes": "M",
    "fungal_infections": "No",
    "libido_decline": "No",
    "kidney_gall_stones": "No",
    "pronoun": "She/Her",
    "pregnant_possible": "No",
    "miscarriages_history": "In 2013",
    "menses_changes": "Yes",
    "menses_changes_details": "Changes noted; scanned note references 2013.",
    "pms_symptoms": "Emotionally sensitive.",
    "peri_menopausal": "Yes",
    "menopausal": "No",
    "post_menopausal": "No",
    "menopausal_symptoms": "Yes",
    "menopausal_symptoms_details": "Irregular periods and duration.",
    "bone_density_test": "No",
    "prostate_problems": "No",
    "major_trauma_5_years": "Yes",
    "import_source": "Offline scanned LAF PDF + NSP Excel import",
    "laf_signed_date": LAF_SIGNED_DATE,
    "laf_page1_date": LAF_PAGE1_DATE,
    "nsp_assessment_date": NSP_ASSESSMENT_DATE,
    "import_notes": (
        "Imported from handwritten/scanned LAF. Mobile number and a few handwritten details should be confirmed later. "
        "Unclear fields were either left blank, set to NA/No only where the form clearly indicated so, or annotated in free text."
    ),
}

NSP1_RESPONSES: Dict[str, str] = {
    "nsp1_q1": "1", "nsp1_q2": "3", "nsp1_q3": "NA", "nsp1_q4": "NA", "nsp1_q5": "NA",
    "nsp1_q6": "NA", "nsp1_q7": "NA", "nsp1_q8": "1", "nsp1_q9": "3", "nsp1_q10": "3",
    "nsp1_q11": "3", "nsp1_q12": "2", "nsp1_q13": "1", "nsp1_q14": "NA", "nsp1_q15": "1",
    "nsp1_q16": "1", "nsp1_q17": "NA", "nsp1_q18": "1", "nsp1_q19": "NA", "nsp1_q20": "NA",
    "nsp1_q21": "2", "nsp1_q22": "2", "nsp1_q23": "NA", "nsp1_q24": "2", "nsp1_q25": "NA",
    "nsp1_q26": "3", "nsp1_q27": "2", "nsp1_q28": "NA", "nsp1_q29": "NA", "nsp1_q30": "NA",
    "nsp1_q31": "NA", "nsp1_q32": "NA", "nsp1_q33": "2", "nsp1_q34": "NA", "nsp1_q35": "NA",
    "nsp1_q36": "2", "nsp1_q37": "NA", "nsp1_q38": "NA", "nsp1_q39": "NA", "nsp1_q40": "NA",
}

NSP2_RESPONSES: Dict[str, str] = {
    "nsp2_q41": "NA", "nsp2_q42": "1", "nsp2_q43": "3", "nsp2_q44": "NA", "nsp2_q45": "3",
    "nsp2_q46": "NA", "nsp2_q47": "NA", "nsp2_q48": "3", "nsp2_q49": "1", "nsp2_q50": "2",
    "nsp2_q51": "NA", "nsp2_q52": "NA", "nsp2_q53": "1", "nsp2_q54": "2", "nsp2_q55": "NA",
    "nsp2_q56": "NA", "nsp2_q57": "1", "nsp2_q58": "2", "nsp2_q59": "2", "nsp2_q60": "NA",
    "nsp2_q61": "3", "nsp2_q62": "NA", "nsp2_q63": "NA", "nsp2_q64": "2", "nsp2_q65": "NA",
    "nsp2_q66": "2", "nsp2_q67": "NA",
}

# Values explicitly filled in the Excel subform tabs. Unlisted items are imported as NA unless linked from NSP.
SUBFORM_EXPLICIT_VALUES: Dict[str, Dict[str, str]] = {
    "Digestive": {
        "Stomach bloated after eating": "2",
        "Constipated": "1",
        "Food allergies/sensitivities": "1",
        "Lower back pain": "3",
        "Excessive gas, belching or burping after meals": "1",
        "Weight gain around the abdomen": "3",
        "Difficulty losing weight": "3",
        "Skin irritations/rashes/acne": "1",
        "Migraine headaches": "2",
        "Mood swings": "2",
        "Hormone imbalance - PMS": "2",
    },
    "Intestinal": {
        "Use of antibiotics": "2",
        "Crave sugars, bread, alcohol": "3",
        "Headaches": "2",
        "Abdominal gas and bloating": "1",
        "Dark circles under eyes": "3",
        "Irritability": "2",
        "Disrupted sleep": "2",
        "Flatulence after meals": "1",
        "Food sensitivities/intolerances": "1",
        "Depressed": "2",
        "Female: PMS/heavy cycles": "2",
        "Constipated": "1",
        "Mood swings": "2",
        "Irritable/loss temper easily": "2",
        "Acne, rashes, skin irritations": "1",
        "Fatigue/low energy": "1",
        "Fatigue": "1",
        "Hormone imbalances - PMS": "2",
        "Chronic gas/bloating": "1",
        "Skin irritations": "1",
        "Insomnia": "2",
    },
    "Immune": {
        "Fatigue/loss of energy": "1",
        "Red, itchy skin": "1",
        "Diagnosed allergies": "1",
        "Visceral fat": "3",
        "Dark circles under eyes": "3",
        "Mental health disorder - depressed/anxious": "2",
        "Fatigue": "1",
    },
    "Glandular": {
        "Gain weight easily, fail to lose on diets": "3",
        "Constipated, less than one bowel movement a day": "1",
        "Hair dry, brittle, dull, lifeless": "2",
        "Insomnia": "2",
        "Depressed/mood swings": "2",
        "Cravings for salt": "1",
        "Disrupted sleep": "2",
        "Frequent migraines": "2",
        "Dark circles under eyes": "3",
        "Loss of sleep/poor sleep habits": "2",
        "Strong, sudden cravings for sweets, starches coffee or alcohol": "3",
        "Fatigue": "1",
        "Frequent headaches": "2",
        "Feeling depressed": "2",
    },
    "Musculoskeletal": {
        "Pins and needles sensation": "3",
        "Female: Menopause": "1",
    },
}


def _answer_from_linked_code(code: str | None) -> str:
    if not code:
        return "NA"
    return NSP1_RESPONSES.get(code) or NSP2_RESPONSES.get(code) or "NA"


def build_admin_assessment() -> Dict[str, Dict[str, str]]:
    templates = _load_templates()
    sections_to_import = ["Digestive", "Intestinal", "Immune", "Glandular", "Musculoskeletal"]
    assessment: Dict[str, Dict[str, str]] = {}
    for section in sections_to_import:
        section_data: Dict[str, str] = {}
        explicit = SUBFORM_EXPLICIT_VALUES.get(section, {})
        for group in templates.get(section, []):
            if group.get("deleted"):
                continue
            heading = group.get("heading", "")
            for item in group.get("items", []):
                if item.get("deleted"):
                    continue
                label = item.get("label", "")
                key = f"{section}|{heading}|{label}"
                value = explicit.get(label)
                if value is None:
                    value = _answer_from_linked_code(item.get("linked_code")) if item.get("linked_code") else "NA"
                if value not in {"NA", "1", "2", "3"}:
                    value = "NA"
                section_data[key] = value
        assessment[section] = section_data
    return assessment


def run_import() -> Dict[str, Any]:
    from components.db import load_db, save_db, normalize_workflow

    db = load_db()
    db.setdefault("users", [])
    db.setdefault("profiles", {})
    db.setdefault("workflow", {})
    db.setdefault("laf_responses", {})
    db.setdefault("nsp1_responses", {})
    db.setdefault("nsp2_responses", {})
    db.setdefault("nsp_scores", {})
    db.setdefault("admin_assessments", {})
    db.setdefault("admin_assessments_by_instance", {})
    db.setdefault("assessment_instances", {})
    db.setdefault("assessment_instance_responses", {})
    db.setdefault("notifications", [])
    db.setdefault("audit_logs", [])

    existing_user = None
    for user in db["users"]:
        if user.get("id") == MEMBER_ID or str(user.get("email", "")).strip().lower() == MEMBER_EMAIL:
            existing_user = user
            break

    created = existing_user is None
    if existing_user is None:
        existing_user = {"id": MEMBER_ID}
        db["users"].append(existing_user)

    existing_user.update({
        "id": MEMBER_ID,
        "name": MEMBER_NAME,
        "email": MEMBER_EMAIL,
        "password_hash": _hash_password(TEMP_PASSWORD),
        "role": "member",
        "must_reset_password": False,
        "is_active": True,
        "auth_provider": existing_user.get("auth_provider", "local_or_oidc"),
    })

    db["profiles"][MEMBER_ID] = {
        "full_name": MEMBER_NAME,
        "gender": "Female",
        "age": "49",
        "height_cm": "152",
        "weight_kg": "74",
        "mobile_number": LAF_RESPONSES.get("mobile_number", ""),
        "phone": LAF_RESPONSES.get("mobile_number", ""),
        "country": "India",
        "city": "Dubai",
        "occupation": "Housewife",
        "email_id": MEMBER_EMAIL,
        "address": "23 Marina, Tower Marina",
    }

    db["laf_responses"][MEMBER_ID] = dict(LAF_RESPONSES)
    db["nsp1_responses"][MEMBER_ID] = dict(NSP1_RESPONSES)
    db["nsp2_responses"][MEMBER_ID] = dict(NSP2_RESPONSES)
    db["nsp_scores"][MEMBER_ID] = {
        "nsp1_total": sum(_map_answer(v) for v in NSP1_RESPONSES.values()),
        "nsp2_total": sum(_map_answer(v) for v in NSP2_RESPONSES.values()),
        "total": sum(_map_answer(v) for v in NSP1_RESPONSES.values()) + sum(_map_answer(v) for v in NSP2_RESPONSES.values()),
        "assessment_date": NSP_ASSESSMENT_DATE,
        "all_na": False,
    }

    admin_assessment = build_admin_assessment()
    db["admin_assessments"][MEMBER_ID] = admin_assessment
    db["admin_assessments_by_instance"][INSTANCE_ID] = {
        "member_id": MEMBER_ID,
        "instance_id": INSTANCE_ID,
        "updated_at": _now_iso(),
        "data": admin_assessment,
        "source": "one_time_backend_import_shweta_mishra",
    }

    inst = {
        "instance_id": INSTANCE_ID,
        "member_id": MEMBER_ID,
        "instance_number": 1,
        "instance_type": "Initial Assessment",
        "requested_pages": ["nsp1", "nsp2"],
        "created_by_admin": "backend_import",
        "created_date": NSP_ASSESSMENT_DATE,
        "due_date": "",
        "admin_note": "Offline PDF/XLSX assessment imported by backend script.",
        "nsp1_required": True,
        "nsp2_required": True,
        "nsp1_completed": True,
        "nsp2_completed": True,
        "consent_accepted": True,
        "submitted_for_review": True,
        "submitted_date": NSP_ASSESSMENT_DATE,
        "status": "review_required",
        "review_status": "imported_pending_admin_finalization",
    }
    db["assessment_instances"][MEMBER_ID] = [inst]
    db["assessment_instance_responses"][INSTANCE_ID] = {
        "nsp1": dict(NSP1_RESPONSES),
        "nsp2": dict(NSP2_RESPONSES),
        "consent": {
            "accepted": True,
            "accepted_date": LAF_SIGNED_DATE,
            "source": "offline_signed_laf_pdf",
        },
    }

    wf = {
        "laf_completed": True,
        "nsp1_completed": True,
        "nsp2_completed": True,
        "submitted_for_review": True,
        "admin_completed": False,
        "final_report_ready": False,
        "body_mind_activation_requested": False,
        "body_mind_unlocked": False,
        "body_mind_completed": False,
        "workflow_status": "submitted",
    }
    db["workflow"][MEMBER_ID] = normalize_workflow(wf)

    # Keep one fresh notification for the imported review queue entry without duplicating endlessly.
    db["notifications"] = [
        n for n in db.get("notifications", [])
        if not (n.get("user_id") == MEMBER_ID and n.get("kind") == "admin_review_required" and n.get("source") == "one_time_backend_import_shweta_mishra")
    ]
    db["notifications"].append({
        "ts": _now_iso(),
        "kind": "admin_review_required",
        "user_id": MEMBER_ID,
        "instance_id": INSTANCE_ID,
        "message": "Offline LAF/NSP assessment imported for Shweta Mishra. Admin review required.",
        "status": "queued",
        "source": "one_time_backend_import_shweta_mishra",
    })

    db["audit_logs"].append({
        "ts": _now_iso(),
        "action": "one_time_backend_import",
        "member_id": MEMBER_ID,
        "member_email": MEMBER_EMAIL,
        "created_user": created,
        "scope": "LAF, NSP1, NSP2, Digestive, Intestinal, Immune, Glandular, Musculoskeletal",
    })

    save_db(db)

    return {
        "ok": True,
        "created_user": created,
        "member_id": MEMBER_ID,
        "member_email": MEMBER_EMAIL,
        "instance_id": INSTANCE_ID,
        "nsp1_answer_count": len(NSP1_RESPONSES),
        "nsp2_answer_count": len(NSP2_RESPONSES),
        "admin_sections": list(admin_assessment.keys()),
        "nsp_total": db["nsp_scores"][MEMBER_ID]["total"],
    }


if __name__ == "__main__":
    result = run_import()
    print(json.dumps(result, indent=2))
