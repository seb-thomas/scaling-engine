/// <reference types="vitest" />
import { getViteConfig } from 'astro/config';

// Astro's Vite config lets tests import .astro components and render them
// with the container API (see src/test/render.ts)
export default getViteConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: './src/test/setup.ts',
  },
});
