import html
import streamlit as st
import streamlit.components.v1 as components

FLASH_KEY = "_hm_system_message"
JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY = "_hm_journal_autosave_silent_message"
JOURNAL_AUTOSAVE_SILENT_RERUN_KEY = "_hm_journal_autosave_silent_rerun"


def _consume_journal_autosave_feedback(level):
    """Handle journal-autosave feedback at the canonical message boundary.

    Daily Log imports ``set_system_message`` directly. Keeping the silent guard
    inside this function makes autosave independent of import and wrapper order.
    Only autosave success feedback is suppressed. Errors, warnings and info
    messages remain visible and retain their normal rerun behaviour.
    """

    silent_kind = st.session_state.get(JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY)
    if not silent_kind:
        return False

    normalized_level = str(level or "info").strip().lower()
    st.session_state.pop(JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY, None)
    if normalized_level == "success":
        return True

    # Never hide a real error or warning, and do not suppress its rerun.
    st.session_state.pop(JOURNAL_AUTOSAVE_SILENT_RERUN_KEY, None)
    return False


def set_system_message(message, level="success", celebrate=False):
    """Store a system message to show near the top on next rerun.

    celebrate=True should be used only for major task completion, not routine autosaves.
    """
    normalized_level = level if level in ["success", "error", "warning", "info"] else "info"
    if _consume_journal_autosave_feedback(normalized_level):
        return

    st.session_state[FLASH_KEY] = {
        "message": str(message),
        "level": normalized_level,
        "celebrate": bool(celebrate),
    }


def render_system_message():
    """Render top-visible system message, optionally celebrate, and scroll it into view."""
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