-- Package Hardening 1, 2 and 3: explicit function execution boundaries.
-- Supabase default function grants can expose SECURITY DEFINER functions to anon and
-- authenticated roles unless those roles are revoked directly.

revoke all on function public.hm_package_require_admin(text) from public, anon, authenticated;
revoke all on function public.hm_admin_save_package(text,text,integer,numeric,numeric,text,jsonb,text,text) from public, anon, authenticated;
revoke all on function public.hm_admin_assign_member_package(text,text,date,date,text,numeric,date,text,text,text,text,integer,text) from public, anon, authenticated;
revoke all on function public.hm_admin_adjust_package_sessions(text,text,integer,text,text) from public, anon, authenticated;
revoke all on function public.hm_admin_update_package_subscription(text,text,text,date,text,numeric,date,text,text) from public, anon, authenticated;
revoke all on function public.hm_admin_record_schedule_limit_override(text,text,text,text) from public, anon, authenticated;

revoke all on function public.hm_package_schedule_subscription_id(jsonb) from public, anon, authenticated;
revoke all on function public.hm_package_schedule_cost(jsonb) from public, anon, authenticated;
revoke all on function public.hm_package_subscription_metrics(text) from public, anon, authenticated;
revoke all on function public.hm_package_member_summary(text) from public, anon, authenticated;

revoke all on function public.hm_member_schedule_contract() from public, anon, authenticated;

grant execute on function public.hm_package_require_admin(text) to service_role;
grant execute on function public.hm_admin_save_package(text,text,integer,numeric,numeric,text,jsonb,text,text) to service_role;
grant execute on function public.hm_admin_assign_member_package(text,text,date,date,text,numeric,date,text,text,text,text,integer,text) to service_role;
grant execute on function public.hm_admin_adjust_package_sessions(text,text,integer,text,text) to service_role;
grant execute on function public.hm_admin_update_package_subscription(text,text,text,date,text,numeric,date,text,text) to service_role;
grant execute on function public.hm_admin_record_schedule_limit_override(text,text,text,text) to service_role;
grant execute on function public.hm_package_schedule_subscription_id(jsonb) to service_role;
grant execute on function public.hm_package_schedule_cost(jsonb) to service_role;
grant execute on function public.hm_package_subscription_metrics(text) to service_role;
grant execute on function public.hm_package_member_summary(text) to service_role;

-- This is the only Package Hardening function exposed to signed-in members. It
-- resolves the member exclusively from auth.jwt()->>'email'.
grant execute on function public.hm_member_schedule_contract() to authenticated;
grant execute on function public.hm_member_schedule_contract() to service_role;
