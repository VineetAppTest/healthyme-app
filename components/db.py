
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
    base={"laf_completed":False,"nsp1_completed":False,"nsp2_completed":False,"submitted_for_review":False,"admin_completed":False,"final_report_ready":False,"workflow_status":"not_started"}
    base.update(wf or {})
    base["workflow_status"]="finalized" if base["final_report_ready"] else ("admin_completed" if base["admin_completed"] else ("submitted" if base["submitted_for_review"] else ("in_progress" if base["laf_completed"] or base["nsp1_completed"] or base["nsp2_completed"] else "not_started")))
    return base
def get_workflow(user_id): return normalize_workflow(load_db()["workflow"].get(user_id,{}))
def update_workflow(user_id, **kwargs):
    db=load_db(); wf=db["workflow"].setdefault(user_id,{}); wf.update(kwargs); db["workflow"][user_id]=normalize_workflow(wf); save_db(db)
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
    wf = db["workflow"].setdefault(user_id, {})
    wf["body_mind_unlocked"] = bool(unlocked)
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
