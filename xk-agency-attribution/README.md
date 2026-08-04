# XK Agency — Attribution & Tracking System

Built and validated against Drive World (Twin Atlas) first. Everything here is designed
to keep working with one client and stay easy for a two-person team to run day to day —
extending to a second client is "run `add-client.js` again," nothing structural.

Three subsystems, one Supabase database:

1. **Tagged links** — short codes per client/platform/video, redirected + click-logged
   through n8n.
2. **Weekly output log** — every published video logged once, guarantee status derived
   from it (no duplicate data entry).
3. **Update-turnaround log** — patch note received → recap live, flagged against the 48h
   SLA.

## How it fits the existing stack

- **Supabase** is the structured data layer (schema below). No new database.
- **n8n** hosts the link-redirect webhook and (optionally) a Sprout sync — deterministic
  plumbing only, per your Hermes/n8n split.
- **Scripts** (Node, `@supabase/supabase-js`) are the day-to-day CLI — logging a video or
  patch note is one command, not a table edit.
- Nothing here requires a new paid service. The "tagged link" is an n8n webhook URL, not
  a URL shortener product.

### Why not real URL params for Roblox?

Roblox game joins don't carry through query-string attribution the way a normal website
does. The workaround here: the "tracked link" people click (TikTok bio, IG bio, etc.) is
actually an n8n webhook URL (`https://<n8n-host>/webhook/r/<code>`). n8n logs the click
(timestamp, referrer, user agent) to Supabase, then 302-redirects to the real destination
(the Roblox game page, or wherever). That gives you a timestamped, per-video, per-platform
click log — a leading indicator you correlate against Roblox CCU/visit spikes by eye.
There's no Roblox analytics API pull in this stack, so that correlation step is manual for
now; wire one up later if it becomes worth automating.

This also means click tracking only works for platforms where the link is actually
clickable (TikTok bio/link, Instagram bio, YouTube description, X). You can still create a
`tracked_links` row for a platform without a clickable link (e.g. Snapchat Spotlight) —
it just won't accumulate clicks, and exists mainly for consistent per-video record-keeping.

## Setup

### 1. Supabase

Run `supabase/migrations/0001_init_schema.sql` once in the Supabase SQL editor (or via
`supabase db push` if you use the CLI). It creates all tables and the status views, and
leaves RLS off — this tool is only ever accessed with the service_role key from scripts/
n8n, never from a browser, so there's no anon-key exposure to guard against.

### 2. n8n

Import `n8n/workflows/link-redirect-logger.json`. After import:

- Add a Supabase credential in n8n (`Settings > Credentials`) and point both Supabase
  nodes at it (they're stubbed with a placeholder credential id — n8n credentials aren't
  portable across instances, so this is a manual one-time step).
- Activate the workflow. Its public URL will be something like
  `https://<your-n8n-host>/webhook/r/:code`.
- Double check the field names in the two Supabase nodes match your n8n version — node
  parameter shapes shift between n8n releases, so treat this JSON as a working starting
  point to verify against your instance, not a guaranteed drop-in.

### 3. Scripts

```
cd xk-agency-attribution/scripts
npm install
cp .env.example .env   # fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, REDIRECT_BASE_URL
```

## Day to day

### Add a new client

```
node add-client.js --name "Drive World" --slug drive-world --game "Twin Atlas" --guarantee-min 5
```

Then add platform handles directly in Supabase Studio's table editor, table
`client_platform_accounts` (rarely changes, not worth a script).

### Log a video (every video, every platform)

```
node log-video.js --client drive-world --platform tiktok --title "Drift build showcase"
```

If the video has an external CTA (bio link, description link), generate a tracked link in
the same step:

```
node log-video.js --client drive-world --platform tiktok --title "Drift build showcase" \
  --link "https://www.roblox.com/games/XXXXXXX/Twin-Atlas"
```

This prints the redirect URL to actually use in the bio/description
(`https://<n8n-host>/webhook/r/drive-world-tt-004`) — not the raw destination URL. Codes
auto-generate as `<client-slug>-<platform-abbr>-<sequence>`; pass `--code` to override.

### Log a patch note + its recap (Update-Response SOP)

```
node log-patch-note.js --client drive-world --source "Roblox DevForum" --summary "v2.3 update"
```

This starts the 48h clock and prints the patch note id. When the recap goes live:

```
node log-video.js --client drive-world --platform youtube_shorts --patch-note <patch_note_id>
```

### Check guarantee + turnaround status

```
node status.js                    # all clients
node status.js --client drive-world
```

Or run the queries in `supabase/sql/queries.sql` directly in Supabase Studio — same data,
no terminal needed. Query 5/6 in that file are the attribution starting point (clicks per
video, raw click timestamps for spike correlation).

### Logging a guarantee exclusion (client-caused delay)

No script for this — it's rare enough to do directly in Supabase Studio. Insert a row into
`guarantee_week_exclusions`:

```sql
insert into guarantee_week_exclusions (client_id, week_start, reason, logged_by)
values (
  (select id from clients where slug = 'drive-world'),
  '2026-08-03',  -- Monday of the excluded week
  'Client did not provide footage until Thursday',
  'you'
);
```

That week is then counted as guarantee-met regardless of video count, and shows up
flagged as `excluded` in `status.js` / the views.

## Extension points (not built — add when actually needed)

- **Sprout sync**: `videos.source = 'sprout_sync'` and `videos.sprout_post_id` exist so an
  n8n cron workflow can upsert from the existing sprout-weekly-puller data as a
  reconciliation pass, without duplicating manual entry. Not built because manual logging
  covers one client fine right now.
- **Second client**: `node add-client.js` — no schema or script changes needed.
- **Roblox CCU/visits pull**: would let spike correlation (query 5/6) become automatic
  instead of eyeballed. Flagging as a real gap, not building until it's worth the API
  integration.
