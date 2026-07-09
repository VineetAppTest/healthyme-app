# H9A.9B Active Profile Diagnostics Placement

Scope:

- Removes `Raw active profile contract payload` from the normal Active Preview tab.
- Keeps Active Preview as a clean admin-side member preview contract.
- Adds a dedicated System Tools diagnostics page:
  - `/Admin_Active_Profile_Contract_Diagnostics`
- Adds Admin Dashboard > System Tools button:
  - `Active Profile Contract Diagnostics`
- Raw active profile payload is visible only on the diagnostics page.

Normal Profile Builder route remains:

- `/Admin_Recommendation_Profile_Builder`

Diagnostic route:

- `/Admin_Active_Profile_Contract_Diagnostics`

Impact:

- No SQL changes.
- No Flutter changes.
- No member-facing display change.
- Active Profile Preview remains admin-only.
- Publish/Activate behavior remains unchanged.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Open `Active Preview`.
3. Confirm the raw contract payload expander is not visible in normal UI.
4. Confirm Active Preview still shows member selector, profile summary, row counts and Day 1 to Day 7 preview.
5. Open Admin Dashboard.
6. Go to System Tools.
7. Click `Active Profile Contract Diagnostics`.
8. Confirm `/Admin_Active_Profile_Contract_Diagnostics` opens.
9. Select a member with an active profile.
10. Confirm raw active profile contract payload is available there only.
