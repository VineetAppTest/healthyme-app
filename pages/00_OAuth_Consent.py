import json
import os

import streamlit as st
import streamlit.components.v1 as components

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
    "This isolated page is used only by the Supabase OAuth Server proof of concept."
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

html_document = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    :root {{ font-family: Inter, Arial, sans-serif; color: #17352d; }}
    body {{ margin: 0; background: #f7faf8; }}
    main {{
      max-width: 560px; margin: 16px auto; padding: 24px;
      background: white; border: 1px solid #d7e5df; border-radius: 18px;
      box-shadow: 0 10px 30px rgba(20,60,48,.08);
    }}
    h2 {{ margin: 0 0 6px; }}
    p {{ color: #5d746c; line-height: 1.45; }}
    label {{ display: block; margin-top: 14px; font-weight: 700; }}
    input {{
      width: 100%; box-sizing: border-box; padding: 12px; margin-top: 6px;
      border: 1px solid #c7d9d2; border-radius: 10px; font-size: 16px;
    }}
    button {{
      padding: 12px 16px; border: 0; border-radius: 10px;
      font-size: 15px; font-weight: 700; cursor: pointer;
    }}
    button:disabled {{ opacity: .65; cursor: wait; }}
    .primary {{ width: 100%; margin-top: 18px; background: #176b55; color: white; }}
    .secondary {{ background: #e9f1ee; color: #17483b; }}
    .danger {{ background: #f8e9e9; color: #8b2020; }}
    .row {{ display: flex; gap: 10px; margin-top: 18px; }}
    .row button {{ flex: 1; }}
    .message {{ margin: 14px 0; padding: 11px; border-radius: 10px; display: none; }}
    .error {{ display: block; background: #fdecec; color: #8e2020; }}
    .info {{ display: block; background: #eaf5f8; color: #0f4c5c; }}
    .scope {{
      display: inline-block; margin: 4px 5px 0 0; padding: 6px 9px;
      background: #edf5f2; border-radius: 999px; font-size: 13px; font-weight: 700;
    }}
    #consent-panel, #restart-panel {{ display: none; }}
  </style>
</head>
<body>
<main>
  <h2>HealthyMe secure authorization</h2>
  <p id="intro">Sign in with your existing Supabase account to continue the test.</p>
  <div id="message" class="message"></div>

  <section id="login-panel">
    <form id="login-form">
      <label for="email">Email</label>
      <input id="email" type="email" required autocomplete="username">
      <label for="password">Password</label>
      <input id="password" type="password" required autocomplete="current-password">
      <button id="signin" class="primary" type="submit">Sign in and review access</button>
    </form>
  </section>

  <section id="consent-panel">
    <h3 id="client-name">Authorize HealthyMe</h3>
    <p>The application is requesting the following identity information:</p>
    <div id="scopes"></div>
    <div class="row">
      <button id="deny" class="danger" type="button">Deny</button>
      <button id="approve" class="secondary" type="button">Approve</button>
    </div>
  </section>

  <section id="restart-panel">
    <p>This authorization request is no longer valid. No password retry can repair an expired request.</p>
    <button id="restart" class="primary" type="button">Start a fresh login</button>
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

  const loginPanel = document.getElementById("login-panel");
  const consentPanel = document.getElementById("consent-panel");
  const restartPanel = document.getElementById("restart-panel");
  const messageBox = document.getElementById("message");
  const clientName = document.getElementById("client-name");
  const scopesBox = document.getElementById("scopes");
  const signInButton = document.getElementById("signin");
  let submissionInProgress = false;

  function showMessage(text, level = "info") {{
    messageBox.textContent = text;
    messageBox.className = `message ${{level}}`;
  }}

  function redirectTop(url) {{
    try {{
      window.parent.location.replace(url);
    }} catch (_error) {{
      window.location.replace(url);
    }}
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
    rawScope.split(/\\s+/).filter(Boolean).forEach((scope) => {{
      const pill = document.createElement("span");
      pill.className = "scope";
      pill.textContent = scope;
      scopesBox.appendChild(pill);
    }});

    loginPanel.style.display = "none";
    consentPanel.style.display = "block";
    showMessage("Identity confirmed. Review and approve the requested access.", "info");
  }}

  document.getElementById("login-form").addEventListener("submit", async (event) => {{
    event.preventDefault();
    if (submissionInProgress) return;
    submissionInProgress = true;
    signInButton.disabled = true;
    showMessage("Confirming your Supabase identity…", "info");

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    const {{ error }} = await supabase.auth.signInWithPassword({{ email, password }});
    document.getElementById("password").value = "";

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

  document.getElementById("approve").addEventListener("click", async () => {{
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

  document.getElementById("deny").addEventListener("click", async () => {{
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

  document.getElementById("restart").addEventListener("click", () => {{
    redirectTop("/Login");
  }});
</script>
</body>
</html>
"""

components.html(html_document, height=740, scrolling=True)
st.stop()
