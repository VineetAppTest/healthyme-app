# HealthyMe MCD v1.8 Addendum — Member Reference Library and Auth Refresh

## Member Reference Library

- The Member Home Reference Library is temporarily hidden from the Streamlit member experience.
- The hidden section includes Recipe Repository, Exercise Repository and Supplements.
- The underlying pages, routes and data contracts remain in the codebase and must not be deleted.
- The feature is controlled through a reversible member feature flag so it can be re-enabled later without rebuilding the modules.
- While disabled, direct member navigation to these routes is blocked and returns the member to Member Home.
- This decision applies only to the Streamlit member experience. It does not delete or redefine the Flutter member repositories.

## Supabase session refresh requirement

- Refreshing the browser must not intentionally log out an authenticated Supabase member.
- An already valid Supabase session should be restored silently after an ordinary refresh.
- The member should be asked to sign in again only when the Supabase session is genuinely missing, expired and non-refreshable, revoked, invalid, or unavailable after an application process restart.
- A refresh must not clear member identity, role, or active member context merely because Streamlit reruns the page.
- Any fallback redirect to Login must preserve the originally requested member destination after successful authentication.

## Streamlit Supabase persistence design

- The browser stores only a random opaque session marker in a Secure, SameSite=Strict cookie.
- Supabase access and refresh tokens are not stored in the URL, query parameters, browser local storage, or the browser cookie.
- Supabase tokens remain in a process-local server-side registry and are keyed by the opaque browser marker.
- On an ordinary browser refresh, the marker is read through Streamlit browser context, the Supabase session is refreshed or re-established server-side, and the HealthyMe role is reapplied.
- The default server-side marker lifetime is 12 hours and can be adjusted through `SUPABASE_BROWSER_SESSION_TTL_SECONDS`.
- HealthyMe role revalidation is throttled to avoid repeated heavy checks on every Streamlit rerun. The default interval is five minutes and can be adjusted through `SUPABASE_ROLE_REFRESH_INTERVAL_SECONDS`.
- Secure logout removes the server-side record, expires the browser marker, and signs out the recoverable Supabase session.
- A deployment restart clears the process-local token registry. In that case, the opaque marker is invalidated and the member must sign in again. A future multi-instance deployment should move this registry to a dedicated encrypted server-side session store.

## Governance

- Flutter remains the member UX baseline for future parity review.
- This addendum must be folded into the next consolidated MCD revision.
