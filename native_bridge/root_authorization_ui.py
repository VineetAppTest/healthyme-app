import json
import os

import streamlit as st


AUTHORIZATION_BUILD = "H13R7D-minimal-wellness-authorizer-v1"
ROLLBACK_BUILD = "H13R7C-healthyme-authorizer-space-mobile-v1"
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

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 7% 4%, rgba(246,168,91,.16), transparent 22rem),
                radial-gradient(circle at 95% 10%, rgba(15,116,92,.13), transparent 23rem),
                linear-gradient(180deg,#fffaf3 0%,#f8f3e9 100%) !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stMainBlockContainer"] {
            max-width: none !important;
            padding: 1rem 2.25rem 1.75rem !important;
        }
        div[data-testid="stHtml"] { width: 100% !important; }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] {
                padding: .65rem .7rem 1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    html_document = rf"""
    <style>
      :root {{
        color-scheme:light;
        --hm-ink:#003e35;
        --hm-ink-soft:#315d52;
        --hm-green:#0f725d;
        --hm-green-dark:#095646;
        --hm-mint:#e8f5ef;
        --hm-mint-strong:#d8eee4;
        --hm-coral:#ee6b5e;
        --hm-coral-dark:#d9574d;
        --hm-gold:#cf9d42;
        --hm-gold-soft:#efd7a8;
        --hm-card:#fffdf8;
        --hm-border:#e5d2ad;
        --hm-muted:#6f7a74;
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
        padding:8px 4px 24px;
      }}
      .hm-topbar {{
        display:flex;align-items:center;justify-content:space-between;
        gap:20px;margin:0 0 18px;
      }}
      .hm-brand-wrap {{ display:flex;align-items:center;gap:12px; }}
      .hm-brand-mark {{
        width:44px;height:44px;display:grid;place-items:center;
        border:1px solid var(--hm-gold-soft);border-radius:14px;
        background:linear-gradient(145deg,#fff5df,#f7e8c8);
        font-size:23px;box-shadow:0 8px 18px rgba(91,63,18,.09);
      }}
      .hm-brand-name {{
        font-size:32px;line-height:1;font-weight:850;letter-spacing:-.7px;
        color:var(--hm-ink);
      }}
      .hm-brand-sub {{ margin-top:6px;font-size:13px;color:var(--hm-muted); }}
      .hm-secure-pill {{
        border:1px solid #b9dacc;
        background:linear-gradient(135deg,#edf8f3,#fff8e9);
        color:var(--hm-ink-soft);border-radius:999px;padding:10px 15px;
        font-size:12px;font-weight:760;white-space:nowrap;
      }}
      .hm-main-grid {{
        display:grid;grid-template-columns:minmax(0,1.04fr) minmax(0,.96fr);
        gap:22px;align-items:stretch;
      }}
      .hm-card {{
        position:relative;overflow:hidden;border:1px solid var(--hm-border);
        border-radius:18px;box-shadow:0 14px 34px rgba(65,48,19,.07);
      }}
      .hm-card::before {{
        content:"";position:absolute;inset:0 0 auto 0;height:6px;
      }}
      .hm-login-card {{
        padding:30px 31px 25px;
        background:
          radial-gradient(circle at 94% 5%,rgba(238,107,94,.08),transparent 14rem),
          rgba(255,253,248,.98);
      }}
      .hm-login-card::before {{
        background:linear-gradient(90deg,var(--hm-coral),#f4ad67);
      }}
      .hm-journey-card {{
        padding:30px;
        display:flex;
        flex-direction:column;
        background:
          radial-gradient(circle at 92% 8%,rgba(207,157,66,.14),transparent 15rem),
          radial-gradient(circle at 8% 88%,rgba(15,114,93,.11),transparent 14rem),
          linear-gradient(145deg,#eef8f3 0%,#fffaf1 65%,#f8efe0 100%);
      }}
      .hm-journey-card::before {{
        background:linear-gradient(90deg,var(--hm-green),#56a788);
      }}
      .hm-login-card h1,.hm-journey-card h2 {{
        margin:0;color:var(--hm-ink);
      }}
      .hm-login-card h1 {{
        font-size:25px;line-height:1.2;margin-bottom:9px;
      }}
      .hm-journey-card h2 {{
        font-size:22px;margin-bottom:9px;
      }}
      .hm-copy,.hm-journey-copy {{
        margin:0 0 18px;color:#5f7068;font-size:14px;line-height:1.55;
      }}
      .hm-field + .hm-field {{ margin-top:14px; }}
      label {{
        display:block;font-size:12px;font-weight:780;color:var(--hm-ink-soft);
      }}
      input {{
        width:100%;margin-top:8px;padding:14px 15px;border:1px solid #cdbf9f;
        border-radius:10px;font-size:15px;outline:none;background:#fff;color:var(--hm-ink);
      }}
      input:focus {{
        border-color:var(--hm-green);
        box-shadow:0 0 0 3px rgba(15,114,93,.12);
      }}
      button {{
        width:100%;margin-top:18px;padding:14px 16px;border:0;border-radius:10px;
        background:linear-gradient(90deg,var(--hm-coral),#f07e63);color:#fff;
        font-size:14px;font-weight:790;cursor:pointer;
        box-shadow:0 8px 18px rgba(238,107,94,.18);
      }}
      button:hover {{
        background:linear-gradient(90deg,var(--hm-coral-dark),#df6b56);
      }}
      button:disabled {{ opacity:.66;cursor:wait; }}
      #hm-message {{
        display:none;margin:14px 0 0;padding:11px 12px;border-radius:10px;
        font-size:12px;line-height:1.45;
      }}
      #hm-message.info {{
        display:block;border:1px solid #cce3da;background:var(--hm-mint);color:#245a48;
      }}
      #hm-message.error {{
        display:block;border:1px solid #efc5c5;background:#fff0ef;color:var(--hm-danger);
      }}
      #hm-progress {{ display:none;text-align:center;padding:58px 12px 42px; }}
      .hm-spinner {{
        width:34px;height:34px;margin:0 auto 14px;border:3px solid #f2d6cf;
        border-top-color:var(--hm-coral);border-radius:50%;animation:spin .8s linear infinite;
      }}
      .hm-progress-title {{ font-weight:790;color:var(--hm-ink);font-size:16px; }}
      .hm-progress-copy {{ margin-top:7px;color:var(--hm-muted);font-size:13px; }}
      .hm-login-note {{
        margin-top:18px;padding:13px 14px;border:1px solid #cce3da;border-radius:11px;
        background:linear-gradient(135deg,var(--hm-mint),#f4fbf7);
        color:#315e50;font-size:12px;line-height:1.5;
      }}
      .hm-login-note strong {{
        display:block;margin-bottom:3px;color:var(--hm-ink);
      }}
      .hm-protected {{ margin-top:14px;color:#788078;font-size:11px; }}
      .hm-restart {{ display:none; }}

      .hm-visual {{
        position:relative;
        flex:1;
        min-height:210px;
        margin:4px 0 20px;
        display:grid;
        place-items:center;
        overflow:hidden;
        border-radius:18px;
        border:1px solid rgba(15,114,93,.14);
        background:
          radial-gradient(circle at 50% 55%,rgba(255,255,255,.92) 0 24%,transparent 25%),
          radial-gradient(circle at 34% 38%,rgba(238,107,94,.16) 0 15%,transparent 16%),
          radial-gradient(circle at 70% 34%,rgba(207,157,66,.18) 0 17%,transparent 18%),
          radial-gradient(circle at 68% 72%,rgba(15,114,93,.14) 0 18%,transparent 19%),
          linear-gradient(145deg,rgba(255,255,255,.60),rgba(232,245,239,.58));
      }}
      .hm-visual::before,.hm-visual::after {{
        content:"";
        position:absolute;
        width:150px;height:68px;
        border-radius:100% 0 100% 0;
        background:linear-gradient(135deg,rgba(15,114,93,.20),rgba(86,167,136,.08));
        transform:rotate(-18deg);
      }}
      .hm-visual::before {{ left:13%;bottom:10%; }}
      .hm-visual::after {{
        right:11%;top:9%;
        transform:rotate(162deg);
        background:linear-gradient(135deg,rgba(238,107,94,.16),rgba(244,173,103,.08));
      }}
      .hm-visual-core {{
        position:relative;z-index:2;
        width:150px;height:150px;
        display:grid;place-items:center;text-align:center;
        border-radius:50%;
        border:1px solid rgba(15,114,93,.18);
        background:rgba(255,253,248,.94);
        box-shadow:0 18px 40px rgba(15,78,61,.10);
        padding:20px;
      }}
      .hm-visual-icon {{
        font-size:34px;line-height:1;margin-bottom:8px;
      }}
      .hm-visual-title {{
        color:var(--hm-ink);font-size:15px;font-weight:820;line-height:1.25;
      }}
      .hm-visual-sub {{
        margin-top:5px;color:#6c7771;font-size:10px;line-height:1.35;
      }}
      .hm-orbit-dot {{
        position:absolute;z-index:3;
        width:14px;height:14px;border-radius:50%;
        box-shadow:0 0 0 7px rgba(255,255,255,.48);
      }}
      .hm-orbit-dot.one {{ left:22%;top:24%;background:var(--hm-coral); }}
      .hm-orbit-dot.two {{ right:20%;top:27%;background:var(--hm-gold); }}
      .hm-orbit-dot.three {{ right:24%;bottom:20%;background:var(--hm-green); }}

      .hm-focus-grid {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:12px;
      }}
      .hm-focus-item {{
        min-height:86px;
        display:flex;
        align-items:flex-start;
        gap:12px;
        padding:16px;
        border:1px solid rgba(15,114,93,.18);
        border-radius:14px;
        background:rgba(255,255,255,.78);
      }}
      .hm-focus-icon {{
        flex:0 0 auto;
        width:34px;height:34px;
        display:grid;place-items:center;
        border-radius:11px;
        background:var(--hm-mint-strong);
        color:var(--hm-green-dark);
        font-size:16px;
      }}
      .hm-focus-item strong {{
        display:block;color:var(--hm-ink);font-size:13px;line-height:1.3;
      }}
      .hm-focus-item span {{
        display:block;margin-top:5px;color:#6d776f;font-size:11px;line-height:1.4;
      }}

      @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
      @media (max-width:900px) {{
        #hm-page {{ max-width:760px; }}
        .hm-topbar {{ align-items:flex-start;flex-direction:column;margin-bottom:15px; }}
        .hm-main-grid {{ grid-template-columns:1fr;gap:16px; }}
        .hm-journey-card {{ min-height:auto; }}
        .hm-visual {{ min-height:190px; }}
      }}
      @media (max-width:620px) {{
        #hm-page {{ padding:4px 0 16px; }}
        .hm-brand-name {{ font-size:27px; }}
        .hm-brand-mark {{ width:40px;height:40px;font-size:21px; }}
        .hm-secure-pill {{ width:100%;text-align:center;padding:8px 12px; }}
        .hm-login-card,.hm-journey-card {{
          padding:22px 20px 20px;border-radius:15px;
        }}
        .hm-login-card h1 {{ font-size:22px; }}
        .hm-journey-card h2 {{ font-size:20px; }}
        .hm-copy,.hm-journey-copy {{ font-size:13px; }}
        .hm-field + .hm-field {{ margin-top:13px; }}
        .hm-visual {{ min-height:155px;margin-bottom:16px; }}
        .hm-visual-core {{ width:124px;height:124px;padding:16px; }}
        .hm-visual-icon {{ font-size:28px;margin-bottom:6px; }}
        .hm-visual-title {{ font-size:13px; }}
        .hm-visual::before,.hm-visual::after {{ width:105px;height:48px; }}
        .hm-focus-grid {{ grid-template-columns:1fr; }}
        .hm-focus-item {{ min-height:auto; }}
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
        <div class="hm-card hm-login-card">
          <div id="hm-login">
            <h1>Secure Login</h1>
            <p class="hm-copy">
              Sign in with your authorised HealthyMe account. Access is granted only after
              HealthyMe verifies your active Member or Admin role.
            </p>

            <form id="hm-form">
              <div class="hm-field">
                <label for="hm-email">Email</label>
                <input id="hm-email" type="email" autocomplete="username" required>
              </div>
              <div class="hm-field">
                <label for="hm-password">Password</label>
                <input id="hm-password" type="password" autocomplete="current-password" required>
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

        <aside class="hm-card hm-journey-card">
          <div>
            <h2>Your wellness journey</h2>
            <p class="hm-journey-copy">
              A focused path from assessment to practical wellness guidance.
            </p>
          </div>

          <div class="hm-visual" aria-hidden="true">
            <span class="hm-orbit-dot one"></span>
            <span class="hm-orbit-dot two"></span>
            <span class="hm-orbit-dot three"></span>
            <div class="hm-visual-core">
              <div>
                <div class="hm-visual-icon">🌿</div>
                <div class="hm-visual-title">Small steps.<br>Clear guidance.</div>
                <div class="hm-visual-sub">Designed around your wellness journey</div>
              </div>
            </div>
          </div>

          <div class="hm-focus-grid">
            <div class="hm-focus-item">
              <span class="hm-focus-icon">✓</span>
              <div>
                <strong>Assessment</strong>
                <span>Lifestyle and NSP assessment in one guided journey.</span>
              </div>
            </div>
            <div class="hm-focus-item">
              <span class="hm-focus-icon">✦</span>
              <div>
                <strong>Expert guidance</strong>
                <span>Review and practical next steps based on your progress.</span>
              </div>
            </div>
          </div>
        </aside>
      </section>
    </main>

    <script type="module">
      import {{ createClient }} from "https://esm.sh/@supabase/supabase-js@2.105.3";

      const authorizationId = {json.dumps(authorization_id)};
      const clientLoginUrl = {json.dumps(client_login_url)};
      const authorizationMarkerPrefix = "hm_h13r2_oauth_reload:";
      const authStepTimeoutMs = 45000;
      const loginPanel = document.getElementById("hm-login");
      const progressPanel = document.getElementById("hm-progress");
      const restartPanel = document.getElementById("hm-restart");
      const messageBox = document.getElementById("hm-message");
      const signInButton = document.getElementById("hm-signin");
      let busy = false;

      function createFreshSupabaseClient() {{
        return createClient(
          {json.dumps(supabase_url)},
          {json.dumps(publishable_key)},
          {{auth:{{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false}}}}
        );
      }}

      function resetPriorAuthorizationMarkers() {{
        try {{
          const storage = window.top?.sessionStorage || window.sessionStorage;
          for (let index = storage.length - 1; index >= 0; index -= 1) {{
            const key = String(storage.key(index) || "");
            if (key.startsWith(authorizationMarkerPrefix)) storage.removeItem(key);
          }}
        }} catch (_error) {{}}
      }}

      function withTimeout(promise, step) {{
        let timeoutId;
        const timeout = new Promise((_, reject) => {{
          timeoutId = window.setTimeout(() => {{
            const error = new Error(`${{step}} took too long. Please start again.`);
            error.name = "HealthyMeAuthTimeout";
            reject(error);
          }}, authStepTimeoutMs);
        }});
        return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timeoutId));
      }}

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

      function requireRestart(message="This secure login request has expired. Please start again.") {{
        loginPanel.style.display = "none";
        progressPanel.style.display = "none";
        restartPanel.style.display = "block";
        showMessage(message, "error");
      }}

      async function approveAndContinue(supabase) {{
        const {{data:details,error:detailsError}} =
          await withTimeout(
            supabase.auth.oauth.getAuthorizationDetails(authorizationId),
            "Secure authorization validation"
          );
        if (detailsError) throw detailsError;

        if (details?.redirect_url && !("authorization_id" in details)) {{
          redirectTop(details.redirect_url);
          return;
        }}

        const {{data,error}} = await withTimeout(
          supabase.auth.oauth.approveAuthorization(authorizationId),
          "HealthyMe access authorization"
        );
        if (error) throw error;
        redirectTop(data.redirect_url);
      }}

      resetPriorAuthorizationMarkers();

      document.getElementById("hm-form").addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (busy) return;
        busy = true;
        signInButton.disabled = true;
        showMessage("Confirming your identity…", "info");

        const email = document.getElementById("hm-email").value.trim();
        const passwordInput = document.getElementById("hm-password");
        const password = passwordInput.value;
        const supabase = createFreshSupabaseClient();
        try {{
          const {{error}} = await withTimeout(
            supabase.auth.signInWithPassword({{email,password}}),
            "Credential confirmation"
          );
          passwordInput.value = "";

          if (error) throw error;

          showProgress();
          await approveAndContinue(supabase);
        }} catch (error) {{
          passwordInput.value = "";
          if (isStale(error) || error?.name === "HealthyMeAuthTimeout") {{
            try {{ await supabase.auth.signOut({{scope:"local"}}); }} catch (_error) {{}}
            requireRestart(
              error?.name === "HealthyMeAuthTimeout"
                ? "Secure login took too long. Please start a fresh login."
                : "This secure login request has expired. Please start again."
            );
            return;
          }}
          loginPanel.style.display = "block";
          progressPanel.style.display = "none";
          showMessage(
            error?.message || "Unable to complete secure login. Please try again.",
            "error"
          );
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
