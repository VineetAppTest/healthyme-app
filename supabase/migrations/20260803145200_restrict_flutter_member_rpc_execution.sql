-- HealthyMe Users/Workflow Batch 2B, Gate 1 follow-up
-- Remove anonymous/default execution from the authenticated Flutter identity
-- link and NSP read/write RPCs while preserving their existing signatures and
-- authenticated mobile access.

revoke all on function public.hm_flutter_link_current_member_auth_user() from PUBLIC;
revoke all on function public.hm_flutter_link_current_member_auth_user() from anon;
revoke all on function public.hm_flutter_link_current_member_auth_user() from authenticated;
grant execute on function public.hm_flutter_link_current_member_auth_user() to authenticated;

revoke all on function public.hm_flutter_get_nsp() from PUBLIC;
revoke all on function public.hm_flutter_get_nsp() from anon;
revoke all on function public.hm_flutter_get_nsp() from authenticated;
grant execute on function public.hm_flutter_get_nsp() to authenticated;

revoke all on function public.hm_flutter_save_nsp1_draft(jsonb) from PUBLIC;
revoke all on function public.hm_flutter_save_nsp1_draft(jsonb) from anon;
revoke all on function public.hm_flutter_save_nsp1_draft(jsonb) from authenticated;
grant execute on function public.hm_flutter_save_nsp1_draft(jsonb) to authenticated;

revoke all on function public.hm_flutter_submit_nsp1(jsonb) from PUBLIC;
revoke all on function public.hm_flutter_submit_nsp1(jsonb) from anon;
revoke all on function public.hm_flutter_submit_nsp1(jsonb) from authenticated;
grant execute on function public.hm_flutter_submit_nsp1(jsonb) to authenticated;

revoke all on function public.hm_flutter_save_nsp2_draft(jsonb) from PUBLIC;
revoke all on function public.hm_flutter_save_nsp2_draft(jsonb) from anon;
revoke all on function public.hm_flutter_save_nsp2_draft(jsonb) from authenticated;
grant execute on function public.hm_flutter_save_nsp2_draft(jsonb) to authenticated;

revoke all on function public.hm_flutter_submit_nsp2(jsonb) from PUBLIC;
revoke all on function public.hm_flutter_submit_nsp2(jsonb) from anon;
revoke all on function public.hm_flutter_submit_nsp2(jsonb) from authenticated;
grant execute on function public.hm_flutter_submit_nsp2(jsonb) to authenticated;

revoke all on function public.hm_flutter_submit_assessment_review() from PUBLIC;
revoke all on function public.hm_flutter_submit_assessment_review() from anon;
revoke all on function public.hm_flutter_submit_assessment_review() from authenticated;
grant execute on function public.hm_flutter_submit_assessment_review() to authenticated;
