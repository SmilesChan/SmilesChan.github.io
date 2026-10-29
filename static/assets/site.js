'use strict';
(() => {
  const root = document.documentElement.dataset.root || './';
  const theme = document.querySelector('[data-theme-toggle]');
  theme?.addEventListener('click', () => {
    const mode = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = mode;
    theme.setAttribute('aria-label', 'Switch to ' + (mode === 'dark' ? 'light' : 'dark') + ' theme');
    try { localStorage.setItem('wentao-theme', mode); } catch (_) {}
  });
  const toggle = document.querySelector('.menu-toggle');
  toggle?.addEventListener('click', () => {
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    document.querySelector('#main-nav').classList.toggle('is-open', !expanded);
  });
  document.querySelectorAll('#main-nav a').forEach(a => a.addEventListener('click', () => {
    toggle?.setAttribute('aria-expanded', 'false');
    document.querySelector('#main-nav').classList.remove('is-open');
  }));
  // Native horizontal scrolling works with touch, trackpads, and the scrollbar.
  document.querySelectorAll('[data-gallery-carousel]').forEach(gallery => {
    const strip = gallery.querySelector('.gallery-grid');
    const previous = gallery.querySelector('[data-gallery-prev]');
    const next = gallery.querySelector('[data-gallery-next]');
    const controls = gallery.querySelector('.gallery-controls');
    const update = () => {
      const end = Math.max(0, strip.scrollWidth - strip.clientWidth);
      previous.disabled = strip.scrollLeft <= 2;
      next.disabled = strip.scrollLeft >= end - 2;
    };
    const behavior = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    const move = direction => strip.scrollBy({left: direction * Math.max(1, strip.clientWidth - 32), behavior: behavior()});
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    strip.addEventListener('scroll', update, {passive: true});
    strip.addEventListener('keydown', event => {
      if (event.target !== strip || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        move(event.key === 'ArrowLeft' ? -1 : 1);
      } else if (event.key === 'Home' || event.key === 'End') {
        event.preventDefault();
        strip.scrollTo({left: event.key === 'Home' ? 0 : strip.scrollWidth, behavior: behavior()});
      }
    });
    strip.querySelectorAll('img').forEach(img => img.addEventListener('load', update));
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(strip);
    else window.addEventListener('resize', update);
    controls.hidden = false;
    update();
  });
  const dialog = document.querySelector('#site-search');
  const query = document.querySelector('#search-query');
  const results = document.querySelector('#search-results');
  function renderResults() {
    const terms = query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    results.replaceChildren();
    if (!terms.length) return;
    const titleScore = x => terms.reduce((score,t) => score + (x.title.toLocaleLowerCase().includes(t) ? 1 : 0),0);
    const found = (window.SITE_SEARCH || []).filter(x => terms.every(t => (x.title + ' ' + x.text).toLocaleLowerCase().includes(t))).sort((a,b) => titleScore(b)-titleScore(a));
    const count = document.createElement('p'); count.className = 'search-hint';
    count.textContent = found.length + ' results'; results.append(count);
    for (const item of found.slice(0, 60)) {
      const a = document.createElement('a'); a.href = root + item.href; a.className = 'search-result';
      const tag = document.createElement('small'); tag.textContent = item.kind;
      const title = document.createElement('strong'); title.textContent = item.title;
      const snippet = document.createElement('span');
      const start = Math.max(0, item.text.toLocaleLowerCase().indexOf(terms[0]) - 55);
      snippet.textContent = (start ? '…' : '') + item.text.slice(start, start + 170) + '…';
      a.append(tag, title, snippet); results.append(a);
    }
    if (!found.length) { const p = document.createElement('p'); p.textContent = 'No matches. Try a broader search term.'; results.append(p); }
  }
  document.querySelectorAll('[data-open-search]').forEach(b => b.addEventListener('click', () => {dialog.showModal(); query.focus();}));
  document.querySelector('[data-close-search]')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
  query?.addEventListener('input', renderResults);
  document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); dialog.showModal(); query.focus(); } });
  const filterSearch = document.querySelector('[data-filter-search]');
  const year = document.querySelector('[data-filter-year]');
  const type = document.querySelector('[data-filter-type]');
  const items = [...document.querySelectorAll('[data-filter-item]')];
  function filter() {
    const terms = (filterSearch?.value || '').trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    items.forEach(item => {
      const visible = terms.every(t => item.textContent.toLocaleLowerCase().includes(t)) && (!year?.value || item.dataset.year === year.value) && (!type?.value || item.dataset.type === type.value);
      item.hidden = !visible; count += visible ? 1 : 0;
    });
    const countEl = document.querySelector('[data-filter-count]'); if (countEl) countEl.textContent = count + (count === 1 ? ' entry' : ' entries');
    const empty = document.querySelector('.empty-filter'); if (empty) empty.hidden = count > 0;
  }
  [filterSearch,year,type].forEach(el => el?.addEventListener('input', filter));
  if (type && ['#1','#2'].includes(location.hash)) type.value = location.hash === '#1' ? 'Conference paper' : 'Journal article';
  if (filterSearch) filter();
  // Keep the original publication list filters usable on preserved auxiliary pages.
  const legacySearch = document.querySelector('.filter-search');
  legacySearch?.addEventListener('input', () => {
    const q = legacySearch.value.toLocaleLowerCase();
    document.querySelectorAll('#container-publications > div').forEach(x => {x.hidden = !x.textContent.toLocaleLowerCase().includes(q);});
  });
})();
