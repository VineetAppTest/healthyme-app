from __future__ import annotations

import datetime as dt
import html
import os
import re
from collections import defaultdict
from typing import Any

import streamlit as st

from components.flash import set_system_message
from components.member_timezone import member_local_today
from components.supplement_member_allocation import (
    list_member_supplement_allocations,
)


LOG_TABLE = "hm_member_supplement_logs"
STATUS_OPTIONS = ("Taken", "Not Taken")
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
TIMING_ORDER = (
    "Early Morning",
    "Morning",
    "Mid-morning",
    "Midday",
    "Afternoon",
    "Evening",
    "Night",
    "Before Bed",
    "With Food",
    "Empty Stomach",
    "After Meals",
)


def _clean(value: object, default: str = "") -> str:
    return default if value is None else str(value).strip()


def _esc(value: object) -> str:
    return html.escape(_clean(value))


def _slug(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _clean(value).casefold()).strip("_") or "item"


def _parse_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(_clean(value)[:10])
    except (TypeError, ValueError):
        return None


def _timings(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = re.split(r"[,;|]", _clean(value))
    return list(dict.fromkeys(_clean(item) for item in raw if _clean(item)))


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean(value, default)
    try:
        value = st.secrets.get(name)
        if value is not None:
            return _clean(value, default)
        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean(value, default)
        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            value = section_values.get(name) or section_values.get(lower_name)
            if value is not None:
                return _clean(value, default)
    except Exception:
        pass
    return default


def _client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret(
        "SUPABASE_ANON_KEY"
    )
    if not url or not key:
        raise RuntimeError("Supabase URL/key is not configured.")
    return create_client(url, key)


def _rows(response: object) -> list[dict[str, Any]]:
    return [dict(row) for row in (getattr(response, "data", None) or [])]


def supplement_entries_for_date(
    member_id: str,
    selected_date: dt.date,
) -> list[dict[str, Any]]:
    """Expand each active allocation into one due row per selected timing."""

    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    allocations = list_member_supplement_allocations(
        member_id,
        include_stopped=True,
    )
    for raw in allocations:
        allocation = dict(raw or {})
        allocation_id = _clean(allocation.get("id"))
        if not allocation_id:
            continue

        start_date = _parse_date(allocation.get("start_date"))
        end_date = _parse_date(allocation.get("end_date"))
        stop_date = _parse_date(allocation.get("stop_date"))
        if start_date and selected_date < start_date:
            continue
        if end_date and selected_date > end_date:
            continue
        if stop_date and selected_date > stop_date:
            continue
        if (
            _clean(allocation.get("status")).casefold() == "stopped"
            and not stop_date
            and not end_date
        ):
            continue

        for timing in _timings(allocation.get("timing")):
            identity = (allocation_id, timing.casefold())
            if identity in seen:
                continue
            seen.add(identity)
            entries.append(
                {
                    "allocation_id": allocation_id,
                    "source_id": _clean(
                        allocation.get("source_id")
                        or allocation.get("supplement_source_id")
                    ),
                    "supplement_name": _clean(
                        allocation.get("supplement_name")
                        or allocation.get("title")
                        or "Supplement"
                    ),
                    "dosage": _clean(allocation.get("dosage")) or "Not specified",
                    "timing": timing,
                }
            )

    timing_rank = {value.casefold(): index for index, value in enumerate(TIMING_ORDER)}
    entries.sort(
        key=lambda row: (
            timing_rank.get(_clean(row.get("timing")).casefold(), len(timing_rank)),
            _clean(row.get("supplement_name")).casefold(),
        )
    )
    return entries


def list_member_supplement_logs(
    member_id: str,
    *,
    log_date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query = _client().table(LOG_TABLE).select("*").eq("member_id", member_id)
    if log_date:
        query = query.eq("log_date", log_date)
    if date_from:
        query = query.gte("log_date", date_from)
    if date_to:
        query = query.lte("log_date", date_to)
    return _rows(query.order("log_date", desc=True).order("timing").execute())


def supplement_log_map(member_id: str, log_date: str) -> dict[tuple[str, str], dict]:
    return {
        (_clean(row.get("allocation_id")), _clean(row.get("timing")).casefold()): row
        for row in list_member_supplement_logs(member_id, log_date=log_date)
    }


def save_member_supplement_log(payload: dict[str, Any]) -> None:
    required = (
        "member_id",
        "log_date",
        "allocation_id",
        "supplement_name",
        "timing",
        "status",
    )
    missing = [field for field in required if not _clean(payload.get(field))]
    if missing:
        raise ValueError(f"Missing supplement log fields: {', '.join(missing)}")
    if payload.get("status") not in STATUS_OPTIONS:
        raise ValueError("Status must be Taken or Not Taken.")

    row = {field: payload.get(field) for field in required}
    row.update(
        {
            "source_id": _clean(payload.get("source_id")) or None,
            "dosage": _clean(payload.get("dosage")) or None,
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    )
    (
        _client()
        .table(LOG_TABLE)
        .upsert(
            row,
            on_conflict="member_id,log_date,allocation_id,timing",
        )
        .execute()
    )


def _inject_styles() -> None:
    st.markdown(
        """
<style id="hm-supplement-journal-v1">
.hm-supplement-entry-meta{display:grid;grid-template-columns:minmax(11rem,2fr) minmax(8rem,1fr) minmax(8rem,1fr);gap:.55rem;margin:.12rem 0 .5rem;}
.hm-supplement-entry-meta>div{border:1px solid #E8DDC7;border-radius:12px;background:#FFFDF8;padding:.55rem .65rem;color:#334155;overflow-wrap:anywhere;}
.hm-supplement-entry-meta b{display:block;color:#064E3B;font-size:.73rem;text-transform:uppercase;letter-spacing:.02em;margin-bottom:.12rem;}
.hm-supplement-saved-day{border:1px solid #E3D4BA;border-radius:16px;background:#FFFDF8;padding:.72rem .82rem;margin:.5rem 0;}
.hm-supplement-saved-day h4{color:#064E3B;margin:0 0 .35rem;font-size:1rem;}
.hm-supplement-saved-row{display:grid;grid-template-columns:minmax(10rem,2fr) minmax(7rem,1fr) minmax(7rem,1fr) minmax(6rem,.8fr);gap:.45rem;padding:.38rem 0;border-top:1px solid #EEE4D2;color:#334155;font-size:.84rem;}
.hm-supplement-saved-row:first-of-type{border-top:0;}
@media(max-width:760px){.hm-supplement-entry-meta,.hm-supplement-saved-row{grid-template-columns:1fr;}}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_saved_days(member_id: str, key_prefix: str, today: dt.date) -> None:
    from_key = f"{key_prefix}_saved_from"
    to_key = f"{key_prefix}_saved_to"
    st.session_state.setdefault(from_key, today - dt.timedelta(days=6))
    st.session_state.setdefault(to_key, today)

    with st.container(border=True):
        st.markdown("### View Saved Days")
        from_col, to_col = st.columns(2)
        with from_col:
            date_from = st.date_input("From", key=from_key)
        with to_col:
            date_to = st.date_input("To", key=to_key)
        if date_from > date_to:
            st.warning("From date cannot be after To date.")
            return

        try:
            rows = list_member_supplement_logs(
                member_id,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        except Exception as exc:
            st.error(f"Saved supplement days could not be loaded: {exc}")
            return
        if not rows:
            st.caption("No saved supplement days found in this range.")
            return

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[_clean(row.get("log_date"))].append(row)
        st.caption(f"Showing {len(grouped)} saved day(s) in the selected range.")
        for date_text in sorted(grouped, reverse=True):
            parsed = _parse_date(date_text)
            display_date = parsed.strftime("%a, %d %b %Y") if parsed else date_text
            item_html = "".join(
                "<div class='hm-supplement-saved-row'>"
                f"<span><b>{_esc(row.get('supplement_name'))}</b></span>"
                f"<span>{_esc(row.get('dosage') or '-')}</span>"
                f"<span>{_esc(row.get('timing'))}</span>"
                f"<span>{_esc(row.get('status'))}</span>"
                "</div>"
                for row in grouped[date_text]
            )
            st.markdown(
                f"<div class='hm-supplement-saved-day'><h4>{_esc(display_date)}</h4>{item_html}</div>",
                unsafe_allow_html=True,
            )


def render_member_supplement_journal(
    member_id: str,
    *,
    key_prefix: str = "hm_daily_log_supplement",
) -> None:
    _inject_styles()
    today = member_local_today(member_id)
    date_key = f"{key_prefix}_date"
    st.session_state.setdefault(date_key, today)

    with st.container(border=True):
        st.markdown("### Supplement Journal Date")
        selected_date = st.date_input(
            "Select the date for this supplement journal entry",
            key=date_key,
        )
    log_date = selected_date.isoformat()

    with st.container(border=True):
        st.markdown("### Supplement Section")
        entries = supplement_entries_for_date(member_id, selected_date)
        try:
            existing = supplement_log_map(member_id, log_date)
        except Exception as exc:
            existing = {}
            st.error(f"Saved supplement entries could not be loaded: {exc}")

        if not entries:
            st.info("No supplement is allocated for the selected date.")
        for entry in entries:
            identity = (
                _clean(entry.get("allocation_id")),
                _clean(entry.get("timing")).casefold(),
            )
            prior = dict(existing.get(identity) or {})
            widget = (
                f"{key_prefix}_{log_date}_{_slug(entry.get('allocation_id'))}_"
                f"{_slug(entry.get('timing'))}"
            )
            with st.container(border=True):
                st.markdown(
                    "<div class='hm-supplement-entry-meta'>"
                    f"<div><b>Supplement</b>{_esc(entry.get('supplement_name'))}</div>"
                    f"<div><b>Dosage</b>{_esc(entry.get('dosage'))}</div>"
                    f"<div><b>Timing</b>{_esc(entry.get('timing'))}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                status_options = ["Select status", *STATUS_OPTIONS]
                prior_status = _clean(prior.get("status"))
                status_col, save_col = st.columns([1.35, 1], gap="small")
                with status_col:
                    status = st.selectbox(
                        "Status",
                        status_options,
                        index=(
                            status_options.index(prior_status)
                            if prior_status in STATUS_OPTIONS
                            else 0
                        ),
                        key=f"{widget}_status",
                    )
                with save_col:
                    st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
                    save_clicked = st.button(
                        "Save Supplement Entry",
                        key=f"{widget}_save",
                        use_container_width=True,
                        disabled=status not in STATUS_OPTIONS,
                    )
                if save_clicked:
                    try:
                        save_member_supplement_log(
                            {
                                "member_id": member_id,
                                "log_date": log_date,
                                **entry,
                                "status": status,
                            }
                        )
                        set_system_message(
                            f"Supplement entry saved for {entry['supplement_name']} "
                            f"at {entry['timing']}.",
                            "success",
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Supplement entry could not be saved: {exc}")

    _render_saved_days(member_id, key_prefix, today)
