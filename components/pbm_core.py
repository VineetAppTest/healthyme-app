from __future__ import annotations

import copy
import datetime as dt
import html
import json
import re
import uuid
from typing import Any, Dict, List, Tuple

import streamlit as st

from components.profile_builder_source_contract import source_snapshot_for_label
from components.recommendation_profile_store import load_member_options, load_profile

APP_BUILD_VERSION = "v100.42"
APP_BUILD_LABEL = "Existing Profile Editing"
SECTIONS = ["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow", "Publish Control", "Active Profile Preview"]
NAV_LABELS = {"Profile Setup": "Setup", "Meal Structure": "Meals", "Exercise Regime": "Exercise", "Supplement Regime": "Supplements", "Preview & End-to-End Flow": "Preview", "Publish Control": "Publish", "Active Profile Preview": "Active"}
MEAL_SLOTS = ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]
EXERCISE_TIME_OF_DAY = ["Morning", "Afternoon", "Evening", "Night", "As advised"]
SUPPLEMENT_TIMELINE = ["Before Breakfast", "After Breakfast", "Before Lunch", "After Lunch", "Before Dinner", "After Dinner", "Before Bed"]
SELECT_MEMBER = "Select member"
SELECT_DRAFT = "-- Select saved profile --"
SELECT_PROFILE = "-- Select editable profile --"
SELECT_RECIPE = "-- Select recipe --"
SELECT_EXERCISE = "-- Select exercise --"
SELECT_SUPPLEMENT = "-- Select supplement --"
SELECT_AGE = "-- Select age band --"
SELECT_DIET = "-- Select diet type --"
PROFILE_DEFAULTS: Dict[str, Any] = {
    "id": "", "profile_name": "", "status": "draft", "region": "",
    "age_band": SELECT_AGE, "diet_type": SELECT_DIET, "health_concerns": [],
    "profile_note": "", "change_note": "",
    "cycle_rule": "Weekly cyclical until replaced or stopped",
    "assigned_member_id": "", "assigned_member_label": SELECT_MEMBER,
    "start_date": dt.date.today(), "clone_source_profile_id": "",
    "clone_source_label": "New profile",
}
SOURCE_FIELDS = {
    "meal": [("meal_type", "Meal Type", "text"), ("diet_type", "Diet Type", "text"), ("prep_time", "Prep Time", "text"), ("calories", "Calories", "text"), ("ingredients", "Ingredients", "area"), ("steps", "Steps", "area"), ("image_reference", "Image Reference", "text")],
    "exercise": [("category", "Category", "text"), ("difficulty", "Difficulty", "text"), ("duration_or_reps", "Duration/Reps", "text"), ("equipment", "Equipment", "text"), ("instructions", "Source Instructions", "area"), ("benefits", "Benefits", "area"), ("image_reference", "Image Reference", "text")],
    "supplement": [("timing", "Source Timing", "text"), ("instructions", "Source Instructions", "area"), ("admin_notes", "Admin Notes", "area")],
}


def clean(value: object, default: str = "") -> str:
    return default if value is None else str(value).strip()


def safe(value: object) -> str:
    return html.escape(clean(value))


