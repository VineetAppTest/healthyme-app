-- Gate 8 evidence remains readable to service role, but direct writes are removed.
-- All evidence inserts must use hm_admin_record_identity_smoke_evidence(...).
revoke all on table public.hm_identity_manual_smoke_evidence from service_role;
grant select on table public.hm_identity_manual_smoke_evidence to service_role;
