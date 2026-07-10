# H9A.10A Repository-to-Profile Builder Source Alignment

Scope:

- Adds a contract-first diagnostic page before member recommendation consumption is built.
- Compares the actual source repositories against what the current Recommendation Profile Builder captures.
- Checks:
  - Recipe repository active rows vs Profile Builder recipe dropdown labels.
  - Exercise repository active rows vs Profile Builder exercise dropdown labels.
  - Active supplement regimen names vs Profile Builder supplement dropdown labels.
  - Recipe and exercise image reference availability.
  - Field-level information currently not preserved by Profile Builder.
- Adds System Tools entry:
  - `Profile Source Alignment`
- Adds route:
  - `/Admin_Profile_Source_Alignment`
- Adds visible version:
  - `v100.37 · Repository Source Alignment`

Important finding expected from this sprint:

- The current Profile Builder still captures slim recommendation rows.
- Recipe and exercise repositories contain richer data than the Profile Builder currently preserves.
- Images should be preserved by reference in the member consumption contract, but do not need to render in normal admin editing.
- Supplement regimen is member-specific and should be pulled from active member supplement rows where relevant instead of re-entered manually.

Impact:

- Admin/System Tools diagnostic only.
- No SQL changes.
- No Flutter changes.
- No member-facing display changes.
- No change to Profile Builder save/publish behavior.

Recommended next step after this sprint:

- H9A.10B — Profile Builder Source Selection Contract
  - Replace label-only selection with source-backed selection.
  - Save source id/name plus full immutable snapshot at publish time.
  - Preserve admin override fields.
  - Preserve image references for member web / Flutter.

Smoke test:

1. Open Admin Dashboard.
2. Go to System Tools.
3. Click `Profile Source Alignment`.
4. Confirm `/Admin_Profile_Source_Alignment` opens.
5. Confirm version `v100.37 · Repository Source Alignment`.
6. Confirm count cards render for Recipe, Exercise, Supplements and missing dropdown labels.
7. Confirm Coverage Assessment table renders.
8. Confirm Dropdown Alignment Check table renders.
9. Confirm Field-level source maps expander opens.
10. Confirm no member-facing page is changed.
