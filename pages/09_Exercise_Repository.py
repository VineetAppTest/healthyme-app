import html
import pathlib

import pandas as pd
import streamlit as st

from components.guards import require_member
from components.db import (
    get_workflow,
    get_resource_assignments,
    save_resource_feedback,
    get_published_recommendation_for_date,
)
from components.storage_assets import resolve_content_image_url
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)

st.set_page_config(page_title="Exercises", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("Exercise Repository", "Your nutritionist-shared movement plan and assigned exercise library.", "Member content")

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"
EXERCISE_COLUMNS = ["title", "description", "category", "difficulty", "goal_tags", "condition_tags", "duration_or_reps", "hidden_calories_v96", "equipment", "image_url", "image_bucket", "image_path", "image_access_type", "instructions", "benefits", "status"]
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1571019613914-85f342c1d3ff?auto=format&fit=crop&w=900&q=80",
]


def _esc(value):
    return html.escape(str(value or ""))


def load_exercises():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=EXERCISE_COLUMNS)
    df = pd.read_csv(DATA_PATH)
    for c in EXERCISE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[EXERCISE_COLUMNS]


def image_for(row, idx):
    return resolve_content_image_url(row, FALLBACK_IMAGES[int(idx) % len(FALLBACK_IMAGES)])


def split_lines(value):
    raw = str(value or "").replace("\r", "\n")
    if "\n" in raw:
        return [x.strip(" •-") for x in raw.split("\n") if x.strip(" •-")]
    if ";" in raw:
        return [x.strip(" •-") for x in raw.split(";") if x.strip(" •-")]
    return [raw.strip()] if raw.strip() else []


def _row_by_id(df, item_id):
    try:
        idx = int(str(item_id))
        if idx in df.index:
            return df.loc[idx], idx
    except Exception:
        pass
    return None, None


def _active_df(df):
    if df.empty:
        return df
    return df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()


def _plan_exercise_ids(share):
    ids = []
    for item in (share or {}).get("exercise_plan", []) or []:
        eid = str(item.get("exercise_id") or "").strip()
        if eid and eid not in ids:
            ids.append(eid)
    return ids


def _chip(text):
    return f"<span class='hm-ex-chip'>{_esc(text)}</span>" if str(text or "").strip() else ""


