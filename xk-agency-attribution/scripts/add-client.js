#!/usr/bin/env node
// Add a new client. This is the only "code" step required to onboard a client —
// everything else (videos, links, patch notes) references it by slug.
//
// Usage:
//   node add-client.js --name "Drive World" --slug drive-world [--game "Twin Atlas"] [--guarantee-min 5]

const { parseArgs } = require('node:util');
const supabase = require('./lib/supabaseClient');

async function main() {
  const { values } = parseArgs({
    options: {
      name: { type: 'string' },
      slug: { type: 'string' },
      game: { type: 'string' },
      'guarantee-min': { type: 'string' },
    },
  });

  if (!values.name || !values.slug) {
    console.error('Usage: node add-client.js --name "Drive World" --slug drive-world [--game "Twin Atlas"] [--guarantee-min 5]');
    process.exit(1);
  }

  const { data, error } = await supabase
    .from('clients')
    .insert({
      name: values.name,
      slug: values.slug,
      game_name: values.game ?? null,
      guarantee_min_videos_per_week: values['guarantee-min'] ? parseInt(values['guarantee-min'], 10) : 5,
    })
    .select()
    .single();

  if (error) {
    console.error('Failed to add client:', error.message);
    process.exit(1);
  }

  console.log(`Added client "${data.name}" (slug: ${data.slug}, id: ${data.id}).`);
  console.log('Optional next step: add platform handles directly in Supabase Studio, table "client_platform_accounts".');
}

main();
