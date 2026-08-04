-- Ad-hoc queries for day-to-day use. Copy/paste into Supabase Studio's SQL editor,
-- or run via `scripts/status.js` for the two most common ones.

-- 1. Current week guarantee status, all clients, worst-first.
select * from v_current_week_guarantee_status
order by guarantee_met asc, client_name;

-- 2. Full weekly guarantee history for one client (swap the slug).
select w.*
from v_weekly_guarantee_status w
where w.client_slug = 'drive-world'
order by w.week_start desc;

-- 3. Update turnaround: anything not cleanly on-target right now.
select *
from v_update_turnaround_status
where status in ('pending', 'overdue', 'late')
order by patch_received_at desc;

-- 4. Platform breakdown for the current week.
select client_name, platform, video_count
from v_weekly_platform_breakdown b
join clients c on c.id = b.client_id
where b.week_start = date_trunc('week', now())::date
order by client_name, platform;

-- 5. Link/click attribution — which videos are driving clicks, highest first.
select *
from v_link_click_summary
order by click_count desc;

-- 6. Raw click log for one tracked link (swap the code), for correlating
--    against a Roblox CCU/visits spike by timestamp.
select clicked_at, referrer, user_agent
from link_clicks lc
join tracked_links tl on tl.id = lc.tracked_link_id
where tl.code = 'drive-world-tt-001'
order by clicked_at;
