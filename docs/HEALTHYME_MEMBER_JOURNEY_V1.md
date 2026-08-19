# HealthyMe Member Journey V1

**Status:** Governing member-experience blueprint for the Next.js migration  
**Effective date:** 2026-08-19  
**Parent authority:** `docs/HEALTHYME_WEB_MIGRATION_SOURCE_OF_TRUTH.md`  
**Direction:** Member journey is the first product journey to be migrated after authentication/session parity.

## 1. Purpose

The Member Web migration is not a page-for-page copy of Streamlit. It preserves HealthyMe member functionality while reorganising the experience so the application tells the member what matters now, what comes next, what requires action, and what is already complete.

The target experience must minimise memory dependence and menu hunting.

Governing pattern:

`Existing member capability -> derive current context -> surface current/next action -> allow deeper browse -> preserve functional outcomes`

## 2. Current functional baseline

The existing Streamlit member experience currently spans these functional areas:

- `pages/01_Login.py` — authentication entry and role routing;
- `pages/02_Member_Home.py` — upcoming consultations, nutritionist messages, assessment/task progress, current workflow status, and links to personalised content;
- `pages/03_LAF_Form.py` — Lifestyle Assessment Form;
- `pages/04_NSP_Page1.py` and `pages/05_NSP_Page2.py` — requested NSP assessment tasks;
- `pages/06_Submit_Status.py` — task completion gate, submission to Admin Review, and assessment history;
- `pages/07_My_Profile.py` — member profile plus member-local timezone configuration;
- `pages/14_Final_Assessment_Report.py` and related assessment/report pages — member assessment output where applicable;
- `pages/18_Daily_Log.py` — daily food, fluid, bowel/notes and related journaling behaviour;
- `pages/19_Body_Mind_Connection.py` — gated Body-Mind task with autosave and explicit completion;
- `pages/33_My_Schedule.py` — package/schedule information, acknowledgement and reschedule workflow;
- `pages/36_Todays_Journey.py` — unified current-day meal, supplement and exercise plan presentation;
- `pages/37_Member_Plan.py` — complete seven-day member plan;
- `pages/40_Member_Supplements.py` — active supplement regimen;
- `pages/41_Member_Exercise.py` — prescribed exercise plus progress recording.

This list is a functional inventory, not the target navigation structure.

## 3. Core member experience rule

**Do not make the member navigate to relevant information. Bring relevant information to the member.**

The primary member experience is organised conceptually around:

- **Now** — the item or action that is relevant at the present moment;
- **Next** — the next meaningful action or scheduled item;
- **Later** — upcoming items that do not require immediate attention;
- **Done** — items with an authoritative existing completion or acknowledgement state.

Important: the frontend must never infer completion merely because time has passed or a card was viewed. `Done` is used only when existing HealthyMe data/business logic provides an authoritative completion/acknowledgement state.

## 4. Member lifecycle states

The member home experience must adapt to the member's lifecycle instead of showing the same dashboard to every member.

### State A — Initial setup / assessment

Typical conditions:

- LAF incomplete; or
- NSP tasks requested and incomplete; or
- Body-Mind explicitly requested/unlocked and incomplete.

Primary experience:

- one dominant `Continue assessment` / current-task card;
- progress across requested tasks;
- due date when present;
- direct action to the next incomplete task;
- completed tasks remain visible as completed, not as competing calls to action;
- Submit for Admin Review becomes prominent only when all required tasks are complete.

The member should not have to choose between NSP Page 1, NSP Page 2 and Body-Mind based on memory if the system can identify the next incomplete required task.

### State B — Submitted / under review

Typical condition:

- current assessment instance submitted for review.

Primary experience:

- clear `Under review` state;
- what has been submitted;
- no misleading active-task CTA;
- relevant consultation/messages remain available;
- existing allowed tools remain available without implying that the review is complete.

### State C — Active plan

Typical condition:

- expert review/finalisation has made the member plan available.

Primary experience:

- time-aware Today experience;
- current/next meal, supplement and exercise surfaced contextually;
- upcoming consultation/task/message surfaced when relevant;
- quick access to log actual behaviour;
- full weekly plan available as secondary/deeper browse.

### State D — Reassessment / task request while active plan continues

Typical condition:

- a Task Request or Reassessment instance is active while normal plan content remains valid.

Primary experience:

- reassessment/task requirement becomes a high-priority action without hiding the member's active care plan;
- due dates and incomplete requested pages are surfaced;
- Today plan remains accessible;
- completed reassessment tasks move to completed state;
- Submit to Admin Review becomes available only when existing task-completion rules say the instance is complete.

## 5. Target information architecture

The member web experience should use a small, persistent primary navigation rather than reproducing every Streamlit page as a top-level destination.

### Primary destinations

