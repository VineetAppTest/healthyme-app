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

st.set_page_config(page_title="Recipes", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("Recipe Repository", "Your nutritionist-shared meal plan and assigned recipe library.", "Member content")

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"
RECIPE_COLUMNS = ["title", "description", "meal_type", "diet_type", "goal_tags", "condition_tags", "prep_time", "calories", "protein", "fat", "carbohydrates", "additional_nutrition", "servings", "portion_size", "image_url", "image_bucket", "image_path", "image_access_type", "ingredients", "steps", "nutrition", "status"]
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?auto=format&fit=crop&w=900&q=80",
]


def _esc(value):
    return html.escape(str(value or ""))


def load_recipes():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=RECIPE_COLUMNS)
    df = pd.read_csv(DATA_PATH)
    for c in RECIPE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[RECIPE_COLUMNS]


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


def _plan_recipe_ids(share):
    ids = []
    for item in (share or {}).get("meal_plan", []) or []:
        rid = str(item.get("recipe_id") or "").strip()
        if rid and rid not in ids:
            ids.append(rid)
    return ids


def _metric(text, label):
    if not str(text or "").strip():
        return ""
    return f"<span class='hm-rx-chip'><b>{_esc(text)}</b> {label}</span>"


st.markdown("""
<style>
.hm-rx-page{max-width:1120px;margin:0 auto;}
.hm-rx-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.35rem 0 .8rem;}
.hm-rx-title{font-size:1.75rem;font-weight:950;color:#064E3B;margin:0;line-height:1.05;}
.hm-rx-sub{font-size:.88rem;color:#475569;font-weight:680;line-height:1.45;max-width:640px;margin:.32rem 0 0;}
.hm-rx-status{border:1px solid #E3C98E;background:#FFFDF8;border-radius:999px;padding:.42rem .72rem;color:#064E3B;font-size:.75rem;font-weight:900;white-space:nowrap;}
.hm-rx-window{border:1px solid #E3C98E;background:linear-gradient(135deg,#FFFDF8 0%,#FFF4DA 100%);border-radius:20px;padding:.95rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.8rem 0;}
.hm-rx-window-title{color:#064E3B;font-size:1rem;font-weight:950;margin-bottom:.35rem;}
.hm-rx-day{border-top:1px solid #F0E4CC;padding:.58rem 0;}
.hm-rx-day-title{color:#064E3B;font-size:.82rem;font-weight:930;margin-bottom:.28rem;}
.hm-rx-meal{color:#334155;font-size:.80rem;font-weight:740;line-height:1.4;margin:.16rem 0;}
.hm-rx-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:.85rem 0 1rem;}
.hm-rx-card{border:1px solid #E3C98E;border-radius:18px;background:#FFFDF8;overflow:hidden;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-rx-card img{width:100%;height:155px;object-fit:cover;display:block;}
.hm-rx-card-body{padding:.82rem;}
.hm-rx-card-title{color:#064E3B;font-size:1rem;font-weight:950;line-height:1.1;margin-bottom:.35rem;}
.hm-rx-card-sub{color:#64748B;font-size:.76rem;font-weight:720;line-height:1.35;min-height:2.1rem;}
.hm-rx-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.68rem;font-weight:820;color:#475569;margin:.34rem .16rem 0 0;}
.hm-rx-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:1rem;color:#64748B;font-size:.86rem;font-weight:740;line-height:1.45;margin:.8rem 0;}
.hm-rx-detail-hero{border-radius:22px;overflow:hidden;border:1px solid #E5D2A9;box-shadow:0 10px 26px rgba(15,23,42,.07);margin:.7rem 0 1rem;}
.hm-rx-detail-hero img{width:100%;height:330px;object-fit:cover;display:block;}
.hm-rx-detail-title{font-family:Georgia,serif;color:#064E3B;font-size:2.25rem;line-height:1.02;font-weight:900;margin:.8rem 0 1rem;}
.hm-rx-detail-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.7rem 0 1rem;}
.hm-rx-pill{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:16px;padding:.75rem;color:#064E3B;box-shadow:0 6px 18px rgba(15,23,42,.045);font-size:.84rem;font-weight:820;}
.hm-rx-section{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:18px;padding:1rem;margin:.75rem 0;}
.hm-rx-row{display:flex;gap:.65rem;align-items:flex-start;padding:.52rem 0;border-bottom:1px solid #EEE3CC;color:#064E3B;font-size:.92rem;line-height:1.38;}
.hm-rx-check{width:1.08rem;height:1.08rem;border-radius:999px;background:#ECFDF5;border:1.5px solid #6D9C6C;color:#065F46;display:inline-flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:950;flex:0 0 auto;margin-top:.05rem;}
@media(max-width:850px){.hm-rx-head{display:block}.hm-rx-status{display:inline-block;margin-top:.55rem}.hm-rx-grid{grid-template-columns:1fr}.hm-rx-detail-grid{grid-template-columns:1fr 1fr}.hm-rx-detail-hero img{height:240px}}
</style>
""", unsafe_allow_html=True)

wf = get_workflow(st.session_state["user_id"])
if not wf.get("admin_completed"):
    st.warning("Your personalized plan will unlock after expert evaluation is completed.")
    st.stop()

user_id = st.session_state["user_id"]
df = _active_df(load_recipes())
share = get_published_recommendation_for_date(user_id)
plan_ids = _plan_recipe_ids(share)
assigned_ids = plan_ids or list(get_resource_assignments(user_id, "recipes"))
if assigned_ids:
    df = df[df.index.astype(str).isin(set(assigned_ids))].copy()

