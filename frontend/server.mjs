// Production server entry point for Astro Bun adapter
// The adapter reads PORT and HOST from environment variables
// Set them before importing the entry point

process.env.PORT = process.env.PORT || '3000';
process.env.HOST = process.env.HOST || '0.0.0.0';

// Import entry point - it will auto-start with the environment variables
import './dist/server/entry.mjs';

console.log(`🚀 Astro SSR server running on http://${process.env.HOST}:${process.env.PORT}`);

