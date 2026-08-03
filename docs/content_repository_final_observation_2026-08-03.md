# Content Repository final observation gate

Date: 2026-08-03
Issue: #347

## Decision

The canonical Supabase Content Repository is the sole live authority for Recipe, Exercise and Supplement definitions. The final gate moves the two retained CSV sources from active `data/` paths into a documentation archive.

No production app-state data is deleted in this step.

## Production observation

- Canonical items: 10
  - Recipe: 2 active, IDs `0,1`
  - Exercise: 3 active, IDs `0,1,2`
  - Supplement: 5 active, existing `suprepo_*` IDs
- Canonical audit events: 10
- Orphan events: 0
- Items missing a created event: 0
- All current content versions: 1
- Retained legacy repository counts: Recipe 2, Exercise 3, Supplement 5
- Exercise legacy SHA-256 remains `fdd4b6945284c46dadcf60b4000a02f2e75daf31efd10b55358cfa4813fa65e0`.
- Supplement legacy SHA-256 remains `dd25cd82f88ad07afdea2e91cfc80f9ccaca60598566fcc34d9697036408790c`.

## Downstream integrity

- Member Recipe allocations: 2; missing IDs 0; unknown canonical IDs 0.
- Member Exercise allocations: 2; missing IDs 0; unknown canonical IDs 0.
- Existing recommendation-share rows and historical plan objects remain untouched.
- Empty schedule placeholders inside recommendation plans are not repository records and are outside this issue's scope.

## Runtime retirement

The final code gate requires:

- no repository-to-app-state sync compatibility functions;
- no publishing-time repository compatibility sync call;
- repository diagnostics counting canonical Recipe and Exercise rows;
- no runtime import or read from `data/recipes.csv` or `data/exercises.csv`;
- archived CSV evidence remaining immutable and checksum-verifiable.

## Safety boundary

This step does not delete:

- `healthyme_app_state.data.recipes`;
- `healthyme_app_state.data.exercises`;
- `healthyme_app_state.data.supplement_repository`;
- member allocations;
- legacy assignment IDs;
- recommendation shares;
- historical source snapshots.

The retained app-state repository arrays are inert rollback evidence and can be physically removed only through a separate explicitly approved data migration.
