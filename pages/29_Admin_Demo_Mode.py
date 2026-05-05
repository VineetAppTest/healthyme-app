import streamlit as st
import json
import pathlib
from datetime import date

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import load_db, save_db, list_members, normalize_workflow, hash_password
from components.assessment_instances import ensure_assessment_instances
from components.flash import set_system_message, render_system_message
from components.scoring import score_answers

st.set_page_config(page_title="Demo Mode", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

BASE = pathlib.Path(__file__).resolve().parents[1]

def load_questions(rel):
    return json.loads((BASE / rel).read_text(encoding="utf-8"))

def demo_answer_for_question(q, idx):
    qtype = q.get("type", "")
    code = q.get("code", "")
    label = q.get("label", q.get("text", "")).lower()

    if qtype == "select":
        opts = q.get("options", [])
        if code == "gender":
            return "Female"
        if code == "country":
            return "India"
        if opts:
            preferred = ["Yes", "No", "Female", "India", "Married", "Moderate", "Good"]
            for p in preferred:
                if p in opts:
                    return p
            return opts[0]
        return "Yes"

    if qtype == "number":
        if "age" in code:
            return "34"
        if "height" in code:
            return "165"
        if "weight" in code:
            return "68"
        return "1"

    if qtype == "phone":
        return "9876543210"

    if qtype == "email":
        return "demo.member@healthyme.local"

    if "name" in label or code == "full_name":
        return "Demo Filled Member"
    if "occupation" in label:
        return "Working Professional"
    if "purpose" in label or "concern" in label:
        return "Demo response: health, energy and wellness assessment."
    if "breakfast" in label:
        return "Poha, tea and fruit."
    if "lunch" in label:
        return "Roti, dal, vegetables and curd."
    if "dinner" in label:
        return "Rice, dal and vegetables."
    if "country" in label:
        return "India"
    if "mobile" in label or "phone" in label:
        return "9876543210"

    return "Demo response"

def build_demo_laf():
    questions = [q for q in load_questions("config/laf_questions.json") if not q.get("deleted")]
    answers = {}
    for idx, q in enumerate(questions, start=1):
        code = q.get("code")
        if not code:
            continue
        answers[code] = demo_answer_for_question(q, idx)

    # Ensure required basics are clean.
    answers.update({
        "full_name": "Demo Filled Member",
        "gender": "Female",
        "age": "34",
        "height_cm": "165",
        "weight_kg": "68",
        "country": "India",
        "mobile_number": "9876543210",
        "email_id": "demo.member@healthyme.local",
        "relationship_status": "Married",
        "libido_decline": "No",
    })
    return answers

def build_demo_nsp(rel, page_prefix):
    questions = [q for q in load_questions(rel) if not q.get("deleted")]
    answers = {}
    pattern = ["1", "2", "NA", "3", "1", "2", "NA"]
    for idx, q in enumerate(questions, start=1):
        code = q.get("code")
        if not code:
            continue
        answers[code] = pattern[idx % len(pattern)]

    # Keep female-specific questions valid for demo female member.
    if page_prefix == "nsp1":
        answers["nsp1_q31"] = "2"
    if page_prefix == "nsp2":
        for code in ["nsp2_q49", "nsp2_q50", "nsp2_q60"]:
            answers[code] = "2"
        # LAF libido default No => NA, but demo can show mapping/override.
        answers["nsp2_q65"] = "NA"
    return answers

def ensure_demo_member():
    db = load_db()
    existing = next((u for u in db.get("users", []) if u.get("email") == "demo.filled@healthyme.local"), None)
    if existing:
        return existing["id"], False

    user_id = "demo_filled"
    if any(u.get("id") == user_id for u in db.get("users", [])):
        user_id = "demo_filled_2"

    db.setdefault("users", []).append({
        "id": user_id,
        "name": "Demo Filled Member",
        "email": "demo.filled@healthyme.local",
        "password_hash": hash_password("password@123"),
        "role": "member",
        "must_reset_password": False,
        "is_active": True,
    })
    db.setdefault("profiles", {})[user_id] = {
        "full_name": "Demo Filled Member",
        "gender": "Female",
        "age": "34",
        "height_cm": "165",
        "weight_kg": "68",
        "mobile_number": "9876543210",
        "country": "India",
        "occupation": "Working Professional",
        "email_id": "demo.filled@healthyme.local",
    }
    db.setdefault("workflow", {})[user_id] = {
        "laf_completed": False,
        "nsp1_completed": False,
        "nsp2_completed": False,
        "submitted_for_review": False,
        "admin_completed": False,
        "final_report_ready": False,
        "workflow_status": "not_started",
    }
    save_db(db)
    return user_id, True

def fill_demo_for_member(member_id, submit_for_review=False):
    db = load_db()
    laf = build_demo_laf()
    nsp1 = build_demo_nsp("config/nsp_page1_questions.json", "nsp1")
    nsp2 = build_demo_nsp("config/nsp_page2_questions.json", "nsp2")

    db.setdefault("laf_responses", {})[member_id] = laf
    db.setdefault("nsp1_responses", {})[member_id] = nsp1
    db.setdefault("nsp2_responses", {})[member_id] = nsp2
    db.setdefault("nsp_scores", {})[member_id] = score_answers(nsp2)

    # Profile sync.
    db.setdefault("profiles", {}).setdefault(member_id, {})
    db["profiles"][member_id].update({
        "full_name": laf.get("full_name"),
        "gender": laf.get("gender"),
        "age": laf.get("age"),
        "height_cm": laf.get("height_cm"),
        "weight_kg": laf.get("weight_kg"),
        "mobile_number": laf.get("mobile_number"),
        "country": laf.get("country"),
        "email_id": laf.get("email_id"),
    })

    # Instance sync.
    save_db(db)
    ensure_assessment_instances(member_id)
    db = load_db()
    instances = db.setdefault("assessment_instances", {}).setdefault(member_id, [])
    current = sorted(instances, key=lambda x: x.get("instance_number", 0))[0]
    instance_id = current["instance_id"]
    db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {})
    db["assessment_instance_responses"][instance_id]["nsp1"] = nsp1
    db["assessment_instance_responses"][instance_id]["nsp2"] = nsp2
    db["assessment_instance_responses"][instance_id]["consent"] = {
        "accepted": bool(submit_for_review),
        "accepted_date": date.today().isoformat() if submit_for_review else "",
        "name_signature": laf.get("full_name", "Demo Filled Member") if submit_for_review else "",
        "instance_id": instance_id,
    }

    for inst in db["assessment_instances"][member_id]:
        if inst["instance_id"] == instance_id:
            inst["nsp1_completed"] = True
            inst["nsp2_completed"] = True
            inst["consent_accepted"] = bool(submit_for_review)
            inst["submitted_for_review"] = bool(submit_for_review)
            inst["submitted_date"] = date.today().isoformat() if submit_for_review else ""
            inst["status"] = "review_required" if submit_for_review else "in_progress"

    wf = db.setdefault("workflow", {}).setdefault(member_id, {})
    wf.update({
        "laf_completed": True,
        "nsp1_completed": True,
        "nsp2_completed": True,
        "submitted_for_review": bool(submit_for_review),
    })
    db["workflow"][member_id] = normalize_workflow(wf)

    if submit_for_review:
        existing = [
            n for n in db.setdefault("notifications", [])
            if n.get("user_id") == member_id and n.get("kind") == "admin_review_required"
        ]
        if not existing:
            db["notifications"].append({
                "ts": date.today().isoformat(),
                "kind": "admin_review_required",
                "user_id": member_id,
                "instance_id": instance_id,
                "message": "Demo assessment submitted. Admin review required.",
                "status": "queued",
            })

    save_db(db)

