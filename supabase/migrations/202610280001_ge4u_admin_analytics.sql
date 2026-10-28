-- GE4u Supabase foundation. All timestamps are timestamptz (UTC).
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  status text not null default 'active' check (status in ('active', 'disabled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists profiles_created_at_idx on public.profiles (created_at desc);
alter table public.profiles enable row level security;
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles for select to authenticated using (id = (select auth.uid()));
revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;

create or replace function public.handle_new_auth_user()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name, status)
  values (new.id, nullif(trim(coalesce(new.raw_user_meta_data ->> 'display_name', '')), ''), 'active')
  on conflict (id) do nothing;
  return new;
end;
$$;
drop trigger if exists on_auth_user_created_ge4u on auth.users;
create trigger on_auth_user_created_ge4u after insert on auth.users for each row execute procedure public.handle_new_auth_user();

create table if not exists public.page_events (
  id bigint generated always as identity primary key,
  visitor_id uuid not null,
  session_id uuid not null,
  path text not null check (length(path) between 1 and 300 and left(path, 1) = '/'),
  referrer_host text,
  event_type text not null default 'page_view' check (event_type = 'page_view'),
  created_at timestamptz not null default now()
);
create index if not exists page_events_created_at_idx on public.page_events (created_at desc);
create index if not exists page_events_session_created_idx on public.page_events (session_id, created_at desc);
create index if not exists page_events_visitor_created_idx on public.page_events (visitor_id, created_at desc);
alter table public.page_events enable row level security;
revoke all on public.page_events from anon, authenticated;

create table if not exists public.learning_events (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  channel_id text not null check (length(channel_id) between 1 and 80),
  event_type text not null check (event_type in ('lesson_started', 'lesson_completed', 'quiz_answered', 'vocabulary_reviewed')),
  item_id text check (item_id is null or length(item_id) <= 160),
  result jsonb not null default '{}'::jsonb,
  idempotency_key uuid not null,
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (user_id, idempotency_key)
);
create index if not exists learning_events_user_time_idx on public.learning_events (user_id, occurred_at desc);
create index if not exists learning_events_channel_time_idx on public.learning_events (channel_id, occurred_at desc);
alter table public.learning_events enable row level security;
drop policy if exists "learning_events_select_own" on public.learning_events;
create policy "learning_events_select_own" on public.learning_events for select to authenticated using (user_id = (select auth.uid()));
revoke all on public.learning_events from anon, authenticated;
grant select on public.learning_events to authenticated;

create table if not exists public.audit_events (
  id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id) on delete set null,
  action text not null check (length(action) between 1 and 120),
  target_type text check (target_type is null or length(target_type) <= 80),
  target_id text check (target_id is null or length(target_id) <= 160),
  outcome text not null check (outcome in ('success', 'denied', 'failure')),
  request_id uuid not null default gen_random_uuid(),
  metadata jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);
create index if not exists audit_events_time_idx on public.audit_events (occurred_at desc);
create index if not exists audit_events_actor_time_idx on public.audit_events (actor_id, occurred_at desc);
alter table public.audit_events enable row level security;
revoke all on public.audit_events from anon, authenticated;

create or replace function public.ge4u_admin_overview(p_start timestamptz, p_end timestamptz)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare result jsonb;
begin
  if p_start is null or p_end is null or p_end <= p_start or p_end - p_start > interval '366 days' then
    raise exception 'Invalid date range';
  end if;
  select jsonb_build_object(
    'source', 'supabase', 'as_of', now(), 'range_start', p_start, 'range_end', p_end,
    'accounts_total', (select count(*) from public.profiles),
    'accounts_new_in_range', (select count(*) from public.profiles where created_at >= p_start and created_at < p_end),
    'page_views', (select count(*) from public.page_events where created_at >= p_start and created_at < p_end),
    'visits', (select count(distinct session_id) from public.page_events where created_at >= p_start and created_at < p_end),
    'unique_visitors', (select count(distinct visitor_id) from public.page_events where created_at >= p_start and created_at < p_end),
    'learning_events', (select count(*) from public.learning_events where occurred_at >= p_start and occurred_at < p_end),
    'status', 'ok'
  ) into result;
  return result;
end;
$$;
revoke all on function public.ge4u_admin_overview(timestamptz, timestamptz) from public, anon, authenticated;
grant execute on function public.ge4u_admin_overview(timestamptz, timestamptz) to service_role;
-- Assign admin only through trusted Auth app_metadata. Never trust user-editable user_metadata.