selected_id = st.session_state.get("hm_recipe_selected_id_v1024")
is_detail = selected_id is not None and str(selected_id).isdigit() and int(selected_id) in df.index

st.markdown("<div class='hm-rx-page'>", unsafe_allow_html=True)

if is_detail:
    row = df.loc[int(selected_id)]
    idx = int(selected_id)
    if st.button("← Back to Meal Plan", use_container_width=True):
        st.session_state.pop("hm_recipe_selected_id_v1024", None)
        st.rerun()
    st.markdown(f"<div class='hm-rx-detail-hero'><img src='{_esc(image_for(row, idx))}'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-rx-detail-title'>{_esc(row.get('title') or 'Recipe')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-rx-sub'>{_esc(row.get('description') or '')}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='hm-rx-detail-grid'>
      <div class='hm-rx-pill'><b>{_esc(row.get('meal_type') or 'Meal')}</b><br>Meal type</div>
      <div class='hm-rx-pill'><b>{_esc(row.get('prep_time') or 'As advised')}</b><br>Timing / prep</div>
      <div class='hm-rx-pill'><b>{_esc(row.get('calories') or 'NA')}</b><br>Calories</div>
      <div class='hm-rx-pill'><b>{_esc(row.get('servings') or 'NA')}</b><br>Servings</div>
    </div>
    """, unsafe_allow_html=True)
    for title, key in [("Ingredients", "ingredients"), ("Instructions", "steps"), ("Nutrition", "nutrition")]:
        lines = split_lines(row.get(key, ""))
        body = "".join([f"<div class='hm-rx-row'><span class='hm-rx-check'>✓</span><div>{_esc(x)}</div></div>" for x in lines]) or "<div class='hm-rx-empty'>No details added yet.</div>"
        st.markdown(f"<div class='hm-rx-section'><div class='hm-rx-window-title'>{title}</div>{body}</div>", unsafe_allow_html=True)
    reset = st.session_state.get(f"recipe_feedback_reset_{idx}", 0)
    with st.expander("Recipe feedback", expanded=False):
        status = st.selectbox("Recipe status", ["Not started", "Tried", "Liked", "Need help / not suitable"], key=f"recipe_feedback_status_{idx}_{reset}")
        rating = st.selectbox("Rating", ["", "1", "2", "3", "4", "5"], key=f"recipe_feedback_rating_{idx}_{reset}")
        notes = st.text_area("Member feedback", value="", key=f"recipe_feedback_notes_{idx}_{reset}")
        if st.button("Submit feedback on recipe 🌿", type="primary", use_container_width=True, key=f"recipe_feedback_submit_{idx}_{reset}"):
            save_resource_feedback(user_id, "recipes", str(idx), title=str(row.get("title") or "Recipe"), status=status, rating=rating, notes=notes)
            st.session_state[f"recipe_feedback_reset_{idx}"] = reset + 1
            st.success("Recipe feedback submitted for admin review.")
            st.rerun()
else:
    st.markdown(f"""
    <div class='hm-rx-head'>
      <div><h1 class='hm-rx-title'>Meal Plan & Recipe Library</h1><div class='hm-rx-sub'>A cleaner Recipe-1 inspired experience, now connected to your real nutritionist-shared plan and assigned recipe repository.</div></div>
      <div class='hm-rx-status'>{len(df)} assigned recipe(s)</div>
    </div>
    """, unsafe_allow_html=True)
    if share:
        st.markdown(f"<div class='hm-rx-window'><div class='hm-rx-window-title'>7-Day Meal Plan · {_esc(share.get('start_date'))} to {_esc(share.get('end_date'))}</div>", unsafe_allow_html=True)
        for item in (share.get("meal_plan", []) or []):
            if not item.get("recipe_id"):
                continue
            row, idx = _row_by_id(load_recipes(), item.get("recipe_id"))
            if row is None:
                continue
            st.markdown(f"<div class='hm-rx-meal'><b>{_esc(item.get('date'))} · {_esc(item.get('meal_slot'))}</b>: {_esc(row.get('title') or 'Recipe')} {_esc('— ' + item.get('notes') if item.get('notes') else '')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    if df.empty:
        st.markdown("<div class='hm-rx-empty'>No recipes have been assigned yet. Your nutritionist will update this section when applicable.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='hm-rx-grid'>", unsafe_allow_html=True)
        # close the CSS grid before Streamlit buttons; cards are rendered one-per-column for reliable click actions.
        st.markdown("</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for pos, (idx, row) in enumerate(df.iterrows()):
            with cols[pos % 3]:
                st.markdown(f"""
                <div class='hm-rx-card'>
                  <img src='{_esc(image_for(row, idx))}'>
                  <div class='hm-rx-card-body'>
                    <div class='hm-rx-card-title'>{_esc(row.get('title') or 'Recipe')}</div>
                    <div class='hm-rx-card-sub'>{_esc(row.get('description') or row.get('meal_type') or '')}</div>
                    {_metric(row.get('calories'), 'cal')} {_metric(row.get('protein'), 'protein')} {_metric(row.get('prep_time'), 'prep')}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Recipe", key=f"hm_rx_view_{idx}", use_container_width=True):
                    st.session_state["hm_recipe_selected_id_v1024"] = str(idx)
                    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
render_page_nav("Recipe Repository", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4: Recipe-1 UX merged into working Recipe Repository with recommendation-share/assignment binding and rollback copy preserved.
