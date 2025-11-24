// Production server entry point for Astro Bun adapter
// Manually starts the server with PORT and HOST from environment variables

const PORT = parseInt(process.env.PORT || '3000');
const HOST = process.env.HOST || '0.0.0.0';

// Import the Astro handler (don't auto-start)
const { handle } = await import('./dist/server/entry.mjs');

// Create and start Bun server with proper configuration
const server = Bun.serve({
  port: PORT,
  hostname: HOST,
  fetch: handle,
});

console.log(`🚀 Astro SSR server running on http://${HOST}:${PORT}`);

