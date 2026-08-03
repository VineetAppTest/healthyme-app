# Content Repository source inventory — 2026-08-03

This is the read-only migration baseline for issue #347. No canonical repository records were written while capturing this inventory.

## Source authorities

| Repository | Current authority | Count | Active | Inactive | Canonical checksum |
|---|---|---:|---:|---:|---|
| Recipe | `data/recipes.csv` | 2 | 2 | 0 | `a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f` |
| Exercise | `healthyme_app_state.data.exercises` | 3 | 3 | 0 | `585764b996d1952226405966efada936b87eae4cfa0f2a6120433f5f560e4716` |
| Supplement | `healthyme_app_state.data.supplement_repository` | 5 | 5 | 0 | `4bb7bcb320b0cb1c83981d38531f14db9c020b0a61b1d74b3765f0b09865bf96` |
| **Total** |  | **10** | **10** | **0** | `52ac68b76032cfdacba2686cf85c7d3b4d954f8d54589ba67890a0af11c40f5e` |

Checksums use the deterministic projection in `components/content_repository_migration.py`: repository type, source ID, display name, normalized status, type-specific payload, source system and legacy reference.

## Checksum correction before backfill

The original Exercise, Supplement and total checksums omitted the generated `legacy_reference` values for the two app-state repositories. Counts, statuses and composite identities were correct, and the underlying source data did not change. The checksums above are the corrected values produced by the actual migration projection with `legacy_reference` included consistently for all three repositories.

The backfill was blocked until this mismatch was understood and the baseline corrected.

## Frozen identities

### Recipe
- `recipe:0`
- `recipe:1`

### Exercise
- `exercise:0`
- `exercise:1`
- `exercise:2`

### Supplement
- `supplement:suprepo_2ceffd32`
- `supplement:suprepo_4b3c1e53`
- `supplement:suprepo_c88d2def`
- `supplement:suprepo_e36aa236`
- `supplement:suprepo_f687a40a`

## Destination readiness

- `hm_content_repository_items`: 0 rows immediately before backfill.
- `hm_content_repository_events`: 0 rows immediately before backfill.
- RLS is enabled on both tables.
- `anon` and `authenticated` have no table privileges.
- Effective `service_role` privileges are limited to:
  - Items: `SELECT`, `INSERT`, `UPDATE`
  - Events: `SELECT`, `INSERT`
- Repository item identity is immutable after insertion.
- Two item triggers are installed for version/timestamp handling and append-only audit capture.

## Migration gate

Backfill must not be accepted unless all of the following match this baseline:

1. source count by repository;
2. composite identity set;
3. corrected per-repository checksum;
4. corrected total checksum;
5. destination count after backfill;
6. exact canonical row comparison;
7. one clean `created` audit event for every inserted canonical item;
8. `content_version = 1` for every inserted item.

The SQL migration additionally compares the live Exercise and Supplement JSON arrays with the revalidated source snapshot and refuses to run if either source changes.
