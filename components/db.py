import datetime
import uuid
import re, html

import json, pathlib, hashlib, uuid, datetime
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "db.json"
from components.storage_backend import load_state, save_state

def load_db():
    db = load_state()
    before = len(db.get("users", []))
    db = ensure_default_admin(db)
    if len(db.get("users", [])) != before:
        save_state(db)
    return db
def save_db(db): save_state(db)
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def ensure_default_admin(db):
    """Guarantee one fallback admin exists if database state has no admin.

    This protects first deploy/Supabase-empty states from locking out the admin.
    It does not overwrite existing admins.
    """
    db.setdefault("users", [])
    has_admin = any(u.get("role") == "admin" and u.get("email", "").lower() == "admin@healthyme.local" for u in db.get("users", []))
    if not has_admin:
        db["users"].append({
            "id": "admin001",
            "name": "Demo Admin",
            "email": "admin@healthyme.local",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "must_reset_password": False,
            "is_active": True,
        })
    return db
def authenticate(email, password):
    email = (email or "").strip().lower()
    password = (password or "").strip()
    db=load_db(); hp=hash_password(password)
    for u in db.get("users", []):
        if u.get("email", "").strip().lower()==email and u.get("password_hash")==hp and u.get("is_active", True): return u
    return None
def create_login_session(user_id):
    """Create a lightweight login token for browser refresh persistence."""
    db = load_db()
    token = str(uuid.uuid4())
    db.setdefault("login_sessions", {})[token] = {
        "user_id": user_id,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "active": True,
    }
    save_db(db)
    return token

def get_user_by_session_token(token):
    token = (token or "").strip()
    if not token:
        return None
    db = load_db()
    session = db.get("login_sessions", {}).get(token)
    if not session or not session.get("active"):
        return None
    user_id = session.get("user_id")
    for u in db.get("users", []):
        if u.get("id") == user_id and u.get("is_active", True):
            return u
    return None

def clear_login_session(token):
    token = (token or "").strip()
    if not token:
        return
    db = load_db()
    if token in db.get("login_sessions", {}):
        db["login_sessions"][token]["active"] = False
        save_db(db)
def find_user_by_email(email):
    email = (email or "").strip().lower()
    if not email:
        return None
    db = load_db()
    for u in db.get("users", []):
        if u.get("email", "").strip().lower() == email and u.get("is_active", True):
            return u
    return None

def ensure_oidc_user_record(email, name="", role="member"):
    """Create a role-mapping user if explicitly needed by admin tools.

    Not used for public signup. Login guards still require an existing authorized user.
    """
    db = load_db()
    existing = None
    for u in db.get("users", []):
        if u.get("email", "").strip().lower() == (email or "").strip().lower():
            existing = u
            break
    if existing:
        return existing["id"]
    user_id = str(uuid.uuid4())[:8]
    db.setdefault("users", []).append({
        "id": user_id,
        "name": name or email,
        "email": email,
        "password_hash": "",
        "role": role,
        "must_reset_password": False,
        "is_active": True,
        "auth_provider": "oidc",
    })
    if role == "member":
        db.setdefault("profiles", {})[user_id] = {"full_name": name or "", "gender": "", "age": "", "height_cm": "", "weight_kg": "", "mobile_number": "", "country": "", "occupation": ""}
        db.setdefault("workflow", {})[user_id] = {"laf_completed":False,"nsp1_completed":False,"nsp2_completed":False,"submitted_for_review":False,"admin_completed":False,"final_report_ready":False,"workflow_status":"not_started"}
    save_db(db)
    return user_id

def change_password(user_id, new_password):
    db=load_db()
    for u in db["users"]:
        if u["id"]==user_id:
            u["password_hash"]=hash_password(new_password); u["must_reset_password"]=False; save_db(db); return
def create_user(name,email,role):
    db=load_db(); user_id=str(uuid.uuid4())[:8]
    db["users"].append({"id":user_id,"name":name,"email":email,"password_hash":hash_password("password@123"),"role":role,"must_reset_password":True,"is_active":True})
    if role=="member":
        db["profiles"][user_id]={"full_name":"","gender":"","age":"","height_cm":"","weight_kg":"","mobile_number":"","country":"","occupation":""}
        db["workflow"][user_id]={"laf_completed":False,"nsp1_completed":False,"nsp2_completed":False,"submitted_for_review":False,"admin_completed":False,"final_report_ready":False,"workflow_status":"not_started"}
    save_db(db); return user_id
def normalize_workflow(wf):
    base={"laf_completed":False,"nsp1_completed":False,"nsp2_completed":False,"submitted_for_review":False,"admin_completed":False,"final_report_ready":False,"body_mind_activation_requested":False,"body_mind_unlocked":False,"body_mind_completed":False,"workflow_status":"not_started"}
    base.update(wf or {})
    base["workflow_status"]="finalized" if base["final_report_ready"] else ("admin_completed" if base["admin_completed"] else ("submitted" if base["submitted_for_review"] else ("in_progress" if base["laf_completed"] or base["nsp1_completed"] or base["nsp2_completed"] else "not_started")))
    return base
def get_workflow(user_id): return normalize_workflow(load_db()["workflow"].get(user_id,{}))
def update_workflow(user_id, **kwargs):
    db=load_db()
    wf=normalize_workflow(db["workflow"].setdefault(user_id,{}))
    wf.update(kwargs)
    db["workflow"][user_id]=normalize_workflow(wf)
    save_db(db)

    # v31: keep assessment instance status aligned with final workflow status.
    if kwargs.get("admin_completed") is True or kwargs.get("final_report_ready") is True:
        sync_member_finalization_state(user_id, body_mind_unlock=None)
def save_form_response(store,user_id,data): db=load_db(); db[store][user_id]=data; save_db(db)
def get_form_response(store,user_id): return load_db().get(store,{}).get(user_id,{})
def save_nsp_score(user_id,data): db=load_db(); db["nsp_scores"][user_id]=data; save_db(db)
def get_nsp_score(user_id): return load_db().get("nsp_scores",{}).get(user_id,{})
def queue_notification(kind,user_id,message): db=load_db(); db["notifications"].append({"ts":datetime.datetime.now().isoformat(timespec="seconds"),"kind":kind,"user_id":user_id,"message":message,"status":"queued"}); save_db(db)
def submit_member_for_review_once(user_id):
    """Mark member submitted for review once and queue admin review notification once.

    Returns True if this was the first submission, False if already submitted earlier.
    """
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    was_already_submitted = bool(wf.get("submitted_for_review"))

    wf["nsp2_completed"] = True
    wf["submitted_for_review"] = True
    db["workflow"][user_id] = normalize_workflow(wf)

    if not was_already_submitted:
        db.setdefault("notifications", []).append({
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "kind": "admin_review_required",
            "user_id": user_id,
            "message": "Member completed all questionnaires. Admin review required.",
            "status": "queued",
        })

    save_db(db)
    return not was_already_submitted

# --------------------------------------------------------------------
# v95: Instance-aware admin assessment helpers for NSP reassessment
# --------------------------------------------------------------------
def _now_iso_v95():
    return datetime.datetime.now().isoformat(timespec="seconds")

def _today_iso_v95():
    return datetime.date.today().isoformat()

def _find_assessment_instance(db, user_id, instance_id):
    if not instance_id:
        return None
    for inst in db.get("assessment_instances", {}).get(user_id, []) or []:
        if inst.get("instance_id") == instance_id:
            return inst
    return None

def save_admin_assessment(user_id, data, instance_id=None):
    db = load_db()
    db.setdefault("admin_assessments", {})
    db.setdefault("admin_assessments_by_instance", {})

    if instance_id:
        db["admin_assessments_by_instance"][instance_id] = {
            "member_id": user_id,
            "instance_id": instance_id,
            "updated_at": _now_iso_v95(),
            "data": data,
        }
        inst = _find_assessment_instance(db, user_id, instance_id)
        if inst:
            inst["admin_draft_saved"] = True
            inst["admin_draft_saved_at"] = _now_iso_v95()

    # Keep legacy member-level storage for non-instance flows and initial assessment compatibility.
    if not instance_id:
        db["admin_assessments"][user_id] = data
    else:
        inst = _find_assessment_instance(db, user_id, instance_id)
        if inst and int(inst.get("instance_number", 0) or 0) == 1:
            db["admin_assessments"][user_id] = data

    save_db(db)

def get_admin_assessment(user_id, instance_id=None):
    db = load_db()
    if instance_id:
        record = db.get("admin_assessments_by_instance", {}).get(instance_id)
        if isinstance(record, dict):
            data = record.get("data", {})
            if isinstance(data, dict) and data:
                return data
    return db.get("admin_assessments", {}).get(user_id, {})

def is_instance_final_report_ready(user_id, instance_id=None):
    db = load_db()
    if instance_id:
        inst = _find_assessment_instance(db, user_id, instance_id)
        if not inst:
            return False
        return bool(inst.get("final_report_ready")) or bool(inst.get("admin_completed")) or str(inst.get("status", "")).lower() == "finalized"
    wf = normalize_workflow(db.get("workflow", {}).get(user_id, {}))
    return bool(wf.get("final_report_ready"))

def member_has_meaningful_data(user_id): return bool(get_form_response("laf_responses",user_id) or get_form_response("nsp1_responses",user_id) or get_form_response("nsp2_responses",user_id))
def list_members():
    db=load_db(); rows=[]
    seen=set()
    for u in db.get("users", []):
        if u.get("role")=="member" and u.get("is_active", True):
            uid = u.get("id")
            if uid in seen:
                continue
            seen.add(uid)
            wf=normalize_workflow(db.get("workflow", {}).get(uid,{}))
            rows.append({"id":uid,"name":u.get("name",""),"email":u.get("email",""),"laf_completed":wf["laf_completed"],"nsp1_completed":wf["nsp1_completed"],"nsp2_completed":wf["nsp2_completed"],"submitted":wf["submitted_for_review"],"admin_completed":wf["admin_completed"],"final_report_ready":wf["final_report_ready"],"workflow_status":wf["workflow_status"]})
    return rows

def count_member_accounts():
    return len(list_members())

def count_admin_accounts():
    db=load_db()
    return len([u for u in db.get("users", []) if u.get("role")=="admin" and u.get("is_active", True)])
def get_profile(user_id):
    return get_profile_with_laf_fallback(user_id)

def update_profile(user_id, data):
    db = load_db()
    existing = db.setdefault("profiles", {}).get(user_id, {})
    merged = dict(existing)
    merged.update(data)

    # Backward-compatible aliases
    if merged.get("mobile_number"):
        merged["phone"] = merged.get("mobile_number")
    if merged.get("country"):
        merged["city"] = merged.get("country")

    db["profiles"][user_id] = merged

    # Keep LAF Basic Profile aligned when member edits My Profile.
    laf = db.setdefault("laf_responses", {}).setdefault(user_id, {})
    for key in [
        "full_name",
        "email_id",
        "gender",
        "age",
        "height_cm",
        "weight_kg",
        "country",
        "mobile_number",
        "occupation",
    ]:
        value = merged.get(key, "")
        if value not in [None, "", "Select", "Not applicable"]:
            laf[key] = str(value)

    # Compatibility for older keys
    if merged.get("mobile_number"):
        laf["phone"] = merged.get("mobile_number")
    if merged.get("country"):
        laf["city"] = merged.get("country")

    db["laf_responses"][user_id] = laf
    save_db(db)

def sync_profile_from_laf(user_id):
    """Populate My Profile from LAF. LAF wins for overlapping fields."""
    db = load_db()
    laf = db.setdefault("laf_responses", {}).get(user_id, {})
    profile = db.setdefault("profiles", {}).setdefault(user_id, {})
    user = next((u for u in db.get("users", []) if u.get("id") == user_id), {})

    # LAF is source of truth for overlapping profile fields.
    field_sources = {
        "full_name": ["full_name"],
        "gender": ["gender"],
        "age": ["age"],
        "height_cm": ["height_cm"],
        "weight_kg": ["weight_kg"],
        "country": ["country", "city", "client_city"],
        "mobile_number": ["mobile_number", "phone", "mobile_phone", "home_phone", "work_phone"],
        "occupation": ["occupation"],
        "email_id": ["email_id"],
    }

    for profile_key, laf_keys in field_sources.items():
        value = ""
        for laf_key in laf_keys:
            if laf.get(laf_key) not in [None, "", "Select", "Not applicable"]:
                value = laf.get(laf_key)
                break
        if not value and profile_key == "email_id":
            value = user.get("email", "")
        if value not in [None, "", "Select", "Not applicable"]:
            profile[profile_key] = str(value)

    # Backward-compatible aliases for older pages/report logic.
    if profile.get("mobile_number"):
        profile["phone"] = profile.get("mobile_number")
    if profile.get("country"):
        profile["city"] = profile.get("country")

    db["profiles"][user_id] = profile
    save_db(db)
    return profile

def get_profile_with_laf_fallback(user_id):
    """Return profile with LAF values overlaid, so My Profile always reflects latest LAF."""
    db = load_db()
    profile = db.setdefault("profiles", {}).get(user_id, {}).copy()
    laf = db.setdefault("laf_responses", {}).get(user_id, {})
    user = next((u for u in db.get("users", []) if u.get("id") == user_id), {})

    # LAF values should override stored profile values for shared fields.
    field_sources = {
        "full_name": ["full_name"],
        "gender": ["gender"],
        "age": ["age"],
        "height_cm": ["height_cm"],
        "weight_kg": ["weight_kg"],
        "country": ["country", "city", "client_city"],
        "mobile_number": ["mobile_number", "phone", "mobile_phone", "home_phone", "work_phone"],
        "occupation": ["occupation"],
        "email_id": ["email_id"],
    }

    for profile_key, laf_keys in field_sources.items():
        for laf_key in laf_keys:
            if laf.get(laf_key) not in [None, "", "Select", "Not applicable"]:
                profile[profile_key] = str(laf.get(laf_key))
                break
        if profile_key == "email_id" and not profile.get(profile_key):
            profile[profile_key] = user.get("email", "")

    # Backward-compatible aliases.
    if not profile.get("mobile_number") and profile.get("phone"):
        profile["mobile_number"] = profile.get("phone")
    if not profile.get("country") and profile.get("city"):
        profile["country"] = profile.get("city")
    if profile.get("mobile_number"):
        profile["phone"] = profile.get("mobile_number")
    if profile.get("country"):
        profile["city"] = profile.get("country")

    return profile


def unlock_body_mind(user_id, unlocked=True):
    db = load_db()
    wf = db["workflow"].setdefault(user_id, {})
    wf["body_mind_unlocked"] = bool(unlocked)
    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)

def get_body_mind_response(user_id):
    db = load_db()
    return db.setdefault("body_mind_responses", {}).get(user_id, {})

def save_body_mind_response(user_id, data, completed=False):
    db = load_db()
    db.setdefault("body_mind_responses", {})[user_id] = data
    wf = db["workflow"].setdefault(user_id, {})
    wf["body_mind_completed"] = bool(completed)
    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)

def update_member_response_with_audit(admin_id, member_id, form_name, field_code, old_value, new_value, rationale):
    db = load_db()
    db.setdefault("response_audit_log", [])
    db["response_audit_log"].append({
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "admin_id": admin_id,
        "member_id": member_id,
        "form_name": form_name,
        "field_code": field_code,
        "old_value": old_value,
        "new_value": new_value,
        "rationale": rationale,
    })
    save_db(db)

