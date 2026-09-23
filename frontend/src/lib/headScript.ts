// Inline <script> run in the <head> of every page, before first paint. Kept as
// a string so Layout can render it verbatim and allow it in the CSP by hash.
export const headScript = `
// Follow the system colour scheme; runs before first paint to prevent a flash
(function() {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const apply = () => document.documentElement.classList.toggle('dark', mq.matches);
  apply();
  mq.addEventListener('change', apply);
})();
// On a broken cover, hide it and reveal the fallback rendered right after it.
// A capturing listener (error doesn't bubble) rather than an inline onerror
// attribute, which the CSP would block.
document.addEventListener('error', (e) => {
  const img = e.target;
  if (img instanceof HTMLImageElement && img.hasAttribute('data-fallback')) {
    img.style.display = 'none';
    img.nextElementSibling?.classList.remove('hidden');
  }
}, true);
`;
