'use strict';
(() => {
  const counter = document.querySelector('[data-site-views]');
  if (!counter || window.top !== window.self) return;
  if (!['http:', 'https:'].includes(location.protocol)) {
    counter.textContent = 'Online only';
    return;
  }
  const configured = document.querySelector('meta[name="site-views-endpoint"]')?.content?.trim();
  if (!configured) {
    counter.textContent = 'Not connected';
    counter.closest('.site-views').title = 'The persistent counter has not been connected to this hosting yet.';
    return;
  }
  let endpoint;
  try {
    endpoint = new URL(configured);
    if (endpoint.protocol !== 'https:' || endpoint.username || endpoint.password) throw new Error();
  } catch {
    counter.textContent = 'Unavailable';
    return;
  }
  let counted = false;
  async function recordView() {
    if (counted) return;
    counted = true;
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 8000);
    try {
      // Simple CORS POST: no cookies, account IDs, referrer or preflight.
      const response = await fetch(endpoint.href, {
        method: 'POST', mode: 'cors', credentials: 'omit', cache: 'no-store',
        referrerPolicy: 'no-referrer', signal: abort.signal,
      });
      if (!response.ok) throw new Error('Counter unavailable');
      const result = await response.json();
      if (!Number.isSafeInteger(result.total) || result.total < 0) throw new Error('Invalid count');
      counter.textContent = new Intl.NumberFormat('en-US').format(result.total);
      if (result.startedAt) counter.closest('.site-views').title = 'Total page views since ' + result.startedAt.slice(0, 10) + '. Reloads count as new views.';
    } catch {
      counter.textContent = 'Unavailable';
    } finally { clearTimeout(timeout); }
  }
  if (document.prerendering) document.addEventListener('prerenderingchange', recordView, {once: true});
  else recordView();
})();
