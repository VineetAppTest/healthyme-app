"""HealthyMe direct Supabase session gateway proof of concept.

This service keeps Supabase email/password authentication but owns the HTTP response
that creates the browser session cookie. It reuses the H13C durable session table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import html
import logging
import os
import secrets
import time
from typing import Any
from urllib.parse import urljoin, urlparse

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from supabase import create_client

LOGGER = logging.getLogger("healthyme.auth_gateway")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

SESSION_TABLE = "hm_streamlit_auth_sessions"
COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "hm_supabase_sid_v2")
COOKIE_DOMAIN = os.getenv("SESSION_COOKIE_DOMAIN", "").strip() or None
COOKIE_TTL_SECONDS = max(int(os.getenv("SESSION_TTL_SECONDS", "43200")), 300)
STREAMLIT_RETURN_URL = os.getenv("STREAMLIT_RETURN_URL", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
GATEWAY_SIGNING_SECRET = os.getenv("GATEWAY_SIGNING_SECRET", "").strip()
COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").strip().lower() != "false"

app = FastAPI(
    title="HealthyMe Session Gateway",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def _require_configuration() -> None:
    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY),
            ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
            ("GATEWAY_SIGNING_SECRET", GATEWAY_SIGNING_SECRET),
            ("STREAMLIT_RETURN_URL", STREAMLIT_RETURN_URL),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required gateway configuration: " + ", ".join(missing)
        )


def _auth_client():
    _require_configuration()
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _service_client():
    _require_configuration()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _session_payload(response: Any) -> dict[str, Any]:
    session = _value(response, "session") or {}
    user = _value(response, "user") or _value(session, "user") or {}
    return {
        "email": str(_value(user, "email", "") or "").strip().lower(),
        "auth_user_id": str(_value(user, "id", "") or "").strip(),
        "access_token": str(_value(session, "access_token", "") or "").strip(),
        "refresh_token": str(_value(session, "refresh_token", "") or "").strip(),
        "token_expires_at": _value(session, "expires_at"),
    }


def _marker_hash(marker: str) -> str:
    return hashlib.sha256(marker.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _safe_return_url(candidate: str | None) -> str:
    _require_configuration()
    configured = urlparse(STREAMLIT_RETURN_URL)
    raw = str(candidate or "").strip()
    if not raw:
        return STREAMLIT_RETURN_URL

    resolved = urlparse(urljoin(STREAMLIT_RETURN_URL, raw))
    if (
        resolved.scheme in {"https", "http"}
        and resolved.scheme == configured.scheme
        and resolved.netloc == configured.netloc
    ):
        return resolved.geturl()
    return STREAMLIT_RETURN_URL


def _csrf_token() -> str:
    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(18)
    message = f"{issued_at}.{nonce}"
    signature = hmac.new(
        GATEWAY_SIGNING_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{message}.{signature}"


def _csrf_valid(token: str) -> bool:
    try:
        issued_at_text, nonce, supplied_signature = token.split(".", 2)
        issued_at = int(issued_at_text)
    except (TypeError, ValueError):
        return False

    if not nonce or abs(int(time.time()) - issued_at) > 10 * 60:
        return False
    message = f"{issued_at_text}.{nonce}"
    expected = hmac.new(
        GATEWAY_SIGNING_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, supplied_signature)


def _render_login(
    *,
    next_url: str,
    message: str = "",
    email: str = "",
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    token = _csrf_token()
    safe_message = html.escape(message)
    message_html = (
        f"<div class='message'>{safe_message}</div>" if safe_message else ""
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HealthyMe Secure Login</title>
  <style>
    body{{font-family:Arial,sans-serif;background:#f5f7f6;margin:0;color:#17352d}}
    main{{max-width:440px;margin:8vh auto;padding:28px;background:white;border-radius:18px;
    box-shadow:0 12px 35px rgba(20,60,48,.12)}}
    h1{{margin:0 0 6px}} p{{color:#557068}} label{{display:block;margin-top:16px;font-weight:700}}
    input{{box-sizing:border-box;width:100%;padding:12px;margin-top:6px;border:1px solid #cddbd6;
    border-radius:10px;font-size:16px}} button{{width:100%;margin-top:22px;padding:13px;border:0;
    border-radius:10px;background:#176b55;color:white;font-size:16px;font-weight:700;cursor:pointer}}
    .message{{margin:14px 0;padding:11px;border-radius:10px;background:#fdecec;color:#8e2020}}
    .small{{font-size:13px;color:#6a7f78;margin-top:18px}}
  </style>
</head>
<body>
<main>
  <h1>HealthyMe</h1>
  <p>Secure access through Supabase Auth</p>
  {message_html}
  <form method="post" action="/login" autocomplete="on">
    <input type="hidden" name="csrf_token" value="{html.escape(token)}">
    <input type="hidden" name="next_url" value="{html.escape(next_url)}">
    <label for="email">Email</label>
    <input id="email" name="email" type="email" required autocomplete="username"
           value="{html.escape(email)}">
    <label for="password">Password</label>
    <input id="password" name="password" type="password" required autocomplete="current-password">
    <button type="submit">Continue with Supabase</button>
  </form>
  <div class="small">No public sign-up. HealthyMe access requires an active authorised account.</div>
</main>
</body>
</html>"""
    return HTMLResponse(page, status_code=status_code)


