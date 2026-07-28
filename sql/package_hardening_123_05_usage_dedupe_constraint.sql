-- PostgREST upsert support for immutable package usage audit.
-- PostgreSQL UNIQUE permits multiple NULL values, so a full unique index is safe.

drop index if exists public.hm_package_usage_dedupe_idx;
create unique index hm_package_usage_dedupe_idx
  on public.hm_package_usage_events(dedupe_key);
