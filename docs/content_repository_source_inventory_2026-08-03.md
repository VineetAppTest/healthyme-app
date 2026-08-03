# Content Repository source inventory — 2026-08-03

This is the read-only migration baseline for issue #347. No canonical repository records were written while capturing this inventory.

## Source authorities

| Repository | Current authority | Count | Active | Inactive | Canonical checksum |
|---|---|---:|---:|---:|---|
| Recipe | `data/recipes.csv` | 2 | 2 | 0 | `a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f` |
| Exercise | `healthyme_app_state.data.exercises` | 3 | 3 | 0 | `3caf6d2f99b54b085b1cd14db9ce40421011ad4721160c5f076c33f56bd1e9a5` |
| Supplement | `healthyme_app_state.data.supplement_repository` | 5 | 5 | 0 | `d5b1d57a904c03f6a2260cb3241b1ff81f6cc15efbaf40a21f102ad88cc4ba87` |
| **Total** |  | **10** | **10** | **0** | `e57853fa2d72dfd8e0a9db7f33a8b3a88180b93992741d628b8f70e00f47379e` |

Checksums use the same deterministic projection as `components/content_repository_migration.py`: repository type, source ID, display name, normalized status, type-specific payload, source system and legacy reference.

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

- `hm_content_repository_items`: 0 rows at baseline capture.
- `hm_content_repository_events`: 0 rows at baseline capture.
- RLS is enabled on both tables.
- `anon` and `authenticated` have no table privileges.
- Effective `service_role` privileges are limited to:
  - Items: `SELECT`, `INSERT`, `UPDATE`
  - Events: `SELECT`, `INSERT`
- Repository item identity is immutable after insertion.
- Two item triggers are installed for version/timestamp handling and append-only audit capture.

## Migration gate

Backfill must not be accepted unless all of the following match this baseline or an explicitly refreshed baseline:

1. source count by repository;
2. composite identity set;
3. per-repository checksum;
4. total checksum;
5. destination count after backfill;
6. one `created` audit event for every newly inserted canonical item.

Any source edit made after this capture requires regeneration of this inventory before backfill.
