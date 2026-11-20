'use strict';
(() => {
  const counter = document.querySelector('[data-site-views]');
  if (!counter || window.top !== window.self) return;
  if (!['http:', 'https:'].includes(location.protocol)) {
    counter.textContent = 'Online only';
    return;
  }
  const meta = name => document.querySelector(`meta[name="${name}"]`)?.content?.trim() || '';
  const configured = meta('site-views-endpoint');
  const provider = meta('site-views-provider') || 'custom';
  if (!configured) {
    counter.textContent = 'Not connected';
    counter.closest('.site-views').title = 'The page-view counter has not been connected.';
    return;
  }
  let endpoint;
  let page;
  try {
    endpoint = new URL(configured);
    if (endpoint.protocol !== 'https:' || endpoint.username || endpoint.password) throw new Error();
    if (!['custom', 'busuanzi'].includes(provider)) throw new Error();
    if (provider === 'busuanzi') {
      page = new URL(document.querySelector('link[rel="canonical"]')?.href || location.href);
      const actual = new URL(location.href);
      if (actual.hostname.replace(/^www\./, '') !== page.hostname.replace(/^www\./, '')) {
        counter.textContent = 'Preview';
        return;
      }
      // Send only the public canonical page URL, without query parameters or fragments.
      page.search = '';
      page.hash = '';
    }
  } catch {
    counter.textContent = 'Unavailable';
    return;
  }
  const box = counter.closest('.site-views');
  const cacheKey = JSON.stringify(['site-views-v1', location.origin, provider, endpoint.href, meta('site-views-started-at')]);
  const validTotal = total => Number.isSafeInteger(total) && total >= 0;
  const format = total => new Intl.NumberFormat('en-US').format(total);
  function showLastKnown() {
    try {
      const cached = JSON.parse(localStorage.getItem(cacheKey));
      if (!validTotal(cached)) return false;
      counter.textContent = format(cached) + ' (last known)';
      box.title = 'Last successfully retrieved total. The current total may be higher.';
      return true;
    } catch { return false; }
  }
  let counted = false;
  const configuredTimeout = Number(meta('site-views-timeout'));
  const timeoutMs = Number.isInteger(configuredTimeout) && configuredTimeout >= 1000 && configuredTimeout <= 30000
    ? configuredTimeout : 8000;
  async function recordView() {
    if (counted) return;
    counted = true;
    showLastKnown();
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), timeoutMs);
    try {
      // One shared-server increment per page load; no cookies or stored visitor identifiers.
      const options = {
        method: 'POST', mode: 'cors', credentials: 'omit', cache: 'no-store',
        referrerPolicy: 'no-referrer', signal: abort.signal,
      };
      if (provider === 'busuanzi') options.headers = {'x-bsz-referer': page.href};
      const response = await fetch(endpoint.href, options);
      if (!response.ok) throw new Error('Counter unavailable');
      const result = await response.json();
      if (provider === 'busuanzi' && result.success !== true) throw new Error('Counter unavailable');
      const total = provider === 'busuanzi' ? result.data?.site_pv : result.total;
      if (!validTotal(total)) throw new Error('Invalid count');
      counter.textContent = format(total);
      try { localStorage.setItem(cacheKey, JSON.stringify(total)); } catch {}
      box.title = 'Total page views. Reloads count as new views.';
      const startedAt = provider === 'busuanzi' ? meta('site-views-started-at') : result.startedAt;
      if (startedAt) counter.closest('.site-views').title = 'Total page views recorded since ' + startedAt.slice(0, 10) + '. Reloads count as new views.';
    } catch {
      if (!showLastKnown()) counter.textContent = 'Temporarily unavailable';
    } finally { clearTimeout(timeout); }
  }
  if (document.prerendering) document.addEventListener('prerenderingchange', recordView, {once: true});
  else recordView();
})();