1. **Today**
   - default member landing destination;
   - lifecycle-aware current state;
   - Now / Next / Later / Done;
   - assessment/task priority when applicable;
   - upcoming consultation;
   - nutritionist communication;
   - quick logging actions.

2. **Plan**
   - today's plan plus full seven-day browse;
   - unified meals, supplements and exercise;
   - day selector / week view;
   - relevant instructions and timings;
   - active-plan information only; no invented completion state.

3. **Log**
   - actual behaviour recording;
   - food/meals;
   - hydration/other fluids;
   - bowel/notes where retained by current functionality;
   - exercise progress/logging;
   - saved-day/history access where current functionality provides it.

4. **More**
   - Schedule;
   - Profile and timezone;
   - assessment/report history;
   - other lower-frequency member functions that should not compete with daily actions.

On mobile this can become a compact bottom navigation. On desktop it may use a compact rail/header navigation, but destination names and hierarchy should remain consistent.

## 6. Today page priority model

The Today page is the core of the new member experience. It should not be a generic dashboard grid.

Priority order should be derived from existing member state:

1. **Critical current action**
   - overdue/urgent requested task if existing data supports urgency;
   - assessment/reassessment next incomplete task;
   - consultation acknowledgement/reschedule state requiring action;
   - otherwise current time-relevant plan item.

2. **Now**
   - current meal/meal period;
   - related supplement timing where existing allocation permits association/context;
   - exercise when its timing/context makes it current;
   - exact language should reflect the precision of stored data. Do not fabricate clock times when HealthyMe only stores a period/meal label.

3. **Next**
   - next scheduled or logically ordered plan item;
   - next requested task if assessment workflow is active;
   - upcoming consultation when relevant.

4. **Later today / upcoming**
   - compact timeline/list of remaining applicable items;
   - upcoming consultation or task due date;
   - not all information expanded at once.

5. **Done**
   - acknowledged consultations;
   - completed assessment pages/tasks;
   - completed/logged items only where the existing backend has an authoritative state;
   - collapsed/secondary by default.

6. **Communication**
   - nutritionist messages surfaced without forcing navigation to a separate message screen;
   - archived/read behaviour must preserve existing semantics.

## 7. Time-awareness rules

Member-local timezone already matters to HealthyMe and must remain authoritative.

The frontend may use existing member-local timezone/profile information to rank and label current content.

Rules:

- do not use server time as member-local time;
- do not fabricate exact times from labels such as Breakfast, Lunch, Evening or Bedtime;
- if only a period is known, show period-aware wording (`Lunch`, `This evening`, `Before bed`) rather than invented times;
- if an exact time exists, it may be used for sorting/current-next context;
- scheduling and reschedule requests must continue to respect member-local timezone semantics;
- plan visibility and start/end date rules remain backend/data-contract driven.

## 8. Assessment and task UX

Current assessment functionality must be preserved, but the member should not be forced to understand the assessment-instance machinery.

The frontend should translate state into plain actions:

- `Complete your Lifestyle Assessment`;
- `Continue NSP Page 1`;
- `Continue NSP Page 2`;
- `Complete Body-Mind`;
- `All requested tasks complete — submit for review`;
- `Submitted — under review`.

The existing requested-pages rules, task completion states, Body-Mind gating, due date, submission idempotency and Admin Review outcomes remain authoritative.

Assessment history remains available, but should not compete with the member's current action.

## 9. Plan UX

The Plan experience should unify information that is currently split across Today’s Plan, Weekly Plan, Supplements and Exercise views.

Target structure:

- day selector with Today prominent;
- chronological/period-based sequence;
- each item labelled as Meal, Supplement or Exercise;
- essential instruction visible without opening another page;
- deeper detail on demand;
- week overview available without forcing horizontal-table interaction on small screens;
- current/upcoming allocations honoured using existing date rules;
- no backend schema change merely to obtain a cleaner layout.

Separate detailed supplement/exercise views may remain as drill-downs where useful, but they should not be required for the member to understand today's instructions.

## 10. Log UX

The Daily Log remains the record of actual behaviour and must not be confused with the prescribed Plan.

Product distinction:

- **Plan = what has been recommended/prescribed.**
- **Log = what the member actually did/consumed/recorded.**

The new UI should make this distinction obvious.

The log should support quick entry from Today where safe, with the full Log destination available for detailed editing/history.

Existing autosave/server-save behaviour, saved-day/history behaviour, validation and journal data contracts must be preserved.

## 11. Schedule UX

Upcoming consultations should be surfaced on Today when relevant, but Schedule remains the full management view.

Preserve:

- package usage/status where applicable;
- member-local time presentation;
- schedule acknowledgement;
- reschedule eligibility;
- pending reschedule state;
- within-24-hour policy/confirmation;
- preferred date/time and reason;
- existing Admin review outcome.

The new experience should avoid unnecessary page-wide refreshes and keep context stable while acknowledging or requesting a reschedule.

## 12. Messages / nutritionist communication

