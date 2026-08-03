-- HealthyMe Content Repository privilege hardening.
--
-- Supabase default privileges can grant service_role broader permissions when a
-- public table is created. Reset the grants explicitly so the application can
-- read and mutate repository records without being able to delete or truncate
-- repository history.

revoke all on table public.hm_content_repository_items from service_role;
revoke all on table public.hm_content_repository_events from service_role;
revoke all on function public.hm_set_content_repository_updated_at() from service_role;
revoke all on function public.hm_capture_content_repository_event() from service_role;

grant select, insert, update on table public.hm_content_repository_items to service_role;
grant select, insert on table public.hm_content_repository_events to service_role;
grant execute on function public.hm_set_content_repository_updated_at() to service_role;
grant execute on function public.hm_capture_content_repository_event() to service_role;