def save_db_direct(db):
    save_db(db)



def save_daily_log(user_id, log_data):
    db = load_db()
    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    entry = dict(log_data)
    entry["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    db["daily_logs"][user_id].append(entry)
    save_db(db)

def get_daily_logs(user_id):
    db = load_db()
    return db.setdefault("daily_logs", {}).get(user_id, [])

def set_body_mind_visibility(user_id, unlocked):
    db = load_db()
    wf = normalize_workflow(db["workflow"].setdefault(user_id, {}))
    admin_done = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready")) or wf.get("workflow_status") == "finalized"

    if bool(unlocked):
        wf["body_mind_activation_requested"] = True
        wf["body_mind_unlocked"] = bool(admin_done)
        db.setdefault("body_mind_access", {})[user_id] = bool(admin_done)
    else:
        wf["body_mind_activation_requested"] = False
        wf["body_mind_unlocked"] = False
        db.setdefault("body_mind_access", {})[user_id] = False

    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)

def get_response_audit_for_member(user_id):
    db = load_db()
    return [x for x in db.get("response_audit_log", []) if x.get("member_id") == user_id]



# ---------------------------------------------------------------------
# Assessment Instance / Reassessment Helpers
# ---------------------------------------------------------------------
def _now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def _today_iso():
    return datetime.date.today().isoformat()

def _page_title(page):
    return {"nsp1": "NSP Page 1", "nsp2": "NSP Page 2"}.get(page, page)

def ensure_assessment_instances(user_id):
    """Create initial assessment instance if missing and migrate current NSP data into it."""
    db = load_db()
    db.setdefault("assessment_instances", {})
    db.setdefault("assessment_instance_responses", {})
    instances = db["assessment_instances"].setdefault(user_id, [])

    if not instances:
        wf = normalize_workflow(db.get("workflow", {}).get(user_id, {}))
        instance_id = f"{user_id}_inst_1"
        status = "review_required" if wf.get("submitted_for_review") else ("in_progress" if wf.get("nsp1_completed") or wf.get("nsp2_completed") else "pending")
        inst = {
            "instance_id": instance_id,
            "member_id": user_id,
            "instance_number": 1,
            "instance_type": "Initial Assessment",
            "requested_pages": ["nsp1", "nsp2"],
            "created_by_admin": "",
            "created_date": _today_iso(),
            "due_date": "",
            "admin_note": "",
            "nsp1_required": True,
            "nsp2_required": True,
            "nsp1_completed": bool(wf.get("nsp1_completed")),
            "nsp2_completed": bool(wf.get("nsp2_completed")),
            "consent_accepted": bool(wf.get("submitted_for_review")),
            "submitted_for_review": bool(wf.get("submitted_for_review")),
            "submitted_date": _today_iso() if wf.get("submitted_for_review") else "",
            "status": status,
        }
        instances.append(inst)
        db["assessment_instance_responses"][instance_id] = {
            "nsp1": db.get("nsp1_responses", {}).get(user_id, {}),
            "nsp2": db.get("nsp2_responses", {}).get(user_id, {}),
            "consent": {},
        }
        db["assessment_instances"][user_id] = instances
        save_db(db)
    return instances

def get_assessment_instances(user_id):
    return ensure_assessment_instances(user_id)

def get_current_assessment_instance(user_id):
    instances = ensure_assessment_instances(user_id)
    open_instances = [i for i in instances if not i.get("submitted_for_review") and i.get("status") in ["pending", "in_progress"]]
    if open_instances:
        # Prefer the latest pending reassessment/assessment.
        return sorted(open_instances, key=lambda x: x.get("instance_number", 0), reverse=True)[0]
    return sorted(instances, key=lambda x: x.get("instance_number", 0), reverse=True)[0]

def get_instance_response(instance_id, page):
    db = load_db()
    return db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {}).get(page, {})

def save_instance_page_response(user_id, page, data):
    db = load_db()
    instances = db.setdefault("assessment_instances", {}).setdefault(user_id, [])
    if not instances:
        save_db(db)
        ensure_assessment_instances(user_id)
        db = load_db()
        instances = db["assessment_instances"][user_id]

    current = get_current_assessment_instance(user_id)
    instance_id = current["instance_id"]
    db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {}).setdefault("consent", {})
    db["assessment_instance_responses"][instance_id][page] = data

    # Keep legacy latest response stores updated for backwards-compatible report pages.
    if page == "nsp1":
        db.setdefault("nsp1_responses", {})[user_id] = data
    if page == "nsp2":
        db.setdefault("nsp2_responses", {})[user_id] = data

    for inst in db["assessment_instances"][user_id]:
        if inst["instance_id"] == instance_id:
            inst["status"] = "in_progress"
            if page == "nsp1":
                inst["nsp1_completed"] = True
            if page == "nsp2":
                inst["nsp2_completed"] = True
            break

    save_db(db)
    return instance_id

def create_reassessment_request(member_id, requested_pages, due_date="", admin_note="", admin_id="admin"):
    db = load_db()
    ensure_assessment_instances(member_id)
    db = load_db()
    instances = db.setdefault("assessment_instances", {}).setdefault(member_id, [])

    # Prevent duplicate open request.
    open_request = [i for i in instances if not i.get("submitted_for_review") and i.get("instance_type") == "Reassessment" and i.get("status") in ["pending", "in_progress"]]
    if open_request:
        return open_request[-1], False

    next_num = max([int(i.get("instance_number", 0)) for i in instances] + [0]) + 1
    instance_id = f"{member_id}_inst_{next_num}"
    pages = [p for p in requested_pages if p in ["nsp1", "nsp2"]]
    if not pages:
        pages = ["nsp1", "nsp2"]

    inst = {
        "instance_id": instance_id,
        "member_id": member_id,
        "instance_number": next_num,
        "instance_type": "Reassessment",
        "requested_pages": pages,
        "created_by_admin": admin_id,
        "created_date": _today_iso(),
        "due_date": due_date,
        "admin_note": admin_note,
        "nsp1_required": "nsp1" in pages,
        "nsp2_required": "nsp2" in pages,
        "nsp1_completed": False,
        "nsp2_completed": False,
        "consent_accepted": False,
        "submitted_for_review": False,
        "submitted_date": "",
        "status": "pending",
    }
    instances.append(inst)
    db["assessment_instances"][member_id] = instances
    db.setdefault("assessment_instance_responses", {})[instance_id] = {"nsp1": {}, "nsp2": {}, "consent": {}}
    db.setdefault("notifications", []).append({
        "ts": _now_iso(),
        "kind": "member_reassessment_request",
        "user_id": member_id,
        "message": f"Reassessment requested: {', '.join(_page_title(p) for p in pages)}",
        "status": "queued",
    })
    save_db(db)
    return inst, True

def submit_current_assessment_instance_once(user_id, consent_data=None):
    """Submit current assessment/reassessment instance once. Returns True on first submit."""
    db = load_db()
    ensure_assessment_instances(user_id)
    db = load_db()
    current = get_current_assessment_instance(user_id)
    instance_id = current["instance_id"]
    was_submitted = bool(current.get("submitted_for_review"))

    # Save consent.
    consent = dict(consent_data or {})
    consent["accepted"] = bool(consent.get("accepted", True))
    consent.setdefault("accepted_date", _today_iso())
    db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {}).setdefault("nsp1", {})
    db["assessment_instance_responses"][instance_id].setdefault("nsp2", {})
    db["assessment_instance_responses"][instance_id]["consent"] = consent

    for inst in db["assessment_instances"][user_id]:
        if inst["instance_id"] == instance_id:
            inst["consent_accepted"] = bool(consent.get("accepted"))
            inst["submitted_for_review"] = True
            inst["submitted_date"] = _today_iso()
            inst["status"] = "review_required"
            inst["nsp1_completed"] = True if inst.get("nsp1_required") else inst.get("nsp1_completed", False)
            inst["nsp2_completed"] = True if inst.get("nsp2_required") else inst.get("nsp2_completed", False)
            current = inst
            break

    # Legacy workflow remains for current dashboard compatibility.
    wf = db.setdefault("workflow", {}).setdefault(user_id, {})
    if current.get("instance_number") == 1:
        wf["nsp1_completed"] = wf.get("nsp1_completed") or current.get("nsp1_completed")
        wf["nsp2_completed"] = wf.get("nsp2_completed") or current.get("nsp2_completed")
    wf["submitted_for_review"] = True
    db["workflow"][user_id] = normalize_workflow(wf)

    if not was_submitted:
        db.setdefault("notifications", []).append({
            "ts": _now_iso(),
            "kind": "admin_review_required",
            "user_id": user_id,
            "instance_id": instance_id,
            "message": f"{current.get('instance_type', 'Assessment')} Instance {current.get('instance_number')} submitted. Admin review required.",
            "status": "queued",
        })

    save_db(db)
    return not was_submitted

def list_review_queue():
    db = load_db()
    # Ensure all member records have an initial instance before scanning.
    for u in db.get("users", []):
        if u.get("role") == "member":
            ensure_assessment_instances(u["id"])
    db = load_db()

    users = {u["id"]: u for u in db.get("users", [])}
    rows = []
    for uid, instances in db.get("assessment_instances", {}).items():
        for inst in instances:
            if inst.get("submitted_for_review") and inst.get("status") == "review_required":
                user = users.get(uid, {})
                rows.append({
                    "member_id": uid,
                    "member_name": user.get("name", uid),
                    "email": user.get("email", ""),
                    "instance_id": inst.get("instance_id"),
                    "instance_number": inst.get("instance_number"),
                    "instance_type": inst.get("instance_type"),
                    "requested_pages": ", ".join(_page_title(p) for p in inst.get("requested_pages", [])),
                    "submitted_date": inst.get("submitted_date", ""),
                    "status": inst.get("status", ""),
                })
    rows.sort(key=lambda x: (x.get("submitted_date", ""), x.get("member_name", "")), reverse=True)
    return rows

def get_all_member_instances():
    db = load_db()
    for u in db.get("users", []):
        if u.get("role") == "member":
            ensure_assessment_instances(u["id"])
    db = load_db()

    users = {u["id"]: u for u in db.get("users", [])}
    rows = []
    for uid, instances in db.get("assessment_instances", {}).items():
        for inst in instances:
            user = users.get(uid, {})
            rows.append({
                "member_id": uid,
                "member_name": user.get("name", uid),
                "email": user.get("email", ""),
                **inst,
            })
    return rows


def get_admin_dashboard_snapshot():
    """Load dashboard data once to prevent repeated database reads."""
    db = load_db()
    members = []
    seen = set()
    for u in db.get("users", []):
        if u.get("role") == "member" and u.get("is_active", True):
            uid = u.get("id")
            if uid in seen:
                continue
            seen.add(uid)
            wf = normalize_workflow(db.get("workflow", {}).get(uid, {}))
            members.append({
                "id": uid,
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "laf_completed": wf["laf_completed"],
                "nsp1_completed": wf["nsp1_completed"],
                "nsp2_completed": wf["nsp2_completed"],
                "submitted": wf["submitted_for_review"],
                "admin_completed": wf["admin_completed"],
                "final_report_ready": wf["final_report_ready"],
                "workflow_status": wf["workflow_status"],
            })

    admin_count = len([
        u for u in db.get("users", [])
        if u.get("role") == "admin" and u.get("is_active", True)
    ])

    # Lightweight queue calculation directly from loaded db, no extra load_db calls.
    users = {u.get("id"): u for u in db.get("users", [])}
    queue = []
    for uid, instances in db.get("assessment_instances", {}).items():
        for inst in instances:
            if inst.get("submitted_for_review") and inst.get("status") == "review_required":
                user = users.get(uid, {})
                pages = inst.get("requested_pages", [])
                queue.append({
                    "member_id": uid,
                    "member_name": user.get("name", uid),
                    "email": user.get("email", ""),
                    "instance_id": inst.get("instance_id"),
                    "instance_number": inst.get("instance_number"),
                    "instance_type": inst.get("instance_type"),
                    "requested_pages": ", ".join("NSP Page 1" if p == "nsp1" else "NSP Page 2" for p in pages),
                    "submitted_date": inst.get("submitted_date", ""),
                    "status": inst.get("status", ""),
                })
    queue.sort(key=lambda x: (x.get("submitted_date", ""), x.get("member_name", "")), reverse=True)

    return {
        "members": members,
        "member_count": len(members),
        "admin_count": admin_count,
        "review_queue": queue,
        "initial_pending": [r for r in queue if r.get("instance_type") == "Initial Assessment"],
        "reassess_pending": [r for r in queue if r.get("instance_type") == "Reassessment"],
        "finalized_count": sum(1 for m in members if m.get("final_report_ready")),
    }


def list_all_users_for_access_manager():
    db = load_db()
    rows = []
    seen = set()
    for u in db.get("users", []):
        uid = u.get("id")
        if uid in seen:
            continue
        seen.add(uid)
        rows.append({
            "id": uid,
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", ""),
            "is_active": bool(u.get("is_active", True)),
            "auth_provider": u.get("auth_provider", "oidc"),
        })
    rows.sort(key=lambda r: (r["role"], r["name"].lower(), r["email"].lower()))
    return rows

def update_user_access_record(user_id, name=None, role=None, is_active=None, email=None, actor="admin"):
    db = load_db()
    users = db.setdefault("users", [])
    target = None
    before = None
    for u in users:
        if u.get("id") == user_id:
            target = u
            before = dict(u)
            break
    if not target:
        return False, "User not found."

    if name is not None:
        target["name"] = name.strip()
    if role is not None:
        target["role"] = role
    if is_active is not None:
        target["is_active"] = bool(is_active)
    if email is not None:
        target["email"] = email.strip().lower()

    db.setdefault("audit_logs", []).append({
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "actor": actor,
        "action": "user_access_update",
        "user_id": user_id,
        "before": before,
        "after": dict(target),
    })
    save_db(db)
    return True, "HealthyMe user updated."

def soft_delete_user_access_record(user_id, actor="admin"):
    return update_user_access_record(user_id, is_active=False, actor=actor)


# --------------------------------------------------------------------
# v5: Allocation + communication helper functions
# --------------------------------------------------------------------

def _now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def get_user_by_id(user_id):
    db = load_db()
    for u in db.get("users", []):
        if u.get("id") == user_id:
            return u
    return None

def list_active_members():
    return list_members()

def _ensure_assignment_store(db):
    db.setdefault("resource_assignments", {})
    db["resource_assignments"].setdefault("recipes", {})
    db["resource_assignments"].setdefault("exercises", {})
    return db

def get_resource_assignments(member_id, resource_type):
    db = _ensure_assignment_store(load_db())
    resource_type = "recipes" if resource_type == "recipes" else "exercises"
    return db["resource_assignments"].get(resource_type, {}).get(member_id, [])

def save_resource_assignments(member_id, resource_type, item_ids, actor="admin"):
    db = _ensure_assignment_store(load_db())
    resource_type = "recipes" if resource_type == "recipes" else "exercises"
    clean_ids = [str(x) for x in item_ids if str(x).strip()]
    db["resource_assignments"].setdefault(resource_type, {})[member_id] = clean_ids

    label = "recipes" if resource_type == "recipes" else "exercises"
    db.setdefault("notifications", []).append({
        "ts": _now_iso(),
        "kind": f"{resource_type}_allocated",
        "user_id": member_id,
        "message": f"Your admin has allocated {len(clean_ids)} {label} to your HealthyMe plan.",
        "status": "queued",
        "email_required": True,
        "created_by": actor,
    })
    save_db(db)
    return True

