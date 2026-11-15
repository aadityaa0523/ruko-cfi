-- Ruko: anonymous impact events, shown publicly at /impact/.
-- Applied to project izxqlbipvrtnsvpwekaw. Safe to re-run.
-- Stored per event: a random device id made in the browser, the event kind, language, a level and (quiz only) a score.
-- Never stored: message text, phone numbers, names, raw IP. The network is a salted hash, used only to cap abuse
-- and to count distinct networks.

create table if not exists public.impact_events (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  device text not null check (device ~ '^[a-z0-9]{12,32}$'),
  kind text not null check (kind in ('visit', 'message_check', 'guard_start', 'call_alert', 'call_pack', 'sample_call',
                                     'family_link', 'family_open', 'number_report', 'outcome',
                                     'quiz_before', 'quiz_after')),
  lang text check (lang is null or length(lang) <= 8),
  level text check (level is null or length(level) <= 24),
  score smallint check (score is null or score between 0 and 12),
  net text
);
create index if not exists impact_events_device_idx on public.impact_events (device, kind, created_at);
create index if not exists impact_events_net_idx on public.impact_events (net, created_at);

alter table public.impact_events enable row level security;
drop policy if exists impact_insert on public.impact_events;
create policy impact_insert on public.impact_events for insert to anon, authenticated with check (true);
revoke select, update, delete on public.impact_events from anon, authenticated;  -- raw rows are never readable

create or replace function public.impact_events_guard() returns trigger
language plpgsql security definer set search_path to '' as $$
declare
  h json := coalesce(nullif(current_setting('request.headers', true), '')::json, '{}'::json);
  ip text := coalesce(h->>'cf-connecting-ip', split_part(h->>'x-forwarded-for', ',', 1), 'unknown');
begin
  new.net := encode(sha256(convert_to('ruko-impact:' || trim(ip), 'UTF8')), 'hex');
  new.created_at := now();
  -- caps so one person or one script cannot inflate the numbers
  if (select count(*) from public.impact_events e where e.net = new.net
      and e.created_at > now() - interval '1 hour') >= 120 then
    raise exception 'too_many_events' using errcode = 'P0001';
  end if;
  if (select count(*) from public.impact_events e where e.device = new.device
      and e.created_at > now() - interval '1 day') >= 200 then
    raise exception 'too_many_events' using errcode = 'P0001';
  end if;
  -- each device's quiz counts once: its first before-round and its first after-round
  if new.kind in ('quiz_before', 'quiz_after') and exists (
      select 1 from public.impact_events e where e.device = new.device and e.kind = new.kind) then
    raise exception 'already_counted' using errcode = 'P0001';
  end if;
  if new.kind = 'quiz_after' and not exists (
      select 1 from public.impact_events e where e.device = new.device and e.kind = 'quiz_before') then
    raise exception 'no_before_round' using errcode = 'P0001';
  end if;
  return new;
end $$;
revoke all on function public.impact_events_guard() from public, anon, authenticated;
drop trigger if exists impact_events_guard on public.impact_events;
create trigger impact_events_guard before insert on public.impact_events
  for each row execute function public.impact_events_guard();

-- Public summary: aggregates only, never a raw row.
create or replace function public.impact_summary() returns json
language sql security definer set search_path to '' stable as $$
  select json_build_object(
    'as_of', now(),
    'since', (select min(created_at) from public.impact_events),
    'devices', (select count(distinct device) from public.impact_events),
    'networks', (select count(distinct net) from public.impact_events),
    'by_kind', coalesce((select json_object_agg(kind, n) from
        (select kind, count(*) n from public.impact_events group by kind) k), '{}'::json),
    'devices_by_kind', coalesce((select json_object_agg(kind, n) from
        (select kind, count(distinct device) n from public.impact_events group by kind) k), '{}'::json),
    'verdicts', coalesce((select json_object_agg(level, n) from
        (select coalesce(level, 'unknown') level, count(*) n from public.impact_events
         where kind = 'message_check' group by 1) v), '{}'::json),
    'outcomes', coalesce((select json_object_agg(level, n) from
        (select coalesce(level, 'unknown') level, count(*) n from public.impact_events
         where kind = 'outcome' group by 1) o), '{}'::json),
    'languages', coalesce((select json_object_agg(lang, n) from
        (select coalesce(lang, 'unknown') lang, count(distinct device) n from public.impact_events group by 1) l), '{}'::json),
    'daily', coalesce((select json_agg(d order by d.day) from
        (select (created_at at time zone 'Asia/Kolkata')::date day, count(*) events, count(distinct device) devices
         from public.impact_events where created_at > now() - interval '60 days' group by 1) d), '[]'::json),
    -- paired quiz scores (same device, before and after), plus which question set came first
    'quiz', coalesce((select json_agg(json_build_array(b.score, a.score, b.level)) from public.impact_events b
        join public.impact_events a on a.device = b.device and a.kind = 'quiz_after'
        where b.kind = 'quiz_before'), '[]'::json),
    'quiz_started', (select count(*) from public.impact_events where kind = 'quiz_before')
  )
$$;
revoke all on function public.impact_summary() from public;
grant execute on function public.impact_summary() to anon, authenticated;
