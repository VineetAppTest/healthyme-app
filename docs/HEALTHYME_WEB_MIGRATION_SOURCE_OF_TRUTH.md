# HealthyMe Web Migration — Source of Truth

**Status:** Governing implementation document  
**Effective date:** 2026-08-19  
**Scope:** HealthyMe web migration from Streamlit to Next.js/Vercel while retaining Supabase as the backend.

## 1. Authority and precedence

This document consolidates the product, UX, architecture, migration, branding and validation decisions agreed for the HealthyMe web migration up to 2026-08-19.

It governs further development unless Vineet gives a newer explicit direction.

If implementation, an older document, an older PR description, an earlier wireframe or an earlier assumption conflicts with this document, this document takes precedence. A later explicit user decision takes precedence over this document and should then be incorporated here so the document remains current.

The migration must be treated as a product migration, not as a cosmetic rewrite.

---

## 2. Core objective

The objective is **not** to make a prettier copy of the existing Streamlit HealthyMe application.

The objective is to:

1. preserve the existing HealthyMe functionality and accepted business behaviour;
2. preserve the existing Supabase backend and data contracts wherever possible;
3. rethink the information architecture and interaction model so the app is clearer and more intuitive;
4. modernize the visual design, responsiveness and interaction quality using Next.js;
5. reduce dependence on user memory, app knowledge and menu hunting;
6. keep the application functionally correct throughout the migration;
7. migrate progressively and safely, with the existing application available as the functional reference/fallback until each replacement slice is accepted.

The governing pattern is:

`Preserve capability -> understand user intent -> redesign interaction -> improve presentation -> validate behaviour -> replace only the accepted slice`

Not:

`Copy Streamlit -> make it prettier -> declare migration complete`

---

## 3. What is being replaced and what is being preserved

### Replace progressively

- Streamlit presentation layer;
- page structure and information architecture where a clearer structure is possible;
- interaction patterns that depend on reruns, excessive navigation or user memory;
- visual hierarchy, spacing, typography, cards, forms and controls;
- responsive behaviour;
- light/dark mode handling;
- state presentation and feedback where the current UX is confusing;
- member-facing discovery patterns that require users to hunt for information.

### Preserve by default

- existing HealthyMe Supabase project;
- production database tables;
- existing IDs and historical records;
- Supabase Auth identities and accepted authentication outcomes;
- Row Level Security policies;
- storage contracts;
- canonical `hm_users` authorization and role semantics;
- existing business rules and lifecycle states;
- allocation, publishing, acknowledgement, completion, journal and status logic;
- current data integrity and history;
- accepted downstream effects of member/admin actions.

The backend is a **protected dependency of the migration**.

A frontend migration task does not authorize a backend change.

If a backend change becomes genuinely necessary, it must be:

1. critical to the required functionality or experience;
2. justified separately;
3. assessed for impact on the existing HealthyMe application;
4. backward-compatible wherever possible;
5. reviewed before implementation;
6. regression-tested across old and new frontends.

Where a frontend adapter can solve the requirement safely, the frontend should adapt to the existing backend rather than reshaping the backend for convenience.

---

## 4. Product migration principle

The existing Streamlit HealthyMe application is the **functional reference**, but it is **not the UX template**.

For each migrated section, development must explicitly distinguish:

### Functional baseline
What does the current section actually do?

This includes:

- inputs;
- outputs;
- validations;
- business rules;
- statuses;
- permissions;
- dependencies;
- downstream effects;
- edge cases;
- success/error states;
- accepted navigation outcomes.

### User intent
What is the Admin or Member actually trying to accomplish?

### Interaction redesign
How can that task be made clearer, faster and more intuitive without breaking the underlying behaviour?

### Visual redesign
How should the final experience look and respond across desktop/mobile, light/dark mode and supported browsers?

### Functional parity validation
Does the new implementation still perform the underlying HealthyMe job correctly?

A screen does not pass merely because it renders successfully or looks better.

---

## 5. UX doctrine — reduce cognitive load

The web application should adopt the same product-thinking direction being applied to the newer HealthyMe native experience.

The user should not have to remember:

- where a feature lives;
- which menu contains a task;
- whether something is due;
- which meal, supplement or exercise is relevant now;
- what to do next;
- whether an item has already been completed.

The application should make the next useful action obvious.

Key UX principles:

- clear hierarchy;
- fewer competing elements;
- logical grouping;
- one obvious primary action where possible;
- progressive disclosure instead of showing everything at once;
- sensible defaults;
- contextual information at the point of action;
- reduced unnecessary clicks and refreshes;
- responsive behaviour;
- visible loading, success, error and empty states;
- consistent terminology;
- accessible contrast and interaction states;
- minimal reliance on memory or app training.