def safe_key(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", clean(value)).strip("_") or "blank"


def as_dict(value: object) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def clean_date(value: object) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(clean(value)[:10])
    except Exception:
        return dt.date.today()


def parse_dosage_frequency(value: object) -> Tuple[int, str]:
    raw = clean(value)
    match = re.match(r"^Frequency:\s*(\d+)\s*;\s*Dosage:\s*(.*)$", raw)
    return (int(match.group(1) or 0), clean(match.group(2))) if match else (0, raw)


def encode_dosage_frequency(frequency: int, dosage: str) -> str:
    return "" if not frequency and not clean(dosage) else f"Frequency: {int(frequency or 0)}; Dosage: {clean(dosage)}"


def parse_timeline(value: object) -> List[str]:
    if isinstance(value, list):
        return [item for item in value if item in SUPPLEMENT_TIMELINE]
    return [part.strip() for part in clean(value).split(",") if part.strip() in SUPPLEMENT_TIMELINE]


def with_placeholder(values: List[str], placeholder: str) -> List[str]:
    cleaned = [clean(v) for v in values or [] if clean(v) and clean(v) != placeholder and not clean(v).startswith("-- Select")]
    return [placeholder] + list(dict.fromkeys(cleaned))


def source_snapshot(kind: str, label: str) -> Dict[str, Any]:
    if not label or label.startswith("-- Select"):
        return {}
    return dict(source_snapshot_for_label("recipe" if kind == "meal" else kind, label) or {})


def image_reference(snapshot: Dict[str, Any]) -> str:
    image = as_dict(snapshot.get("image"))
    values = []
    for field in ("image_url", "image_bucket", "image_path"):
        value = clean(image.get(field) or snapshot.get(field))
        if value:
            values.append(value)
    return " | ".join(values) or "No image reference"


def frequency_from_source(value: object) -> int:
    raw = clean(value).lower()
    for word, number in {"once": 1, "one": 1, "daily": 1, "twice": 2, "two": 2, "thrice": 3, "three": 3}.items():
        if word in raw:
            return number
    match = re.search(r"\d+", raw)
    return max(0, min(7, int(match.group(0)))) if match else 0


def timeline_from_source(value: object) -> List[str]:
    direct = parse_timeline(value)
    if direct:
        return direct
    raw = clean(value).lower()
    output: List[str] = []
    for tokens, option in [(("breakfast", "morning"), "After Breakfast"), (("lunch", "afternoon"), "After Lunch"), (("dinner", "evening"), "After Dinner"), (("bed", "night", "sleep"), "Before Bed")]:
        if any(token in raw for token in tokens) and option not in output:
            output.append(option)
    return output


def new_row(kind: str, day: int, slot: str) -> Dict[str, Any]:
    return {"ui_id": uuid.uuid4().hex, "item_type": kind, "day_number": day, "slot_name": slot, "item_order": 1, "reference_label": "", "portion": "", "instruction": "", "scheduled_time": "", "intensity": "", "dosage_frequency": "", "frequency": 0, "timeline": [], "dosage": "", "source_admin_overrides": {}}


def normalise_item(row: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(row or {})
    item["ui_id"] = clean(item.get("id")) or uuid.uuid4().hex
    item["item_type"] = clean(item.get("item_type"))
    item["day_number"] = int(item.get("day_number") or 1)
    item["slot_name"] = clean(item.get("slot_name"))
    item["item_order"] = int(item.get("item_order") or 1)
    snapshot = as_dict(item.get("source_snapshot"))
    item["source_admin_overrides"] = as_dict(snapshot.get("admin_source_overrides"))
    if item["item_type"] == "supplement":
        item["frequency"], item["dosage"] = parse_dosage_frequency(item.get("dosage_frequency"))
        item["timeline"] = parse_timeline(item.get("scheduled_time"))
    return item


def profile_from_db(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": clean(profile.get("id")), "profile_name": clean(profile.get("profile_name")), "status": clean(profile.get("status"), "draft").lower(), "region": clean(profile.get("region")), "age_band": clean(profile.get("age_band")) or SELECT_AGE, "diet_type": clean(profile.get("diet_type")) or SELECT_DIET, "health_concerns": list(profile.get("health_concerns") or []), "profile_note": clean(profile.get("profile_note")), "change_note": clean(profile.get("change_note")), "cycle_rule": clean(profile.get("cycle_rule"), "Weekly cyclical until replaced or stopped"), "assigned_member_id": clean(profile.get("assigned_member_id")), "assigned_member_label": clean(profile.get("assigned_member_label")) or SELECT_MEMBER, "start_date": clean_date(profile.get("start_date")), "clone_source_profile_id": clean(profile.get("clone_source_profile_id")), "clone_source_label": clean(profile.get("clone_source_label")) or "New profile"}


def clear_widgets(*prefixes: str) -> None:
    for key in list(st.session_state.keys()):
        if any(str(key).startswith(prefix) for prefix in prefixes):
            st.session_state.pop(key, None)


def ensure_state() -> None:
    st.session_state.setdefault("pbm_section", "Profile Setup")
    st.session_state.setdefault("pbm_profile", copy.deepcopy(PROFILE_DEFAULTS))
    st.session_state.setdefault("pbm_items", [])
    st.session_state.setdefault("pbm_loaded_profile_id", "")
    st.session_state.setdefault("pbm_loaded_member_id", "")
    st.session_state.setdefault("pbm_epoch", 0)


def bump_epoch() -> None:
    st.session_state["pbm_epoch"] = int(st.session_state.get("pbm_epoch", 0)) + 1


def reset_profile() -> None:
    st.session_state["pbm_profile"] = copy.deepcopy(PROFILE_DEFAULTS)
    st.session_state["pbm_items"] = []
    st.session_state["pbm_loaded_profile_id"] = ""
    st.session_state["pbm_loaded_member_id"] = ""
    bump_epoch()


def apply_loaded(profile: Dict[str, Any], items: List[Dict[str, Any]], shell_only: bool = False) -> None:
    st.session_state["pbm_profile"] = profile_from_db(profile)
    st.session_state["pbm_items"] = [] if shell_only else [normalise_item(row) for row in items]
    st.session_state["pbm_loaded_profile_id"] = clean(profile.get("id"))
    st.session_state["pbm_loaded_member_id"] = clean(profile.get("assigned_member_id"))
    bump_epoch()


def load_selected(profile_id: str, shell_only: bool = False) -> Tuple[bool, str]:
    ok, profile, items, message = load_profile(profile_id)
    if ok:
        apply_loaded(profile, items, shell_only)
    return ok, message


def profile_payload() -> Dict[str, Any]:
    profile = st.session_state["pbm_profile"]
    return {**profile, "start_date": profile.get("start_date").isoformat() if isinstance(profile.get("start_date"), dt.date) else clean(profile.get("start_date")), "created_by_user_id": st.session_state.get("user_id", ""), "created_by_email": st.session_state.get("user_email", "")}


def member_maps() -> Tuple[List[str], Dict[str, str], Dict[str, str], str]:
    options, message = load_member_options()
    labels: List[str] = []
    label_to_id: Dict[str, str] = {}
    id_to_label: Dict[str, str] = {}
    for row in options:
        label, member_id = clean(row.get("label")), clean(row.get("id"))
        if label:
            labels.append(label)
            label_to_id[label] = member_id
        if member_id:
            id_to_label[member_id] = label
    if SELECT_MEMBER not in label_to_id:
        labels.insert(0, SELECT_MEMBER)
        label_to_id[SELECT_MEMBER] = ""
    return labels, label_to_id, id_to_label, message


def rows_for(kind: str, day: int, slot: str) -> List[Dict[str, Any]]:
    rows = [row for row in st.session_state["pbm_items"] if row.get("item_type") == kind and int(row.get("day_number") or 0) == day and row.get("slot_name") == slot]
    if not rows:
        row = new_row(kind, day, slot)
        st.session_state["pbm_items"].append(row)
        rows = [row]
    rows.sort(key=lambda value: int(value.get("item_order") or 1))
    for index, row in enumerate(rows, 1):
        row["item_order"] = index
    return rows


def row_has_content(row: Dict[str, Any]) -> bool:
    return any(clean(row.get(field)) for field in ("reference_label", "portion", "instruction", "scheduled_time", "dosage_frequency"))


def storage_rows(kind: str) -> List[Dict[str, Any]]:
    output = []
    for source in st.session_state["pbm_items"]:
        if source.get("item_type") != kind:
            continue
        row = dict(source)
        if kind == "supplement":
            row["scheduled_time"] = ", ".join(row.get("timeline") or [])
            row["dosage_frequency"] = encode_dosage_frequency(int(row.get("frequency") or 0), clean(row.get("dosage")))
        if row_has_content(row):
            output.append(row)
    return output


def day_label(day: int) -> str:
    start = st.session_state["pbm_profile"].get("start_date")
    start = start if isinstance(start, dt.date) else dt.date.today()
    return f"Day {day} — {(start + dt.timedelta(days=day-1)).strftime('%a, %d %b')}"
