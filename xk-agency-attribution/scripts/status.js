#!/usr/bin/env node
// At-a-glance status: current week guarantee + update turnaround.
//
// Usage:
//   node status.js               # all clients
//   node status.js --client drive-world

const { parseArgs } = require('node:util');
const supabase = require('./lib/supabaseClient');

async function main() {
  const { values } = parseArgs({ options: { client: { type: 'string' } } });

  console.log('=== Current Week Guarantee Status ===');
  let guaranteeQuery = supabase.from('v_current_week_guarantee_status').select('*');
  if (values.client) guaranteeQuery = guaranteeQuery.eq('client_slug', values.client);
  const { data: guarantee, error: gErr } = await guaranteeQuery;

  if (gErr) {
    console.error(gErr.message);
    process.exit(1);
  }

  if (!guarantee.length) {
    console.log('No clients found.');
  }
  for (const row of guarantee) {
    const flag = row.guarantee_met ? 'OK     ' : 'AT RISK';
    const excludedNote = row.excluded ? ` [excluded: ${row.exclusion_reason}]` : '';
    console.log(`[${flag}] ${row.client_name} — ${row.videos_delivered}/${row.guarantee_min} videos this week (week of ${row.week_start})${excludedNote}`);
  }

  console.log('\n=== Update Turnaround Status (not on-target) ===');
  let turnaroundQuery = supabase
    .from('v_update_turnaround_status')
    .select('*')
    .in('status', ['pending', 'overdue', 'late'])
    .order('patch_received_at', { ascending: false });
  if (values.client) turnaroundQuery = turnaroundQuery.eq('client_slug', values.client);
  const { data: turnaround, error: tErr } = await turnaroundQuery;

  if (tErr) {
    console.error(tErr.message);
    process.exit(1);
  }

  if (!turnaround.length) {
    console.log('Nothing pending, overdue, or late — all recaps on target.');
  }
  for (const row of turnaround) {
    const kind = row.recap_video_id ? 'turnaround' : 'elapsed, no recap yet';
    console.log(`[${row.status.toUpperCase()}] ${row.client_name} — patch received ${row.patch_received_at}, ${row.hours_elapsed_or_turnaround}h ${kind}`);
  }
}

main();
