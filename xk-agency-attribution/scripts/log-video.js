#!/usr/bin/env node
// Log a published video (feeds the weekly guarantee log), and optionally
// generate a tracked link for it in the same step.
//
// Usage:
//   node log-video.js --client drive-world --platform tiktok [--title "..."] \
//     [--publish-at 2026-08-04T10:00:00Z] [--native-url https://tiktok.com/...] \
//     [--patch-note <patch_note_id>] [--link https://www.roblox.com/games/...] [--code custom-code]
//
// --patch-note marks this video as the update-recap for that patch note
//   (used for the 48h turnaround log).
// --link generates a tracked_links row + short code for attribution; omit it
//   for videos with no external CTA.

const { parseArgs } = require('node:util');
const supabase = require('./lib/supabaseClient');

const PLATFORM_ABBR = {
  tiktok: 'tt',
  instagram: 'ig',
  youtube_shorts: 'yt',
  snapchat_spotlight: 'sc',
  x: 'x',
};

async function generateCode(clientId, clientSlug, platform) {
  const abbr = PLATFORM_ABBR[platform];
  const { count, error } = await supabase
    .from('tracked_links')
    .select('id', { count: 'exact', head: true })
    .eq('client_id', clientId)
    .eq('platform', platform);

  if (error) throw new Error(error.message);

  const seq = String((count ?? 0) + 1).padStart(3, '0');
  return `${clientSlug}-${abbr}-${seq}`;
}

async function main() {
  const { values } = parseArgs({
    options: {
      client: { type: 'string' },
      platform: { type: 'string' },
      title: { type: 'string' },
      'publish-at': { type: 'string' },
      'native-url': { type: 'string' },
      'patch-note': { type: 'string' },
      link: { type: 'string' },
      code: { type: 'string' },
    },
  });

  if (!values.client || !values.platform) {
    console.error(
      'Usage: node log-video.js --client <slug> --platform <tiktok|instagram|youtube_shorts|snapchat_spotlight|x> ' +
      '[--title "..."] [--publish-at ISO] [--native-url URL] [--patch-note <id>] [--link <destination_url>] [--code <custom-code>]'
    );
    process.exit(1);
  }

  if (!PLATFORM_ABBR[values.platform]) {
    console.error(`Unknown platform "${values.platform}". Must be one of: ${Object.keys(PLATFORM_ABBR).join(', ')}`);
    process.exit(1);
  }

  const { data: client, error: clientErr } = await supabase
    .from('clients')
    .select('id, slug')
    .eq('slug', values.client)
    .single();

  if (clientErr || !client) {
    console.error(`No client found with slug "${values.client}". Add it first with add-client.js.`);
    process.exit(1);
  }

  const publishAt = values['publish-at'] ? new Date(values['publish-at']) : new Date();
  if (Number.isNaN(publishAt.getTime())) {
    console.error(`Invalid --publish-at value: ${values['publish-at']}`);
    process.exit(1);
  }

  const videoRow = {
    client_id: client.id,
    platform: values.platform,
    title: values.title ?? null,
    publish_at: publishAt.toISOString(),
    native_url: values['native-url'] ?? null,
    video_type: values['patch-note'] ? 'update_recap' : 'standard',
    patch_note_id: values['patch-note'] ?? null,
    source: 'manual',
  };

  const { data: video, error: videoErr } = await supabase
    .from('videos')
    .insert(videoRow)
    .select()
    .single();

  if (videoErr) {
    console.error('Failed to log video:', videoErr.message);
    process.exit(1);
  }

  console.log(`Logged video ${video.id} for ${values.client} on ${values.platform} (${videoRow.video_type}), published ${videoRow.publish_at}.`);

  if (values.link) {
    const code = values.code ?? (await generateCode(client.id, client.slug, values.platform));

    const { data: link, error: linkErr } = await supabase
      .from('tracked_links')
      .insert({
        client_id: client.id,
        video_id: video.id,
        platform: values.platform,
        code,
        destination_url: values.link,
      })
      .select()
      .single();

    if (linkErr) {
      console.error('Video logged, but failed to create tracked link:', linkErr.message);
      process.exit(1);
    }

    const base = process.env.REDIRECT_BASE_URL ?? 'https://<your-n8n-host>/webhook/r';
    console.log(`Tracked link: ${base}/${link.code}  ->  ${link.destination_url}`);
    console.log('Use that redirect URL (not the raw destination) in the bio/link/description.');
  }
}

main();
