(() => {
  'use strict';
  // Keep links to the former root presentation working after the homepage move.
  if ((location.pathname === '/' || location.pathname.endsWith('/index.html')) && location.hash.startsWith('#/')) {
    location.replace(new URL('slides-2026-09-15.html', location.href).pathname + location.search + location.hash);
    return;
  }
  let language = 'th';
  try { if (localStorage.getItem('ecs-site-language') === 'en') language = 'en'; } catch (_) {}
  function setLanguage(next) {
    language = next === 'en' ? 'en' : 'th';
    document.documentElement.lang = language;
    document.querySelectorAll('[data-lang]').forEach(node => { node.hidden = node.dataset.lang !== language; });
    document.querySelectorAll('[data-language]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === language)));
    document.querySelectorAll('[data-label-th]').forEach(node => node.setAttribute('aria-label', node.dataset[language === 'th' ? 'labelTh' : 'labelEn']));
    document.querySelectorAll('[data-placeholder-th]').forEach(node => { node.placeholder = node.dataset[language === 'th' ? 'placeholderTh' : 'placeholderEn']; });
    if (document.body.dataset.titleTh) document.title = document.body.dataset[language === 'th' ? 'titleTh' : 'titleEn'];
    try { localStorage.setItem('ecs-site-language', language); } catch (_) {}
  }
  document.querySelectorAll('[data-language]').forEach(button => button.addEventListener('click', () => setLanguage(button.dataset.language)));
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.getElementById('site-nav');
  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); toggle.focus();
    }
  });
  const search = document.getElementById('archive-search');
  const type = document.getElementById('archive-type');
  function filterArchive() {
    const term = (search?.value || '').trim().toLocaleLowerCase();
    const minutesOnly = type?.value === 'minutes';
    let count = 0;
    document.querySelectorAll('[data-meeting-search]').forEach(row => {
      const visible = row.dataset.meetingSearch.includes(term) && (!minutesOnly || row.dataset.hasMinutes === 'true');
      row.hidden = !visible; if (visible) count++;
    });
    const empty = document.getElementById('archive-empty');
    if (empty) empty.hidden = count > 0;
    document.querySelectorAll('.archive-year').forEach(group => { group.hidden = !Array.from(group.querySelectorAll('[data-meeting-search]')).some(row => !row.hidden); });
  }
  search?.addEventListener('input', filterArchive);
  type?.addEventListener('change', filterArchive);
  setLanguage(language);
})();
