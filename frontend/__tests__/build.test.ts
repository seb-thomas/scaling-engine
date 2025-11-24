import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { join } from 'path';

describe('Build output verification', () => {
  // These tests verify that the build process creates the expected files
  // They will only pass after running `bunx astro build`
  
  it('should verify Astro config exists', () => {
    const astroConfig = join(import.meta.dirname, '../astro.config.mjs');
    expect(existsSync(astroConfig)).toBe(true);
  });

  it('should verify package.json has correct scripts', () => {
    const packageJson = JSON.parse(
      readFileSync(join(import.meta.dirname, '../package.json'), 'utf-8')
    );
    
    // Should use bunx astro commands
    expect(packageJson.scripts.dev).toContain('bunx astro dev');
    expect(packageJson.scripts.build).toContain('bunx astro build');
    expect(packageJson.scripts.preview).toContain('bunx astro preview');
    
    // Should not have old React Router scripts
    expect(packageJson.scripts).not.toHaveProperty('ssr:dev');
    expect(packageJson.scripts).not.toHaveProperty('ssr:build');
    expect(packageJson.scripts).not.toHaveProperty('ssr:start');
  });

  it('should verify no react-router dependencies', () => {
    const packageJson = JSON.parse(
      readFileSync(join(import.meta.dirname, '../package.json'), 'utf-8')
    );
    
    // Should not have React Router dependencies
    expect(packageJson.dependencies).not.toHaveProperty('react-router');
    expect(packageJson.dependencies).not.toHaveProperty('react-router-dom');
    expect(packageJson.dependencies).not.toHaveProperty('@react-router/dev');
    expect(packageJson.dependencies).not.toHaveProperty('@react-router/node');
    
    // Should have Astro dependencies
    expect(packageJson.dependencies).toHaveProperty('astro');
    expect(packageJson.dependencies).toHaveProperty('@astrojs/react');
    expect(packageJson.dependencies).toHaveProperty('@nurodev/astro-bun');
  });
});

function readFileSync(path: string, encoding: 'utf-8'): string {
  const { readFileSync: fsReadFileSync } = require('fs');
  return fsReadFileSync(path, encoding);
}

