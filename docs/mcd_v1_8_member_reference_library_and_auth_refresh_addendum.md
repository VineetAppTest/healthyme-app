# HealthyMe MCD v1.8 Addendum — Member Reference Library and Auth Refresh

## Member Reference Library

- The Member Home Reference Library is temporarily hidden from the Streamlit member experience.
- The hidden section includes Recipe Repository, Exercise Repository and Supplements.
- The underlying pages, routes and data contracts remain in the codebase and must not be deleted.
- The feature is controlled through a reversible member feature flag so it can be re-enabled later without rebuilding the modules.
- While disabled, direct member navigation to these routes is blocked and returns the member to Member Home.
- This decision applies only to the Streamlit member experience. It does not delete or redefine the Flutter member repositories.

## Supabase session refresh requirement

- Refreshing the browser must not intentionally route a member into an admin identity or admin dashboard.
- An already-resolved Supabase member session must remain stable during normal Streamlit reruns and in-app navigation.
- A missing session must return to the neutral Login page and preserve the originally requested member destination.
- Member recovery must not automatically fall back to an existing Auth0 admin browser identity.
- The member should be asked to sign in again only when the Supabase member session cannot be safely restored.

## PR #128 persistence workaround — withdrawn

- The PR #128 process-local cookie registry is withdrawn from the active implementation.
- The registry was cleared by an application/Render process restart while the browser marker remained, which produced an invalid recovery path.
- Rendering the cookie component during protected-page recovery also introduced page flicker and an error risk.
- The temporary hotfix removes that browser component and restores stable role-separated login handling.
- The legacy opaque cookie marker is not trusted for authentication; it is detected only to prevent stale Auth0 admin auto-routing during member recovery.

## Durable persistence direction

- No-logout recovery across a full Render/application restart requires a persistent server-side session store rather than process memory.
- The future design should use an opaque browser marker plus a dedicated encrypted server-side session record with expiry and revocation.
- Supabase access and refresh tokens must never be placed in the URL, query parameters or browser local storage.
- That persistent-session design requires a controlled data-contract/SQL sprint and security review before activation.

## Governance

- Flutter remains the member UX baseline for future parity review.
- The retained Reference Library decision and the corrected authentication direction must be folded into the next consolidated MCD revision.
