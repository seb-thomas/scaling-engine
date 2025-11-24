import { describe, it, expect } from 'vitest';
import { existsSync, readdirSync } from 'fs';
import { join } from 'path';
import { readFileSync } from 'fs';

describe('Migration verification - ensure old files are removed', () => {
  const frontendRoot = join(import.meta.dirname, '..');

  it('should not have old app/ directory', () => {
    const appDir = join(frontendRoot, 'app');
    expect(existsSync(appDir)).toBe(false);
  });

  it('should not have old server.tsx', () => {
    const serverFile = join(frontendRoot, 'server.tsx');
    expect(existsSync(serverFile)).toBe(false);
  });

  it('should not have old src/main.tsx', () => {
    const mainFile = join(frontendRoot, 'src', 'main.tsx');
    expect(existsSync(mainFile)).toBe(false);
  });

  it('should not have old src/App.tsx', () => {
    const appFile = join(frontendRoot, 'src', 'App.tsx');
    expect(existsSync(appFile)).toBe(false);
  });

  it('should not have old vite.config.ts', () => {
    const viteConfig = join(frontendRoot, 'vite.config.ts');
    expect(existsSync(viteConfig)).toBe(false);
  });

  it('should have Astro pages directory', () => {
    const pagesDir = join(frontendRoot, 'src', 'pages');
    expect(existsSync(pagesDir)).toBe(true);
    
    // Should have Astro files
    const pages = readdirSync(pagesDir, { recursive: true });
    const astroFiles = pages.filter((p: string) => p.toString().endsWith('.astro'));
    expect(astroFiles.length).toBeGreaterThan(0);
  });

  it('should have Astro layouts directory', () => {
    const layoutsDir = join(frontendRoot, 'src', 'layouts');
    expect(existsSync(layoutsDir)).toBe(true);
    
    const layouts = readdirSync(layoutsDir);
    expect(layouts.some((f: string) => f.endsWith('.astro'))).toBe(true);
  });

  it('should have astro.config.mjs', () => {
    const astroConfig = join(frontendRoot, 'astro.config.mjs');
    expect(existsSync(astroConfig)).toBe(true);
  });

  it('should verify components do not use react-router', () => {
    const componentsDir = join(frontendRoot, 'src', 'components');
    const componentFiles = readdirSync(componentsDir, { recursive: true })
      .filter((f: string) => f.toString().endsWith('.tsx') && !f.toString().includes('__tests__'));
    
    for (const file of componentFiles.slice(0, 10)) { // Check first 10 files
      const content = readFileSync(join(componentsDir, file.toString()), 'utf-8');
      // Should not import from react-router
      expect(content).not.toMatch(/from ['"]react-router/);
      // Should not use Link from react-router
      if (content.includes('Link')) {
        expect(content).not.toMatch(/import.*Link.*from ['"]react-router/);
      }
    }
  });
});

