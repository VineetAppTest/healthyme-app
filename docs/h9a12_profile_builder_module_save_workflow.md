# H9A.12 — Profile Builder Module-Specific Save Workflow

## Decision

The Recommendation Profile Builder is separated into a profile shell and three independently saved recommendation modules.

## Setup

Setup creates and saves the profile shell only. It owns profile-level information such as profile name, member assignment, start date, cycle rule, region, age band, diet type, health concerns, change note and profile-level nutritionist note.

Saving Setup must not create, replace or delete Meal, Exercise or Supplement rows.

Cloning from Setup copies profile-level information only. Recommendation rows are managed and saved from their respective modules.

## Meals, Exercise and Supplements

Each module follows the same controlled sequence:

1. Select Member.
2. Select a Draft Profile filtered to that member.
3. Load the selected profile.
4. Edit only the selected module.
5. Use the module-specific save action.

Module saves replace only rows of the matching item type for the selected profile:

- Meals saves `item_type = meal` only.
- Exercise saves `item_type = exercise` only.
- Supplements saves `item_type = supplement` only.

No module save may clear or overwrite rows owned by another module.

## Preview, Publish and Active

Preview, Publish and Active retain their existing behavior. Preview aggregates the loaded profile shell and all saved module rows. Publish and Active continue to use the existing profile activation and member-facing contracts.

## Integrity controls

- A module cannot be saved until a member and that member’s draft profile are selected and loaded.
- Profile options are filtered by member to prevent cross-member profile edits.
- Only Draft profiles are editable through module pages.
- Existing profile and item tables remain the source of truth; no SQL schema change is required.
- Authentication, navigation, publishing and active-profile logic remain unchanged.
