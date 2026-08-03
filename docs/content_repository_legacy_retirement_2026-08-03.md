# Content Repository legacy retirement checkpoint

Date: 2026-08-03
Issue: #347

## Canonical authority

Recipe, Exercise and Supplement now read and write through `public.hm_content_repository_items` and its audit table.

Production baseline at this checkpoint:

| Repository | Canonical rows | Retained legacy rows |
| --- | ---: | ---: |
| Recipe | 2 | 2 |
| Exercise | 3 | 3 |
| Supplement | 5 | 5 |

The retained legacy rows and CSV files are rollback evidence only. They are not to be edited, synchronized or treated as live repository authorities.

## Retirement completed in this checkpoint

- Recipe compatibility sync is read-only.
- Exercise compatibility sync is read-only.
- Supplement repository has no app-state fallback or write path.
- Admin Recipe, Exercise and Supplement pages have no legacy CSV or app-state write path.
- Canonical repository writes remain verified through a fresh Supabase read.
- Historical recommendation and member-plan snapshots remain unchanged.

## Deliberately retained

- `data/recipes.csv`
- `data/exercises.csv`
- `healthyme_app_state.data.recipes`
- `healthyme_app_state.data.exercises`
- `healthyme_app_state.data.supplement_repository`

These are retained temporarily for rollback evidence and production observation. Their presence does not make them an active authority.

## Next retirement gate

After production observation confirms the three canonical repository flows:

1. Refactor the member Recipe and Exercise repository pages to import canonical repository modules directly.
2. Remove the pandas CSV compatibility runtimes.
3. Re-run member filtering, detail, feedback, allocation and refresh-persistence tests.
4. Archive or remove the retained legacy app-state repository keys only through a separately reviewed production migration.

No historical allocation, recommendation snapshot or audit record should be deleted as part of legacy authority retirement.