topbar("Demo Mode", "Fill LAF, NSP Page 1 and NSP Page 2 at the click of a button for testing/demo.", "Admin testing")
render_system_message()

members = list_members()
member_options = [f"{m['id']} — {m['name']} — {m['email']}" for m in members]

card_start()
st.subheader("Demo Mode options")
st.markdown(
    """
    <div class='warning-banner'>
      <b>Use only for testing/demo.</b><br>
      This will auto-fill LAF, NSP Page 1 and NSP Page 2 with sample responses. Do not use it for real client records.
    </div>
    """,
    unsafe_allow_html=True,
)

mode = st.radio(
    "Choose demo action",
    [
        "Create/Use Demo Filled Member",
        "Fill selected existing member",
    ],
)

submit_for_review = st.checkbox("Also mark assessment as submitted for admin review", value=True)

if mode == "Create/Use Demo Filled Member":
    if st.button("Create/Fill Demo Member Now", type="primary", use_container_width=True):
        member_id, created = ensure_demo_member()
        fill_demo_for_member(member_id, submit_for_review=submit_for_review)
        set_system_message(
            "Demo member created/filled successfully. LAF, NSP Page 1 and NSP Page 2 are now populated.",
            "success",
            celebrate=True,
        )
        st.rerun()
else:
    if not member_options:
        st.info("No members available.")
    else:
        selected = st.selectbox("Select member to auto-fill", member_options)
        member_id = selected.split(" — ")[0]
        if st.button("Fill Selected Member Now", type="primary", use_container_width=True):
            fill_demo_for_member(member_id, submit_for_review=submit_for_review)
            set_system_message(
                "Selected member has been auto-filled successfully.",
                "success",
                celebrate=True,
            )
            st.rerun()
card_end()

card_start()
st.subheader("Demo credentials")
st.markdown(
    """
    If you use the demo-filled member option, login as:
    ```text
    demo.filled@healthyme.local
    password@123
    ```
    """
)
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")