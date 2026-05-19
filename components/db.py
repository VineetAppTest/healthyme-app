import datetime
import uuid

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
def save_admin_assessment(user_id,data): db=load_db(); db["admin_assessments"][user_id]=data; save_db(db)
def get_admin_assessment(user_id): return load_db().get("admin_assessments",{}).get(user_id,{})
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
# v26: Finalize admin assessment safely
# --------------------------------------------------------------------
def finalize_admin_assessment(user_id, assessment_data, activation_selected=False):
    """Save admin assessment, mark final report ready, and sync workflow + instance status."""
    db = load_db()
    db.setdefault("admin_assessments", {})[user_id] = assessment_data
    wf_before = normalize_workflow(db.setdefault("workflow", {}).setdefault(user_id, {}))
    already_finalized = bool(wf_before.get("admin_completed")) or bool(wf_before.get("final_report_ready"))
    save_db(db)

    final_wf = sync_member_finalization_state(
        user_id,
        body_mind_unlock=True if activation_selected or bool(wf_before.get("body_mind_activation_requested")) else None,
    )

    return {
        "already_finalized": already_finalized,
        "body_mind_unlocked": bool(final_wf.get("body_mind_unlocked")),
        "body_mind_activation_requested": bool(final_wf.get("body_mind_activation_requested")),
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
    merged = {str(k): v for k, v in store.items()}

    # Include old day records in daily_logs.
    for x in db.get("daily_logs", {}).get(user_id, []) or []:
        if x.get("log_type") == "daily_food_journal_day" and x.get("date") and str(x.get("date")) not in merged:
            merged[str(x.get("date"))] = x

    # Include old row-based food_journal records grouped by date.
    legacy = _legacy_food_journal_days_for_user(db, user_id)
    for d, day in legacy.items():
        if d not in merged:
            merged[d] = day

    rows = list(merged.values())
    rows.sort(key=lambda r: (r.get("date", ""), r.get("timestamp", "")), reverse=True)
    return rows


# --------------------------------------------------------------------
# v48: Nutritionist message archive/read support
# --------------------------------------------------------------------
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
