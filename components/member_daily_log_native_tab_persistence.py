from __future__ import annotations

import functools
import inspect

import streamlit as st


_MARKER = "_hm_member_daily_log_native_tab_persistence_v2"
_PAGE_SUFFIX = "pages/18_Daily_Log.py"
_LABELS = ("Food Journal", "Exercise Journal")


def _page_in_stack() -> bool:
    for frame_info in inspect.stack():
        page_file = str(frame_info.frame.f_globals.get("__file__") or "").replace("\\", "/")
        if page_file.endswith(_PAGE_SUFFIX):
            return True
    return False


def _is_bound_callable(value) -> bool:
    return callable(value) and getattr(value, "__self__", None) is not None


def _unwrap_native_tabs(candidate):
    """Walk HealthyMe wrappers without unbinding Streamlit's tabs method."""

    current = candidate
    seen: set[int] = set()
    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        if _is_bound_callable(current):
            return current
        next_callable = getattr(current, "__wrapped__", None)
        if not callable(next_callable):
            next_callable = getattr(current, "_hm_original_tabs", None)
        if not callable(next_callable) or next_callable is current:
            break
        current = next_callable
    return current


def _bound_native_tabs(current_tabs):
    """Prefer Streamlit's bound main-container method, with a safe wrapper fallback."""

    main_container = getattr(st, "_main", None)
    native_tabs = getattr(main_container, "tabs", None)
    if callable(native_tabs):
        return native_tabs
    resolved = _unwrap_native_tabs(current_tabs)
    return resolved if callable(resolved) else current_tabs


def _render_tab_persistence_guard() -> None:
    st.html(
        r"""
<script>
(() => {
  let topWindow;
  try { topWindow = window.top || window.parent || window; }
  catch (_error) { topWindow = window; }
  let doc;
  try { doc = topWindow.document; }
  catch (_error) { return; }

  const storageKey = "hm_daily_log_active_native_tab_v1";
  const labels = ["Food Journal", "Exercise Journal"];

  function tabButtons() {
    return Array.from(doc.querySelectorAll(
      '[data-testid="stTabs"] [role="tab"], [data-baseweb="tab-list"] [role="tab"]'
    )).filter((button) => labels.includes(String(button.textContent || "").trim()));
  }

  function remember(button) {
    const label = String(button.textContent || "").trim();
    if (!labels.includes(label)) return;
    try { topWindow.sessionStorage.setItem(storageKey, label); }
    catch (_error) {}
  }

  function bindAndRestore() {
    const buttons = tabButtons();
    if (buttons.length < 2) return false;
    for (const button of buttons) {
      if (button.dataset.hmDailyLogPersistenceBound !== "1") {
        button.dataset.hmDailyLogPersistenceBound = "1";
        button.addEventListener("click", () => remember(button), { passive: true });
      }
    }
    let selected = "Food Journal";
    try {
      const stored = topWindow.sessionStorage.getItem(storageKey);
      if (labels.includes(stored)) selected = stored;
    } catch (_error) {}
    const target = buttons.find(
      (button) => String(button.textContent || "").trim() === selected
    );
    if (target && target.getAttribute("aria-selected") !== "true") target.click();
    return true;
  }

  if (topWindow.__hmDailyLogTabObserverV1) {
    try { topWindow.__hmDailyLogTabObserverV1.disconnect(); }
    catch (_error) {}
  }
  const observer = new MutationObserver(() => bindAndRestore());
  topWindow.__hmDailyLogTabObserverV1 = observer;
  if (doc.body) observer.observe(doc.body, { childList: true, subtree: true });
  bindAndRestore();
  [40, 120, 300, 700, 1500].forEach((delay) => topWindow.setTimeout(bindAndRestore, delay));
})();
</script>
        """,
        unsafe_allow_javascript=True,
    )


def install_member_daily_log_native_tab_persistence() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return
    native_tabs = _bound_native_tabs(current_tabs)

    @functools.wraps(current_tabs)
    def native_daily_log_tabs(labels, *args, **kwargs):
        normalized = tuple(str(label) for label in labels)
        if normalized == _LABELS and _page_in_stack():
            result = native_tabs(labels, *args, **kwargs)
            _render_tab_persistence_guard()
            return result
        return current_tabs(labels, *args, **kwargs)

    setattr(native_daily_log_tabs, _MARKER, True)
    setattr(native_daily_log_tabs, "_hm_original_tabs", current_tabs)
    st.tabs = native_daily_log_tabs