def queue_member_message(member_id, sender_role, subject, message, actor_id=""):
    db = load_db()
    db.setdefault("messages", [])
    msg = {
        "id": str(uuid.uuid4())[:8],
        "ts": _now_iso(),
        "member_id": member_id,
        "sender_role": sender_role,
        "actor_id": actor_id,
        "subject": subject,
        "message": message,
        "status": "queued",
        "email_required": True,
    }
    db["messages"].append(msg)
    db.setdefault("notifications", []).append({
        "ts": msg["ts"],
        "kind": "app_message",
        "user_id": member_id,
        "message": f"{subject}: {message[:160]}",
        "status": "queued",
        "email_required": True,
        "created_by": actor_id or sender_role,
    })
    save_db(db)
    return msg

def get_member_messages(member_id, limit=10):
    db = load_db()
    rows = [m for m in db.get("messages", []) if m.get("member_id") == member_id]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def queue_daily_log_reminder(member_id, actor="admin"):
    member = get_user_by_id(member_id) or {}
    db = load_db()
    db.setdefault("notifications", []).append({
        "ts": _now_iso(),
        "kind": "daily_log_reminder",
        "user_id": member_id,
        "message": "Gentle reminder: please fill your Daily Log through the HealthyMe app.",
        "status": "queued",
        "email_required": True,
        "email_to": member.get("email", ""),
        "created_by": actor,
    })
    save_db(db)
    return True



# --------------------------------------------------------------------
# v25: Body-Mind request + activation sync helper
# --------------------------------------------------------------------
def sync_body_mind_after_admin_completion(user_id, activation_selected=False):
    """v29 sync: Body-Mind unlock is manual and requires final admin completion.

    Rule:
    - If admin final work is complete and activation_selected=True, unlock.
    - If admin final work is not complete and activation_selected=True, store request only.
    - Do not auto-unlock merely because final report is ready.
    """
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    admin_done = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready"))

    if activation_selected:
        wf["body_mind_activation_requested"] = True
        wf["body_mind_unlocked"] = bool(admin_done)
    else:
        # Preserve existing state. Do not disable here.
        wf["body_mind_unlocked"] = bool(wf.get("body_mind_unlocked"))

    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)
    return bool(wf.get("body_mind_unlocked"))

def request_body_mind_activation(user_id):
    """Record manual admin request for Body-Mind activation."""
    ok, _msg = manually_unlock_body_mind_after_finalization(user_id)
    if ok:
        return True
    return sync_body_mind_after_admin_completion(user_id, activation_selected=True)

def clear_body_mind_activation(user_id):
    """Explicitly disable Body-Mind visibility and clear pending request."""
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    wf["body_mind_activation_requested"] = False
    wf["body_mind_unlocked"] = False
    db["workflow"][user_id] = normalize_workflow(wf)
    db.setdefault("body_mind_access", {})[user_id] = False
    save_db(db)
    return True



# --------------------------------------------------------------------
# v95: Finalize admin assessment safely, with reassessment instance support
# --------------------------------------------------------------------
def finalize_admin_assessment(user_id, assessment_data, activation_selected=False, instance_id=None):
    """Save admin assessment and mark final report ready.

    For normal/legacy flow, this keeps existing global workflow finalization behavior.
    For reassessment flow, this finalizes only the selected assessment instance and stores
    the admin review under admin_assessments_by_instance[instance_id].
    """
    db = load_db()
    db.setdefault("admin_assessments", {})
    db.setdefault("admin_assessments_by_instance", {})

    wf_before = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    already_finalized = bool(wf_before.get("admin_completed")) or bool(wf_before.get("final_report_ready"))

    if instance_id:
        db["admin_assessments_by_instance"][instance_id] = {
            "member_id": user_id,
            "instance_id": instance_id,
            "updated_at": _now_iso_v95(),
            "finalized_at": _now_iso_v95(),
            "data": assessment_data,
        }

        selected_inst = _find_assessment_instance(db, user_id, instance_id)
        selected_inst_number = int(selected_inst.get("instance_number", 0) or 0) if selected_inst else 0
        selected_inst_type = str(selected_inst.get("instance_type", "")).lower() if selected_inst else ""

        if selected_inst:
            selected_inst["admin_completed"] = True
            selected_inst["final_report_ready"] = True
            selected_inst["review_status"] = "finalized"
            selected_inst["status"] = "finalized"
            selected_inst["admin_completed_date"] = _today_iso_v95()
            selected_inst["finalized_date"] = _today_iso_v95()

        # Preserve legacy member-level admin assessment for initial assessment compatibility only.
        if selected_inst_number == 1 or selected_inst_type == "initial assessment":
            db["admin_assessments"][user_id] = assessment_data

        # Keep global workflow finalized if already finalized; if this is the first/initial finalization,
        # finalize global workflow too. Reassessment finalization should not corrupt older instances.
        wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
        if selected_inst_number == 1 or not bool(wf.get("final_report_ready")):
            wf["admin_completed"] = True
            wf["final_report_ready"] = True
            wf["workflow_status"] = "finalized"
            wf["submitted_for_review"] = True

        if activation_selected:
            wf["body_mind_activation_requested"] = True
            wf["body_mind_unlocked"] = True
            db.setdefault("body_mind_access", {})[user_id] = True

        db["workflow"][user_id] = normalize_workflow(wf)
        save_db(db)

        final_wf = get_workflow(user_id)
        return {
            "already_finalized": already_finalized,
            "body_mind_unlocked": bool(final_wf.get("body_mind_unlocked")),
            "body_mind_activation_requested": bool(final_wf.get("body_mind_activation_requested")),
            "instance_id": instance_id,
            "instance_final_report_ready": True,
        }

    # Legacy/global flow.
    db["admin_assessments"][user_id] = assessment_data
    save_db(db)

    final_wf = sync_member_finalization_state(
        user_id,
        body_mind_unlock=True if activation_selected or bool(wf_before.get("body_mind_activation_requested")) else None,
    )

    return {
        "already_finalized": already_finalized,
        "body_mind_unlocked": bool(final_wf.get("body_mind_unlocked")),
        "body_mind_activation_requested": bool(final_wf.get("body_mind_activation_requested")),
        "instance_id": "",
        "instance_final_report_ready": False,
    }


# --------------------------------------------------------------------
# v32: Hard sync Body-Mind after manual activation
# --------------------------------------------------------------------
def hard_sync_body_mind_if_requested(user_id):
    """Repair Body-Mind visibility if finalization is done and manual activation was requested.

    This does not unlock on finalization alone. It requires body_mind_activation_requested=True.
    """
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    final_done = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready")) or wf.get("workflow_status") == "finalized"
    requested = bool(wf.get("body_mind_activation_requested"))

    if final_done and requested and not bool(wf.get("body_mind_unlocked")):
        wf["body_mind_unlocked"] = True
        db["workflow"][user_id] = normalize_workflow(wf)
        save_db(db)
        return True

    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)
    return bool(wf.get("body_mind_unlocked"))

def manually_unlock_body_mind_after_finalization(user_id):
    """One-click manual unlock after final admin completion.

    Writes workflow flags and explicit access marker together.
    """
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    admin_done = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready")) or wf.get("workflow_status") == "finalized"

    if not admin_done:
        db["workflow"][user_id] = normalize_workflow(wf)
        save_db(db)
        return False, "Admin final assessment is not completed yet."

    wf["admin_completed"] = True
    wf["final_report_ready"] = True
    wf["workflow_status"] = "finalized"
    wf["body_mind_activation_requested"] = True
    wf["body_mind_unlocked"] = True

    db["workflow"][user_id] = normalize_workflow(wf)
    db.setdefault("body_mind_access", {})[user_id] = True

    for inst in db.get("assessment_instances", {}).get(user_id, []) or []:
        if inst.get("submitted_for_review") or inst.get("status") in ["review_required", "submitted", "pending_review", "in_review", "finalized"]:
            inst["status"] = "finalized"
            inst["admin_completed"] = True
            inst["final_report_ready"] = True
            inst["review_status"] = "finalized"

    save_db(db)
    return True, "Body-Mind Connection manually activated."


# --------------------------------------------------------------------
# v32: Workflow finalization sync helper
# --------------------------------------------------------------------
def sync_member_finalization_state(user_id, *, body_mind_unlock=None):
    db = load_db()
    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    wf["admin_completed"] = True
    wf["final_report_ready"] = True
    wf["workflow_status"] = "finalized"
    wf["submitted_for_review"] = True

    if body_mind_unlock is True:
        wf["body_mind_activation_requested"] = True
        wf["body_mind_unlocked"] = True
    elif body_mind_unlock is False:
        wf["body_mind_activation_requested"] = False
        wf["body_mind_unlocked"] = False
    else:
        # If request exists, repair unlock. Do not unlock without request.
        if wf.get("body_mind_activation_requested"):
            wf["body_mind_unlocked"] = True

    db["workflow"][user_id] = normalize_workflow(wf)

    for inst in db.get("assessment_instances", {}).get(user_id, []) or []:
        if inst.get("submitted_for_review") or inst.get("status") in ["review_required", "submitted", "pending_review", "in_review", "finalized"]:
            inst["status"] = "finalized"
            inst["admin_completed"] = True
            inst["final_report_ready"] = True
            inst["review_status"] = "finalized"

    save_db(db)
    return get_workflow(user_id)


# --------------------------------------------------------------------
# v33: Explicit Body-Mind access marker
# --------------------------------------------------------------------
def _body_mind_access_store(db):
    db.setdefault("body_mind_access", {})
    return db["body_mind_access"]

def set_explicit_body_mind_access(user_id, enabled=True):
    """Persist explicit member access for Body-Mind.

    This is a safety-layer separate from workflow flags so manual admin activation
    cannot be lost due to stale workflow/instance state.
    """
    db = load_db()
    store = _body_mind_access_store(db)
    store[user_id] = bool(enabled)

    wf = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    if enabled:
        wf["body_mind_activation_requested"] = True
        wf["body_mind_unlocked"] = True
    else:
        wf["body_mind_activation_requested"] = False
        wf["body_mind_unlocked"] = False

    db["workflow"][user_id] = normalize_workflow(wf)
    save_db(db)
    return bool(enabled)

def has_explicit_body_mind_access(user_id):
    db = load_db()
    store = db.get("body_mind_access", {})
    if bool(store.get(user_id)):
        return True
    wf = normalize_workflow(db.get("workflow", {}).get(user_id, {}))
    return bool(wf.get("body_mind_unlocked"))




# --------------------------------------------------------------------
# v42: Day-based Daily Food Journal + date-linked supervision notes
# --------------------------------------------------------------------
def _daily_food_journal_store(db):
    db.setdefault("daily_food_journals", {})
    return db["daily_food_journals"]

def save_daily_food_journal_day(user_id, log_date, day_data):
    """Save complete daily food journal for one date.

    This is day-based and contains all meal groups in one object.
    """
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    payload = dict(day_data or {})
    payload["date"] = str(log_date)
    payload["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    payload["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = payload

    # Also mirror a compact latest entry in existing daily_logs for backward compatibility.
    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [x for x in db["daily_logs"][user_id] if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))]
    legacy.append(payload)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return payload

def get_daily_food_journal_day(user_id, log_date):
    db = load_db()
    return db.get("daily_food_journals", {}).get(user_id, {}).get(str(log_date), {})

def get_daily_food_journal_days(user_id):
    db = load_db()
    store = db.get("daily_food_journals", {}).get(user_id, {}) or {}
    rows = list(store.values())
    # Include legacy day records if they exist but were not migrated into daily_food_journals.
    for x in db.get("daily_logs", {}).get(user_id, []) or []:
        if x.get("log_type") == "daily_food_journal_day" and x.get("date") and x.get("date") not in store:
            rows.append(x)
    rows.sort(key=lambda r: (r.get("date", ""), r.get("timestamp", "")), reverse=True)
    return rows

def save_daily_log_supervision_note(member_id, note, actor_id="admin", log_date=None):
    """Save admin supervision note linked to a specific food journal date."""
    note = (note or "").strip()
    if not note:
        return None
    db = load_db()
    db.setdefault("daily_log_supervision_notes", {}).setdefault(member_id, [])
    item = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "member_id": member_id,
        "log_date": str(log_date or ""),
        "note": note,
        "actor_id": actor_id,
    }
    db["daily_log_supervision_notes"][member_id].append(item)

    date_text = f" for {item['log_date']}" if item.get("log_date") else ""
    db.setdefault("messages", []).append({
        "id": str(uuid.uuid4())[:8],
        "ts": item["ts"],
        "member_id": member_id,
        "sender_role": "nutritionist",
        "actor_id": actor_id,
        "subject": f"Nutritionist Note{date_text}",
        "message": note,
        "status": "queued",
        "email_required": True,
        "log_date": item.get("log_date", ""),
    })
    db.setdefault("notifications", []).append({
        "ts": item["ts"],
        "kind": "nutritionist_note",
        "user_id": member_id,
        "message": f"Nutritionist Note{date_text}: {note[:160]}",
        "status": "queued",
        "email_required": True,
        "created_by": actor_id or "admin",
        "log_date": item.get("log_date", ""),
    })
    save_db(db)
    return item

def get_daily_log_supervision_notes(member_id, limit=20, log_date=None):
    db = load_db()
    rows = list(db.get("daily_log_supervision_notes", {}).get(member_id, []))
    if log_date is not None:
        rows = [r for r in rows if str(r.get("log_date", "")) == str(log_date)]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]


# --------------------------------------------------------------------
# v43: Editable meal type repository + progressive meal save
# --------------------------------------------------------------------
def get_meal_type_repository():
    """Return active meal sections configured by admin."""
    db = load_db()
    default_rows = [
        {"key": "breakfast", "label": "Breakfast", "active": True, "sort_order": 1},
        {"key": "lunch", "label": "Lunch", "active": True, "sort_order": 2},
        {"key": "evening_snack", "label": "Evening Snack", "active": True, "sort_order": 3},
        {"key": "dinner", "label": "Dinner", "active": True, "sort_order": 4},
        {"key": "bedtime", "label": "Bedtime", "active": True, "sort_order": 5},
        {"key": "other", "label": "Other", "active": True, "sort_order": 6},
    ]
    rows = db.get("meal_type_repository")
    if not rows:
        db["meal_type_repository"] = default_rows
        save_db(db)
        rows = default_rows
    rows = [r for r in rows if r.get("active", True)]
    rows.sort(key=lambda r: int(r.get("sort_order", 999)))
    return rows

def save_meal_type_repository(rows):
    """Save admin configured meal sections."""
    db = load_db()
    clean = []
    for idx, r in enumerate(rows or [], start=1):
        label = str(r.get("label", "")).strip()
        if not label:
            continue
        key = str(r.get("key") or label.lower().replace(" ", "_").replace("/", "_")).strip()
        clean.append({
            "key": key,
            "label": label,
            "active": bool(r.get("active", True)),
            "sort_order": int(r.get("sort_order", idx) or idx),
        })
    db["meal_type_repository"] = clean
    save_db(db)
    return clean

