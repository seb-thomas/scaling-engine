import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Dockerfile', () => {
  it('should not reference deleted server.tsx file', () => {
    const dockerfile = readFileSync(join(import.meta.dirname, '../Dockerfile'), 'utf-8');
    
    // Should not contain references to old server.tsx
    expect(dockerfile).not.toContain('server.tsx');
    expect(dockerfile).not.toContain('dist-ssr');
    expect(dockerfile).not.toContain('build/client');
  });

  it('should use Astro build command', () => {
    const dockerfile = readFileSync(join(import.meta.dirname, '../Dockerfile'), 'utf-8');
    
    // Should use bunx astro build
    expect(dockerfile).toContain('bunx astro build');
  });

  it('should reference correct Astro build output paths', () => {
    const dockerfile = readFileSync(join(import.meta.dirname, '../Dockerfile'), 'utf-8');
    
    // Should reference dist/server/entry.mjs (Astro Bun adapter output)
    expect(dockerfile).toContain('dist/server/entry.mjs');
    expect(dockerfile).toContain('dist/');
  });

  it('should not reference old React Router build paths', () => {
    const dockerfile = readFileSync(join(import.meta.dirname, '../Dockerfile'), 'utf-8');
    
    // Should not contain old paths
    expect(dockerfile).not.toContain('build/client');
    expect(dockerfile).not.toContain('index.html');
  });
});

