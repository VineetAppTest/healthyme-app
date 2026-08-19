-- Production operation for HealthyMe project arptwzvlugxrqtvbrmtl.
-- Run only after the consultation-reminders Edge Function and the reminder
-- ledger migration are deployed to the target project.

create extension if not exists pg_cron with schema pg_catalog;
create extension if not exists pg_net with schema extensions;
create extension if not exists pgcrypto with schema extensions;
create extension if not exists supabase_vault with schema vault;

-- The cron invocation secret is generated inside Postgres and remains encrypted
-- at rest in Supabase Vault. It is never stored in Git or returned to the app.
do $$
begin
    if not exists (
        select 1
        from vault.decrypted_secrets
        where name = 'healthyme_consultation_cron_secret'
    ) then
        perform vault.create_secret(
            encode(extensions.gen_random_bytes(32), 'hex'),
            'healthyme_consultation_cron_secret',
            'Authenticates the HealthyMe consultation reminder cron to its Edge Function.'
        );
    end if;
end
$$;

select cron.schedule(
    'healthyme-consultation-reminders-15m',
    '*/15 * * * *',
    $cron$
    select net.http_post(
        url := 'https://arptwzvlugxrqtvbrmtl.supabase.co/functions/v1/consultation-reminders',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'x-healthyme-cron-secret', (
                select decrypted_secret
                from vault.decrypted_secrets
                where name = 'healthyme_consultation_cron_secret'
                limit 1
            )
        ),
        body := jsonb_build_object(
            'trigger', 'supabase_cron',
            'invoked_at', now()
        ),
        -- Gmail SMTP delivery may take longer than a simple HTTP-provider call.
        -- The Edge Function processes a bounded batch and Free-plan functions
        -- have a 150-second wall-clock limit, so keep the caller below that.
        timeout_milliseconds := 120000
    ) as request_id;
    $cron$
);

-- Verification queries (read-only):
-- select jobid, jobname, schedule, active from cron.job
-- where jobname = 'healthyme-consultation-reminders-15m';
--
-- select jobid, runid, status, return_message, start_time, end_time
-- from cron.job_run_details
-- where jobid = (
--     select jobid from cron.job
--     where jobname = 'healthyme-consultation-reminders-15m'
-- )
-- order by start_time desc
-- limit 10;