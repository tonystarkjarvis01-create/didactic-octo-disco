-- XK Agency: Attribution & Tracking System
-- Initial schema: clients, videos, tracked links/clicks, patch notes, guarantee exclusions.
--
-- Run this once in Supabase SQL editor (or via `supabase db push` if you use the CLI).
-- All access is via the service_role key from n8n / scripts, never exposed to a browser,
-- so RLS is intentionally left off — this is an internal ops tool, not a public app.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Core entities
-- ---------------------------------------------------------------------------

create table clients (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,               -- e.g. 'drive-world', used in link codes
  game_name text,                          -- e.g. 'Twin Atlas'
  guarantee_min_videos_per_week integer not null default 5,
  created_at timestamptz not null default now()
);

create table client_platform_accounts (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  platform text not null check (platform in ('tiktok','instagram','youtube_shorts','snapchat_spotlight','x')),
  handle text not null,                    -- e.g. '@driveworldrblx'
  created_at timestamptz not null default now(),
  unique (client_id, platform)
);

-- ---------------------------------------------------------------------------
-- Weekly output log (feeds the 5-video guarantee)
-- ---------------------------------------------------------------------------

create table patch_notes (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  patch_received_at timestamptz not null default now(),
  source text,                             -- e.g. 'Roblox DevForum', 'client Discord'
  summary text,
  created_at timestamptz not null default now()
);

create table videos (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  platform text not null check (platform in ('tiktok','instagram','youtube_shorts','snapchat_spotlight','x')),
  title text,
  video_type text not null default 'standard' check (video_type in ('standard','update_recap')),
  patch_note_id uuid references patch_notes(id),   -- set only for update_recap videos
  publish_at timestamptz not null default now(),
  native_url text,                         -- link to the actual post, if handy
  source text not null default 'manual' check (source in ('manual','sprout_sync')),
  sprout_post_id text unique,              -- dedup key if/when synced from Sprout Social
  created_at timestamptz not null default now()
);

create index videos_client_publish_idx on videos (client_id, publish_at);
create index videos_patch_note_idx on videos (patch_note_id);

-- Marks an entire week as excluded from the guarantee (client-caused delay etc).
-- Applies to the whole week rather than individual videos, since the guarantee
-- is evaluated per client per week.
create table guarantee_week_exclusions (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  week_start date not null,                -- Monday of the excluded week
  reason text not null,
  logged_by text,
  created_at timestamptz not null default now(),
  unique (client_id, week_start)
);

-- ---------------------------------------------------------------------------
-- Attribution: tagged links / redemption codes
-- ---------------------------------------------------------------------------

create table tracked_links (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  video_id uuid references videos(id) on delete set null,
  platform text not null check (platform in ('tiktok','instagram','youtube_shorts','snapchat_spotlight','x')),
  code text not null unique,               -- short code, e.g. 'drive-world-tt-003'
  destination_url text not null,           -- where the redirect sends traffic (Roblox game link, etc.)
  notes text,
  created_at timestamptz not null default now()
);

create index tracked_links_client_idx on tracked_links (client_id);

create table link_clicks (
  id uuid primary key default gen_random_uuid(),
  tracked_link_id uuid not null references tracked_links(id) on delete cascade,
  clicked_at timestamptz not null default now(),
  referrer text,
  user_agent text
);

create index link_clicks_link_idx on link_clicks (tracked_link_id, clicked_at);

-- ---------------------------------------------------------------------------
-- Views: at-a-glance status queries
-- ---------------------------------------------------------------------------

-- Platform breakdown per client per week.
create view v_weekly_platform_breakdown as
select
  client_id,
  date_trunc('week', publish_at)::date as week_start,
  platform,
  count(*) as video_count
from videos
group by client_id, week_start, platform;

