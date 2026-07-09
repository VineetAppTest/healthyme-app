# H9A.6C Profile Builder Default Values Rule

Sprint 1 acceptance rule:

- User-entered fields should start blank.
- Choice fields should start with a clear `-- Select ... --` value.
- Only system-controlled fields may have defaults.

Allowed defaults:

- Profile Status = Draft
- Plan Start Date = Today
- Cycle Rule = Weekly cyclical until replaced or stopped
- Implementation Status = Sprint 1: draft save/load only

Select placeholders must not be saved as real business data.
