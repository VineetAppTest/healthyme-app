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
- The member should be asked to sign in again only when the Supabase session is genuinely missing, expired and non-refreshable, revoked, or invalid.
- A refresh must not clear member identity, role, or active member context merely because Streamlit reruns the page.
- Any fallback redirect to Login must preserve the originally requested member destination after successful authentication.

## Governance

- Flutter remains the member UX baseline for future parity review.
- This addendum must be folded into the next consolidated MCD revision.
