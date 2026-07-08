"""
One-time backend import/update for Harshita Sajjanhar final email.

Creates/updates the member login authorization record and populates LAF responses only.

Safe to run more than once: it upserts the same member_id/email and overwrites only
this member's LAF/profile/workflow records touched by this import.

Note: This does not create Auth0 users. Create/update the Auth0 user separately.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import sys

_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ROOT_FOR_IMPORT))

MEMBER_ID = "harshita_sajjanhar_01"
MEMBER_EMAIL = "harshita.sajjanhar@gmail.com"
MEMBER_NAME = "Harshita Sajjanhar"
TEMP_PASSWORD = "Password@123"
LAF_FORM_DATE = "2026-01-24"
LAF_SIGNED_DATE = "2026-01-28"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


LAF_RESPONSES: Dict[str, Any] = {
    # Identity / profile
    "full_name": MEMBER_NAME,
    "first_name_from_laf": "Harshita",
    "email_id": MEMBER_EMAIL,
    "gender": "Female",
    "pronoun": "F",
    "age": "39",
    "height_cm": "157",
    "weight_kg": "63",
    "relationship_status": "Married",
    "occupation": "I run bed and breakfast from home",
    "address": "karwijzeederf 19",
    "city": "Diemen",
    "province": "",
    "postal_code": "1112JN",
    "mobile_number": "+31618181366",
    "country": "Netherlands",
    "laf_form_date": LAF_FORM_DATE,
    "laf_signed_date": LAF_SIGNED_DATE,

    # Page 1 lifestyle
    "purpose_guidance": "Increase energy levels, increase focus, lose excess fat specially mid section.",
    "main_health_concerns": "Not feeling well rested after waking up. Weak focus and inability to form routine; cannot stick to exercise routines.",
    "major_trauma_5_years": "No",
    "stress_level": "7",
    "stress_factors": {
        "financial": "NA",
        "career": "Yes",
        "personal": "NA",
        "marriage": "NA",
        "health": "Yes",
        "family": "NA",
        "spiritual": "NA",
        "unfulfilled_expectations": "Yes",
        "other": "",
    },
    "stress_manifestation": "",
    "coping_mechanisms": "Listen to music, go out, coffee.",
    "exercise_details": "Yoga 1-2 times/week. Sometimes difficult to stick to this also.",
    "energy_level": "4",
    "energy_lulls_highs": "Mornings are low energy; feels more active at night sometimes.",
    "sleep_hours": "8-8.5 hrs",
    "sleep_time": "12:00",
    "wake_time": "8:30-9:00",
    "trouble_falling_asleep": "",
    "trouble_staying_asleep": "",
    "awaken_rested": "No",
    "snore": "Yes",
    "enjoy_work": "Yes",
    "work_hours": "8-10 hrs/day",
    "work_start_end": "No fixed timings",
    "work_shifts_regular": "No fixed timings",
    "changed_employment_12_months": "No",

    # Page 2 lifestyle and medical history
    "smoke_tobacco": "No",
    "household_smoke": "No",
    "medicinal_marijuana": "No",
    "recreational_drugs": "No",
    "dependency_treatment": "No",
    "weight_goal": "Lose weight",
    "weight_goal_amount": "8-9 kgs",
    "goal_weight_timeline": "1 year",
    "weight_change_motivation": "Feel at ease in body, reduce back pain, feel lighter.",
    "screen_time_driving": "",
    "screen_time_tv": "30-60 mins",
    "screen_time_reading": "",
    "screen_time_computer": "",
    "body_household_products": "Natural",
    "interests_hobbies": "Plants, DIY creative projects.",
    "vacation_regularly": "Yes",
    "last_vacation": "November",
    "spiritual_discipline": "No",
    "prescription_medication": "No",
    "prescription_medication_list": "",
    "otc_medication": "No",
    "otc_medication_list": "",
    "supplements_list": "Just started taking Brahmi; been 1 week.",
    "birth_control": "",
    "antibiotics_5_years": "Yes",
    "antibiotics_details": "Last time was last year in India for sickness + fever + throat infection.",

    # Page 3 medical/family history
    "allergies_sensitivities": "Yes",
    "allergies_sensitivities_list": "Some foods cause intense cramps: avocado, eggs, pineapple.",
    "anaphylaxis": "",
    "silver_mercury_fillings": "No",
    "diagnosed_illness": "No",
    "diagnosed_illness_details": "",
    "hospitalized": "No",
    "hospitalized_reason": "",
    "surgery_gall_bladder": "No",
    "surgery_tonsils": "No",
    "surgery_appendix": "No",
    "bowel_movement_frequency": "1",
    "strain_bowel_movement": "Occasionally",
    "strain_related_food_circumstances": "Drinking less water.",
    "loose_bowel_movements": "",
    "loose_related_food_circumstances": "",
    "undigested_food_stools": "",
    "family_history": {
        "mental_health_disorder": "M - Schizophrenia",
        "asthma": "G",
        "type_2_diabetes": "G",
        "cardiovascular_disease": "M",
    },
    "fungal_infections": "No",
    "libido_decline": "Yes",
    "libido_decline_details": "Not as willing to initiate or interested in sexual activity as before.",
    "kidney_gall_stones": "",

    # Page 4 female/pronoun and dietary habits
    "pregnant_possible": "No",
    "pregnancy_trimester": "",
    "miscarriages_history": "No",
    "menses_changes": "No",
    "menses_changes_details": "",
    "pms_symptoms": "",
    "peri_menopausal": "",
    "menopausal": "",
    "post_menopausal": "",
    "menopausal_symptoms": "",
    "menopausal_symptoms_details": "",
    "bone_density_test": "No",
    "bone_density_result": "",
    "prostate_problems": "Not applicable",
    "meals_per_day": "2",
    "main_meal_times": "1:30 PM and 8:00 PM",
    "snacks_per_day": "1",
    "snack_times": "Evening",
    "weekly_food_budget": "",
    "food_preparation_skills": "7",
    "eats_meals_with_family": "Yes",
    "eats_meals_alone": "Yes",
    "eats_meals_on_the_run": "No",
    "eats_restaurant": "No",
    "eats_fast_food": "No",
    "diet_restrictions_due_to_others": "No",
    "diet_restrictions_explain": "",
    "fruit_servings": "1",
    "fruit_types": ["Fresh", "Dried"],
    "vegetable_servings": "3",
    "vegetable_types": ["Cooked", "Raw"],
    "grain_servings": "2",
    "grain_types": ["Whole"],
    "protein_servings": "",
    "protein_type": "Lentils, beans",
    "dairy_products_type": "",
    "other_servings": "",

    # Page 5 typical meals / intake
    "breakfast": "I don't eat breakfast; try to do IF.",
    "lunch": "Soups, toast with roasted vegetables, leftovers sometimes, salads.",
    "dinner": "Rice, roti, sabzi, Thai curries, dal.",
    "snacks": "Fruit, nuts, peanut butter, biscuits, coffee.",
    "food_frequency_scores": {
        "aluminum_pans": "1",
        "margarine": "1",
        "candy": "1",
        "microwave": "2",
        "fried_foods": "1",
        "fast_foods": "1",
        "luncheon_meats": "1",
        "cigarettes": "1",
        "artificial_sweeteners": "1",
        "refined_foods": "2",
    },
    "drinks": {
        "coffee_per_week": "2 cups/week",
        "herbal_tea_per_week": "1 cup/week",
        "other": "Oat milk",
    },
    "diet_type": "Vegetarian",
    "meat_frequency": "Not applicable",
    "dairy_frequency": "3-5/week",
    "favourite_foods": "Thai curries + rice, rice with dal/sabzi, mushrooms.",
    "favourite_foods_frequency": "3-4 times a week",
    "food_cravings": "Sweets after meals",
    "food_cravings_frequency": "Everyday",
    "avoid_foods": "Yes",
    "avoid_foods_reason": "Ready-made sauces, supermarket ready foods, foods with ingredients that are difficult to understand.",
    "symptoms_if_meals_missed": "Yes",
    "symptoms_if_meals_missed_explain": "Eating too fast when eating next, leading to stomach pain and vomiting.",
    "symptoms_after_meals": "No",
    "symptoms_after_meals_explain": "",

    # Page 6 Body-Mind Connection and declaration
    "body_mind_primary_symptom": "Low energy and not being able to stick to routine.",
    "body_mind_daily_effect": "Cannot do as much as she would like to do. Procrastination = disappointment.",
    "body_mind_emotions": ["Anger", "Sadness", "Annoyed", "Exhausted", "Irritated", "Frustrated", "Disappointed"],
    "body_mind_positive_changes": "",
    "body_mind_comments": "",
    "client_statement_signed": "Yes",
    "client_statement_date": LAF_SIGNED_DATE,

    # Import notes
    "import_source": "Offline LAF PDF import for Harshita Sajjanhar",
    "import_notes": (
        "Imported from fillable PDF form fields. Email harshita.sajjanhar@gmail.com used for member login authorization. "
        "Fields not provided in the LAF are blank/NA and can be completed later."
    ),
}


def run_import() -> Dict[str, Any]:
    from components.db import load_db, save_db, normalize_workflow

    db = load_db()
    db.setdefault("users", [])
    db.setdefault("profiles", {})
    db.setdefault("workflow", {})
    db.setdefault("laf_responses", {})
    db.setdefault("notifications", [])
    db.setdefault("audit_logs", [])

    existing_user = None
    for user in db["users"]:
        if user.get("id") == MEMBER_ID or str(user.get("email", "")).strip().lower() == MEMBER_EMAIL.lower():
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
        "age": "39",
        "height_cm": "157",
        "weight_kg": "63",
        "mobile_number": "+31618181366",
        "phone": "+31618181366",
        "country": "Netherlands",
        "city": "Diemen",
        "occupation": "I run bed and breakfast from home",
        "email_id": MEMBER_EMAIL,
        "address": "karwijzeederf 19",
        "postal_code": "1112JN",
    }

    db["laf_responses"][MEMBER_ID] = dict(LAF_RESPONSES)

    existing_wf = db.get("workflow", {}).get(MEMBER_ID, {})
    wf = {
        **existing_wf,
        "laf_completed": True,
        "nsp1_completed": False,
        "nsp2_completed": False,
        "submitted_for_review": False,
        "admin_completed": False,
        "final_report_ready": False,
        "body_mind_activation_requested": False,
        "body_mind_unlocked": False,
        "body_mind_completed": False,
        "workflow_status": "laf_imported",
    }
    db["workflow"][MEMBER_ID] = normalize_workflow(wf)

    db["notifications"] = [
        n for n in db.get("notifications", [])
        if not (n.get("user_id") == MEMBER_ID and n.get("source") == "one_time_backend_import_harshita_laf")
    ]
    db["notifications"].append({
        "ts": _now_iso(),
        "kind": "laf_imported",
        "user_id": MEMBER_ID,
        "message": "Offline LAF imported for Harshita Sajjanhar. NSP/subforms not imported yet.",
        "status": "queued",
        "source": "one_time_backend_import_harshita_laf",
    })

    db["audit_logs"].append({
        "ts": _now_iso(),
        "action": "one_time_backend_import",
        "member_id": MEMBER_ID,
        "member_email": MEMBER_EMAIL,
        "created_user": created,
        "scope": "LAF only",
        "source": "one_time_backend_import_harshita_laf",
    })

    save_db(db)

    return {
        "ok": True,
        "created_user": created,
        "member_id": MEMBER_ID,
        "member_email": MEMBER_EMAIL,
        "member_name": MEMBER_NAME,
        "scope": "LAF only",
        "laf_form_date": LAF_FORM_DATE,
        "laf_signed_date": LAF_SIGNED_DATE,
        "auth0_required_separately": True,
        "login_email": MEMBER_EMAIL,
    }


if __name__ == "__main__":
    result = run_import()
    print(json.dumps(result, indent=2))