st.markdown("""
<style>
.hm-ex-page{max-width:1120px;margin:0 auto;}
.hm-ex-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.35rem 0 .8rem;}
.hm-ex-title{font-size:1.75rem;font-weight:950;color:#064E3B;margin:0;line-height:1.05;}
.hm-ex-sub{font-size:.88rem;color:#475569;font-weight:680;line-height:1.45;max-width:640px;margin:.32rem 0 0;}
.hm-ex-status{border:1px solid #E3C98E;background:#FFFDF8;border-radius:999px;padding:.42rem .72rem;color:#064E3B;font-size:.75rem;font-weight:900;white-space:nowrap;}
.hm-ex-window{border:1px solid #E3C98E;background:linear-gradient(135deg,#F0FDFA 0%,#FFFDF8 100%);border-radius:20px;padding:.95rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.8rem 0;}
.hm-ex-window-title{color:#064E3B;font-size:1rem;font-weight:950;margin-bottom:.35rem;}
.hm-ex-line{color:#334155;font-size:.82rem;font-weight:740;line-height:1.4;margin:.2rem 0;border-top:1px solid #E0F2F1;padding-top:.4rem;}
.hm-ex-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:.85rem 0 1rem;}
.hm-ex-card{border:1px solid #E3C98E;border-radius:18px;background:#FFFDF8;overflow:hidden;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-ex-thumb{height:150px;background:#E8D8BE;}
.hm-ex-thumb img{width:100%;height:150px;object-fit:cover;display:block;}
.hm-ex-card-body{padding:.82rem;}
.hm-ex-card-title{color:#064E3B;font-size:1rem;font-weight:950;line-height:1.1;margin-bottom:.35rem;}
.hm-ex-card-sub{color:#64748B;font-size:.76rem;font-weight:720;line-height:1.35;min-height:2.1rem;}
.hm-ex-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.68rem;font-weight:850;color:#475569;margin:.34rem .16rem 0 0;}
.hm-ex-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:1rem;color:#64748B;font-size:.86rem;font-weight:740;line-height:1.45;margin:.8rem 0;}
.hm-ex-detail-hero{border-radius:22px;overflow:hidden;border:1px solid #E5D2A9;box-shadow:0 10px 26px rgba(15,23,42,.07);margin:.7rem 0 1rem;}
.hm-ex-detail-hero img{width:100%;height:330px;object-fit:cover;display:block;}
.hm-ex-detail-title{font-family:Georgia,serif;color:#064E3B;font-size:2.25rem;line-height:1.02;font-weight:900;margin:.8rem 0 1rem;}
.hm-ex-detail-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.7rem 0 1rem;}
.hm-ex-pill{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:16px;padding:.75rem;color:#064E3B;box-shadow:0 6px 18px rgba(15,23,42,.045);font-size:.84rem;font-weight:820;}
.hm-ex-section{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:18px;padding:1rem;margin:.75rem 0;}
.hm-ex-row{display:flex;gap:.65rem;align-items:flex-start;padding:.52rem 0;border-bottom:1px solid #EEE3CC;color:#064E3B;font-size:.92rem;line-height:1.38;}
.hm-ex-check{width:1.08rem;height:1.08rem;border-radius:999px;background:#ECFDF5;border:1.5px solid #6D9C6C;color:#065F46;display:inline-flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:950;flex:0 0 auto;margin-top:.05rem;}
@media(max-width:850px){.hm-ex-head{display:block}.hm-ex-status{display:inline-block;margin-top:.55rem}.hm-ex-grid{grid-template-columns:1fr}.hm-ex-detail-grid{grid-template-columns:1fr 1fr}.hm-ex-detail-hero img{height:240px}}
</style>
""", unsafe_allow_html=True)

wf = get_workflow(st.session_state["user_id"])
if not wf.get("admin_completed"):
    st.warning("Your personalized plan will unlock after expert evaluation is completed.")
    st.stop()

user_id = st.session_state["user_id"]
df = _active_df(load_exercises())
share = get_published_recommendation_for_date(user_id)
plan_ids = _plan_exercise_ids(share)
assigned_ids = plan_ids or list(get_resource_assignments(user_id, "exercises"))
if assigned_ids:
    df = df[df.index.astype(str).isin(set(assigned_ids))].copy()

selected_id = st.session_state.get("hm_exercise_selected_id_v1024")
is_detail = selected_id is not None and str(selected_id).isdigit() and int(selected_id) in df.index

st.markdown("<div class='hm-ex-page'>", unsafe_allow_html=True)

