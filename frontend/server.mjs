// Production server entry point for Astro Bun adapter
// This ensures the server starts with correct PORT and HOST settings

import { start } from './dist/server/entry.mjs';

const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';

// Start the server
start({
  port: PORT,
  host: HOST,
});

console.log(`🚀 Astro SSR server running on http://${HOST}:${PORT}`);