-- Full historical audit trail of guarantee status, one row per client per week
-- that has ever had a video logged.
create view v_weekly_guarantee_status as
select
  c.id as client_id,
  c.slug as client_slug,
  c.name as client_name,
  gs.week_start,
  coalesce(v.video_count, 0) as videos_delivered,
  c.guarantee_min_videos_per_week as guarantee_min,
  (e.id is not null) as excluded,
  e.reason as exclusion_reason,
  (
    (e.id is not null)
    or coalesce(v.video_count, 0) >= c.guarantee_min_videos_per_week
  ) as guarantee_met
from clients c
join lateral (
  select generate_series(
    date_trunc('week', (select min(publish_at) from videos where client_id = c.id)),
    date_trunc('week', now()),
    interval '1 week'
  )::date as week_start
) gs on true
left join (
  select client_id, date_trunc('week', publish_at)::date as week_start, count(*) as video_count
  from videos
  group by client_id, week_start
) v on v.client_id = c.id and v.week_start = gs.week_start
left join guarantee_week_exclusions e on e.client_id = c.id and e.week_start = gs.week_start
where exists (select 1 from videos where client_id = c.id);

-- Quick glance: this week's guarantee status for every client, including
-- clients with zero videos logged yet (unlike v_weekly_guarantee_status,
-- which only shows weeks after a client's first video).
create view v_current_week_guarantee_status as
select
  c.id as client_id,
  c.slug as client_slug,
  c.name as client_name,
  date_trunc('week', now())::date as week_start,
  coalesce(v.video_count, 0) as videos_delivered,
  c.guarantee_min_videos_per_week as guarantee_min,
  (e.id is not null) as excluded,
  e.reason as exclusion_reason,
  (
    (e.id is not null)
    or coalesce(v.video_count, 0) >= c.guarantee_min_videos_per_week
  ) as guarantee_met
from clients c
left join (
  select client_id, count(*) as video_count
  from videos
  where date_trunc('week', publish_at) = date_trunc('week', now())
  group by client_id
) v on v.client_id = c.id
left join guarantee_week_exclusions e
  on e.client_id = c.id and e.week_start = date_trunc('week', now())::date;

-- Update-turnaround status: patch note received -> recap video live.
-- status is one of:
--   on_target  - recap published within 48h
--   late       - recap published, but after 48h
--   overdue    - no recap yet, and 48h has already passed
--   pending    - no recap yet, still within the 48h window
create view v_update_turnaround_status as
select
  pn.id as patch_note_id,
  pn.client_id,
  c.slug as client_slug,
  c.name as client_name,
  pn.patch_received_at,
  pn.summary,
  v.id as recap_video_id,
  v.publish_at as recap_published_at,
  case
    when v.id is not null
      then round(extract(epoch from (v.publish_at - pn.patch_received_at)) / 3600.0, 1)
    else round(extract(epoch from (now() - pn.patch_received_at)) / 3600.0, 1)
  end as hours_elapsed_or_turnaround,
  case
    when v.id is not null and (v.publish_at - pn.patch_received_at) <= interval '48 hours' then 'on_target'
    when v.id is not null then 'late'
    when (now() - pn.patch_received_at) > interval '48 hours' then 'overdue'
    else 'pending'
  end as status
from patch_notes pn
join clients c on c.id = pn.client_id
left join videos v on v.patch_note_id = pn.id;

-- Attribution: click activity per tracked link, joined back to the video that used it.
-- This is the starting point for "which video drove which spike" — overlay clicked_at
-- timestamps against Roblox CCU/visits manually, since there's no Roblox analytics
-- API pull in this stack yet.
create view v_link_click_summary as
select
  tl.id as tracked_link_id,
  tl.client_id,
  c.slug as client_slug,
  tl.platform,
  tl.code,
  tl.destination_url,
  v.id as video_id,
  v.title as video_title,
  v.publish_at as video_publish_at,
  count(lc.id) as click_count,
  max(lc.clicked_at) as last_click_at
from tracked_links tl
join clients c on c.id = tl.client_id
left join videos v on v.id = tl.video_id
left join link_clicks lc on lc.tracked_link_id = tl.id
group by tl.id, tl.client_id, c.slug, tl.platform, tl.code, tl.destination_url, v.id, v.title, v.publish_at;
