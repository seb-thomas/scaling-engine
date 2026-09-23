import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://astro.build/config
export default defineConfig({
  adapter: node({ mode: 'standalone' }),
  output: 'server',
  build: {
    // The stylesheet is ~5 KiB gzipped: inlining it saves a render-blocking request
    inlineStylesheets: 'always',
  },
  security: {
    // Emits a CSP <meta> with hashes of every script and style Astro renders.
    // Inline style="" attributes are allowed (covers and wave backgrounds are
    // coloured per book/show); inline script attributes are not.
    // frame-ancestors can't go in a <meta>, so nginx sends that one.
    csp: {
      directives: [
        "default-src 'self'",
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
      ],
      styleDirective: {
        resources: [
          { resource: "'self'", kind: 'element' },
          { resource: "'unsafe-inline'", kind: 'attribute' },
        ],
      },
    },
  },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  },
});

