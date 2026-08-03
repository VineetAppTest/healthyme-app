-- Normalize Gate 8 public and service-role grants after creation.
revoke all on table public.hm_identity_manual_smoke_evidence from public, anon, authenticated;
grant select, insert on table public.hm_identity_manual_smoke_evidence to service_role;

revoke execute on function public.hm_admin_record_identity_smoke_evidence(
  text, text, text, text, text, text, jsonb, text, text, text, text, timestamptz, jsonb
) from public, anon, authenticated;
grant execute on function public.hm_admin_record_identity_smoke_evidence(
  text, text, text, text, text, text, jsonb, text, text, text, text, timestamptz, jsonb
) to service_role;

revoke execute on function public.hm_identity_projection_retirement_readiness(integer)
  from public, anon, authenticated;
grant execute on function public.hm_identity_projection_retirement_readiness(integer)
  to service_role;
