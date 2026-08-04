#!/usr/bin/env node
// Log when a patch note was received, starting the 48h turnaround clock.
//
// Usage:
//   node log-patch-note.js --client drive-world [--received-at ISO] [--source "..."] [--summary "..."]

const { parseArgs } = require('node:util');
const supabase = require('./lib/supabaseClient');

async function main() {
  const { values } = parseArgs({
    options: {
      client: { type: 'string' },
      'received-at': { type: 'string' },
      source: { type: 'string' },
      summary: { type: 'string' },
    },
  });

  if (!values.client) {
    console.error('Usage: node log-patch-note.js --client <slug> [--received-at ISO] [--source "..."] [--summary "..."]');
    process.exit(1);
  }

  const { data: client, error: clientErr } = await supabase
    .from('clients')
    .select('id')
    .eq('slug', values.client)
    .single();

  if (clientErr || !client) {
    console.error(`No client found with slug "${values.client}". Add it first with add-client.js.`);
    process.exit(1);
  }

  const receivedAt = values['received-at'] ? new Date(values['received-at']) : new Date();
  if (Number.isNaN(receivedAt.getTime())) {
    console.error(`Invalid --received-at value: ${values['received-at']}`);
    process.exit(1);
  }

  const { data: patchNote, error } = await supabase
    .from('patch_notes')
    .insert({
      client_id: client.id,
      patch_received_at: receivedAt.toISOString(),
      source: values.source ?? null,
      summary: values.summary ?? null,
    })
    .select()
    .single();

  if (error) {
    console.error('Failed to log patch note:', error.message);
    process.exit(1);
  }

  const deadline = new Date(receivedAt.getTime() + 48 * 3600 * 1000);
  console.log(`Logged patch note ${patchNote.id} for ${values.client}.`);
  console.log(`48h deadline: ${deadline.toISOString()}`);
  console.log(`When the recap video goes live, run:`);
  console.log(`  node log-video.js --client ${values.client} --platform <platform> --patch-note ${patchNote.id}`);
}

main();
