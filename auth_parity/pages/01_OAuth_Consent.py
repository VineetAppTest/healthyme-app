import json
import os

import streamlit as st


BUILD = "H13Q1-supabase-oauth-consent-v2-native-route-guard"


def _secret(name: str) -> str:
    value = os.environ.get(name)
    if value is not None:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value or "").strip()


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


st.set_page_config(
    page_title="HealthyMe Supabase Authorization Test",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# The consent URL is a one-time authorization route. If Streamlit has already
# restored the native identity, never leave the browser parked on or refreshing
# the old authorization_id URL; return to the app root instead.
if _native_identity_present():
    st.html(
        '<script>window.location.replace("/");</script>',
        unsafe_allow_javascript=True,
    )
    st.stop()

provider = _secret("AUTH_TEST_PROVIDER").lower()
authorization_id = str(st.query_params.get("authorization_id") or "").strip()
supabase_url = _secret("SUPABASE_URL")
publishable_key = _secret("SUPABASE_ANON_KEY") or _secret("SUPABASE_PUBLISHABLE_KEY")

st.title("Supabase OIDC authorization test")
st.caption(
    "This page exists only for the Supabase OAuth Server comparison. "
    "It performs no HealthyMe role lookup and stores no tokens in localStorage."
)
st.code(BUILD)

if provider != "supabaseoidc":
    st.error("This authorization page is enabled only when AUTH_TEST_PROVIDER='supabaseoidc'.")
    st.stop()

if not authorization_id:
    st.error("The authorization request is missing or expired. Return to the app root and start a fresh login.")
    st.stop()

if not supabase_url or not publishable_key:
    st.error("SUPABASE_URL and a Supabase publishable/anon key are required for this test.")
    st.stop()

html_document = rf"""
<style>
  #h13q1-root {{
    max-width: 560px; margin: 12px auto; padding: 24px;
    border: 1px solid #d7e5df; border-radius: 16px; background: #fff;
    font-family: Arial, sans-serif; color: #17352d;
  }}
  #h13q1-root label {{ display:block; margin-top:14px; font-weight:700; }}
  #h13q1-root input {{
    width:100%; box-sizing:border-box; margin-top:6px; padding:12px;
    border:1px solid #c7d9d2; border-radius:10px; font-size:16px;
  }}
  #h13q1-root button {{
    padding:12px 16px; border:0; border-radius:10px; font-weight:700; cursor:pointer;
  }}
  #h13q1-root button:disabled {{ opacity:.65; cursor:wait; }}
  #h13q1-root .primary {{ width:100%; margin-top:18px; background:#176b55; color:#fff; }}
  #h13q1-root .row {{ display:flex; gap:10px; margin-top:18px; }}
  #h13q1-root .row button {{ flex:1; }}
  #h13q1-root .approve {{ background:#dff2ea; color:#17483b; }}
  #h13q1-root .deny {{ background:#f8e9e9; color:#8b2020; }}
  #h13q1-message {{ display:none; margin:14px 0; padding:11px; border-radius:10px; }}
  #h13q1-message.info {{ display:block; background:#eaf5f8; color:#0f4c5c; }}
  #h13q1-message.error {{ display:block; background:#fdecec; color:#8e2020; }}
  #h13q1-consent, #h13q1-restart {{ display:none; }}
  .h13q1-scope {{
    display:inline-block; margin:4px 5px 0 0; padding:6px 9px;
    background:#edf5f2; border-radius:999px; font-size:13px; font-weight:700;
  }}
</style>

<main id="h13q1-root">
  <h2>Supabase identity authorization</h2>
  <p>Sign in with the existing Supabase account, then approve the native OIDC identity request.</p>
  <div id="h13q1-message"></div>

  <section id="h13q1-login">
    <form id="h13q1-form">
      <label for="h13q1-email">Email</label>
      <input id="h13q1-email" type="email" autocomplete="username" required>
      <label for="h13q1-password">Password</label>
      <input id="h13q1-password" type="password" autocomplete="current-password" required>
      <button id="h13q1-signin" class="primary" type="submit">Sign in and review access</button>
    </form>
  </section>

  <section id="h13q1-consent">
    <h3 id="h13q1-client">Authorize identity test</h3>
    <p>The application requests only the following OIDC identity scopes:</p>
    <div id="h13q1-scopes"></div>
    <div class="row">
      <button id="h13q1-deny" class="deny" type="button">Deny</button>
      <button id="h13q1-approve" class="approve" type="button">Approve</button>
    </div>
  </section>

  <section id="h13q1-restart">
    <p>The authorization request expired or was already consumed.</p>
    <button id="h13q1-restart-button" class="primary" type="button">Start a fresh login</button>
  </section>
</main>

<script type="module">
  import {{ createClient }} from "https://esm.sh/@supabase/supabase-js@2.105.3";

  const supabase = createClient(
    {json.dumps(supabase_url)},
    {json.dumps(publishable_key)},
    {{ auth: {{ persistSession:false, autoRefreshToken:false, detectSessionInUrl:false }} }}
  );
  const authorizationId = {json.dumps(authorization_id)};
  const loginPanel = document.getElementById("h13q1-login");
  const consentPanel = document.getElementById("h13q1-consent");
  const restartPanel = document.getElementById("h13q1-restart");
  const messageBox = document.getElementById("h13q1-message");
  const signInButton = document.getElementById("h13q1-signin");
  let busy = false;

  function showMessage(text, level="info") {{
    messageBox.textContent = text;
    messageBox.className = level;
  }}

  function redirectTop(url) {{
    window.location.replace(url);
  }}

  function isStale(error) {{
    const message = String(error?.message || error || "").toLowerCase();
    return message.includes("authorization not found")
      || message.includes("invalid authorization")
      || message.includes("authorization request cannot be processed");
  }}

  function requireRestart() {{
    loginPanel.style.display = "none";
    consentPanel.style.display = "none";
    restartPanel.style.display = "block";
    showMessage("This authorization request is no longer valid. Start a fresh login.", "error");
  }}

  async function loadDetails() {{
    const {{ data, error }} = await supabase.auth.oauth.getAuthorizationDetails(authorizationId);
    if (error) throw error;
    if (data?.redirect_url && !("authorization_id" in data)) {{
      redirectTop(data.redirect_url);
      return;
    }}
    document.getElementById("h13q1-client").textContent =
      `Authorize ${{data?.client?.name || "identity test"}}`;
    const scopes = String(data?.scope || "openid email profile").split(/\s+/).filter(Boolean);
    const scopesBox = document.getElementById("h13q1-scopes");
    scopesBox.innerHTML = "";
    for (const scope of scopes) {{
      const pill = document.createElement("span");
      pill.className = "h13q1-scope";
      pill.textContent = scope;
      scopesBox.appendChild(pill);
    }}
    loginPanel.style.display = "none";
    consentPanel.style.display = "block";
    showMessage("Identity confirmed. Review and approve the request.", "info");
  }}

  document.getElementById("h13q1-form").addEventListener("submit", async (event) => {{
    event.preventDefault();
    if (busy) return;
    busy = true;
    signInButton.disabled = true;
    showMessage("Confirming the Supabase identity…", "info");
    const email = document.getElementById("h13q1-email").value.trim();
    const passwordInput = document.getElementById("h13q1-password");
    const {{ error }} = await supabase.auth.signInWithPassword({{ email, password:passwordInput.value }});
    passwordInput.value = "";
    if (error) {{
      showMessage(error.message || "Supabase sign-in failed.", "error");
      busy = false;
      signInButton.disabled = false;
      return;
    }}
    try {{
      await loadDetails();
    }} catch (error) {{
      if (isStale(error)) {{
        try {{ await supabase.auth.signOut(); }} catch (_error) {{}}
        requireRestart();
        return;
      }}
      showMessage(error?.message || "Unable to load the authorization request.", "error");
      busy = false;
      signInButton.disabled = false;
    }}
  }});

  document.getElementById("h13q1-approve").addEventListener("click", async () => {{
    showMessage("Approving identity access…", "info");
    const {{ data, error }} = await supabase.auth.oauth.approveAuthorization(authorizationId);
    if (error) {{
      if (isStale(error)) return requireRestart();
      showMessage(error.message || "Approval failed.", "error");
      return;
    }}
    redirectTop(data.redirect_url);
  }});

  document.getElementById("h13q1-deny").addEventListener("click", async () => {{
    const {{ data, error }} = await supabase.auth.oauth.denyAuthorization(authorizationId);
    if (error) {{
      if (isStale(error)) return requireRestart();
      showMessage(error.message || "Unable to deny the request.", "error");
      return;
    }}
    redirectTop(data.redirect_url);
  }});

  document.getElementById("h13q1-restart-button").addEventListener("click", () => {{
    redirectTop("/");
  }});
</script>
"""

st.html(html_document, unsafe_allow_javascript=True)
st.stop()
