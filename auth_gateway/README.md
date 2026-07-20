# HealthyMe H13G1 Session Gateway PoC

This isolated FastAPI service keeps the existing Supabase email/password login but
moves browser-cookie creation to a normal HTTP response.

## Flow

1. The user opens `/login`.
2. The gateway authenticates the email/password with Supabase Auth.
3. It generates a random opaque marker.
4. Only the marker hash and Supabase refreshable session are stored in
   `public.hm_streamlit_auth_sessions`.
5. The gateway responds with a `Secure`, `HttpOnly` cookie.
6. The browser redirects to the configured Streamlit URL.
7. Existing H13C restoration reads the cookie from the initial request and resolves
   the HealthyMe Admin or Member role.

## Required existing database object

Run the existing migration before deploying:

`sql/h13c_streamlit_durable_auth_sessions.sql`

No additional migration is included in H13G1.

## Environment variables

Copy `.env.example` and provide all blank values. The service-role key is server-only.

The PoC assumes:

- gateway custom host: `auth.healthyme.in`
- Streamlit app host under the same parent domain
- `SESSION_COOKIE_DOMAIN=.healthyme.in`

Do not use a parent-domain cookie until both hosts are controlled by HealthyMe.

## Local syntax check

```bash
python -m py_compile auth_gateway/app.py
```

## Run

```bash
pip install -r auth_gateway/requirements.txt
uvicorn auth_gateway.app:app --host 0.0.0.0 --port 8000
```

## PoC test

1. Confirm `/healthz` returns `{"status":"ok"}`.
2. Open `/login`.
3. Sign in as Admin and verify the browser reaches Streamlit.
4. Refresh Admin Dashboard.
5. Sign out through `/logout`.
6. Repeat for Member Home, Daily Log and My Schedule.
7. Record login duration and refresh duration.

## Production gaps intentionally left open

- Gateway-level distributed rate limiting.
- Centralised audit events and alerting.
- Final branded login UI.
- Direct integration of the gateway form into the Streamlit login page.
- Automated end-to-end browser tests.
- A reverse-proxy decision if HealthyMe later wants `/auth/*` instead of
  `auth.healthyme.in`.