Nutritionist messages should be contextual member information, not a destination the member must remember to visit.

Preserve:

- unread/current messages;
- message subject/date/body;
- archive/read action and downstream archive semantics.

A new message should be visible from Today/notification context. Archived/history access can remain secondary.

## 13. Profile and timezone

Profile is a lower-frequency destination but timezone is a high-impact input to the proactive experience.

Preserve:

- LAF-to-profile population behaviour;
- editable profile fields;
- validation;
- country/city/timezone selection;
- member-local timezone persistence;
- downstream use of member-local date/time.

The member should not have to visit Profile routinely for the Today experience to work.

## 14. Responsive behaviour

Member web must be designed mobile-first without becoming a stretched mobile layout on desktop.

Requirements:

- one-hand-friendly primary actions on mobile;
- no essential functionality hidden behind hover;
- no wide tables as the only way to read a weekly plan;
- compact bottom navigation on mobile;
- readable desktop density;
- consistent light/dark mode;
- Safari/iPhone/Mac contrast and input-state validation;
- no content jump caused by routine interactions where avoidable.

## 15. Backend boundary

No backend change is authorised by this member-journey redesign.

Implementation should use frontend adapters/selectors to turn existing HealthyMe data into the new journey model.

If a desired interaction cannot be supported from existing data, the implementation must first distinguish:

1. presentation limitation that can be solved in frontend;
2. missing derived logic that can be computed safely in frontend;
3. genuinely missing backend capability.

Only category 3 can become a separate backend-change proposal, with explicit impact assessment and approval.

## 16. Frontend orchestration model

The Next.js frontend should introduce a member orchestration layer that converts existing backend data into a presentation model without changing source records.

Conceptual inputs:

- authenticated member identity;
- canonical member role/active status;
- workflow state;
- current assessment instance and requested pages;
- task completion/submission state;
- current member plan allocations;
- member-local timezone;
- upcoming schedules and acknowledgement/reschedule state;
- current nutritionist messages;
- existing journal/completion states.

Conceptual output:

- lifecycle state;
- primary current action;
- Now items;
- Next item(s);
- Later items;
- Done items backed by authoritative completion state;
- secondary navigation destinations.

This orchestration layer is a frontend interpretation layer only. It must not become a second source of truth for business state.

## 17. Migration order — member first

### Member Gate M0 — Member journey contract

- current member functional inventory completed;
- target IA and lifecycle states defined;
- backend boundary confirmed;
- no production changes.

### Member Gate M1 — Authentication/session/member-role parity

- Supabase member sign-in;
- durable browser session/reload;
- canonical `hm_users` active-member authorisation;
- secure logout;
- direct-route protection/return behaviour;
- no silent re-login.

### Member Gate M2 — Member shell + Today read-only orchestration

- persistent member navigation;
- responsive shell;
- member-local context;
- lifecycle-aware Today presentation;
- read-only current plan/messages/schedule/task state first;
- no write behaviour until the relevant contract is validated.

### Member Gate M3 — Assessment/task actions

- LAF / NSP / Body-Mind navigation and completion parity;
- Submit to Admin Review parity;
- due date/progress;
- task/request/reassessment lifecycle.

### Member Gate M4 — Plan

- Today + seven-day plan;
- meals + supplements + exercise unified presentation;
- responsive week browse.

### Member Gate M5 — Log / actual behaviour

- Daily Log parity;
- exercise progress/logging;
- autosave/save/history behaviour.

### Member Gate M6 — Schedule + communication

- acknowledgement;
- reschedule;
- package/schedule view;
- nutritionist message archive/history.

### Member Gate M7 — Profile/reports/remaining member functions

- profile/timezone;
- assessment/report access;
- remaining lower-frequency member functions.

### Member Gate M8 — End-to-end UAT and cutover

- full lifecycle UAT across assessment, review, active plan and reassessment states;
- responsive/light/dark/Safari checks;
- old Streamlit member journey remains fallback until accepted;
- retirement only after explicit acceptance.

## 18. Member UAT questions

Every member slice must answer yes to the applicable questions:

1. Can the member tell what matters now without navigating through menus?
2. Can the member tell what to do next?
3. Is the primary action obvious?
4. Are plan and actual-log concepts clearly separated?
5. Are dates/times shown in the member's correct local context?
6. Are completed items only marked completed when HealthyMe has an authoritative state?
7. Can the member reach full details/history when needed?
8. Does the workflow preserve existing validations, permissions, downstream effects and submission rules?
9. Does the experience remain clear on mobile, desktop, light and dark mode?
10. Can the old Streamlit member path still serve as fallback until acceptance?

## 19. Immediate implementation decision

The migration proceeds member-first.

Authentication/session parity remains the first technical safety gate because all member data and routes depend on identity and canonical role resolution. After that, the first product screen is the lifecycle-aware **Today** experience, not the Admin Dashboard.
