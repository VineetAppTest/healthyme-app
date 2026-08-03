# Recommendation Profile Builder — Phase 2 Canonical Reads

Issue: #343  
Build: `v100.44 · Canonical Repository Reads`

## Objective

Move the live Recommendation Profile Builder from visible-name source selection to the canonical repository IDs frozen in Phase 1.

Phase 2 changes the editing and module-save path. It does not change Publish, Active-profile selection, member consumption, authentication, roles, routing or RLS.

## Live source flow

```text
Recipe / Exercise / Supplement Repository
            ↓
Canonical source contract
            ↓
Source ID selected in Profile Builder
            ↓
Display label shown to Admin/Nutritionist
            ↓
Saved immutable source snapshot
```

`source_id` is the identity. `reference_label` remains the readable name.

## Selection behaviour

- New selections list active repository items only.
- Duplicate visible names remain separate and show an ID suffix only when required.
- Source details are resolved through the selected ID, not by guessing from the visible name.
- Supplement source details no longer restore Admin Notes.
- A repository read failure leaves that source list empty; mock Recipe, Exercise or Supplement names are not presented as real source data.

## Existing-profile compatibility

### Saved canonical source

A loaded row retains its saved snapshot as a separate **Saved profile source** option. Rendering the row does not refresh or rewrite that snapshot.

An Admin/Nutritionist may deliberately select the current active repository option to refresh the row to the repository’s latest content.

### Inactive or removed source

A source that is no longer active remains visible inside the profile where it was previously saved. It is excluded from new selections.

### Legacy label-only source

- A legacy name is linked to a canonical ID only when exactly one repository item matches.
- If multiple items share the same name, the row remains a **Legacy saved source** instead of being silently linked to the wrong item.
- The user may explicitly select the intended canonical repository item.

## Module save bridge

Meals, Exercise and Supplements continue using the existing module-store API. A transitional runtime installs the canonical implementation before the Builder imports its renderers.

The canonical save path preserves:

- source type;
- source ID;
- display label;
- immutable original snapshot;
- Admin source-detail overrides;
- image-reference fields.

The bridge can be removed when the canonical store becomes the primary implementation during the later cleanup phase.

## Non-regression boundary

No change to:

- Profile Setup save or member assignment;
- Draft/Active edit entitlement;
- Clone Setup;
- Preview behaviour beyond consuming the loaded row data;
- Publish/activation and replacement rules;
- Active Preview;
- View Profiles;
- member-facing recommendation consumption;
- authentication, role guard, routing or RLS.

## Smoke test after deployment

1. Open Recommendation Profile Builder and load an existing Draft.
2. Open Meals, Exercise and Supplements; confirm saved source rows remain selected.
3. Confirm a saved row displays **Saved profile source** and its historical details remain unchanged.
4. Select a new active repository item and confirm source details update immediately.
5. Save each module, reload it and confirm the same source ID/name/details return.
6. Confirm duplicate source names show ID suffixes and remain independently selectable.
7. Confirm inactive/removed saved sources remain readable but are absent from new-selection choices.
8. Confirm a legacy label-only row is linked only when the name is unique; ambiguous names remain labelled as legacy.
9. Confirm Supplement Pulled Source Details do not show Admin Notes.
10. Confirm Setup, Preview, Publish, Active and View Profiles still open normally.
11. Confirm Nutritionist can edit but cannot Publish.
12. Confirm login, refresh, Back, Dashboard and logout remain unchanged.
