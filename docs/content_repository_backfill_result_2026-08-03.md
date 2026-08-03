# Content Repository controlled backfill result — 2026-08-03

## Result

The controlled production backfill completed successfully for issue #347.

Supabase migration history:

- Version: `20260803050345`
- Name: `backfill_standard_content_repository`

No live Recipe, Exercise or Supplement page was switched during this step.

## Canonical items

| Repository | Expected | Stored | Active | Inactive | Version range |
|---|---:|---:|---:|---:|---|
| Recipe | 2 | 2 | 2 | 0 | 1–1 |
| Exercise | 3 | 3 | 3 | 0 | 1–1 |
| Supplement | 5 | 5 | 5 | 0 | 1–1 |
| **Total** | **10** | **10** | **10** | **0** | **1–1** |

Fresh comparison between the live legacy sources and the canonical destination returned:

- Expected records: `10`
- Stored records: `10`
- Field-level differences: `0`

The comparison covered composite identity, display name, normalized status, payload, source system and legacy reference.

## Frozen identities verified

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

Every identity retained the expected `legacy_reference`.

## Audit verification

- Created events: `10`
- Distinct repository items represented: `10`
- Event actor: `system:content_repository_backfill`
- Events with a non-null `before_record`: `0`
- Events missing an `after_record`: `0`
- Audit identity mismatches: `0`

## Legacy-source preservation

Exercise and Supplement app-state authorities remained unchanged after the backfill:

- Exercise count: `3`
- Exercise raw SHA-256: `fdd4b6945284c46dadcf60b4000a02f2e75daf31efd10b55358cfa4813fa65e0`
- Supplement count: `5`
- Supplement raw SHA-256: `dd25cd82f88ad07afdea2e91cfc80f9ccaca60598566fcc34d9697036408790c`

Recipe source remained at Git blob SHA:

- `5112e778aea7bddf08977cdf8e43fe30d42e896e`

## Security verification

Both canonical tables retain RLS with no browser grants.

Effective `service_role` privileges:

- `hm_content_repository_items`: `INSERT`, `SELECT`, `UPDATE`
- `hm_content_repository_events`: `INSERT`, `SELECT`

There is no application DELETE or TRUNCATE privilege.

## Jarvis gate

**PASS**

The backfill is accepted as a stable data checkpoint. The next phase may prepare a repository-by-repository cutover, starting with Exercise, but no cutover should occur in this PR.