if is_detail:
    row = df.loc[int(selected_id)]
    idx = int(selected_id)
    if st.button("← Back to Exercise Plan", use_container_width=True):
        st.session_state.pop("hm_exercise_selected_id_v1024", None)
        st.rerun()
    st.markdown(f"<div class='hm-ex-detail-hero'><img src='{_esc(image_for(row, idx))}'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-ex-detail-title'>{_esc(row.get('title') or 'Exercise')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-ex-sub'>{_esc(row.get('description') or '')}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='hm-ex-detail-grid'>
      <div class='hm-ex-pill'><b>{_esc(row.get('category') or 'Movement')}</b><br>Category</div>
      <div class='hm-ex-pill'><b>{_esc(row.get('duration_or_reps') or 'As advised')}</b><br>Duration / reps</div>
      <div class='hm-ex-pill'><b>{_esc(row.get('difficulty') or 'As advised')}</b><br>Difficulty</div>
      <div class='hm-ex-pill'><b>{_esc(row.get('equipment') or 'None')}</b><br>Equipment</div>
    </div>
    """, unsafe_allow_html=True)
    for title, key in [("Instructions", "instructions"), ("Benefits", "benefits")]:
        lines = split_lines(row.get(key, ""))
        body = "".join([f"<div class='hm-ex-row'><span class='hm-ex-check'>✓</span><div>{_esc(x)}</div></div>" for x in lines]) or "<div class='hm-ex-empty'>No details added yet.</div>"
        st.markdown(f"<div class='hm-ex-section'><div class='hm-ex-window-title'>{title}</div>{body}</div>", unsafe_allow_html=True)
    reset = st.session_state.get(f"exercise_feedback_reset_{idx}", 0)
    with st.expander("Exercise feedback", expanded=False):
        status = st.selectbox("Exercise status", ["Not started", "Completed", "Partially completed", "Need help / not suitable"], key=f"exercise_feedback_status_{idx}_{reset}")
        rating = st.selectbox("Rating", ["", "1", "2", "3", "4", "5"], key=f"exercise_feedback_rating_{idx}_{reset}")
        notes = st.text_area("Member feedback", value="", key=f"exercise_feedback_notes_{idx}_{reset}")
        if st.button("Submit feedback on exercise 🌿", type="primary", use_container_width=True, key=f"exercise_feedback_submit_{idx}_{reset}"):
            save_resource_feedback(user_id, "exercises", str(idx), title=str(row.get("title") or "Exercise"), status=status, rating=rating, notes=notes)
            st.session_state[f"exercise_feedback_reset_{idx}"] = reset + 1
            st.success("Exercise feedback submitted for admin review.")
            st.rerun()
else:
    st.markdown(f"""
    <div class='hm-ex-head'>
      <div><h1 class='hm-ex-title'>Exercise Plan & Movement Library</h1><div class='hm-ex-sub'>An Exercise-1 inspired experience, now connected to your real nutritionist-shared 7-day exercise plan.</div></div>
      <div class='hm-ex-status'>{len(df)} assigned exercise(s)</div>
    </div>
    """, unsafe_allow_html=True)
    if share:
        st.markdown(f"<div class='hm-ex-window'><div class='hm-ex-window-title'>7-Day Exercise Plan · {_esc(share.get('start_date'))} to {_esc(share.get('end_date'))}</div>", unsafe_allow_html=True)
        for item in (share.get("exercise_plan", []) or []):
            if not item.get("exercise_id"):
                continue
            row, idx = _row_by_id(load_exercises(), item.get("exercise_id"))
            if row is None:
                continue
            st.markdown(f"<div class='hm-ex-line'><b>{_esc(item.get('date'))}</b>: {_esc(row.get('title') or 'Exercise')} {_esc('— ' + item.get('timing') if item.get('timing') else '')} {_esc('— ' + item.get('notes') if item.get('notes') else '')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    if df.empty:
        st.markdown("<div class='hm-ex-empty'>No exercises have been assigned yet. Your nutritionist will update this section when applicable.</div>", unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for pos, (idx, row) in enumerate(df.iterrows()):
            with cols[pos % 3]:
                st.markdown(f"""
                <div class='hm-ex-card'>
                  <div class='hm-ex-thumb'><img src='{_esc(image_for(row, idx))}'></div>
                  <div class='hm-ex-card-body'>
                    <div class='hm-ex-card-title'>{_esc(row.get('title') or 'Exercise')}</div>
                    <div class='hm-ex-card-sub'>{_esc(row.get('description') or row.get('category') or '')}</div>
                    {_chip(row.get('duration_or_reps'))} {_chip(row.get('difficulty'))} {_chip(row.get('equipment'))}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Exercise", key=f"hm_ex_view_{idx}", use_container_width=True):
                    st.session_state["hm_exercise_selected_id_v1024"] = str(idx)
                    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
render_page_nav("Exercise Repository", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4: Exercise-1 UX merged into working Exercise Repository with recommendation-share/assignment binding and rollback copy preserved.
