import json
import os

import streamlit as st


AUTHORIZATION_BUILD = "H13R7-healthyme-authorizer-ux-v1"
ROLLBACK_BUILD = "H13R5-production-direct-login-v1"
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

    st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide")

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
      * {{ box-sizing:border-box; }}
      html,body {{
        margin:0;padding:0;background:#ffffff;
        font-family:Inter,Arial,sans-serif;color:#17352d;
      }}
      body {{ min-height:100vh; }}
      #hm-page {{
        width:min(1180px,calc(100% - 44px));
        margin:0 auto;padding:28px 0 26px;
      }}
      .hm-topbar {{
        display:flex;align-items:flex-start;justify-content:space-between;
        gap:18px;margin-bottom:22px;
      }}
      .hm-brand-name {{
        font-size:30px;line-height:1;font-weight:850;letter-spacing:-.6px;color:#063e31;
      }}
      .hm-brand-sub {{ margin-top:7px;font-size:13px;color:#6d7d77; }}
      .hm-secure-pill {{
        border:1px solid #cfe2da;background:#eff8f4;color:#245b49;
        border-radius:999px;padding:10px 14px;font-size:12px;font-weight:750;
        white-space:nowrap;
      }}
      .hm-main-grid {{
        display:grid;grid-template-columns:minmax(0,.96fr) minmax(0,1.04fr);
        gap:34px;align-items:stretch;
      }}
      .hm-login-card {{
        border:1px solid #d9e2de;border-radius:12px;background:#fff;
        padding:22px 22px 20px;min-height:100%;
        box-shadow:0 8px 22px rgba(15,63,48,.035);
      }}
      .hm-login-card h1 {{
        margin:0 0 7px;font-size:22px;line-height:1.2;color:#123f32;
      }}
      .hm-copy {{ margin:0 0 16px;color:#687872;font-size:13px;line-height:1.55; }}
      label {{
        display:block;margin-top:13px;font-size:12px;font-weight:780;color:#234b3e;
      }}
      input {{
        width:100%;margin-top:7px;padding:12px 13px;border:1px solid #c8d9d2;
        border-radius:9px;font-size:15px;outline:none;background:#fff;color:#17352d;
      }}
      input:focus {{ border-color:#176b55;box-shadow:0 0 0 3px rgba(23,107,85,.10); }}
      button {{
        width:100%;margin-top:17px;padding:12px 15px;border:0;border-radius:8px;
        background:#ff4f57;color:#fff;font-size:13px;font-weight:780;cursor:pointer;
      }}
      button:hover {{ filter:brightness(.98); }}
      button:disabled {{ opacity:.66;cursor:wait; }}
      #hm-message {{
        display:none;margin:13px 0 0;padding:10px 11px;border-radius:9px;
        font-size:12px;line-height:1.45;
      }}
      #hm-message.info {{ display:block;background:#edf7f4;color:#245a48; }}
      #hm-message.error {{ display:block;background:#fdecec;color:#8e2020; }}
      #hm-progress {{ display:none;text-align:center;padding:35px 8px 22px; }}
      .hm-spinner {{
        width:30px;height:30px;margin:0 auto 13px;border:3px solid #d8ebe4;
        border-top-color:#176b55;border-radius:50%;animation:spin .8s linear infinite;
      }}
      .hm-progress-title {{ font-weight:780;color:#234b3e;font-size:15px; }}
      .hm-progress-copy {{ margin-top:6px;color:#71817b;font-size:12px; }}
      .hm-login-note {{
        margin-top:18px;padding:12px 13px;border:1px solid #cee4dc;
        border-radius:10px;background:#edf7f4;color:#315e50;font-size:12px;line-height:1.5;
      }}
      .hm-login-note strong {{ display:block;margin-bottom:2px;color:#245847; }}
      .hm-protected {{ margin-top:13px;text-align:center;color:#788780;font-size:11px; }}
      .hm-restart {{ display:none; }}
      .hm-journey-card {{
        min-height:100%;border:1px solid #dbe7e2;border-radius:14px;
        padding:26px;background:linear-gradient(145deg,#fbfdfc,#f0f8f4);
        box-shadow:0 9px 24px rgba(21,61,49,.055);
      }}
      .hm-journey-card h2 {{ margin:0 0 9px;color:#173d33;font-size:19px; }}
      .hm-journey-copy {{ margin:0 0 18px;color:#687872;font-size:13px;line-height:1.55; }}
      .hm-journey-grid {{ display:grid;grid-template-columns:1fr 1fr;gap:10px; }}
      .hm-journey-item {{
        border:1px solid #dce8e3;border-radius:10px;background:#fff;
        padding:12px;color:#34594c;font-size:12px;font-weight:720;
      }}
      .hm-feature-strip {{
        display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:20px;
      }}
      .hm-feature {{
        border:1px solid #dfe8e4;border-radius:10px;background:#fff;
        padding:12px 14px;display:flex;flex-direction:column;gap:3px;
      }}
      .hm-feature strong {{ color:#234b3e;font-size:12px; }}
      .hm-feature span {{ color:#74817d;font-size:11px; }}
      @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
      @media (max-width:800px) {{
        #hm-page {{ width:min(100% - 24px,680px);padding-top:18px; }}
        .hm-topbar {{ align-items:flex-start;flex-direction:column;margin-bottom:16px; }}
        .hm-main-grid {{ grid-template-columns:1fr;gap:16px; }}
        .hm-feature-strip {{ grid-template-columns:1fr; }}
      }}
      @media (max-width:520px) {{
        .hm-brand-name {{ font-size:26px; }}
        .hm-login-card,.hm-journey-card {{ padding:19px; }}
        .hm-journey-grid {{ grid-template-columns:1fr; }}
      }}
    </style>

    <main id="hm-page">
      <header class="hm-topbar">
        <div>
          <div class="hm-brand-name">HealthyMe</div>
          <div class="hm-brand-sub">Guided wellness assessment platform</div>
        </div>
        <div class="hm-secure-pill">Supabase OIDC · Secure access</div>
      </header>

      <section class="hm-main-grid">
        <div class="hm-login-card">
          <div id="hm-login">
            <h1>Secure Login</h1>
            <p class="hm-copy">
              Sign in with your authorised HealthyMe account. Access is granted only after
              HealthyMe verifies your active Member or Admin role.
            </p>
            <form id="hm-form">
              <label for="hm-email">Email</label>
              <input id="hm-email" type="email" autocomplete="username" required>
              <label for="hm-password">Password</label>
              <input id="hm-password" type="password" autocomplete="current-password" required>
              <button id="hm-signin" type="submit">Sign in securely</button>
            </form>

            <div class="hm-login-note">
              <strong>No public sign-up</strong>
              Supabase confirms your identity. HealthyMe then checks your active Member or Admin
              authorisation before opening the application.
            </div>
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

          <div class="hm-protected">🔒 Protected by Supabase secure authentication</div>
        </div>

        <aside class="hm-journey-card">
          <h2>Your wellness journey</h2>
          <p class="hm-journey-copy">
            A secure, expert-led path from assessment to practical wellness guidance.
          </p>
          <div class="hm-journey-grid">
            <div class="hm-journey-item">✓ Secure Supabase Login</div>
            <div class="hm-journey-item">✓ Lifestyle Assessment</div>
            <div class="hm-journey-item">✓ NSP Assessment</div>
            <div class="hm-journey-item">🔒 Expert Review</div>
          </div>
        </aside>
      </section>

      <section class="hm-feature-strip">
        <div class="hm-feature"><strong>Secure</strong><span>Supabase OIDC</span></div>
        <div class="hm-feature"><strong>Role-based</strong><span>Member / Admin</span></div>
        <div class="hm-feature"><strong>Private</strong><span>Native Streamlit session</span></div>
      </section>
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
