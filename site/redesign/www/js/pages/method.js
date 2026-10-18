/* Method page: the nine-step disclosure timeline, the in-page index with scroll-spy, tier badges,
   current category membership and the per-site port plan (both from data/sites.json). */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Nine steps: HIG DisclosureGroup rows ---------- */
  var steps = Array.prototype.slice.call(document.querySelectorAll('.m-step'));
  var triggers = steps.map(function (s) { return s.querySelector('.hig-disclosure__trigger'); });
  var expandBtn = document.querySelector('.m-expand');

  function setOpen(step, open) {
    var t = step.querySelector('.hig-disclosure__trigger');
    var c = document.getElementById(t.getAttribute('aria-controls'));
    step.classList.toggle('hig-disclosure--open', open);
    t.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (c) c.hidden = !open;
  }
  function syncExpandLabel() {
    if (!expandBtn) return;
    var allOpen = steps.every(function (s) { return s.classList.contains('hig-disclosure--open'); });
    expandBtn.textContent = allOpen ? 'Collapse All' : 'Expand All';
  }

  // Without script every step reads open; with script, start with the first step open.
  steps.forEach(function (s, i) { setOpen(s, i === 0); });
  triggers.forEach(function (t, i) {
    t.addEventListener('click', function () {
      setOpen(steps[i], t.getAttribute('aria-expanded') !== 'true');
      syncExpandLabel();
    });
    t.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowDown') n = Math.min(triggers.length - 1, i + 1);
      else if (e.key === 'ArrowUp') n = Math.max(0, i - 1);
      else if (e.key === 'Home') n = 0;
      else if (e.key === 'End') n = triggers.length - 1;
      if (n === null) return;
      e.preventDefault();
      triggers[n].focus();
    });
  });
  if (expandBtn) {
    expandBtn.hidden = false;
    expandBtn.addEventListener('click', function () {
      var open = expandBtn.textContent === 'Expand All';
      steps.forEach(function (s) { setOpen(s, open); });
      syncExpandLabel();
    });
    syncExpandLabel();
  }

  /* ---------- In-page index: scroll-spy ---------- */
  var toc = document.querySelector('.m-toc');
  var list = toc && toc.querySelector('.m-toc__list');
  var links = toc ? Array.prototype.slice.call(toc.querySelectorAll('.m-toc__link')) : [];
  var sections = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var current = -1;
  var wide = window.matchMedia('(min-width: 1280px)');

  function revealInRow(a) {
    if (!list || wide.matches || list.scrollWidth <= list.clientWidth) return;
    var lr = list.getBoundingClientRect();
    var ar = a.getBoundingClientRect();
    var pad = 16;
    var delta = 0;
    if (ar.left < lr.left + pad) delta = ar.left - lr.left - pad;
    else if (ar.right > lr.right - pad) delta = ar.right - lr.right + pad;
    if (delta) list.scrollTo({ left: list.scrollLeft + delta, behavior: reduceMotion.matches ? 'auto' : 'smooth' });
  }
  function setCurrent(i) {
    if (i === current) return;
    current = i;
    links.forEach(function (a, j) {
      if (j === i) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
    if (i >= 0) revealInRow(links[i]);
  }
  function spy() {
    var pinned = toc && getComputedStyle(toc).position === 'sticky' && !wide.matches;
    var offset = (pinned ? toc.offsetHeight : 0) + Math.min(160, window.innerHeight * 0.25);
    var idx = -1;
    sections.forEach(function (s, i) { if (s && s.getBoundingClientRect().top <= offset) idx = i; });
    // At the very bottom, the last section is the one being read even if its top never reaches the line.
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) idx = sections.length - 1;
    setCurrent(idx < 0 ? 0 : idx);
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () { ticking = false; spy(); });
  }
  if (links.length) {
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    links.forEach(function (a, i) {
      a.addEventListener('click', function () {
        // Mark the destination right away; scroll-spy confirms it once scrolling settles.
        setCurrent(i);
      });
    });
    spy();
  }

  // Hairline under the sticky capsule row once it is pinned (narrow layouts).
  var sentinel = document.querySelector('.m-sentinel');
  if (toc && sentinel && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      toc.classList.toggle('is-stuck', !entries[0].isIntersecting);
    }).observe(sentinel);
  }

  /* ---------- Tier badges and current category membership ---------- */
  document.querySelectorAll('[data-tier]').forEach(function (el) {
    el.innerHTML = FC.tier(el.getAttribute('data-tier'), { pill: true });
  });

  /* ---------- Per-site port plan ---------- */
  var rowsEl = document.getElementById('m-plan-rows');

  function cells(site) {
    var html = '';
    var held = site.tierKey === 'special';
    for (var i = 0; i < site.pathway; i++) {
      var kind = i < site.starter ? (held ? 'held' : 'now') : 'future';
      html += '<span class="m-key m-key--' + kind + '"></span>';
    }
    return html;
  }

  function renderPlan(sites) {
    var ordered = sites.slice().sort(function (a, b) { return a.rank - b.rank; });
    var now = 0, future = 0;
    var html = '<ul class="m-plan__list" role="list">';
    ordered.forEach(function (s) {
      now += s.starter; future += s.pathway;
      var held = s.tierKey === 'special';
      var label = s.id + ', ' + s.name + ': ' + s.starter + ' install-now ' + (s.starter === 1 ? 'port' : 'ports') +
        (held ? ' (placeholder, not recommended)' : '') + ', ' + s.pathway + ' future-ready';
      html += '<li class="m-plan__row">' +
        '<a class="m-plan__site" href="sites.html#' + FC.esc(s.id) + '"><span class="m-plan__id">' + FC.esc(s.id) + '</span>' +
        '<span class="m-plan__name">' + FC.esc(s.name) + '</span></a>' +
        '<span class="m-plan__viz"><span class="m-plan__cells" role="img" aria-label="' + FC.esc(label) + '">' + cells(s) + '</span>' +
        '<span class="m-plan__nums" aria-hidden="true"><b>' + s.starter + '</b> of ' + s.pathway +
        (held ? '<span class="m-plan__flag">Placeholder</span>' : '') + '</span></span></li>';
    });
    html += '</ul>';
    html += '<p class="m-plan__total"><span>All 12 sites</span><span>' + now + ' install now · ' + future + ' future-ready</span></p>';
    html += '<p class="footnote m-plan__foot">Hatched squares at PWC003 are its 2 placeholder ports, counted in the total but not recommended.</p>';
    rowsEl.innerHTML = html;
  }

  function renderMembership(sites) {
    var byTier = {};
    sites.slice().sort(function (a, b) { return a.rank - b.rank; }).forEach(function (s) {
      (byTier[s.tierKey] = byTier[s.tierKey] || []).push(s);
    });
    document.querySelectorAll('.m-cat').forEach(function (li) {
      var list = byTier[li.getAttribute('data-tier-key')];
      var p = li.querySelector('.m-cat__sites');
      if (!list || !list.length || !p) return;
      p.innerHTML = '<span class="m-cat__sites-label">In the current results:</span>' + list.map(function (s) {
        return '<a href="sites.html#' + FC.esc(s.id) + '" aria-label="' + FC.esc(s.id + ', ' + s.name) + '">' + FC.esc(s.id) + '</a>';
      }).join('');
      p.hidden = false;
    });
  }

  FC.data().then(function (d) {
    var sites = (d && d.sites) || [];
    if (rowsEl) renderPlan(sites);
    renderMembership(sites);
  }).catch(function () {
    if (rowsEl) {
      rowsEl.innerHTML = '<p class="m-plan__status footnote">The per-site port plan could not be loaded. The totals above still apply. Reload the page to try again.</p>';
    }
  });
})();