def _store_durable_session(payload: dict[str, Any]) -> str:
    required = ("email", "access_token", "refresh_token")
    if any(not payload.get(key) for key in required):
        raise RuntimeError("Supabase returned an incomplete refreshable session.")

    marker = secrets.token_urlsafe(48)
    now = _utc_now()
    expiry = now + timedelta(seconds=COOKIE_TTL_SECONDS)
    row = {
        "marker_hash": _marker_hash(marker),
        "user_email": payload["email"],
        "auth_user_id": payload.get("auth_user_id") or None,
        "app_role": None,
        "app_user_snapshot": {},
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "token_expires_at": payload.get("token_expires_at"),
        "expires_at": _iso(expiry),
        "role_checked_at": None,
        "last_seen_at": _iso(now),
        "metadata": {"source": "healthyme_h13g1_gateway"},
    }
    response = _service_client().table(SESSION_TABLE).insert(row).execute()
    data = _value(response, "data", None)
    if not data:
        raise RuntimeError("The durable session row was not created.")
    return marker


def _revoke_durable_session(marker: str) -> None:
    if not marker:
        return
    now = _iso(_utc_now())
    (
        _service_client()
        .table(SESSION_TABLE)
        .update(
            {
                "revoked_at": now,
                "last_seen_at": now,
                "access_token": None,
                "refresh_token": None,
            }
        )
        .eq("marker_hash", _marker_hash(marker))
        .execute()
    )


def _set_session_cookie(response: RedirectResponse, marker: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=marker,
        max_age=COOKIE_TTL_SECONDS,
        path="/",
        domain=COOKIE_DOMAIN,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def _clear_session_cookie(response: RedirectResponse) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        domain=COOKIE_DOMAIN,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


@app.get("/healthz")
def healthz() -> JSONResponse:
    configured = all(
        (
            SUPABASE_URL,
            SUPABASE_ANON_KEY,
            SUPABASE_SERVICE_ROLE_KEY,
            GATEWAY_SIGNING_SECRET,
            STREAMLIT_RETURN_URL,
        )
    )
    return JSONResponse(
        {"status": "ok" if configured else "configuration_incomplete"},
        status_code=200 if configured else 503,
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(next: str | None = None) -> HTMLResponse:
    return _render_login(next_url=_safe_return_url(next))


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next_url: str = Form(""),
):
    destination = _safe_return_url(next_url)
    clean_email = email.strip().lower()

    if not _csrf_valid(csrf_token):
        return _render_login(
            next_url=destination,
            message="The login form expired. Please try again.",
            email=clean_email,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        auth_response = _auth_client().auth.sign_in_with_password(
            {"email": clean_email, "password": password}
        )
        marker = _store_durable_session(_session_payload(auth_response))
    except Exception:
        LOGGER.exception(
            "Gateway login failed for request from %s",
            request.client.host if request.client else "unknown",
        )
        return _render_login(
            next_url=destination,
            message="Login could not be completed. Check the credentials and try again.",
            email=clean_email,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse(
        url=destination,
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _set_session_cookie(response, marker)
    return response


@app.get("/logout", response_class=HTMLResponse)
def logout_page() -> HTMLResponse:
    token = _csrf_token()
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>HealthyMe Logout</title></head>
<body style="font-family:Arial,sans-serif;max-width:420px;margin:10vh auto">
<h2>Sign out of HealthyMe?</h2>
<form method="post" action="/logout">
<input type="hidden" name="csrf_token" value="{html.escape(token)}">
<button type="submit" style="padding:12px 18px">Sign out</button>
</form></body></html>"""
    return HTMLResponse(page)


@app.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    destination = STREAMLIT_RETURN_URL or "/"
    if not _csrf_valid(csrf_token):
        return HTMLResponse(
            "The logout request expired. Please return to HealthyMe and try again.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    marker = request.cookies.get(COOKIE_NAME, "")
    try:
        _revoke_durable_session(marker)
    except Exception:
        LOGGER.exception("Gateway logout could not revoke the durable session.")

    response = RedirectResponse(
        url=destination,
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _clear_session_cookie(response)
    return response
