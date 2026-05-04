import datetime
from components.db import load_db, save_db, normalize_workflow

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
        return sorted(open_instances, key=lambda x: x.get("instance_number", 0), reverse=True)[0]
    return sorted(instances, key=lambda x: x.get("instance_number", 0), reverse=True)[0]

def get_instance_response(instance_id, page):
    db = load_db()
    return db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {}).get(page, {})

def save_instance_page_response(user_id, page, data):
    db = load_db()
    db.setdefault("assessment_instances", {})
    db.setdefault("assessment_instance_responses", {})
    if not db["assessment_instances"].get(user_id):
        save_db(db)
        ensure_assessment_instances(user_id)
        db = load_db()

    current = get_current_assessment_instance(user_id)
    instance_id = current["instance_id"]
    db.setdefault("assessment_instance_responses", {}).setdefault(instance_id, {}).setdefault("consent", {})
    db["assessment_instance_responses"][instance_id][page] = data

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

    open_request = [i for i in instances if not i.get("submitted_for_review") and i.get("instance_type") == "Reassessment" and i.get("status") in ["pending", "in_progress"]]
    if open_request:
        return open_request[-1], False

    next_num = max([int(i.get("instance_number", 0)) for i in instances] + [0]) + 1
    instance_id = f"{member_id}_inst_{next_num}"
    pages = [p for p in requested_pages if p in ["nsp1", "nsp2"]] or ["nsp1", "nsp2"]

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
    db = load_db()
    ensure_assessment_instances(user_id)
    db = load_db()
    current = get_current_assessment_instance(user_id)
    instance_id = current["instance_id"]
    was_submitted = bool(current.get("submitted_for_review"))

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