def save_daily_food_journal_meal(user_id, log_date, meal_key, meal_payload):
    """Save/update a single meal section inside a daily journal."""
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    day = store.get(str(log_date), {
        "date": str(log_date),
        "meals": {},
        "physical_activity": "",
        "poop": "",
        "notes": "",
        "log_type": "daily_food_journal_day",
    })
    day.setdefault("meals", {})
    day["meals"][meal_key] = dict(meal_payload or {})
    day["date"] = str(log_date)
    day["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    day["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = day

    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [x for x in db["daily_logs"][user_id] if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))]
    legacy.append(day)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return day

def save_daily_food_journal_day_details(user_id, log_date, physical_activity="", poop="", notes=""):
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    day = store.get(str(log_date), {
        "date": str(log_date),
        "meals": {},
        "log_type": "daily_food_journal_day",
    })
    day["physical_activity"] = physical_activity
    day["poop"] = poop
    day["notes"] = notes
    day["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    day["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = day
    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [x for x in db["daily_logs"][user_id] if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))]
    legacy.append(day)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return day


# --------------------------------------------------------------------
# v45: ensure Other meal section is available
# --------------------------------------------------------------------
def ensure_other_meal_section():
    db = load_db()
    rows = db.get("meal_type_repository") or []
    if not rows:
        rows = get_meal_type_repository()
    if not any(str(r.get("key")) == "other" and bool(r.get("active", True)) for r in rows):
        rows.append({"key": "other", "label": "Other", "active": True, "sort_order": max([int(r.get("sort_order", 0) or 0) for r in rows] + [0]) + 1})
        db["meal_type_repository"] = rows
        save_db(db)
    return rows


# --------------------------------------------------------------------
# v47: Daily food journal backward compatibility
# --------------------------------------------------------------------
def _legacy_food_journal_days_for_user(db, user_id):
    """Convert old one-row food_journal entries into the new day-based structure."""
    grouped = {}
    meal_label_to_key = {
        "breakfast": "breakfast",
        "lunch": "lunch",
        "evening snack": "evening_snack",
        "dinner": "dinner",
        "bedtime": "bedtime",
        "early morning": "early_morning",
        "mid morning": "mid_morning",
    }
    for item in db.get("daily_logs", {}).get(user_id, []) or []:
        if item.get("log_type") == "daily_food_journal_day":
            continue
        if not (item.get("log_type") == "food_journal" or any(k in item for k in ["meal_type", "food", "portion_size", "mood_energy", "physical_activity", "poop"])):
            continue

        d = str(item.get("date") or item.get("timestamp", "")[:10] or "")
        if not d:
            continue

        day = grouped.setdefault(d, {
            "date": d,
            "meals": {},
            "physical_activity": "",
            "poop": "",
            "notes": "",
            "timestamp": item.get("timestamp", ""),
            "log_type": "daily_food_journal_day",
            "_source": "legacy_daily_logs",
        })

        meal_label = str(item.get("meal_type") or "Other").strip() or "Other"
        base_key = meal_label_to_key.get(meal_label.lower(), "")
        if not base_key:
            existing_other = [k for k in day["meals"].keys() if k.startswith("other_")]
            base_key = f"other_{len(existing_other) + 1}"

        # If same meal appears multiple times, keep first key and create extra Other slots.
        key = base_key
        if key in day["meals"] and any(item.get(x) for x in ["food", "water", "portion_size", "mood_energy"]):
            if base_key.startswith("other_"):
                key = f"other_{len([k for k in day['meals'].keys() if k.startswith('other_')]) + 1}"
            else:
                key = f"{base_key}_extra"

        day["meals"][key] = {
            "label": meal_label,
            "time": item.get("time", ""),
            "food": item.get("food", item.get("food_log", "")),
            "water": item.get("water", item.get("water_ml", "")),
            "portion_size": item.get("portion_size", ""),
            "mood_energy": item.get("mood_energy", ""),
        }

        if item.get("physical_activity") or item.get("exercise_notes"):
            day["physical_activity"] = item.get("physical_activity", item.get("exercise_notes", ""))
        if item.get("poop"):
            day["poop"] = item.get("poop", "")
        if item.get("notes"):
            day["notes"] = item.get("notes", "")

    return grouped

def get_daily_food_journal_day(user_id, log_date):
    db = load_db()
    current = db.get("daily_food_journals", {}).get(user_id, {}).get(str(log_date), {})
    if current:
        return current
    legacy = _legacy_food_journal_days_for_user(db, user_id)
    return legacy.get(str(log_date), {})

def get_daily_food_journal_days(user_id):
    db = load_db()
    store = db.get("daily_food_journals", {}).get(user_id, {}) or {}
    merged = {}

    # v97.20: saved-day key is the source of truth for keyed daily_food_journals.
    # Older rows can carry a stale inner "date"; do not trust that for filtering/display.
    for k, v in store.items():
        row = dict(v or {})
        row["date"] = str(k)
        row["_journal_date_key"] = str(k)
        row["_filter_date_source"] = "daily_food_journals_key"
        merged[str(k)] = row

    # Include old day records in daily_logs.
    for x in db.get("daily_logs", {}).get(user_id, []) or []:
        if x.get("log_type") == "daily_food_journal_day" and x.get("date") and str(x.get("date")) not in merged:
            row = dict(x or {})
            row["date"] = str(x.get("date"))
            row["_journal_date_key"] = str(x.get("date"))
            row["_filter_date_source"] = "daily_logs_date"
            merged[str(x.get("date"))] = row

    # Include old row-based food_journal records grouped by date.
    legacy = _legacy_food_journal_days_for_user(db, user_id)
    for d, day in legacy.items():
        if d not in merged:
            row = dict(day or {})
            row["date"] = str(d)
            row["_journal_date_key"] = str(d)
            row["_filter_date_source"] = "legacy_grouped_date"
            merged[d] = row

    rows = list(merged.values())
    rows.sort(key=lambda r: (str(r.get("_journal_date_key", r.get("date", ""))), str(r.get("timestamp", ""))), reverse=True)
    return rows


def mark_member_message_read(member_id, message_id):
    """Mark one member message as read/archive it from the main screen."""
    db = load_db()
    changed = False
    for m in db.get("messages", []):
        if m.get("member_id") == member_id and m.get("id") == message_id:
            m["read"] = True
            m["archived"] = True
            m["read_ts"] = datetime.datetime.now().isoformat(timespec="seconds")
            changed = True
            break
    if changed:
        save_db(db)
    return changed

def get_member_unread_messages(member_id, limit=10):
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id and not m.get("read") and not m.get("archived")
    ]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def get_member_archived_messages(member_id, limit=50):
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id and (m.get("read") or m.get("archived"))
    ]
    rows.sort(key=lambda r: r.get("read_ts", r.get("ts", "")), reverse=True)
    return rows[:limit]


# --------------------------------------------------------------------
# v54: Final Nutritionist read/archive behavior
# --------------------------------------------------------------------
def _today_iso_for_archive():
    return datetime.date.today().isoformat()

def _message_effective_date(msg):
    """Return date string used for automatic nutritionist message archiving."""
    return str(msg.get("log_date") or msg.get("date") or (msg.get("ts", "")[:10] if msg.get("ts") else ""))

def auto_archive_expired_nutritionist_messages(member_id):
    """Archive nutritionist messages whose linked date has passed.

    This keeps old notes out of Member Home but retained in archive.
    """
    db = load_db()
    today = _today_iso_for_archive()
    changed = False
    for m in db.get("messages", []):
        if m.get("member_id") != member_id:
            continue
        role = str(m.get("sender_role", "")).lower()
        subject = str(m.get("subject", "")).lower()
        is_nutritionist = role in ["nutritionist", "admin"] or "nutritionist" in subject or "daily log supervision" in subject
        if not is_nutritionist:
            continue
        if m.get("read") or m.get("archived"):
            continue
        d = _message_effective_date(m)
        if d and d < today:
            m["archived"] = True
            m["auto_archived"] = True
            m["archive_reason"] = "date_passed"
            m["read_ts"] = datetime.datetime.now().isoformat(timespec="seconds")
            changed = True
    if changed:
        save_db(db)
    return changed

def mark_member_message_read(member_id, message_id):
    """Mark one member message as read/archive it from the main screen."""
    db = load_db()
    changed = False
    for m in db.get("messages", []):
        if m.get("member_id") == member_id and m.get("id") == message_id:
            m["read"] = True
            m["archived"] = True
            m["read_ts"] = datetime.datetime.now().isoformat(timespec="seconds")
            m["archive_reason"] = "member_read"
            changed = True
            break
    if changed:
        save_db(db)
    return changed

def get_member_unread_messages(member_id, limit=10):
    auto_archive_expired_nutritionist_messages(member_id)
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id
        and not m.get("read")
        and not m.get("archived")
    ]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def get_member_messages(member_id, limit=10):
    """Main-screen messages: unread/unarchived only."""
    return get_member_unread_messages(member_id, limit=limit)

def get_member_archived_messages(member_id, limit=50):
    auto_archive_expired_nutritionist_messages(member_id)
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id and (m.get("read") or m.get("archived"))
    ]
    rows.sort(key=lambda r: r.get("read_ts", r.get("ts", "")), reverse=True)
    return rows[:limit]


# --------------------------------------------------------------------
# v56: Daily Log Nutritionist Note member notification
# --------------------------------------------------------------------
def save_daily_log_supervision_note(member_id, note, actor_id="nutritionist", log_date=None):
    """Save nutritionist note, show it to member, and queue app/email notification.

    Member Home reads from db["messages"], so this function must always append
    an unread/unarchived member message in addition to the archive note row.
    """
    note = (note or "").strip()
    if not note:
        return None

    db = load_db()
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    note_id = str(uuid.uuid4())[:8]
    date_str = str(log_date or "")

    db.setdefault("daily_log_supervision_notes", {}).setdefault(member_id, [])
    item = {
        "id": note_id,
        "ts": ts,
        "member_id": member_id,
        "log_date": date_str,
        "note": note,
        "actor_id": actor_id or "nutritionist",
        "sender_role": "nutritionist",
        "read": False,
        "archived": False,
    }
    db["daily_log_supervision_notes"][member_id].append(item)

    date_text = f" for {date_str}" if date_str else ""
    message_id = str(uuid.uuid4())[:8]
    db.setdefault("messages", []).append({
        "id": message_id,
        "ts": ts,
        "member_id": member_id,
        "sender_role": "nutritionist",
        "actor_id": actor_id or "nutritionist",
        "subject": f"Nutritionist Note{date_text}",
        "message": note,
        "status": "queued",
        "email_required": True,
        "log_date": date_str,
        "read": False,
        "archived": False,
        "source": "daily_log_supervision_note",
        "note_id": note_id,
    })

    db.setdefault("notifications", []).append({
        "id": str(uuid.uuid4())[:8],
        "ts": ts,
        "kind": "nutritionist_note",
        "user_id": member_id,
        "member_id": member_id,
        "message": f"Nutritionist Note{date_text}: {note[:160]}",
        "status": "queued",
        "email_required": True,
        "created_by": actor_id or "nutritionist",
        "log_date": date_str,
        "source_message_id": message_id,
    })

    save_db(db)
    return item

def get_member_unread_messages(member_id, limit=10):
    """Return messages that must be visible on Member Home.

    v56 keeps today's/future nutritionist notes visible until the member reads/archives them.
    Past dated notes are auto-archived by auto_archive_expired_nutritionist_messages().
    """
    auto_archive_expired_nutritionist_messages(member_id)
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id
        and not m.get("read")
        and not m.get("archived")
    ]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def get_member_messages(member_id, limit=10):
    return get_member_unread_messages(member_id, limit=limit)


# --------------------------------------------------------------------
# v57: Daily Log note visibility + water day detail helpers
# --------------------------------------------------------------------
def get_daily_log_notes_by_date(member_id, log_date, limit=20):
    """Return nutritionist notes for one specific Daily Log date."""
    db = load_db()
    rows = list(db.get("daily_log_supervision_notes", {}).get(member_id, []))
    rows = [r for r in rows if str(r.get("log_date", "")) == str(log_date)]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def get_latest_daily_log_note_for_date(member_id, log_date):
    rows = get_daily_log_notes_by_date(member_id, log_date, limit=1)
    return rows[0] if rows else None

def mark_member_message_read(member_id, message_id):
    """Read/archive one member notification message."""
    db = load_db()
    changed = False
    for m in db.get("messages", []):
        if m.get("member_id") == member_id and m.get("id") == message_id:
            m["read"] = True
            m["archived"] = True
            m["read_ts"] = datetime.datetime.now().isoformat(timespec="seconds")
            m["archive_reason"] = "member_read"
            changed = True
            break
    if changed:
        save_db(db)
    return changed

def get_member_unread_messages(member_id, limit=10):
    """Unread nutritionist/member notifications remain visible until member reads them.

    We intentionally do NOT auto-hide unread messages when the date passes.
    """
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id
        and not m.get("read")
        and not m.get("archived")
    ]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:limit]

def get_member_messages(member_id, limit=10):
    return get_member_unread_messages(member_id, limit=limit)

def get_member_archived_messages(member_id, limit=50):
    db = load_db()
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id and (m.get("read") or m.get("archived"))
    ]
    rows.sort(key=lambda r: r.get("read_ts", r.get("ts", "")), reverse=True)
    return rows[:limit]

def save_daily_food_journal_day_details(user_id, log_date, physical_activity="", poop="", notes="", water_litres=""):
    """Save full-day details including water intake in litres."""
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    day = store.get(str(log_date), {
        "date": str(log_date),
        "meals": {},
        "log_type": "daily_food_journal_day",
    })
    day["physical_activity"] = physical_activity
    day["poop"] = poop
    day["notes"] = notes
    day["water_litres"] = water_litres
    day["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    day["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = day

    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [x for x in db["daily_logs"][user_id] if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))]
    legacy.append(day)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return day


# --------------------------------------------------------------------
# v57: Daily Log nutritionist note notification override
# --------------------------------------------------------------------
def save_daily_log_supervision_note(member_id, note, actor_id="nutritionist", log_date=None):
    note = (note or "").strip()
    if not note:
        return None

    db = load_db()
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    note_id = str(uuid.uuid4())[:8]
    date_str = str(log_date or "")

    db.setdefault("daily_log_supervision_notes", {}).setdefault(member_id, [])
    item = {
        "id": note_id,
        "ts": ts,
        "member_id": member_id,
        "log_date": date_str,
        "note": note,
        "actor_id": actor_id or "nutritionist",
        "sender_role": "nutritionist",
    }
    db["daily_log_supervision_notes"][member_id].append(item)

    date_text = f" for {date_str}" if date_str else ""
    message_id = str(uuid.uuid4())[:8]
    db.setdefault("messages", []).append({
        "id": message_id,
        "ts": ts,
        "member_id": member_id,
        "sender_role": "nutritionist",
        "actor_id": actor_id or "nutritionist",
        "subject": f"Nutritionist Note{date_text}",
        "message": note,
        "status": "queued",
        "email_required": True,
        "log_date": date_str,
        "read": False,
        "archived": False,
        "source": "daily_log_supervision_note",
        "note_id": note_id,
    })

    db.setdefault("notifications", []).append({
        "id": str(uuid.uuid4())[:8],
        "ts": ts,
        "kind": "nutritionist_note",
        "user_id": member_id,
        "member_id": member_id,
        "message": f"Nutritionist Note{date_text}: {note[:160]}",
        "status": "queued",
        "email_required": True,
        "created_by": actor_id or "nutritionist",
        "log_date": date_str,
        "source_message_id": message_id,
    })
    save_db(db)
    return item


