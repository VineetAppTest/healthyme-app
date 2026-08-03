# Member Planning separation contract

Date: 2026-08-03  
Issue: #360

## Decision

HealthyMe Member Planning will be separated into four responsibility areas:

1. **Meal Profile Builder** — profile setup and meal structure only.
2. **Exercise Member Allocation** — independent member-specific Exercise workflow.
3. **Supplement Member Allocation** — independent member-specific Supplement workflow.
4. **Current Member Plan** — consolidated read model for Meals, Exercise and Supplements.

Current Member Plan must never become another persistence authority.

## Repository boundary

Recipe, Exercise and Supplement definitions remain in the canonical Supabase Content Repository completed under issue #347.

Member-specific fields do not belong to reusable repository definitions. These include:

- member identity;
- allocation dates;
- dosage, frequency and timing;
- member instructions and notes;
- allocation lifecycle status;
- stop dates and stop reasons.

Repository display labels are presentation only. Allocations must ultimately reference canonical `source_type + source_id` identity.

## Current production inventory freeze

Read-only observation from `healthyme_app_state_v1` on 2026-08-03:

| Concern | Current store | Shape | Observed volume |
|---|---|---|---:|
| Meal structure | `meal_type_repository` | array | 6 rows |
| Recipe allocations | `member_recipe_allocations` | member-keyed object of arrays | 1 member bucket |
| Exercise allocations | `member_exercise_allocations` | member-keyed object of arrays | 1 member bucket |
| Supplement allocations | `member_supplements` | array | 6 rows |
| Published recommendation plan | `recommendation_shares` | member-keyed object | 1 member bucket |

### Confirmed identity fields

- Recipe allocation: `recipe_id` → `recipe_repository:<source_id>`.
- Exercise allocation: `exercise_id` → `exercise_repository:<source_id>`.
- Supplement allocation: existing rows retain allocation `id`, but do not expose a dedicated canonical Supplement repository `source_id` field consistently. Phase D must introduce compatibility mapping without replacing existing allocation IDs or lifecycle history.

## Target ownership

### Meal Profile Builder

Owns:

- profile setup;
- meal structure;
- Recipe source snapshots used by meals.

Explicitly excludes:

- Exercise allocation;
- Supplement allocation.

### Exercise Member Allocation

Owns:

- member identity;
- canonical Exercise source reference;
- dates;
- instructions and notes;
- active/inactive allocation lifecycle.

### Supplement Member Allocation

Owns:

- member identity;
- canonical Supplement source reference;
- dosage, frequency and timing;
- dates and instructions;
- active/stopped allocation lifecycle.

Repository `admin_notes` are excluded from new member snapshots.

### Current Member Plan

Reads:

- meal plan;
- exercise allocations;
- supplement allocations.

It consolidates these domains for Member and future Flutter consumption, but does not write repository definitions or duplicate allocation records.

## Delivery sequence

1. Contract and inventory freeze — this phase.
2. Meal Profile Builder meals-only cutover.
3. Independent Exercise allocation workflow.
4. Independent Supplement allocation workflow with legacy mapping.
5. Current Member Plan consolidation.

## Safety boundary

This phase does not:

- modify live pages;
- change Supabase schema;
- rewrite or delete allocations;
- modify recommendation shares;
- change authentication or routing;
- modify Content Repository IDs or payloads.

Existing active and historical member plans remain untouched.
