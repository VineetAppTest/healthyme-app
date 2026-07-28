import json
import os

import streamlit as st


AUTHORIZATION_BUILD = "H13R7A-healthyme-authorizer-width-palette-v1"
ROLLBACK_BUILD = "H13R7-healthyme-authorizer-ux-v1"
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
    # Preserve the accepted callback cleanup. Once Streamlit has created the
    # native identity, the consumed one-time authorization parameter is removed.
    if _native_identity_present():
        st.query_params.clear()
        st.rerun()

    supabase_url = _secret("SUPABASE_URL")
    publishable_key = _secret("SUPABASE_ANON_KEY") or _secret(
        "SUPABASE_PUBLISHABLE_KEY"
    )
    client_login_url = _secret("AUTH_CLIENT_LOGIN_URL", DEFAULT_CLIENT_LOGIN_URL)

    st.set_page_config(
        page_title="HealthyMe Login",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if not authorization_id:
        st.error("This secure login request has expired or is incomplete.")
        st.link_button(
            "Return to HealthyMe login",
            client_login_url,
            use_container_width=True,
        )
        st.stop()

    if not supabase_url or not publishable_key:
        st.error("HealthyMe secure login is temporarily unavailable.")
        with st.expander("Technical details", expanded=False):
            st.code("SUPABASE_URL and a Supabase publishable key are required.")
            st.code(AUTHORIZATION_BUILD)
        st.stop()

    # The authorizer is rendered inside the Streamlit shell. Remove the default
    # centred-page constraint so the accepted HealthyMe login composition can use
    # the available browser width.
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 11% 10%, rgba(220, 190, 121, .12), transparent 24rem),
                linear-gradient(180deg, #fffaf1 0%, #fbf5e9 100%) !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: none !important;
            padding: 1.15rem 2.5rem 2rem !important;
        }
        div[data-testid="stHtml"] {
            width: 100% !important;
        }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] {
                padding: .75rem .85rem 1.25rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    html_document = rf"""
    <style>
      :root {{
        color-scheme: light;
        --hm-ink:#003f35;
        --hm-ink-soft:#315c50;
        --hm-green:#0e6a56;
        --hm-green-dark:#075244;
        --hm-cream:#fffaf1;
        --hm-card:#fffdf8;
        --hm-mint:#eef7f2;
        --hm-gold:#c99a3d;
        --hm-gold-soft:#ead7ae;
        --hm-border:#e7d8bb;
        --hm-muted:#6d7a73;
        --hm-danger:#a93636;
      }}
      * {{ box-sizing:border-box; }}
      html,body {{
        margin:0;padding:0;background:transparent;
        font-family:Inter,Arial,sans-serif;color:var(--hm-ink);
      }}
      body {{ min-height:100vh; }}
      #hm-page {{
        width:100%;
        max-width:1240px;
        margin:0 auto;
        padding:10px 4px 28px;
      }}
      .hm-topbar {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:24px;
        margin:0 0 20px;
        padding:0 2px;
      }}
      .hm-brand-wrap {{
        display:flex;
        align-items:center;
        gap:12px;
      }}
      .hm-brand-mark {{
        width:42px;
        height:42px;
        display:grid;
        place-items:center;
        border:1px solid var(--hm-gold-soft);
        border-radius:13px;
        background:#f7edd7;
        font-size:22px;
        box-shadow:0 5px 14px rgba(83,58,18,.07);
      }}
      .hm-brand-name {{
        font-size:31px;
        line-height:1;
        font-weight:850;
        letter-spacing:-.7px;
        color:var(--hm-ink);
      }}
      .hm-brand-sub {{
        margin-top:6px;
        font-size:13px;
        color:var(--hm-muted);
      }}
      .hm-secure-pill {{
        border:1px solid var(--hm-gold-soft);
        background:#fff8e8;
        color:var(--hm-ink-soft);
        border-radius:999px;
        padding:10px 15px;
        font-size:12px;
        font-weight:760;
        white-space:nowrap;
      }}
      .hm-main-grid {{
        display:grid;
        grid-template-columns:minmax(0,1.07fr) minmax(0,.93fr);
        gap:22px;
        align-items:stretch;
      }}
      .hm-login-card,
      .hm-journey-card {{
        border:1px solid var(--hm-border);
        border-radius:17px;
        background:rgba(255,253,248,.96);
        box-shadow:0 12px 30px rgba(70,52,19,.055);
      }}
      .hm-login-card {{
        padding:28px 30px 24px;
      }}
      .hm-login-card h1 {{
        margin:0 0 8px;
        font-size:25px;
        line-height:1.2;
        color:var(--hm-ink);
      }}
      .hm-copy {{
        max-width:620px;
        margin:0 0 18px;
        color:#5f7068;
        font-size:14px;
        line-height:1.55;
      }}
      .hm-form-grid {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:16px;
      }}
      .hm-field {{ min-width:0; }}
      label {{
        display:block;
        margin-top:0;
        font-size:12px;
        font-weight:780;
        color:var(--hm-ink-soft);
      }}
      input {{
        width:100%;
        margin-top:8px;
        padding:14px 15px;
        border:1px solid #cdbf9f;
        border-radius:10px;
        font-size:15px;
        outline:none;
        background:#fff;
        color:var(--hm-ink);
      }}
      input:focus {{
        border-color:var(--hm-green);
        box-shadow:0 0 0 3px rgba(14,106,86,.12);
      }}
      button {{
        width:100%;
        margin-top:18px;
        padding:14px 16px;
        border:0;
        border-radius:10px;
        background:var(--hm-green);
        color:#fff;
        font-size:14px;
        font-weight:790;
        cursor:pointer;
        box-shadow:0 7px 16px rgba(14,106,86,.14);
      }}
      button:hover {{ background:var(--hm-green-dark); }}
      button:disabled {{ opacity:.66;cursor:wait; }}
      #hm-message {{
        display:none;
        margin:14px 0 0;
        padding:11px 12px;
        border-radius:10px;
        font-size:12px;
        line-height:1.45;
      }}
      #hm-message.info {{
        display:block;
        border:1px solid #cce3da;
        background:var(--hm-mint);
        color:#245a48;
      }}
      #hm-message.error {{
        display:block;
        border:1px solid #efc5c5;
        background:#fff0ef;
        color:var(--hm-danger);
      }}
      #hm-progress {{
        display:none;
        text-align:center;
        padding:54px 12px 40px;
      }}
      .hm-spinner {{
        width:34px;
        height:34px;
        margin:0 auto 14px;
        border:3px solid #d9eadf;
        border-top-color:var(--hm-green);
        border-radius:50%;
        animation:spin .8s linear infinite;
      }}
      .hm-progress-title {{
        font-weight:790;
        color:var(--hm-ink);
        font-size:16px;
      }}
      .hm-progress-copy {{
        margin-top:7px;
        color:var(--hm-muted);
        font-size:13px;
      }}
      .hm-login-note {{
        margin-top:18px;
        padding:13px 14px;
        border:1px solid #d7e5de;
        border-radius:11px;
        background:var(--hm-mint);
        color:#315e50;
        font-size:12px;
        line-height:1.5;
      }}
      .hm-login-note strong {{
        display:block;
        margin-bottom:3px;
        color:var(--hm-ink);
      }}
      .hm-protected {{
        margin-top:14px;
        color:#788078;
        font-size:11px;
      }}
      .hm-restart {{ display:none; }}
      .hm-journey-card {{
        padding:30px;
        background:
          radial-gradient(circle at 88% 18%, rgba(205,162,79,.13), transparent 14rem),
          linear-gradient(145deg,#fffdf8,#f4f0e5);
      }}
      .hm-journey-card h2 {{
        margin:0 0 10px;
        color:var(--hm-ink);
        font-size:21px;
      }}
      .hm-journey-copy {{
        margin:0 0 20px;
        color:#62736b;
        font-size:14px;
        line-height:1.55;
      }}
      .hm-journey-grid {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:12px;
      }}
      .hm-journey-item {{
        min-height:70px;
        display:flex;
        align-items:center;
        border:1px solid #e1d5bd;
        border-radius:11px;
        background:#fffdf9;
        padding:14px;
        color:var(--hm-ink-soft);
        font-size:12px;
        font-weight:740;
      }}
      .hm-feature-strip {{
        display:grid;
        grid-template-columns:repeat(3,1fr);
        gap:12px;
        margin-top:18px;
      }}
      .hm-feature {{
        border:1px solid var(--hm-border);
        border-radius:11px;
        background:rgba(255,253,248,.94);
        padding:13px 15px;
        display:flex;
        flex-direction:column;
        gap:4px;
      }}
      .hm-feature strong {{
        color:var(--hm-ink);
        font-size:12px;
      }}
      .hm-feature span {{
        color:#737d77;
        font-size:11px;
      }}
      @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
      @media (max-width:900px) {{
        #hm-page {{ max-width:760px; }}
        .hm-topbar {{
          align-items:flex-start;
          flex-direction:column;
          margin-bottom:16px;
        }}
        .hm-main-grid {{
          grid-template-columns:1fr;
          gap:16px;
        }}
      }}
      @media (max-width:620px) {{
        .hm-brand-name {{ font-size:27px; }}
        .hm-secure-pill {{ padding:8px 12px; }}
        .hm-login-card,
        .hm-journey-card {{ padding:20px; }}
        .hm-form-grid {{ grid-template-columns:1fr;gap:13px; }}
        .hm-journey-grid {{ grid-template-columns:1fr; }}
        .hm-feature-strip {{ grid-template-columns:1fr; }}
      }}
    </style>

    <main id="hm-page">
      <header class="hm-topbar">
        <div class="hm-brand-wrap">
          <div class="hm-brand-mark">🌿</div>
          <div>
            <div class="hm-brand-name">HealthyMe</div>
            <div class="hm-brand-sub">Guided wellness assessment platform</div>
          </div>
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
              <div class="hm-form-grid">
                <div class="hm-field">
                  <label for="hm-email">Email</label>
                  <input id="hm-email" type="email" autocomplete="username" required>
                </div>
                <div class="hm-field">
                  <label for="hm-password">Password</label>
                  <input id="hm-password" type="password" autocomplete="current-password" required>
                </div>
              </div>
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
