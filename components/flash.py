import html
import inspect

import streamlit as st
import streamlit.components.v1 as components

FLASH_KEY = "_hm_system_message"


def set_system_message(message, level="success", celebrate=False):
    """Store a system message to show near the top on next rerun.

    celebrate=True should be used only for major task completion, not routine autosaves.
    """
    st.session_state[FLASH_KEY] = {
        "message": str(message),
        "level": level if level in ["success", "error", "warning", "info"] else "info",
        "celebrate": bool(celebrate),
    }


def _apply_daily_log_exercise_inline_bridge() -> None:
    """Replace the retired Daily Log redirect with the shared inline journal.

    PR #152 introduced the Exercise Journal tab before its reusable view was
    extracted. This compatibility bridge is deliberately restricted to the
    Daily Log module and can be removed once that page imports the shared view
    directly.
    """
    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        if not caller:
            return
        caller_file = str(caller.f_globals.get("__file__", "")).replace("\\", "/")
        if not caller_file.endswith("pages/18_Daily_Log.py"):
            return
        if "_render_exercise_journal_placeholder" not in caller.f_globals:
            return

        from components.member_exercise_view import render_member_exercise_journal

        def _render_inline_exercise_journal():
            render_member_exercise_journal(key_prefix="daily_log_exercise")

        caller.f_globals["_render_exercise_journal_placeholder"] = (
            _render_inline_exercise_journal
        )
    finally:
        del frame


def render_system_message():
    """Render top-visible system message, optionally celebrate, and scroll it into view."""
    _apply_daily_log_exercise_inline_bridge()

    payload = st.session_state.pop(FLASH_KEY, None)
    if not payload:
        return

    level = payload.get("level", "info")
    message = html.escape(payload.get("message", ""))
    celebrate = bool(payload.get("celebrate")) and level == "success"

    if celebrate:
        st.balloons()

    styles = {
        "success": ("#ECFDF5", "#047857", "#A7F3D0", "✅"),
        "error": ("#FEF2F2", "#B91C1C", "#FECACA", "⚠️"),
        "warning": ("#FFFBEB", "#B45309", "#FDE68A", "⚠️"),
        "info": ("#EFF6FF", "#1D4ED8", "#BFDBFE", "ℹ️"),
    }
    bg, color, border, icon = styles.get(level, styles["info"])

    celebration_line = "<br><span style='font-weight:700;'>Great job — this major step is complete.</span>" if celebrate else ""

    st.markdown(
        f"""
        <div id="hm-system-message" style="
            background:{bg};
            color:{color};
            border:1px solid {border};
            border-radius:18px;
            padding:14px 18px;
            margin:12px 0 18px 0;
            font-weight:800;
            box-shadow:0 12px 30px rgba(15,23,42,.08);
        ">
            <span style="font-size:1.05rem;">{icon}</span>
            <span style="margin-left:8px;">{message}</span>
            {celebration_line}
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (function(){
            function scrollToMessage(){
                try {
                    const doc = window.parent.document;
                    const el = doc.getElementById("hm-system-message");
                    if (el) {
                        el.scrollIntoView({behavior:"smooth", block:"center"});
                    }
                } catch(e) {}
            }
            scrollToMessage();
            setTimeout(scrollToMessage, 80);
            setTimeout(scrollToMessage, 250);
            setTimeout(scrollToMessage, 600);
        })();
        </script>
        """,
        height=0,
    )