# --------------------------------------------------------------------
# v59: Full-day details structured poop fields
# --------------------------------------------------------------------
def save_daily_food_journal_day_details(
    user_id,
    log_date,
    physical_activity="",
    poop="",
    notes="",
    water_litres="",
    poop_rounds="Select",
    poop_timings=None,
    feeling_after_poop="",
):
    """Save full-day details including water and structured poop fields.

    Backward compatible: old `poop` field is still stored as a readable summary.
    """
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    day = store.get(str(log_date), {
        "date": str(log_date),
        "meals": {},
        "log_type": "daily_food_journal_day",
    })

    poop_timings = poop_timings or []
    clean_timings = [str(x or "").strip() for x in poop_timings]

    # Build a readable legacy summary for existing table/report views.
    structured_summary = ""
    if poop_rounds and str(poop_rounds) != "Select":
        timing_text = ", ".join([x for x in clean_timings if x])
        structured_summary = f"{poop_rounds} round(s)"
        if timing_text:
            structured_summary += f" at {timing_text}"
        if feeling_after_poop:
            structured_summary += f" / {feeling_after_poop}"

    day["physical_activity"] = physical_activity
    day["poop"] = structured_summary or poop
    day["poop_rounds"] = poop_rounds
    day["poop_timings"] = clean_timings
    day["feeling_after_poop"] = feeling_after_poop
    day["notes"] = notes
    day["water_litres"] = water_litres
    day["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    day["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = day

    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [
        x for x in db["daily_logs"][user_id]
        if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))
    ]
    legacy.append(day)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return day


# --------------------------------------------------------------------
# v66: Nutritionist message dedupe / idempotent note notification
# --------------------------------------------------------------------
def _normalise_note_text_for_dedupe(text):
    return " ".join(str(text or "").strip().split()).lower()

def _nutritionist_message_dedupe_key(member_id, log_date, note):
    return f"{member_id}|{str(log_date or '')}|{_normalise_note_text_for_dedupe(note)}"

def _dedupe_member_messages_in_memory(db):
    """Remove duplicate unread/read message records created by prior patch cycles.

    Keeps the earliest message record for each member/date/text/source combination.
    """
    seen = set()
    cleaned = []
    changed = False
    for m in db.get("messages", []) or []:
        source = str(m.get("source", ""))
        sender = str(m.get("sender_role", "")).lower()
        subject = str(m.get("subject", "")).lower()
        is_nutritionist_note = (
            source == "daily_log_supervision_note"
            or sender == "nutritionist"
            or "nutritionist note" in subject
            or "daily log supervision" in subject
        )
        if is_nutritionist_note:
            key = _nutritionist_message_dedupe_key(
                m.get("member_id", ""),
                m.get("log_date", ""),
                m.get("message", ""),
            )
            if key in seen:
                changed = True
                continue
            seen.add(key)
        cleaned.append(m)
    if changed:
        db["messages"] = cleaned
    return changed

def save_daily_log_supervision_note(member_id, note, actor_id="nutritionist", log_date=None):
    """Save nutritionist note and create exactly one member-visible message.

    v66 is idempotent for same member + same date + same note text.
    """
    note = (note or "").strip()
    if not note:
        return None

    db = load_db()
    _dedupe_member_messages_in_memory(db)

    ts = datetime.datetime.now().isoformat(timespec="seconds")
    date_str = str(log_date or "")
    dedupe_key = _nutritionist_message_dedupe_key(member_id, date_str, note)

    # Avoid duplicate note rows too.
    db.setdefault("daily_log_supervision_notes", {}).setdefault(member_id, [])
    existing_note = None
    for n in db["daily_log_supervision_notes"][member_id]:
        if _nutritionist_message_dedupe_key(member_id, n.get("log_date", ""), n.get("note", "")) == dedupe_key:
            existing_note = n
            break

    if existing_note:
        note_id = existing_note.get("id") or str(uuid.uuid4())[:8]
        existing_note["id"] = note_id
        item = existing_note
    else:
        note_id = str(uuid.uuid4())[:8]
        item = {
            "id": note_id,
            "ts": ts,
            "member_id": member_id,
            "log_date": date_str,
            "note": note,
            "actor_id": actor_id or "nutritionist",
            "sender_role": "nutritionist",
        }
        db["daily_log_supervision_notes"][member_id].append(item)

    # Create exactly one member-visible message for this note.
    existing_message = None
    for m in db.get("messages", []) or []:
        if _nutritionist_message_dedupe_key(member_id, m.get("log_date", ""), m.get("message", "")) == dedupe_key:
            existing_message = m
            break

    date_text = f" for {date_str}" if date_str else ""
    if existing_message:
        existing_message["sender_role"] = "nutritionist"
        existing_message["subject"] = f"Nutritionist Note{date_text}"
        existing_message["source"] = "daily_log_supervision_note"
        existing_message["note_id"] = note_id
        # If it was already read, do not reset it to unread.
        existing_message.setdefault("read", False)
        existing_message.setdefault("archived", False)
        message_id = existing_message.get("id", str(uuid.uuid4())[:8])
        existing_message["id"] = message_id
    else:
        message_id = str(uuid.uuid4())[:8]
        db.setdefault("messages", []).append({
            "id": message_id,
            "ts": ts,
            "member_id": member_id,
            "sender_role": "nutritionist",
            "actor_id": actor_id or "nutritionist",
            "subject": f"Nutritionist Note{date_text}",
            "message": note,
            "status": "queued",
            "email_required": True,
            "log_date": date_str,
            "read": False,
            "archived": False,
            "source": "daily_log_supervision_note",
            "note_id": note_id,
        })

    # Queue notification once per source message id.
    db.setdefault("notifications", [])
    if not any(n.get("source_message_id") == message_id for n in db["notifications"]):
        db["notifications"].append({
            "id": str(uuid.uuid4())[:8],
            "ts": ts,
            "kind": "nutritionist_note",
            "user_id": member_id,
            "member_id": member_id,
            "message": f"Nutritionist Note{date_text}: {note[:160]}",
            "status": "queued",
            "email_required": True,
            "created_by": actor_id or "nutritionist",
            "log_date": date_str,
            "source_message_id": message_id,
        })

    save_db(db)
    return item

def get_member_unread_messages(member_id, limit=10):
    """Unread/unarchived messages, deduped before display."""
    db = load_db()
    changed = _dedupe_member_messages_in_memory(db)
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id
        and not m.get("read")
        and not m.get("archived")
    ]
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    if changed:
        save_db(db)
    return rows[:limit]

def get_member_messages(member_id, limit=10):
    return get_member_unread_messages(member_id, limit=limit)

def get_member_archived_messages(member_id, limit=50):
    db = load_db()
    changed = _dedupe_member_messages_in_memory(db)
    rows = [
        m for m in db.get("messages", [])
        if m.get("member_id") == member_id and (m.get("read") or m.get("archived"))
    ]
    rows.sort(key=lambda r: r.get("read_ts", r.get("ts", "")), reverse=True)
    if changed:
        save_db(db)
    return rows[:limit]