---

## 6. Member experience — proactive, contextual and time-aware

This is a core design rule, not an enhancement.

**Do not make the member navigate to relevant information. Bring relevant information to the member.**

The member-facing app should organize relevant information around:

- **Now** — what applies at this moment;
- **Next** — the next meal, supplement, exercise, task or consultation requiring attention;
- **Later** — upcoming items that do not require immediate action;
- **Done** — completed or acknowledged items.

Where existing HealthyMe data already includes timing, schedule, due-date or allocation information, the new frontend should use that information to prioritize what the member sees.

Examples:

- a meal becomes prominent as its scheduled time approaches;
- a supplement linked to a meal appears in that context;
- an exercise due later in the day moves into the Next position;
- a task with a due date is surfaced before it becomes overdue;
- an upcoming consultation appears contextually rather than requiring menu discovery;
- completed items naturally move out of the primary attention area.

This should generally be implemented with contextual cards, timely prompts and notifications rather than excessive blocking pop-ups.

Member UAT must include the question:

> Can the member understand what applies to them and what they should do next without remembering the app structure?

If the answer is no, the experience is not yet sufficiently intuitive even if the functionality is technically present.

---

## 7. Admin experience — workflow-first, not dashboard-first

The HealthyMe Admin application has evolved beyond a simple internal dashboard. It contains transactional workflows such as:

- member/profile management;
- Meal Builder;
- Exercise Allocation;
- Supplement Allocation;
- repository management;
- publishing;
- editing;
- plan review;
- notifications and workflow states.

The migration should therefore treat Admin as a proper operational application.

Admin redesign should optimize for:

- clear task flows;
- compact but readable information density;
- strong form structure;
- obvious editing/publishing states;
- predictable navigation;
- preserved context when moving between screens;
- low-risk actions;
- clear validation;
- minimal rerender/refresh disruption;
- responsive layout;
- consistency across related builders and repositories.

The objective is not to expose every available backend field. It is to show the information and controls needed to complete the current Admin task correctly.

---

## 8. Example standard — Meal Builder

The Meal Builder must not be reproduced as a visually improved copy of the existing Streamlit form.

### Preserve functionality

- repository food selection;
- meal construction;
- portions and serving units;
- day allocation;
- plan dates;
- member allocation;
- publishing;
- saved/published plan behaviour;
- relevant notifications/status effects;
- existing business and data rules.

### Improve interaction

- clearer plan-level controls;
- better grouping of meal sections;
- fewer distracting controls;
- sensible Add Meal / Remove Meal placement;
- better day selection;
- dropdown/multiselect where appropriate;
- structured HH/MM inputs where required;
- obvious Draft/Publish state;
- clearer archived/published plan reuse where supported by current functionality;
- more compact use of space;
- clearer validation messages;
- reduced confusion between plan-level and meal-level actions.

The same preserve-then-redesign pattern applies to Exercise Allocation, Supplement Allocation, Member/Profile management, Repository and the remaining web workflows.

---

## 9. Architecture

### Existing system

- Streamlit remains active as the current functional implementation during migration.
- Existing HealthyMe Supabase remains the backend.

### New system

- Next.js App Router + TypeScript under `/web`;
- hosted independently on Vercel;
- existing HealthyMe Supabase used for Auth/data/storage under existing rules;
- Supabase SSR session handling for the Next.js web app;
- privileged/service credentials must never be shipped to browser code.

High-level architecture:

`Existing Streamlit frontend -> existing HealthyMe Supabase <- new Next.js/Vercel frontend`

Both frontends may coexist during migration.

---

## 10. Authentication and authorization

Authentication and authorization are high-risk areas and are not to be casually redesigned.

The Next.js implementation must reproduce accepted HealthyMe outcomes, including:

- Supabase sign-in;
- durable browser session/reload behaviour;
- secure sign-out;
- canonical `hm_users` mapping;
- Admin vs Member role routing;
- inactive/unauthorized user rejection;
- direct-route handling;
- no silent re-login after explicit logout.

The canonical role model remains authoritative. The migration must not create a parallel or conflicting authorization model merely because it is easier in Next.js.

The Streamlit login should not be retired until the new authentication/session behaviour passes focused browser UAT.

---

## 11. Branding and naming

The product name is intentionally decoupled from application functionality.

`HealthyMe` remains the working/default name until a replacement brand is approved.

Branding must be centralized through configuration/assets so a later change of:

- product name;
- logo;
- tagline;
- favicon;
- core brand assets;

can be made without rewriting screens or touching business logic.

No migration work should be blocked by the unresolved final brand name.

`Intuitive Nutrition` must not be hard-coded as the final name because the name/conflict screening did not support treating it as a cleared final brand.

The intended pattern is:

