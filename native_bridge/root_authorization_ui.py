import json
import os

import streamlit as st


AUTHORIZATION_BUILD = "H13R3-unified-healthyme-authorizer-v1"
ROLLBACK_BUILD = "H13R2-production-root-authorizer-v1"
DEFAULT_CLIENT_LOGIN_URL = "https://healthymeappbyankita.streamlit.app/Login"


def _secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value if value is not None else default).strip()


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def render_root_authorization_ui(authorization_id: str) -> None:
    # Preserve the accepted H13R2 callback cleanup. Once Streamlit has created the
    # native identity, the consumed one-time authorization parameter is removed.
    if _native_identity_present():
        st.query_params.clear()
        st.rerun()

    supabase_url = _secret("SUPABASE_URL")
    publishable_key = _secret("SUPABASE_ANON_KEY") or _secret("SUPABASE_PUBLISHABLE_KEY")
    client_login_url = _secret("AUTH_CLIENT_LOGIN_URL", DEFAULT_CLIENT_LOGIN_URL)

    st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="centered")

    if not authorization_id:
        st.error("This secure login request has expired or is incomplete.")
        st.link_button("Return to HealthyMe login", client_login_url, use_container_width=True)
        st.stop()

    if not supabase_url or not publishable_key:
        st.error("HealthyMe secure login is temporarily unavailable.")
        with st.expander("Technical details", expanded=False):
            st.code("SUPABASE_URL and a Supabase publishable key are required.")
            st.code(AUTHORIZATION_BUILD)
        st.stop()

    html_document = rf"""
    <style>
      :root {{ color-scheme: light; }}
      html,body {{ margin:0;padding:0;background:#f7faf8;font-family:Inter,Arial,sans-serif;color:#17352d; }}
      #hm-login-shell {{ max-width:460px;margin:8px auto 0;padding:12px 8px 20px; }}
      .hm-brand {{ display:flex;align-items:center;gap:12px;margin:0 0 18px; }}
      .hm-mark {{ width:42px;height:42px;border-radius:14px;background:#e6f3ee;display:grid;place-items:center;font-size:22px; }}
      .hm-brand-name {{ font-size:28px;line-height:1;font-weight:800;color:#123f32; }}
      .hm-brand-sub {{ margin-top:5px;font-size:13px;color:#697a74; }}
      .hm-card {{ padding:24px;border:1px solid #dce8e3;border-radius:18px;background:#fff;box-shadow:0 12px 32px rgba(24,74,58,.07); }}
      .hm-card h2 {{ margin:0 0 7px;font-size:23px;color:#173d33; }}
      .hm-copy {{ margin:0 0 18px;color:#677872;font-size:14px;line-height:1.5; }}
      label {{ display:block;margin-top:14px;font-size:13px;font-weight:750;color:#294c40; }}
      input {{ width:100%;box-sizing:border-box;margin-top:7px;padding:13px 14px;border:1px solid #c9dad3;border-radius:11px;font-size:16px;outline:none;background:#fff; }}
      input:focus {{ border-color:#176b55;box-shadow:0 0 0 3px rgba(23,107,85,.10); }}
      button {{ width:100%;margin-top:19px;padding:13px 16px;border:0;border-radius:11px;background:#176b55;color:#fff;font-size:15px;font-weight:750;cursor:pointer; }}
      button:disabled {{ opacity:.68;cursor:wait; }}
      #hm-message {{ display:none;margin:14px 0 0;padding:11px 12px;border-radius:10px;font-size:13px;line-height:1.4; }}
      #hm-message.info {{ display:block;background:#edf7f4;color:#245a48; }}
      #hm-message.error {{ display:block;background:#fdecec;color:#8e2020; }}
      #hm-progress {{ display:none;text-align:center;padding:12px 0 2px; }}
      .hm-spinner {{ width:28px;height:28px;margin:4px auto 12px;border:3px solid #d8ebe4;border-top-color:#176b55;border-radius:50%;animation:spin .8s linear infinite; }}
      .hm-progress-title {{ font-weight:750;color:#234b3e; }}
      .hm-progress-copy {{ margin-top:5px;color:#71817b;font-size:13px; }}
      .hm-secure {{ margin-top:14px;text-align:center;color:#788780;font-size:12px; }}
      .hm-restart {{ display:none; }}
      .hm-technical {{ margin-top:16px;text-align:center;color:#9aa6a1;font-size:10px; }}
      @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
      @media (max-width:520px) {{ #hm-login-shell {{ margin-top:0;padding:4px 2px 14px; }} .hm-card {{ padding:20px; }} }}
    </style>

    <main id="hm-login-shell">
      <div class="hm-brand">
        <div class="hm-mark">🌿</div>
        <div>
          <div class="hm-brand-name">HealthyMe</div>
          <div class="hm-brand-sub">Secure wellness access</div>
        </div>
      </div>

      <section class="hm-card">
        <div id="hm-login">
          <h2>Sign in to continue</h2>
          <p class="hm-copy">Use your registered HealthyMe email and password.</p>
          <form id="hm-form">
            <label for="hm-email">Email</label>
            <input id="hm-email" type="email" autocomplete="username" required>
            <label for="hm-password">Password</label>
            <input id="hm-password" type="password" autocomplete="current-password" required>
            <button id="hm-signin" type="submit">Sign in securely</button>
          </form>
        </div>

        <div id="hm-progress">
          <div class="hm-spinner"></div>
          <div class="hm-progress-title">Signing you in securely…</div>
          <div class="hm-progress-copy">HealthyMe is confirming your identity and access.</div>
        </div>

        <div id="hm-message"></div>

        <div id="hm-restart" class="hm-restart">
          <button id="hm-restart-button" type="button">Return to HealthyMe login</button>
        </div>

        <div class="hm-secure">🔒 Protected by Supabase secure authentication</div>
      </section>
      <div class="hm-technical">{{AUTHORIZATION_BUILD}} · rollback {{ROLLBACK_BUILD}}</div>
    </main>

    <script type="module">
      import {{ createClient }} from "https://esm.sh/@supabase/supabase-js@2.105.3";

      const supabase = createClient(
        {json.dumps(supabase_url)},
        {json.dumps(publishable_key)},
        {{auth:{{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false}}}}
      );
      const authorizationId = {json.dumps(authorization_id)};
      const clientLoginUrl = {json.dumps(client_login_url)};
      const loginPanel = document.getElementById("hm-login");
      const progressPanel = document.getElementById("hm-progress");
      const restartPanel = document.getElementById("hm-restart");
      const messageBox = document.getElementById("hm-message");
      const signInButton = document.getElementById("hm-signin");
      let busy = false;

      function showMessage(text, level="info") {{
        messageBox.textContent = text;
        messageBox.className = level;
      }}

      function showProgress() {{
        loginPanel.style.display = "none";
        restartPanel.style.display = "none";
        progressPanel.style.display = "block";
        messageBox.className = "";
      }}

      function redirectTop(url) {{
        try {{ window.top.location.replace(url); }}
        catch (_error) {{ window.location.replace(url); }}
      }}

      function isStale(error) {{
        const message = String(error?.message || error || "").toLowerCase();
        return message.includes("authorization not found")
          || message.includes("invalid authorization")
          || message.includes("authorization request cannot be processed")
          || message.includes("expired");
      }}

      function requireRestart() {{
        loginPanel.style.display = "none";
        progressPanel.style.display = "none";
        restartPanel.style.display = "block";
        showMessage("This secure login request has expired. Please start again.", "error");
      }}

      async function approveAndContinue() {{
        const {{data:details,error:detailsError}} =
          await supabase.auth.oauth.getAuthorizationDetails(authorizationId);
        if (detailsError) throw detailsError;

        if (details?.redirect_url && !("authorization_id" in details)) {{
          redirectTop(details.redirect_url);
          return;
        }}

        const {{data,error}} = await supabase.auth.oauth.approveAuthorization(authorizationId);
        if (error) throw error;
        redirectTop(data.redirect_url);
      }}

      document.getElementById("hm-form").addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (busy) return;
        busy = true;
        signInButton.disabled = true;
        showMessage("Confirming your identity…", "info");

        const email = document.getElementById("hm-email").value.trim();
        const passwordInput = document.getElementById("hm-password");
        const {{error}} = await supabase.auth.signInWithPassword({{
          email,
          password:passwordInput.value
        }});
        passwordInput.value = "";

        if (error) {{
          showMessage(error.message || "Unable to sign in. Please check your details.", "error");
          busy = false;
          signInButton.disabled = false;
          return;
        }}

        showProgress();
        try {{
          await approveAndContinue();
        }} catch (error) {{
          if (isStale(error)) {{
            try {{ await supabase.auth.signOut(); }} catch (_error) {{}}
            requireRestart();
            return;
          }}
          loginPanel.style.display = "block";
          progressPanel.style.display = "none";
          showMessage(error?.message || "Unable to complete secure login.", "error");
          busy = false;
          signInButton.disabled = false;
        }}
      }});

      document.getElementById("hm-restart-button").addEventListener("click", () => {{
        redirectTop(clientLoginUrl);
      }});
    </script>
    """

    st.html(html_document, unsafe_allow_javascript=True)
    st.stop()