# --------------------------------------------------------------------
# v97: Full-day details with Other Fluids support
# --------------------------------------------------------------------
def save_daily_food_journal_day_details(
    user_id,
    log_date,
    physical_activity="",
    poop="",
    notes="",
    water_litres="",
    poop_rounds="Select",
    poop_timings=None,
    feeling_after_poop="",
    other_fluids=None,
):
    """Save full-day details including water, structured poop and other fluids."""
    db = load_db()
    store = _daily_food_journal_store(db).setdefault(user_id, {})
    day = store.get(str(log_date), {
        "date": str(log_date),
        "meals": {},
        "log_type": "daily_food_journal_day",
    })

    poop_timings = poop_timings or []
    clean_timings = [str(x or "").strip() for x in poop_timings]

    cleaned_other_fluids = []
    for item in (other_fluids or []):
        if not isinstance(item, dict):
            continue
        fluid_type = str(item.get("type", "") or "").strip()
        time_text = str(item.get("time", "") or "").strip()
        quantity = str(item.get("quantity", "") or "").strip()
        note = str(item.get("notes", "") or "").strip()
        if fluid_type or time_text or quantity or note:
            cleaned_other_fluids.append({
                "type": fluid_type,
                "time": time_text,
                "quantity": quantity,
                "notes": note,
            })

    structured_summary = ""
    if poop_rounds and str(poop_rounds) != "Select":
        timing_text = ", ".join([x for x in clean_timings if x])
        structured_summary = f"{poop_rounds} round(s)"
        if timing_text:
            structured_summary += f" at {timing_text}"
        if feeling_after_poop:
            structured_summary += f" / {feeling_after_poop}"

    day["physical_activity"] = physical_activity
    day["poop"] = structured_summary or poop
    day["poop_rounds"] = poop_rounds
    day["poop_timings"] = clean_timings
    day["feeling_after_poop"] = feeling_after_poop
    day["notes"] = notes
    day["water_litres"] = water_litres
    day["other_fluids"] = cleaned_other_fluids
    day["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    day["log_type"] = "daily_food_journal_day"
    store[str(log_date)] = day

    db.setdefault("daily_logs", {}).setdefault(user_id, [])
    legacy = [
        x for x in db["daily_logs"][user_id]
        if not (x.get("log_type") == "daily_food_journal_day" and x.get("date") == str(log_date))
    ]
    legacy.append(day)
    db["daily_logs"][user_id] = legacy[-120:]
    save_db(db)
    return day


# --------------------------------------------------------------------
# v100.0: Recipe / Exercise member feedback helpers
# --------------------------------------------------------------------

def _ensure_resource_feedback_store(db):
    db.setdefault("resource_feedback", {})
    db["resource_feedback"].setdefault("recipes", {})
    db["resource_feedback"].setdefault("exercises", {})
    db.setdefault("resource_feedback_log", [])
    return db

def save_resource_feedback(member_id, resource_type, item_id, title="", status="", rating="", notes="", actor="member"):
    db = _ensure_resource_feedback_store(load_db())
    resource_type = "recipes" if resource_type == "recipes" else "exercises"
    member_id = str(member_id or "").strip()
    item_id = str(item_id or "").strip()
    if not member_id or not item_id:
        return False
    record = {
        "member_id": member_id,
        "resource_type": resource_type,
        "item_id": item_id,
        "title": str(title or "").strip(),
        "status": str(status or "").strip(),
        "rating": str(rating or "").strip(),
        "notes": str(notes or "").strip(),
        "updated_at": _now_iso(),
        "actor": actor or "member",
    }
    db["resource_feedback"].setdefault(resource_type, {}).setdefault(member_id, {})[item_id] = record
    db.setdefault("resource_feedback_log", []).append(record.copy())
    db.setdefault("notifications", []).append({
        "ts": record["updated_at"],
        "kind": f"{resource_type}_feedback_submitted",
        "user_id": member_id,
        "message": f"{record.get('title') or resource_type.title()} feedback submitted.",
        "status": "queued",
    })
    save_db(db)
    return True

def get_resource_feedback(member_id, resource_type, item_id):
    db = _ensure_resource_feedback_store(load_db())
    resource_type = "recipes" if resource_type == "recipes" else "exercises"
    return db.get("resource_feedback", {}).get(resource_type, {}).get(str(member_id), {}).get(str(item_id), {})

def list_resource_feedback(member_id=None, resource_type=None):
    db = _ensure_resource_feedback_store(load_db())
    rows = []
    types = ["recipes", "exercises"] if resource_type not in ["recipes", "exercises"] else [resource_type]
    for rt in types:
        by_member = db.get("resource_feedback", {}).get(rt, {})
        for mid, items in by_member.items():
            if member_id and str(mid) != str(member_id):
                continue
            for _item_id, rec in items.items():
                row = dict(rec)
                row.setdefault("resource_type", rt)
                row.setdefault("member_id", mid)
                rows.append(row)
    rows.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return rows

def resource_feedback_counts(member_id, resource_type):
    rows = list_resource_feedback(member_id=member_id, resource_type=resource_type)
    total = len(rows)
    completed = sum(1 for r in rows if str(r.get("status", "")).lower() in ["tried", "completed", "done", "followed", "liked"])
    return {"total": total, "completed": completed, "rows": rows}


# --------------------------------------------------------------------
# v101.0: Scheduling helpers
# --------------------------------------------------------------------

def _ensure_schedule_store(db):
    db.setdefault("schedules", [])
    db.setdefault("messages", [])
    db.setdefault("notifications", [])
    return db

def _schedule_member_lookup_v101(db, member_id):
    for u in db.get("users", []):
        if u.get("id") == member_id:
            return u
    return {}

def create_member_schedule(
    member_id,
    title,
    schedule_type,
    schedule_date,
    start_time,
    end_time="",
    mode="",
    location_or_link="",
    notes="",
    actor_id="admin",
):
    """Create a member schedule item and queue member app/email notification.

    Stored in db['schedules']; no schema migration required.
    """
    db = _ensure_schedule_store(load_db())
    member = _schedule_member_lookup_v101(db, member_id)
    schedule_id = str(uuid.uuid4())[:8]
    created_at = _now_iso()
    title = str(title or "").strip() or str(schedule_type or "Scheduled session").strip() or "Scheduled session"
    schedule = {
        "id": schedule_id,
        "member_id": member_id,
        "member_name": member.get("name", ""),
        "member_email": member.get("email", ""),
        "title": title,
        "schedule_type": str(schedule_type or "").strip(),
        "schedule_date": str(schedule_date or "").strip(),
        "start_time": str(start_time or "").strip(),
        "end_time": str(end_time or "").strip(),
        "mode": str(mode or "").strip(),
        "location_or_link": str(location_or_link or "").strip(),
        "notes": str(notes or "").strip(),
        "status": "scheduled",
        "created_at": created_at,
        "created_by": actor_id or "admin",
        "acknowledged_at": "",
        "completed_at": "",
        "cancelled_at": "",
    }
    db["schedules"].append(schedule)

    time_window = schedule["start_time"]
    if schedule["end_time"]:
        time_window = f"{schedule['start_time']} - {schedule['end_time']}"
    subject = f"Schedule: {title}"
    message = (
        f"{title} is scheduled for {schedule['schedule_date']} at {time_window}."
        f" Mode: {schedule['mode'] or 'Not specified'}."
    )
    if schedule["location_or_link"]:
        message += f" Link/location: {schedule['location_or_link']}."
    if schedule["notes"]:
        message += f" Note: {schedule['notes']}"

    msg = {
        "id": str(uuid.uuid4())[:8],
        "ts": created_at,
        "member_id": member_id,
        "sender_role": "admin",
        "actor_id": actor_id or "admin",
        "subject": subject,
        "message": message,
        "status": "queued",
        "email_required": True,
        "source": "schedule",
        "schedule_id": schedule_id,
    }
    db["messages"].append(msg)
    db["notifications"].append({
        "ts": created_at,
        "kind": "schedule_created",
        "user_id": member_id,
        "message": f"{subject}: {message[:160]}",
        "status": "queued",
        "email_required": True,
        "email_to": member.get("email", ""),
        "created_by": actor_id or "admin",
        "schedule_id": schedule_id,
    })
    save_db(db)
    return schedule

def list_member_schedules(member_id=None, include_cancelled=False, limit=50):
    db = _ensure_schedule_store(load_db())
    rows = []
    for row in db.get("schedules", []):
        if member_id and row.get("member_id") != member_id:
            continue
        if not include_cancelled and row.get("status") == "cancelled":
            continue
        rows.append(dict(row))

    def _sort_key(r):
        return (str(r.get("schedule_date", "")), str(r.get("start_time", "")), str(r.get("created_at", "")))

    rows.sort(key=_sort_key)
    if limit:
        return rows[:limit]
    return rows

def list_upcoming_member_schedules(member_id, limit=3):
    rows = [
        r for r in list_member_schedules(member_id=member_id, include_cancelled=False, limit=0)
        if r.get("status") in ["scheduled", "acknowledged"]
    ]
    return rows[:limit]

def update_member_schedule_status(schedule_id, status, actor_id="admin"):
    db = _ensure_schedule_store(load_db())
    allowed = {"scheduled", "acknowledged", "completed", "cancelled"}
    status = status if status in allowed else "scheduled"
    now = _now_iso()
    updated = None
    for row in db.get("schedules", []):
        if row.get("id") == schedule_id:
            row["status"] = status
            row["updated_at"] = now
            row["updated_by"] = actor_id or "admin"
            if status == "completed":
                row["completed_at"] = now
            if status == "cancelled":
                row["cancelled_at"] = now
            if status == "acknowledged":
                row["acknowledged_at"] = now
            updated = dict(row)
            break
    if updated:
        save_db(db)
    return updated

def acknowledge_member_schedule(schedule_id, member_id):
    db = _ensure_schedule_store(load_db())
    now = _now_iso()
    updated = None
    for row in db.get("schedules", []):
        if row.get("id") == schedule_id and row.get("member_id") == member_id:
            if row.get("status") == "scheduled":
                row["status"] = "acknowledged"
                row["acknowledged_at"] = now
                row["updated_at"] = now
                row["updated_by"] = member_id
            updated = dict(row)
            break
    if updated:
        save_db(db)
    return updated

def schedule_status_label_v101(status):
    mapping = {
        "scheduled": "Scheduled",
        "acknowledged": "Acknowledged",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }
    return mapping.get(status, str(status or "Scheduled").replace("_", " ").title())


# --------------------------------------------------------------------
# v101.2: Member reschedule request helpers
# --------------------------------------------------------------------

def _hm_v1012_parse_schedule_dt(schedule):
    import datetime as _dt
    date_text = str(schedule.get("schedule_date", "") or "").strip()
    time_text = str(schedule.get("start_time", "") or "").strip()
    if not date_text or not time_text:
        return None
    for fmt in ("%Y-%m-%d %I:%M %p", "%Y/%m/%d %I:%M %p", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return _dt.datetime.strptime(f"{date_text} {time_text}", fmt)
        except Exception:
            pass
    return None

def _hm_v1012_is_within_24_hours(schedule):
    import datetime as _dt
    scheduled_dt = _hm_v1012_parse_schedule_dt(schedule)
    if not scheduled_dt:
        return False
    now = _dt.datetime.now()
    delta = scheduled_dt - now
    return _dt.timedelta(0) <= delta <= _dt.timedelta(hours=24)

def request_member_schedule_reschedule(
    schedule_id,
    member_id,
    requested_date,
    requested_start_time,
    requested_end_time="",
    reason="",
):
    """Member requests a reschedule. Admin approval is required.

    24-hour rule:
    - >24 hours before meeting: prior session not consumed.
    - within 24 hours: prior session may be counted/consumed and rescheduled session counts separately.
    """
    import uuid as _uuid
    db = _ensure_schedule_store(load_db())
    db.setdefault("reschedule_requests", [])
    now = _now_iso()
    schedule = None
    for row in db.get("schedules", []):
        if row.get("id") == schedule_id and row.get("member_id") == member_id:
            schedule = row
            break
    if not schedule:
        return None

    # Do not create another pending request for the same schedule.
    for existing in db.get("reschedule_requests", []):
        if existing.get("schedule_id") == schedule_id and existing.get("status") == "pending":
            return dict(existing)

    within_24 = _hm_v1012_is_within_24_hours(schedule)
    request_id = str(_uuid.uuid4())[:8]
    request_row = {
        "id": request_id,
        "schedule_id": schedule_id,
        "member_id": member_id,
        "member_name": schedule.get("member_name", ""),
        "member_email": schedule.get("member_email", ""),
        "current_title": schedule.get("title", ""),
        "current_date": schedule.get("schedule_date", ""),
        "current_start_time": schedule.get("start_time", ""),
        "current_end_time": schedule.get("end_time", ""),
        "requested_date": str(requested_date or "").strip(),
        "requested_start_time": str(requested_start_time or "").strip(),
        "requested_end_time": str(requested_end_time or "").strip(),
        "reason": str(reason or "").strip(),
        "within_24_hours": bool(within_24),
        "prior_session_counted_if_approved": bool(within_24),
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    db["reschedule_requests"].append(request_row)

    schedule["reschedule_request_status"] = "pending"
    schedule["latest_reschedule_request_id"] = request_id
    schedule["updated_at"] = now
    schedule["updated_by"] = member_id

    admin_message = (
        f"Reschedule requested for {schedule.get('title','Scheduled session')} "
        f"from {schedule.get('schedule_date','')} {schedule.get('start_time','')} "
        f"to {request_row['requested_date']} {request_row['requested_start_time']}."
    )
    if within_24:
        admin_message += " This request is within 24 hours; prior session may be counted as consumed."

    db.setdefault("notifications", []).append({
        "ts": now,
        "kind": "reschedule_requested",
        "user_id": "admin",
        "member_id": member_id,
        "message": admin_message,
        "status": "queued",
        "email_required": False,
        "schedule_id": schedule_id,
        "reschedule_request_id": request_id,
    })
    save_db(db)
    return request_row

def list_reschedule_requests(member_id=None, status=None, limit=100):
    db = _ensure_schedule_store(load_db())
    db.setdefault("reschedule_requests", [])
    rows = []
    for row in db.get("reschedule_requests", []):
        if member_id and row.get("member_id") != member_id:
            continue
        if status and row.get("status") != status:
            continue
        rows.append(dict(row))
    rows.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)
    return rows[:limit] if limit else rows

def get_reschedule_request(request_id):
    db = _ensure_schedule_store(load_db())
    for row in db.get("reschedule_requests", []):
        if row.get("id") == request_id:
            return dict(row)
    return None

def decide_reschedule_request(request_id, decision, admin_note="", actor_id="admin"):
    """Approve or reject a member reschedule request.

    Approval:
    - marks request approved
    - marks original schedule rescheduled
    - creates a new schedule row with requested date/time
    - if within 24 hours, original schedule is marked counted/consumed
    - queues member notification
    """
    import uuid as _uuid
    db = _ensure_schedule_store(load_db())
    db.setdefault("reschedule_requests", [])
    now = _now_iso()
    decision = "approved" if decision == "approved" else "rejected"
    req = None
    for row in db.get("reschedule_requests", []):
        if row.get("id") == request_id:
            req = row
            break
    if not req:
        return None

    schedule = None
    for row in db.get("schedules", []):
        if row.get("id") == req.get("schedule_id"):
            schedule = row
            break

    req["status"] = decision
    req["admin_note"] = str(admin_note or "").strip()
    req["updated_at"] = now
    req["decided_at"] = now
    req["decided_by"] = actor_id or "admin"

    new_schedule = None
    if decision == "approved" and schedule:
        schedule["status"] = "rescheduled"
        schedule["reschedule_request_status"] = "approved"
        schedule["rescheduled_at"] = now
        schedule["updated_at"] = now
        schedule["updated_by"] = actor_id or "admin"
        schedule["session_counted"] = bool(req.get("within_24_hours"))

        title = schedule.get("title", "Scheduled session")
        new_id = str(_uuid.uuid4())[:8]
        new_schedule = dict(schedule)
        new_schedule.update({
            "id": new_id,
            "schedule_date": req.get("requested_date", ""),
            "start_time": req.get("requested_start_time", ""),
            "end_time": req.get("requested_end_time", ""),
            "status": "scheduled",
            "created_at": now,
            "created_by": actor_id or "admin",
            "updated_at": now,
            "updated_by": actor_id or "admin",
            "acknowledged_at": "",
            "completed_at": "",
            "cancelled_at": "",
            "rescheduled_from_schedule_id": schedule.get("id"),
            "reschedule_request_id": request_id,
            "reschedule_request_status": "",
            "latest_reschedule_request_id": "",
            "session_counted": False,
        })
        db["schedules"].append(new_schedule)
        req["new_schedule_id"] = new_id

        member_message = (
            f"Your reschedule request for {title} has been approved. "
            f"New schedule: {new_schedule.get('schedule_date','')} at {new_schedule.get('start_time','')}."
        )
        if req.get("within_24_hours"):
            member_message += " Note: This request was within 24 hours; the previous session may be counted as consumed."
    else:
        if schedule:
            schedule["reschedule_request_status"] = "rejected"
            schedule["updated_at"] = now
            schedule["updated_by"] = actor_id or "admin"
        member_message = (
            f"Your reschedule request for {req.get('current_title','scheduled session')} was not approved."
        )
        if admin_note:
            member_message += f" Note: {admin_note}"

    db.setdefault("messages", []).append({
        "id": str(_uuid.uuid4())[:8],
        "ts": now,
        "member_id": req.get("member_id"),
        "sender_role": "admin",
        "actor_id": actor_id or "admin",
        "subject": "Reschedule request update",
        "message": member_message,
        "status": "queued",
        "email_required": True,
        "source": "reschedule",
        "schedule_id": req.get("schedule_id"),
        "reschedule_request_id": request_id,
    })
    db.setdefault("notifications", []).append({
        "ts": now,
        "kind": f"reschedule_{decision}",
        "user_id": req.get("member_id"),
        "member_id": req.get("member_id"),
        "message": member_message,
        "status": "queued",
        "email_required": True,
        "email_to": req.get("member_email", ""),
        "created_by": actor_id or "admin",
        "schedule_id": req.get("schedule_id"),
        "reschedule_request_id": request_id,
    })

    save_db(db)
    return {"request": dict(req), "new_schedule": dict(new_schedule) if new_schedule else None}

def reschedule_policy_text_v1012(within_24):
    if within_24:
        return (
            "This request is within 24 hours of the scheduled session. "
            "If approved, the current session may still be counted as consumed and the rescheduled session may count separately."
        )
    return (
        "This request is outside the 24-hour window. "
        "If approved, the prior session will not be counted as consumed."
    )


# --------------------------------------------------------------------
# v101.4: Existing member NSP system-score recalculation helpers
# --------------------------------------------------------------------

def _hm_v1014_answer_count(answers):
    return sum(1 for v in (answers or {}).values() if v not in [None, "", "Select"])

def _hm_v1014_top_systems(rows):
    sorted_rows = sorted(rows or [], key=lambda r: int(r.get("Score", 0) or 0), reverse=True)
    if not sorted_rows:
        return []
    selected = sorted_rows[:3]
    if len(sorted_rows) > 3:
        third_score = int(selected[-1].get("Score", 0) or 0)
        for row in sorted_rows[3:]:
            if int(row.get("Score", 0) or 0) == third_score:
                selected.append(row)
            else:
                break
    return [
        {"system": row.get("System", ""), "score": int(row.get("Score", 0) or 0)}
        for row in selected
    ]

def _hm_v1014_recalc_rows(nsp1, nsp2):
    from components.systems_rating import calculate_systems_rating
    rows = calculate_systems_rating(nsp1 or {}, nsp2 or {})
    return [
        {"No.": row.get("No."), "System": row.get("System"), "Score": int(row.get("Score", 0) or 0)}
        for row in rows
    ]

def recalculate_member_nsp_system_scores(member_id, actor_id="admin"):
    """Recalculate stored NSP system-score snapshots for one existing member.

    This does not alter raw NSP answers. It stores recalculated snapshots based on
    the current Excel-derived systems_rating_map.json.
    """
    db = load_db()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    users = {u.get("id"): u for u in db.get("users", [])}
    member = users.get(member_id, {})

    db.setdefault("nsp_system_scores", {})
    db.setdefault("nsp_system_scores_by_instance", {})
    db.setdefault("nsp_recalculation_audit", [])

    legacy_nsp1 = db.get("nsp1_responses", {}).get(member_id, {}) or {}
    legacy_nsp2 = db.get("nsp2_responses", {}).get(member_id, {}) or {}
    legacy_count = _hm_v1014_answer_count(legacy_nsp1) + _hm_v1014_answer_count(legacy_nsp2)

    member_snapshot = None
    if legacy_count:
        rows = _hm_v1014_recalc_rows(legacy_nsp1, legacy_nsp2)
        member_snapshot = {
            "member_id": member_id,
            "member_name": member.get("name", ""),
            "member_email": member.get("email", ""),
            "source": "legacy_member_responses",
            "calculated_at": now,
            "calculated_by": actor_id or "admin",
            "nsp1_answer_count": _hm_v1014_answer_count(legacy_nsp1),
            "nsp2_answer_count": _hm_v1014_answer_count(legacy_nsp2),
            "systems": rows,
            "top_systems": _hm_v1014_top_systems(rows),
            "mapping_version": "v101.3_excel_non_grey_mapping",
        }
        db["nsp_system_scores"][member_id] = member_snapshot

    instance_snapshots = []
    for inst in db.get("assessment_instances", {}).get(member_id, []) or []:
        instance_id = inst.get("instance_id", "")
        inst_resp = db.get("assessment_instance_responses", {}).get(instance_id, {}) or {}
        inst_nsp1 = inst_resp.get("nsp1", {}) or {}
        inst_nsp2 = inst_resp.get("nsp2", {}) or {}
        inst_count = _hm_v1014_answer_count(inst_nsp1) + _hm_v1014_answer_count(inst_nsp2)
        if not inst_count:
            continue

        rows = _hm_v1014_recalc_rows(inst_nsp1, inst_nsp2)
        snapshot = {
            "member_id": member_id,
            "member_name": member.get("name", ""),
            "member_email": member.get("email", ""),
            "instance_id": instance_id,
            "instance_number": inst.get("instance_number"),
            "instance_type": inst.get("instance_type", ""),
            "source": "assessment_instance_responses",
            "calculated_at": now,
            "calculated_by": actor_id or "admin",
            "nsp1_answer_count": _hm_v1014_answer_count(inst_nsp1),
            "nsp2_answer_count": _hm_v1014_answer_count(inst_nsp2),
            "systems": rows,
            "top_systems": _hm_v1014_top_systems(rows),
            "mapping_version": "v101.3_excel_non_grey_mapping",
        }
        db["nsp_system_scores_by_instance"][instance_id] = snapshot
        inst["nsp_system_scores_calculated_at"] = now
        inst["nsp_top_systems_snapshot"] = snapshot["top_systems"]
        instance_snapshots.append(snapshot)

        # If legacy snapshot was absent, use latest instance snapshot as member-level reference.
        if not member_snapshot:
            member_snapshot = dict(snapshot)
            member_snapshot["source"] = "latest_assessment_instance_responses"
            db["nsp_system_scores"][member_id] = member_snapshot

    audit_entry = {
        "ts": now,
        "actor_id": actor_id or "admin",
        "member_id": member_id,
        "member_name": member.get("name", ""),
        "member_email": member.get("email", ""),
        "legacy_answer_count": legacy_count,
        "instance_snapshots_recalculated": len(instance_snapshots),
        "member_snapshot_created": bool(member_snapshot),
        "top_systems": (member_snapshot or {}).get("top_systems", []),
        "mapping_version": "v101.3_excel_non_grey_mapping",
    }
    db["nsp_recalculation_audit"].append(audit_entry)
    save_db(db)
    return audit_entry

def recalculate_all_nsp_system_scores(actor_id="admin"):
    """Recalculate stored NSP system-score snapshots for all existing members."""
    db = load_db()
    members = [u for u in db.get("users", []) if u.get("role") == "member"]
    results = []
    for member in members:
        results.append(recalculate_member_nsp_system_scores(member.get("id"), actor_id=actor_id or "admin"))
    return results

def list_nsp_recalculation_status():
    db = load_db()
    scores = db.get("nsp_system_scores", {}) or {}
    by_instance = db.get("nsp_system_scores_by_instance", {}) or {}
    rows = []
    for u in db.get("users", []):
        if u.get("role") != "member":
            continue
        member_id = u.get("id")
        legacy_nsp1 = db.get("nsp1_responses", {}).get(member_id, {}) or {}
        legacy_nsp2 = db.get("nsp2_responses", {}).get(member_id, {}) or {}
        instances = db.get("assessment_instances", {}).get(member_id, []) or []
        inst_recalc_count = sum(1 for inst in instances if inst.get("instance_id") in by_instance)
        snapshot = scores.get(member_id, {}) or {}
        top_system = ""
        if snapshot.get("top_systems"):
            first = snapshot["top_systems"][0]
            top_system = f"{first.get('system','')} ({first.get('score',0)})"
        rows.append({
            "member_id": member_id,
            "member_name": u.get("name", ""),
            "email": u.get("email", ""),
            "legacy_nsp_answers": _hm_v1014_answer_count(legacy_nsp1) + _hm_v1014_answer_count(legacy_nsp2),
            "instances": len(instances),
            "instances_recalculated": inst_recalc_count,
            "member_snapshot": "Yes" if snapshot else "No",
            "last_calculated_at": snapshot.get("calculated_at", ""),
            "top_system": top_system,
        })
    return rows

def get_nsp_system_score_snapshot(member_id, instance_id=None):
    db = load_db()
    if instance_id:
        return db.get("nsp_system_scores_by_instance", {}).get(instance_id, {})
    return db.get("nsp_system_scores", {}).get(member_id, {})



# --------------------------------------------------------------------
# v102.3A: Supplements persistence helpers
# --------------------------------------------------------------------


def _strip_html_to_text_v102_4(value):
    """Convert accidental persisted HTML/markup into safe plain text.

    A few interim builds allowed rendered chip/card HTML to leak into
    supplement and recommendation text fields. This helper is intentionally
    defensive: it repeatedly decodes escaped HTML, removes tags, and normalises
    whitespace so older saved values never render as raw <div>/<span> text.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    text = raw
    for _ in range(5):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    # Common leaked presentation wrappers should become separators, not visible text.
    text = re.sub(r"<\s*br\s*/?>", ", ", text, flags=re.I)
    text = re.sub(r"</\s*(div|p|span|li|td|th)\s*>", ", ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u00a0", " ").replace("&nbsp;", " ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return text


def _split_instruction_marker_v102_4(value, *, before_marker=False):
    text = _strip_html_to_text_v102_4(value)
    match = re.search(r"instructions\s*:", text, flags=re.I)
    if not match:
        return text
    if before_marker:
        return text[:match.start()].strip(" ,")
    return text[match.end():].strip(" ,")

def _supp_now_iso_v102_3a():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _supp_clean_text_v102_3a(value):
    return _strip_html_to_text_v102_4(value)


def _supp_clean_date_v102_3a(value):
    if value in (None, ""):
        return ""
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def _supp_parse_date_v102_3a(value):
    raw = _supp_clean_text_v102_3a(value)
    if not raw:
        return None
    try:
        return datetime.date.fromisoformat(raw[:10])
    except Exception:
        return None


def _supp_find_member_v102_3a(db, member_id):
    member_id = str(member_id or "").strip()
    for user in db.get("users", []):
        if str(user.get("id")) == member_id:
            return user
    return {}


def _ensure_supplement_store_v102_3a(db):
    db.setdefault("member_supplements", [])
    db.setdefault("supplement_audit_logs", [])
    db.setdefault("notifications", [])
    if not isinstance(db.get("member_supplements"), list):
        db["member_supplements"] = []
    if not isinstance(db.get("supplement_audit_logs"), list):
        db["supplement_audit_logs"] = []
    return db


def _normalise_supplement_record_v102_3a(record):
    record = dict(record or {})
    record.setdefault("id", str(uuid.uuid4())[:8])
    record.setdefault("member_id", "")
    record.setdefault("member_email", "")
    record.setdefault("member_name", "")
    record.setdefault("supplement_name", record.get("name", ""))
    record.setdefault("dosage", "")
    record.setdefault("frequency", "")
    record.setdefault("timing", "")
    record.setdefault("instructions", "")
    record.setdefault("start_date", "")
    record.setdefault("end_date", "")
    record.setdefault("stop_date", "")
    record.setdefault("status", "Active")
    record.setdefault("admin_notes", "")
    record.setdefault("stop_reason", "")
    record.setdefault("created_at", "")
    record.setdefault("updated_at", "")
    record.setdefault("created_by", "")
    record.setdefault("updated_by", "")
    record.setdefault("stopped_at", "")
    record.setdefault("stopped_by", "")
    for key in ["member_id", "member_email", "member_name", "supplement_name", "dosage", "frequency", "timing", "instructions", "start_date", "end_date", "stop_date", "status", "admin_notes", "stop_reason", "created_at", "updated_at", "created_by", "updated_by", "stopped_at", "stopped_by"]:
        record[key] = _supp_clean_text_v102_3a(record.get(key))
    # Repair any older persisted chip/card HTML that carried instructions inside timing/text fields.
    timing_with_marker = _strip_html_to_text_v102_4(record.get("timing"))
    instruction_with_marker = _strip_html_to_text_v102_4(record.get("instructions"))
    timing_instruction = _split_instruction_marker_v102_4(timing_with_marker, before_marker=False) if re.search(r"instructions\s*:", timing_with_marker, flags=re.I) else ""
    record["timing"] = _split_instruction_marker_v102_4(timing_with_marker, before_marker=True)
    record["instructions"] = _split_instruction_marker_v102_4(instruction_with_marker, before_marker=False)
    if not record.get("instructions") and timing_instruction:
        record["instructions"] = timing_instruction
    if record["status"].lower() not in ["active", "stopped"]:
        record["status"] = "Active"
    record["status"] = "Stopped" if record["status"].lower() == "stopped" else "Active"
    return record


def _write_supplement_audit_v102_3a(db, action, record, actor_id="", changes=None):
    db.setdefault("supplement_audit_logs", [])
    db["supplement_audit_logs"].append({
        "ts": _supp_now_iso_v102_3a(),
        "action": action,
        "supplement_id": record.get("id", ""),
        "member_id": record.get("member_id", ""),
        "member_email": record.get("member_email", ""),
        "supplement_name": record.get("supplement_name", ""),
        "actor_id": actor_id or "admin",
        "changes": changes or {},
    })
    db["supplement_audit_logs"] = db["supplement_audit_logs"][-500:]


def _auto_stop_expired_supplements_v102_3a(db, actor_id="system"):
    """Deactivate active supplements whose predefined end date has arrived.

    End Date is stored separately from Stop Date. When the End Date is today
    or in the past, the normal stop fields are completed automatically and
    the stop reason is fixed as "Predefined Timelines".
    """
    _ensure_supplement_store_v102_3a(db)
    today = datetime.date.today()
    now = _supp_now_iso_v102_3a()
    changed = False
    for idx, raw in enumerate(list(db.get("member_supplements", []))):
        row = _normalise_supplement_record_v102_3a(raw)
        before = dict(row)
        end_dt = _supp_parse_date_v102_3a(row.get("end_date"))
        if row.get("status") == "Active" and end_dt and end_dt <= today:
            row["status"] = "Stopped"
            row["stop_date"] = end_dt.isoformat()
            row["stop_reason"] = "Predefined Timelines"
            row["stopped_at"] = now
            row["stopped_by"] = actor_id or "system"
            row["updated_at"] = now
            row["updated_by"] = actor_id or "system"
            db["member_supplements"][idx] = _normalise_supplement_record_v102_3a(row)
            _write_supplement_audit_v102_3a(
                db,
                "auto_stopped",
                row,
                actor_id=actor_id or "system",
                changes={
                    "status": {"from": before.get("status", ""), "to": "Stopped"},
                    "stop_date": row.get("stop_date", ""),
                    "stop_reason": "Predefined Timelines",
                },
            )
            db.setdefault("notifications", []).append({
                "ts": now,
                "kind": "supplement_regimen_updated",
                "user_id": row.get("member_id", ""),
                "message": "Your nutritionist has updated your supplement regimen.",
                "status": "queued",
                "email_required": False,
                "created_by": actor_id or "system",
            })
            changed = True
        elif row != raw:
            db["member_supplements"][idx] = row
            changed = True
    return changed


def list_member_supplements(member_id=None, status=None, include_inactive_member=True):
    """Return persisted supplement records.

    member_id filters to one member. status can be Active or Stopped.
    Member pages should call list_active_member_supplements(member_id) for publishing.
    """
    db = _ensure_supplement_store_v102_3a(load_db())
    rows = []
    status_filter = _supp_clean_text_v102_3a(status).lower()
    member_id_filter = _supp_clean_text_v102_3a(member_id)
    active_member_ids = None
    if not include_inactive_member:
        active_member_ids = {str(u.get("id")) for u in db.get("users", []) if u.get("role") == "member" and u.get("is_active", True)}
    changed = _auto_stop_expired_supplements_v102_3a(db)
    for raw in db.get("member_supplements", []):
        row = _normalise_supplement_record_v102_3a(raw)
        if member_id_filter and str(row.get("member_id")) != member_id_filter:
            continue
        if status_filter and str(row.get("status", "")).lower() != status_filter:
            continue
        if active_member_ids is not None and str(row.get("member_id")) not in active_member_ids:
            continue
        rows.append(row)
    if changed:
        save_db(db)
    rows.sort(key=lambda r: (0 if r.get("status") == "Active" else 1, str(r.get("updated_at") or r.get("created_at") or "")), reverse=True)
    return rows


def list_active_member_supplements(member_id):
    """Member-publishing helper: only this member's active assigned regimen."""
    return list_member_supplements(member_id=member_id, status="Active")


def add_member_supplement(member_id, data, actor_id="admin"):
    db = _ensure_supplement_store_v102_3a(load_db())
    member_id = _supp_clean_text_v102_3a(member_id)
    if not member_id:
        raise ValueError("Member is required.")
    member = _supp_find_member_v102_3a(db, member_id)
    if not member:
        raise ValueError("Selected member was not found.")
    name = _supp_clean_text_v102_3a((data or {}).get("supplement_name") or (data or {}).get("name"))
    if not name:
        raise ValueError("Supplement name is required.")
    now = _supp_now_iso_v102_3a()
    record = _normalise_supplement_record_v102_3a({
        "id": str(uuid.uuid4())[:8],
        "member_id": member_id,
        "member_email": member.get("email", ""),
        "member_name": member.get("name", ""),
        "supplement_name": name,
        "dosage": (data or {}).get("dosage", ""),
        "frequency": (data or {}).get("frequency", ""),
        "timing": (data or {}).get("timing", ""),
        "instructions": (data or {}).get("instructions", ""),
        "start_date": _supp_clean_date_v102_3a((data or {}).get("start_date", "")),
        "end_date": _supp_clean_date_v102_3a((data or {}).get("end_date", "")),
        "stop_date": "",
        "status": "Active",
        "admin_notes": (data or {}).get("admin_notes", ""),
        "stop_reason": "",
        "created_at": now,
        "updated_at": now,
        "created_by": actor_id or "admin",
        "updated_by": actor_id or "admin",
    })
    start_dt = _supp_parse_date_v102_3a(record.get("start_date"))
    end_dt = _supp_parse_date_v102_3a(record.get("end_date"))
    if start_dt and end_dt and end_dt < start_dt:
        raise ValueError("End Date cannot be earlier than Start Date.")
    db["member_supplements"].append(record)
    _write_supplement_audit_v102_3a(db, "created", record, actor_id=actor_id)
    db.setdefault("notifications", []).append({
        "ts": now,
        "kind": "supplement_regimen_updated",
        "user_id": member_id,
        "message": "Your nutritionist has updated your supplement regimen.",
        "status": "queued",
        "email_required": False,
        "created_by": actor_id or "admin",
    })
    save_db(db)
    return record


def update_member_supplement(supplement_id, updates, actor_id="admin"):
    db = _ensure_supplement_store_v102_3a(load_db())
    supplement_id = _supp_clean_text_v102_3a(supplement_id)
    allowed = {"supplement_name", "dosage", "frequency", "timing", "instructions", "start_date", "end_date", "admin_notes"}
    for idx, raw in enumerate(db.get("member_supplements", [])):
        row = _normalise_supplement_record_v102_3a(raw)
        if str(row.get("id")) != supplement_id:
            continue
        if row.get("status") != "Active":
            raise ValueError("Stopped supplements cannot be edited. Add a new active supplement instead.")
        before = dict(row)
        for key in allowed:
            if key in (updates or {}):
                value = (updates or {}).get(key)
                row[key] = _supp_clean_date_v102_3a(value) if key in {"start_date", "end_date"} else _supp_clean_text_v102_3a(value)
        if not row.get("supplement_name"):
            raise ValueError("Supplement name is required.")
        start_dt = _supp_parse_date_v102_3a(row.get("start_date"))
        end_dt = _supp_parse_date_v102_3a(row.get("end_date"))
        if start_dt and end_dt and end_dt < start_dt:
            raise ValueError("End Date cannot be earlier than Start Date.")
        row["updated_at"] = _supp_now_iso_v102_3a()
        row["updated_by"] = actor_id or "admin"
        db["member_supplements"][idx] = _normalise_supplement_record_v102_3a(row)
        changes = {k: {"from": before.get(k, ""), "to": row.get(k, "")} for k in allowed if before.get(k, "") != row.get(k, "")}
        _write_supplement_audit_v102_3a(db, "updated", row, actor_id=actor_id, changes=changes)
        db.setdefault("notifications", []).append({
            "ts": row["updated_at"],
            "kind": "supplement_regimen_updated",
            "user_id": row.get("member_id", ""),
            "message": "Your nutritionist has updated your supplement regimen.",
            "status": "queued",
            "email_required": False,
            "created_by": actor_id or "admin",
        })
        save_db(db)
        return db["member_supplements"][idx]
    raise ValueError("Supplement record was not found.")


def stop_member_supplement(supplement_id, stop_date=None, stop_reason="", actor_id="admin"):
    db = _ensure_supplement_store_v102_3a(load_db())
    supplement_id = _supp_clean_text_v102_3a(supplement_id)
    for idx, raw in enumerate(db.get("member_supplements", [])):
        row = _normalise_supplement_record_v102_3a(raw)
        if str(row.get("id")) != supplement_id:
            continue
        before = dict(row)
        now = _supp_now_iso_v102_3a()
        row["status"] = "Stopped"
        row["stop_date"] = _supp_clean_date_v102_3a(stop_date) or datetime.date.today().isoformat()
        row["stop_reason"] = _supp_clean_text_v102_3a(stop_reason)
        row["stopped_at"] = now
        row["stopped_by"] = actor_id or "admin"
        row["updated_at"] = now
        row["updated_by"] = actor_id or "admin"
        db["member_supplements"][idx] = _normalise_supplement_record_v102_3a(row)
        _write_supplement_audit_v102_3a(db, "stopped", row, actor_id=actor_id, changes={"status": {"from": before.get("status", ""), "to": "Stopped"}, "stop_date": row.get("stop_date", "")})
        db.setdefault("notifications", []).append({
            "ts": now,
            "kind": "supplement_regimen_updated",
            "user_id": row.get("member_id", ""),
            "message": "Your nutritionist has updated your supplement regimen.",
            "status": "queued",
            "email_required": False,
            "created_by": actor_id or "admin",
        })
        save_db(db)
        return db["member_supplements"][idx]
    raise ValueError("Supplement record was not found.")


def supplement_regimen_counts(member_id):
    rows = list_member_supplements(member_id=member_id)
    return {
        "active": len([r for r in rows if r.get("status") == "Active"]),
        "stopped": len([r for r in rows if r.get("status") == "Stopped"]),
        "total": len(rows),
    }


# --------------------------------------------------------------------
# v102.4: Recommendations Share + Today's Journey helpers
# --------------------------------------------------------------------

def _rec_now_iso_v102_4():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _rec_clean_text_v102_4(value):
    return _strip_html_to_text_v102_4(value)


def _rec_date_iso_v102_4(value):
    if value in (None, ""):
        return ""
    try:
        return value.isoformat()
    except Exception:
        return str(value)[:10]


def _rec_parse_date_v102_4(value):
    raw = _rec_clean_text_v102_4(value)
    if not raw:
        return None
    try:
        return datetime.date.fromisoformat(raw[:10])
    except Exception:
        return None


def _rec_find_member_v102_4(db, member_id):
    member_id = _rec_clean_text_v102_4(member_id)
    for user in db.get("users", []):
        if str(user.get("id")) == member_id:
            return user
    return {}


def _ensure_recommendations_store_v102_4(db):
    db.setdefault("recommendation_shares", {})
    db.setdefault("recommendation_share_audit", [])
    db.setdefault("resource_assignments", {})
    db["resource_assignments"].setdefault("recipes", {})
    db["resource_assignments"].setdefault("exercises", {})
    if not isinstance(db.get("recommendation_shares"), dict):
        db["recommendation_shares"] = {}
    if not isinstance(db.get("recommendation_share_audit"), list):
        db["recommendation_share_audit"] = []
    return db


def _rec_days_for_window_v102_4(start_date):
    start_dt = _rec_parse_date_v102_4(start_date) or datetime.date.today()
    return [(start_dt + datetime.timedelta(days=i)).isoformat() for i in range(7)]


def _rec_normalise_meal_plan_v102_4(plan, start_date):
    days = _rec_days_for_window_v102_4(start_date)
    slots = ["Breakfast", "Lunch", "Snacks", "Dinner", "Bedtime"]
    existing = {}
    for item in plan or []:
        if not isinstance(item, dict):
            continue
        key = (_rec_date_iso_v102_4(item.get("date")), _rec_clean_text_v102_4(item.get("meal_slot")) or _rec_clean_text_v102_4(item.get("slot")))
        existing[key] = item
    rows = []
    for i, day in enumerate(days, start=1):
        for slot in slots:
            item = existing.get((day, slot), {})
            rows.append({
                "day_number": i,
                "date": day,
                "meal_slot": slot,
                "recipe_id": _rec_clean_text_v102_4(item.get("recipe_id")),
                "notes": _rec_clean_text_v102_4(item.get("notes")),
            })
    return rows


def _rec_normalise_exercise_plan_v102_4(plan, start_date):
    days = _rec_days_for_window_v102_4(start_date)
    existing = {}
    for item in plan or []:
        if not isinstance(item, dict):
            continue
        existing[_rec_date_iso_v102_4(item.get("date"))] = item
    rows = []
    for i, day in enumerate(days, start=1):
        item = existing.get(day, {})
        rows.append({
            "day_number": i,
            "date": day,
            "exercise_id": _rec_clean_text_v102_4(item.get("exercise_id")),
            "timing": _rec_clean_text_v102_4(item.get("timing")),
            "notes": _rec_clean_text_v102_4(item.get("notes")),
        })
    return rows


def _rec_normalise_supplement_detail_v102_4(detail):
    detail = dict(detail or {})
    raw_id = detail.get("supplement_id") or detail.get("source_supplement_id") or detail.get("id")
    start_raw = _rec_clean_text_v102_4(detail.get("start_date"))
    end_raw = _rec_clean_text_v102_4(detail.get("end_date"))
    return {
        "supplement_id": _rec_clean_text_v102_4(raw_id),
        "supplement_name": _rec_clean_text_v102_4(detail.get("supplement_name") or detail.get("name")),
        "dosage": _rec_clean_text_v102_4(detail.get("dosage")),
        "frequency": _rec_clean_text_v102_4(detail.get("frequency")),
        "timing": _split_instruction_marker_v102_4(detail.get("timing"), before_marker=True),
        "start_date": start_raw[:10] if start_raw else "",
        "end_date": end_raw[:10] if end_raw else "",
        "instructions": _split_instruction_marker_v102_4(detail.get("instructions") or detail.get("member_instructions"), before_marker=False),
        "admin_notes": _rec_clean_text_v102_4(detail.get("admin_notes")),
    }


def _rec_normalise_supplement_plan_v102_4(plan, start_date):
    days = _rec_days_for_window_v102_4(start_date)
    existing = {}
    for item in plan or []:
        if not isinstance(item, dict):
            continue
        existing[_rec_date_iso_v102_4(item.get("date"))] = item
    rows = []
    for i, day in enumerate(days, start=1):
        item = existing.get(day, {})
        supplement_ids = item.get("supplement_ids", [])
        if isinstance(supplement_ids, str):
            supplement_ids = [x.strip() for x in supplement_ids.replace("|", ",").split(",") if x.strip()]
        supplement_ids = [str(x).strip() for x in (supplement_ids or []) if str(x).strip()]

        details = []
        for raw_detail in item.get("supplement_details", []) or []:
            if not isinstance(raw_detail, dict):
                continue
            clean_detail = _rec_normalise_supplement_detail_v102_4(raw_detail)
            sid = clean_detail.get("supplement_id")
            if sid and sid not in supplement_ids:
                supplement_ids.append(sid)
            if sid or clean_detail.get("supplement_name"):
                details.append(clean_detail)

        # Keep the detail order aligned with the selected IDs so member views remain predictable.
        detail_by_id = {str(d.get("supplement_id")): d for d in details if d.get("supplement_id")}
        ordered_details = []
        used_ids = set()
        for sid in supplement_ids:
            detail = detail_by_id.get(str(sid))
            if detail:
                ordered_details.append(detail)
                used_ids.add(str(sid))
        for detail in details:
            sid = str(detail.get("supplement_id") or "")
            if sid not in used_ids:
                ordered_details.append(detail)

        rows.append({
            "day_number": i,
            "date": day,
            "supplement_ids": supplement_ids,
            "supplement_details": ordered_details,
            "notes": _rec_clean_text_v102_4(item.get("notes")),
        })
    return rows


def _normalise_recommendation_share_v102_4(share, member=None):
    share = dict(share or {})
    start_dt = _rec_parse_date_v102_4(share.get("start_date")) or datetime.date.today()
    end_dt = start_dt + datetime.timedelta(days=6)
    share.setdefault("id", str(uuid.uuid4())[:8])
    share["member_id"] = _rec_clean_text_v102_4(share.get("member_id") or (member or {}).get("id", ""))
    share["member_email"] = _rec_clean_text_v102_4(share.get("member_email") or (member or {}).get("email", ""))
    share["member_name"] = _rec_clean_text_v102_4(share.get("member_name") or (member or {}).get("name", ""))
    share["start_date"] = start_dt.isoformat()
    share["end_date"] = end_dt.isoformat()
    share["status"] = _rec_clean_text_v102_4(share.get("status") or "Draft")
    if share["status"] not in ["Draft", "Published", "Archived"]:
        share["status"] = "Draft"
    share["nutritionist_report"] = _rec_clean_text_v102_4(share.get("nutritionist_report"))
    share["meal_plan"] = _rec_normalise_meal_plan_v102_4(share.get("meal_plan", []), share["start_date"])
    share["exercise_plan"] = _rec_normalise_exercise_plan_v102_4(share.get("exercise_plan", []), share["start_date"])
    share["supplement_plan"] = _rec_normalise_supplement_plan_v102_4(share.get("supplement_plan", []), share["start_date"])
    share.setdefault("created_at", "")
    share.setdefault("updated_at", "")
    share.setdefault("published_at", "")
    share.setdefault("created_by", "")
    share.setdefault("updated_by", "")
    share.setdefault("published_by", "")
    share["created_at"] = _rec_clean_text_v102_4(share.get("created_at"))
    share["updated_at"] = _rec_clean_text_v102_4(share.get("updated_at"))
    share["published_at"] = _rec_clean_text_v102_4(share.get("published_at"))
    share["created_by"] = _rec_clean_text_v102_4(share.get("created_by"))
    share["updated_by"] = _rec_clean_text_v102_4(share.get("updated_by"))
    share["published_by"] = _rec_clean_text_v102_4(share.get("published_by"))
    return share


def _recommendation_windows_overlap_v102_4(a, b):
    a_start = _rec_parse_date_v102_4(a.get("start_date"))
    a_end = _rec_parse_date_v102_4(a.get("end_date"))
    b_start = _rec_parse_date_v102_4(b.get("start_date"))
    b_end = _rec_parse_date_v102_4(b.get("end_date"))
    if not all([a_start, a_end, b_start, b_end]):
        return False
    return a_start <= b_end and b_start <= a_end


def _materialize_recommendation_resource_assignments_v102_4(db, member_id, share):
    meal_ids = []
    for item in share.get("meal_plan", []) or []:
        rid = _rec_clean_text_v102_4(item.get("recipe_id"))
        if rid and rid not in meal_ids:
            meal_ids.append(rid)
    exercise_ids = []
    for item in share.get("exercise_plan", []) or []:
        eid = _rec_clean_text_v102_4(item.get("exercise_id"))
        if eid and eid not in exercise_ids:
            exercise_ids.append(eid)
    db.setdefault("resource_assignments", {}).setdefault("recipes", {})[member_id] = meal_ids
    db.setdefault("resource_assignments", {}).setdefault("exercises", {})[member_id] = exercise_ids


def save_recommendation_share(member_id, share_data, actor_id="admin", publish=False):
    """Create/update the 7-day Recommendations Share for a member.

    This is the source of truth for Today's Journey. On publish, recipe and
    exercise IDs are also materialized into the existing member repositories so
    the upgraded Recipe/Exercise pages remain connected to the same plan.
    """
    db = _ensure_recommendations_store_v102_4(load_db())
    member_id = _rec_clean_text_v102_4(member_id)
    member = _rec_find_member_v102_4(db, member_id)
    if not member:
        raise ValueError("Selected member was not found.")
    now = _rec_now_iso_v102_4()
    share = _normalise_recommendation_share_v102_4(share_data, member=member)
    share["member_id"] = member_id
    share["member_email"] = member.get("email", "")
    share["member_name"] = member.get("name", "")
    existing_list = db.setdefault("recommendation_shares", {}).setdefault(member_id, [])
    existing_index = None
    for idx, raw in enumerate(existing_list):
        if str(raw.get("id")) == str(share.get("id")):
            existing_index = idx
            break
    if existing_index is not None:
        before = _normalise_recommendation_share_v102_4(existing_list[existing_index], member=member)
        share["created_at"] = before.get("created_at") or now
        share["created_by"] = before.get("created_by") or actor_id or "admin"
    else:
        share["created_at"] = now
        share["created_by"] = actor_id or "admin"
    share["updated_at"] = now
    share["updated_by"] = actor_id or "admin"
    if publish:
        share["status"] = "Published"
        share["published_at"] = now
        share["published_by"] = actor_id or "admin"
        for idx, raw in enumerate(existing_list):
            other = _normalise_recommendation_share_v102_4(raw, member=member)
            if str(other.get("id")) != str(share.get("id")) and other.get("status") == "Published" and _recommendation_windows_overlap_v102_4(other, share):
                other["status"] = "Archived"
                other["updated_at"] = now
                other["updated_by"] = actor_id or "admin"
                existing_list[idx] = other
        _materialize_recommendation_resource_assignments_v102_4(db, member_id, share)
        db.setdefault("notifications", []).append({
            "ts": now,
            "kind": "recommendations_shared",
            "user_id": member_id,
            "message": "Your nutritionist has shared your recommendations and today's journey.",
            "status": "queued",
            "email_required": True,
            "created_by": actor_id or "admin",
        })
    elif share.get("status") != "Published":
        share["status"] = "Draft"
    if existing_index is not None:
        existing_list[existing_index] = share
    else:
        existing_list.append(share)
    db["recommendation_shares"][member_id] = existing_list[-20:]
    db.setdefault("recommendation_share_audit", []).append({
        "ts": now,
        "action": "published" if publish else "saved_draft",
        "share_id": share.get("id"),
        "member_id": member_id,
        "actor_id": actor_id or "admin",
        "start_date": share.get("start_date"),
        "end_date": share.get("end_date"),
    })
    db["recommendation_share_audit"] = db["recommendation_share_audit"][-500:]
    save_db(db)
    return share


def list_recommendation_shares(member_id, status=None):
    db = _ensure_recommendations_store_v102_4(load_db())
    member_id = _rec_clean_text_v102_4(member_id)
    member = _rec_find_member_v102_4(db, member_id)
    rows = [_normalise_recommendation_share_v102_4(x, member=member) for x in db.get("recommendation_shares", {}).get(member_id, [])]
    if status:
        rows = [r for r in rows if str(r.get("status")) == str(status)]
    rows.sort(key=lambda r: (str(r.get("updated_at") or r.get("created_at") or ""), str(r.get("start_date") or "")), reverse=True)
    return rows


def get_latest_recommendation_share(member_id, include_draft=True):
    rows = list_recommendation_shares(member_id)
    if include_draft:
        return rows[0] if rows else None
    published = [r for r in rows if r.get("status") == "Published"]
    return published[0] if published else None


def get_published_recommendation_for_date(member_id, target_date=None, fallback_latest=False):
    target = _rec_parse_date_v102_4(target_date) or datetime.date.today()
    published = list_recommendation_shares(member_id, status="Published")
    in_window = []
    for share in published:
        start_dt = _rec_parse_date_v102_4(share.get("start_date"))
        end_dt = _rec_parse_date_v102_4(share.get("end_date"))
        if start_dt and end_dt and start_dt <= target <= end_dt:
            in_window.append(share)
    if in_window:
        return in_window[0]
    return published[0] if (fallback_latest and published) else None