`Product identity -> configuration`

`Application functionality -> independent of product identity`

---

## 12. Migration method

The migration is progressive, never big-bang.

For each slice:

`Existing Streamlit workflow -> understand functional baseline -> redesign IA/UX -> implement in Next.js -> compare behaviour -> focused UAT -> accept -> retire only that old workflow`

Until a slice is explicitly accepted, the Streamlit implementation remains the reference/fallback.

No old workflow is retired merely because the new screen renders successfully.

---

## 13. Migration sequence

### Gate 0 — Foundation

- parallel Next.js application under `/web`;
- current framework conventions;
- Supabase browser/server session plumbing;
- Vercel capable of targeting `/web` independently;
- no production backend change.

### Gate 1 — Authentication/session parity

- Supabase login;
- session persistence/reload;
- secure logout;
- canonical `hm_users` authorization;
- Admin/Member routing;
- direct-page routing/return behaviour;
- inactive/unauthorized handling;
- no silent re-login.

### Gate 2 — Admin shell and Admin Dashboard

Rebuild the shell and dashboard using the new interaction/visual standards while preserving underlying data and accepted actions.

### Gate 3 onward — controlled workflow slices

Current intended order:

1. Member/Profile management;
2. Meal Builder;
3. Exercise Allocation;
4. Supplement Allocation;
5. Repository;
6. remaining Admin workflows;
7. Member Web workflows if retained.

The sequence may be adjusted by explicit product direction, but the preserve-redesign-validate replacement method does not change.

---

## 14. Visual and interaction quality standard

Next.js/Vercel is being adopted to obtain stronger control over the experience. The migration should therefore materially improve:

- information hierarchy;
- visual clarity;
- responsive design;
- mobile/desktop behaviour;
- light/dark mode;
- Safari/Apple compatibility;
- transitions and state changes;
- perceived performance;
- form usability;
- consistency;
- component reuse;
- navigation predictability;
- avoidance of visible page-wide refresh behaviour where unnecessary.

Visual decoration is important, but it follows functional structure and interaction clarity. A visually polished but confusing workflow is not acceptable.

---

## 15. Functional quality standard

Functionality remains the final gate.

Every migrated slice must preserve all applicable:

- data reads/writes;
- permissions;
- status transitions;
- validation rules;
- lifecycle behaviour;
- notifications;
- history;
- downstream effects;
- completion logic;
- role boundaries.

The migration must not silently remove functionality merely because it is hard to reproduce elegantly.

If existing functionality is intentionally to be removed or changed, that is a product decision and requires explicit approval rather than being bundled into the migration.

---

## 16. Validation standard

Every migrated slice must pass, as applicable:

1. lint;
2. TypeScript type checking;
3. production build;
4. relevant automated regression coverage;
5. focused browser tests for the new workflow;
6. responsive checks;
7. light/dark-mode checks;
8. Apple/Safari checks where relevant;
9. functional comparison with accepted Streamlit behaviour;
10. manual UAT before retirement of the old section.

Member-facing slices additionally require an intuitiveness check: the member must be able to identify what applies now and what to do next without relying on memory of the application structure.

Admin-facing slices additionally require a workflow check: the Admin must be able to complete the intended operational task with clear context, state and validation.

---

## 17. Regression and rollback rule

- Existing Streamlit remains operational during migration.
- New Next.js work remains isolated until validated.
- A migrated slice is not authoritative until accepted.
- If a new slice fails UAT or causes regression, the existing Streamlit path remains the fallback.
- Backend changes must not be used as a shortcut to make migration easier.
- New work must account for previously accepted HealthyMe behaviour and avoid reintroducing known regressions.

---

## 18. Development decision checklist

Before implementing any migration change, answer:

1. What current HealthyMe functionality does this replace?
2. What user problem/task is being solved?
3. What existing behaviour must be preserved?
4. Can the interaction be made more intuitive than the Streamlit implementation?
5. Does the user have to remember where to look, or can the app surface the right information proactively?
6. Is any backend change being proposed? If yes, is it truly critical?
7. Could the same goal be achieved safely in the frontend instead?
8. Does the design work responsively and in light/dark mode?
9. How will functional parity be tested?
10. What is the rollback/fallback until acceptance?

If these questions cannot be answered, implementation should not proceed as an ordinary migration task.

---

## 19. Governing summary

The HealthyMe web migration is governed by five non-negotiable ideas:

1. **Preserve functionality.**
2. **Protect the backend.**
3. **Redesign the experience instead of copying Streamlit.**
4. **Make the app proactive and intuitive so users do not have to hunt or remember.**
5. **Replace progressively and validate before retiring anything.**

This document is the standing reference for further HealthyMe Next.js/Vercel development until superseded by a later explicit product decision.