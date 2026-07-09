# H9A.8C Dashboard Recommendations Cleanup

Scope:

- Keeps the final `Recommendation Profile Builder` as the normal admin recommendation workflow.
- Removes `Recommendations Share` and `Unified Recommendations` from the main `Reports & Logs` workflow section.
- Moves them to `System Tools` as legacy/diagnostic controls:
  - `Legacy Recommendations Share`
  - `Unified Recommendations Diagnostics`
- No deletion yet.
- Old V2/V4/V5/interim versions remain backend/code-only if still present and should be handled in a later cleanup sprint after final flow stability is confirmed.

Rationale:

- `Recommendation Profile Builder` is now the final direction.
- `Recommendations Share` is an older manual 7-day recommendation composer.
- `Unified Recommendations` is a technical contract/diagnostic workbench.
- Both should not remain prominent daily workflow buttons.

Impact:

- Dashboard-only cleanup.
- No SQL changes.
- No Flutter changes.
- No member-facing changes.
- No route deletion in this sprint.

Smoke test:

1. Open Admin Dashboard.
2. Confirm `Reports & Logs` shows only Daily Logs, Questions and Responses.
3. Confirm `Content & Allocation` still shows Recommendation Profile Builder.
4. Confirm `System Tools` now shows Legacy Recommendations Share and Unified Recommendations Diagnostics.
5. Confirm both legacy/diagnostic pages still open from System Tools.
