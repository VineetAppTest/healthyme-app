import json
import os

import streamlit as st

from components.ui_common import apply_luxe_theme, inject_global_styles


st.set_page_config(
    page_title="HealthyMe OAuth Consent",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


def _secret(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
        if value is not None:
            return str(value).strip()
        for section in ("supabase", "healthyme", "auth"):
            block = st.secrets.get(section)
            if block:
                candidate = block.get(name) or block.get(name.lower())
                if candidate is not None:
                    return str(candidate).strip()
    except Exception:
        pass
    return ""


authorization_id = str(st.query_params.get("authorization_id") or "").strip()
supabase_url = _secret("SUPABASE_URL")
publishable_key = _secret("SUPABASE_ANON_KEY") or _secret("SUPABASE_PUBLISHABLE_KEY")

st.markdown("## HealthyMe authorization")
st.caption(
    "H13O2 v8 top-level authorization — this page is used only by the Supabase OAuth Server proof of concept."
)

if not authorization_id:
    st.error("The authorization request is missing or has expired. Start a fresh login.")
    st.page_link("pages/01_Login.py", label="Return to Login", icon="↩️")
    st.stop()

if not supabase_url or not publishable_key:
    st.error(
        "The temporary app is missing SUPABASE_URL and a Supabase publishable/anon key."
    )
    st.stop()

# Streamlit 1.59 executes this trusted HTML directly in the page DOM when
# unsafe_allow_javascript=True. It is intentionally not rendered in an iframe because
# the Supabase OAuth authorization request and the temporary authenticated Supabase
# session must live in the same top-level browser context.
html_document = f"""
<style>
  #hm-oauth-root {{
    max-width: 560px; margin: 16px auto; padding: 24px;
    background: white; border: 1px solid #d7e5df; border-radius: 18px;
    box-shadow: 0 10px 30px rgba(20,60,48,.08);
    font-family: Inter, Arial, sans-serif; color: #17352d;
  }}
  #hm-oauth-root h2 {{ margin: 0 0 6px; }}
  #hm-oauth-root p {{ color: #5d746c; line-height: 1.45; }}
  #hm-oauth-root label {{ display: block; margin-top: 14px; font-weight: 700; }}
  #hm-oauth-root input {{
    width: 100%; box-sizing: border-box; padding: 12px; margin-top: 6px;
    border: 1px solid #c7d9d2; border-radius: 10px; font-size: 16px;
  }}
  #hm-oauth-root button {{
    padding: 12px 16px; border: 0; border-radius: 10px;
    font-size: 15px; font-weight: 700; cursor: pointer;
  }}
  #hm-oauth-root button:disabled {{ opacity: .65; cursor: wait; }}
  #hm-oauth-root .primary {{ width: 100%; margin-top: 18px; background: #176b55; color: white; }}
  #hm-oauth-root .secondary {{ background: #e9f1ee; color: #17483b; }}
  #hm-oauth-root .danger {{ background: #f8e9e9; color: #8b2020; }}
  #hm-oauth-root .row {{ display: flex; gap: 10px; margin-top: 18px; }}
  #hm-oauth-root .row button {{ flex: 1; }}
  #hm-oauth-root .message {{ margin: 14px 0; padding: 11px; border-radius: 10px; display: none; }}
  #hm-oauth-root .error {{ display: block; background: #fdecec; color: #8e2020; }}
  #hm-oauth-root .info {{ display: block; background: #eaf5f8; color: #0f4c5c; }}
  #hm-oauth-root .scope {{
    display: inline-block; margin: 4px 5px 0 0; padding: 6px 9px;
    background: #edf5f2; border-radius: 999px; font-size: 13px; font-weight: 700;
  }}
  #hm-oauth-consent-panel, #hm-oauth-restart-panel {{ display: none; }}
</style>

<main id="hm-oauth-root">
  <h2>HealthyMe secure authorization</h2>
  <p>Sign in with your existing Supabase account to continue the test.</p>
  <div id="hm-oauth-message" class="message"></div>

  <section id="hm-oauth-login-panel">
    <form id="hm-oauth-login-form">
      <label for="hm-oauth-email">Email</label>
      <input id="hm-oauth-email" type="email" required autocomplete="username">
      <label for="hm-oauth-password">Password</label>
      <input id="hm-oauth-password" type="password" required autocomplete="current-password">
      <button id="hm-oauth-signin" class="primary" type="submit">Sign in and review access</button>
    </form>
  </section>

  <section id="hm-oauth-consent-panel">
    <h3 id="hm-oauth-client-name">Authorize HealthyMe</h3>
    <p>The application is requesting the following identity information:</p>
    <div id="hm-oauth-scopes"></div>
    <div class="row">
      <button id="hm-oauth-deny" class="danger" type="button">Deny</button>
      <button id="hm-oauth-approve" class="secondary" type="button">Approve</button>
    </div>
  </section>

  <section id="hm-oauth-restart-panel">
    <p>This authorization request is no longer valid. No password retry can repair an expired request.</p>
    <button id="hm-oauth-restart" class="primary" type="button">Start a fresh login</button>
  </section>
</main>

<script type="module">
  import {{ createClient }} from "https://esm.sh/@supabase/supabase-js@2.105.3";

  const supabaseUrl = {json.dumps(supabase_url)};
  const publishableKey = {json.dumps(publishable_key)};
  const authorizationId = {json.dumps(authorization_id)};

  const supabase = createClient(supabaseUrl, publishableKey, {{
    auth: {{
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false
    }}
  }});

  const loginPanel = document.getElementById("hm-oauth-login-panel");
  const consentPanel = document.getElementById("hm-oauth-consent-panel");
  const restartPanel = document.getElementById("hm-oauth-restart-panel");
  const messageBox = document.getElementById("hm-oauth-message");
  const clientName = document.getElementById("hm-oauth-client-name");
  const scopesBox = document.getElementById("hm-oauth-scopes");
  const signInButton = document.getElementById("hm-oauth-signin");
  let submissionInProgress = false;

  function showMessage(text, level = "info") {{
    messageBox.textContent = text;
    messageBox.className = `message ${{level}}`;
  }}

  function redirectTop(url) {{
    window.location.replace(url);
  }}

  function isStaleAuthorization(error) {{
    const message = String(error?.message || error || "").toLowerCase();
    return message.includes("authorization not found")
      || message.includes("invalid authorization")
      || message.includes("authorization request cannot be processed");
  }}

  function showRestartRequired() {{
    loginPanel.style.display = "none";
    consentPanel.style.display = "none";
    restartPanel.style.display = "block";
    showMessage(
      "This authorization request expired or was already consumed. Start a fresh login; do not re-enter your password on this page.",
      "error"
    );
  }}

  async function loadAuthorizationDetails() {{
    const {{ data, error }} =
      await supabase.auth.oauth.getAuthorizationDetails(authorizationId);

    if (error) throw error;
    if (data?.redirect_url && !("authorization_id" in data)) {{
      redirectTop(data.redirect_url);
      return;
    }}

    const client = data?.client || {{}};
    clientName.textContent = `Authorize ${{client.name || "HealthyMe"}}`;
    const rawScope = data?.scope || "openid email profile";
    scopesBox.innerHTML = "";
    rawScope.split(/\s+/).filter(Boolean).forEach((scope) => {{
      const pill = document.createElement("span");
      pill.className = "scope";
      pill.textContent = scope;
      scopesBox.appendChild(pill);
    }});

    loginPanel.style.display = "none";
    consentPanel.style.display = "block";
    showMessage("Identity confirmed. Review and approve the requested access.", "info");
  }}

  document.getElementById("hm-oauth-login-form").addEventListener("submit", async (event) => {{
    event.preventDefault();
    if (submissionInProgress) return;
    submissionInProgress = true;
    signInButton.disabled = true;
    showMessage("Confirming your Supabase identity…", "info");

    const email = document.getElementById("hm-oauth-email").value.trim();
    const password = document.getElementById("hm-oauth-password").value;

    const {{ error }} = await supabase.auth.signInWithPassword({{ email, password }});
    document.getElementById("hm-oauth-password").value = "";

    if (error) {{
      showMessage(error.message || "Supabase login failed.", "error");
      submissionInProgress = false;
      signInButton.disabled = false;
      return;
    }}

    try {{
      await loadAuthorizationDetails();
    }} catch (error) {{
      if (isStaleAuthorization(error)) {{
        try {{ await supabase.auth.signOut(); }} catch (_signOutError) {{}}
        showRestartRequired();
        return;
      }}
      showMessage(error?.message || "Unable to load the authorization request.", "error");
      submissionInProgress = false;
      signInButton.disabled = false;
    }}
  }});

  document.getElementById("hm-oauth-approve").addEventListener("click", async () => {{
    showMessage("Approving access…", "info");
    const {{ data, error }} =
      await supabase.auth.oauth.approveAuthorization(authorizationId);
    if (error) {{
      if (isStaleAuthorization(error)) {{
        showRestartRequired();
        return;
      }}
      showMessage(error.message || "Approval failed.", "error");
      return;
    }}
    redirectTop(data.redirect_url);
  }});

  document.getElementById("hm-oauth-deny").addEventListener("click", async () => {{
    showMessage("Denying access…", "info");
    const {{ data, error }} =
      await supabase.auth.oauth.denyAuthorization(authorizationId);
    if (error) {{
      if (isStaleAuthorization(error)) {{
        showRestartRequired();
        return;
      }}
      showMessage(error.message || "Unable to deny the request.", "error");
      return;
    }}
    redirectTop(data.redirect_url);
  }});

  document.getElementById("hm-oauth-restart").addEventListener("click", () => {{
    redirectTop("/Login");
  }});
</script>
"""

st.html(html_document, unsafe_allow_javascript=True)
st.stop()
