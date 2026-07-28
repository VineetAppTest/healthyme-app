-- Package Hardening 1, 2 and 3: covering indexes for member foreign keys.

create index if not exists hm_package_usage_events_member_idx
  on public.hm_package_usage_events(member_id, created_at desc);

create index if not exists hm_package_payments_member_idx
  on public.hm_package_payments(member_id, created_at desc);

create index if not exists hm_package_subscription_events_member_idx
  on public.hm_package_subscription_events(member_id, created_at desc);
