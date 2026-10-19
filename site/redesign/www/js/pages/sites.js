/* Sites: a master-detail split view of the twelve candidate sites.
   Wide (>=1024px): list column beside a detail pane; selecting a row replaces the URL hash.
   Narrow: the list is a full page; a row pushes a detail view (#ID) so the browser Back button returns to the list.
   Numbers come only from data/sites.json. */
(function () {
  'use strict';
  var FC = window.FC;
  var WIDE = window.matchMedia('(min-width: 1024px)');
  var BASE_TITLE = 'Sites · EV-SIENT';

  var S = { scoring: null, stab: null, scoreById: {}, topNote: '', sites: [], byId: {}, q: '', jur: 'all', sort: 'rank', sel: null, view: null, listScroll: 0, rendered: null };
  var E = {};
  var gaugeSeq = 0;

  function $(id) { return document.getElementById(id); }
  function norm(s) { return String(s == null ? '' : s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  function fmt1(n) { return (Math.round(n * 10) / 10).toFixed(1); }

  /* ---------- Ordering and filtering ---------- */
  function ordered() {
    var a = S.sites.slice();
    if (S.sort === 'name') a.sort(function (x, y) { return x.name.localeCompare(y.name, 'en'); });
    else a.sort(function (x, y) { return x.rank - y.rank; });
    return a;
  }
  function visible() {
    var terms = norm(S.q).split(/\s+/).filter(Boolean);
    return ordered().filter(function (s) {
      if (S.jur !== 'all' && s.jurisdiction !== S.jur) return false;
      return terms.every(function (t) { return s._hay.indexOf(t) >= 0; });
    });
  }
  /* Previous/Next follow the list as it is currently filtered and sorted; if the open site is filtered out, the full sorted list. */
  function stepOrder() {
    var v = visible();
    return v.some(function (s) { return s.id === S.sel; }) ? v : ordered();
  }

  /* ---------- List ---------- */
  function rowHTML(s) {
    var sub = FC.esc(s.jurisdiction) + ' · ' + FC.esc(FC.siteType(s.type));
    var desc = 'Rank ' + s.rank + ' of ' + S.sites.length + ', ' + s.jurisdiction + ', ' + FC.siteType(s.type) +
      ', score ' + fmt1(s.score) + ' out of 100, ' + FC.TIERS[s.tierKey].short;
    return '<li class="hig-list-row hig-list-row--actionable hig-list-row--subtitle sites-row" data-id="' + s.id + '">' +
      '<div class="hig-list-row__content">' +
        '<span class="sites-row__rank num" aria-hidden="true">' + s.rank + '</span>' +
        '<span class="hig-list-row__body">' +
          '<span class="hig-list-row__text">' +
            '<a class="hig-list-row__action hig-list-row__title sites-row__name" href="#' + s.id + '" data-id="' + s.id + '" tabindex="-1" aria-describedby="sr-' + s.id + '">' + FC.esc(s.name) + '</a>' +
            '<span class="hig-list-row__subtitle">' + sub + '</span>' +
            '<span class="sites-row__tier">' + FC.tier(s.tierKey) + '</span>' +
          '</span>' +
          '<span class="hig-list-row__trailing">' +
            '<span class="sites-row__score num" aria-hidden="true">' + fmt1(s.score) + '</span>' +
            '<span class="hig-list-row__chevron sites-row__chevron" aria-hidden="true">' + FC.icon('chevron.right', { size: 20, strokeWidth: 2.4 }) + '</span>' +
          '</span>' +
          '<span id="sr-' + s.id + '" class="hig-visually-hidden">' + FC.esc(desc) + '</span>' +
        '</span>' +
      '</div></li>';
  }

  function renderList() {
    var list = visible();
    E.rows.innerHTML = list.map(rowHTML).join('');
    var any = list.length > 0;
    E.list.hidden = !any;
    E.empty.hidden = any;
    var total = S.sites.length;
    if (!any) {
      var q = S.q.trim();
      E.emptyText.textContent = q
        ? 'No sites match \u201c' + q + '\u201d' + (S.jur !== 'all' ? ' in ' + S.jur : '') + '.'
        : 'No sites match.';
      E.count.textContent = 'No sites shown';
    } else {
      E.count.textContent = list.length === total ? total + ' sites' : list.length + ' of ' + total + ' sites';
    }
    markSelection();
    updatePager();
  }

  function rowLinks() { return Array.prototype.slice.call(E.rows.querySelectorAll('a[data-id]')); }

  /* Selection highlight and a single tab stop (the selected row, else the first). */
  function markSelection() {
    var links = rowLinks();
    var split = WIDE.matches;
    var stop = null;
    links.forEach(function (a) {
      var on = a.getAttribute('data-id') === S.sel;
      var li = a.closest('.sites-row');
      li.classList.toggle('hig-list-row--highlighted', on && split);
      if (on && split) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      if (on) stop = a;
    });
    if (!stop && links.length) stop = links[0];
    links.forEach(function (a) { a.tabIndex = a === stop ? 0 : -1; });
  }

  /* ---------- Detail ---------- */
  function waitInfo(m) {
    if (m < 2) return { key: 'short', word: 'Short', icon: 'checkmark.circle' };
    if (m <= 15) return { key: 'moderate', word: 'Moderate', icon: 'clock' };
    return { key: 'long', word: 'Long, review', icon: 'exclamationmark.triangle' };
  }

  function gaugeHTML(value) {
    var D = 58, SW = 5.52, R = (D - SW) / 2, C = D / 2;
    var f = Math.max(0, Math.min(1, value / 100));
    function pt(a) { var t = a * Math.PI / 180; return [C + R * Math.sin(t), C - R * Math.cos(t)]; }
    var end = 360 * f, p0 = pt(0), p1 = pt(end);
    var d = 'M' + p0[0].toFixed(3) + ' ' + p0[1].toFixed(3) + 'A' + R + ' ' + R + ' 0 ' + (end > 180 ? 1 : 0) + ' 1 ' + p1[0].toFixed(3) + ' ' + p1[1].toFixed(3);
    var mid = 'sd-gauge-mask-' + (++gaugeSeq);
    var v = fmt1(value);
    return '<div class="hig-gauge hig-gauge--circular hig-gauge--style-capacity hig-gauge--ios hig-gauge--tinted sd-gauge" role="meter"' +
      ' aria-label="Readiness score" aria-valuenow="' + value + '" aria-valuemin="0" aria-valuemax="100" aria-valuetext="' + v + ' out of 100">' +
      '<svg class="hig-gauge__dial" viewBox="0 0 58 58" width="58" height="58" aria-hidden="true" focusable="false">' +
        '<defs><mask id="' + mid + '" maskUnits="userSpaceOnUse" x="0" y="0" width="58" height="58"><rect width="58" height="58" fill="#fff"/>' +
        '<path d="' + d + '" fill="none" stroke="#000" stroke-width="' + SW + '" stroke-linecap="round"/></mask></defs>' +
        '<circle class="hig-gauge__track hig-gauge__track--capacity" cx="' + C + '" cy="' + C + '" r="' + R + '" fill="none" stroke-width="' + SW + '" mask="url(#' + mid + ')"/>' +
        '<path class="hig-gauge__fill sd-gauge__fill" d="' + d + '" fill="none" stroke-width="' + SW + '" stroke-linecap="round"/>' +
      '</svg><span class="hig-gauge__value" aria-hidden="true">' + v + '</span></div>';
  }

  function sectionHTML(title, rows, footer, extraClass) {
    var hid = 'sd-h-' + title.toLowerCase().replace(/[^a-z]+/g, '-');
    return '<section class="hig-list-section sd-section' + (extraClass ? ' ' + extraClass : '') + '" aria-labelledby="' + hid + '">' +
      '<div class="hig-list-section__header hig-list-section__header--prominent"><h3 class="hig-list-section__title" id="' + hid + '">' + FC.esc(title) + '</h3></div>' +
      '<ul class="hig-list-section__rows">' + rows + '</ul>' +
      (footer ? '<p class="hig-list-section__footer">' + footer + '</p>' : '') +
      '</section>';
  }
  function simpleRow(title, subtitle, trailing, opts) {
    opts = opts || {};
    return '<li class="hig-list-row' + (subtitle ? ' hig-list-row--subtitle' : '') + (opts.icon ? ' hig-list-row--leading' : '') + (opts.cls ? ' ' + opts.cls : '') + '">' +
      '<div class="hig-list-row__content">' +
      (opts.icon ? '<span class="hig-list-row__symbol sd-symbol' + (opts.iconTone ? ' sd-tone--' + opts.iconTone : '') + '" aria-hidden="true">' + FC.icon(opts.icon, { size: 22 }) + '</span>' : '') +
      '<span class="hig-list-row__body"><span class="hig-list-row__text"><span class="hig-list-row__title">' + title + '</span>' +
      (subtitle ? '<span class="hig-list-row__subtitle">' + subtitle + '</span>' : '') + '</span>' +
      (trailing ? '<span class="hig-list-row__trailing">' + trailing + '</span>' : '') +
      '</span></div></li>';
  }
  function linkRow(href, title, icon) {
    return '<li class="hig-list-row hig-list-row--actionable hig-list-row--leading"><div class="hig-list-row__content">' +
      '<span class="hig-list-row__symbol" aria-hidden="true">' + FC.icon(icon, { size: 22 }) + '</span>' +
      '<span class="hig-list-row__body"><span class="hig-list-row__text"><a class="hig-list-row__action hig-list-row__title" href="' + href + '">' + FC.esc(title) + '</a></span>' +
      '<span class="hig-list-row__trailing"><span class="hig-list-row__chevron" aria-hidden="true">' + FC.icon('chevron.right', { size: 20, strokeWidth: 2.4 }) + '</span></span>' +
      '</span></div></li>';
  }
  function notice(icon, tone, title, body) {
    return '<div class="notice sd-notice sd-notice--' + tone + '" role="note"><span class="notice__icon" aria-hidden="true">' + FC.icon(icon, { size: 20 }) + '</span>' +
      '<div><p class="notice__title">' + title + '</p><p class="notice__body">' + body + '</p></div></div>';
  }

  function heroHTML(s) {
    var place = FC.esc(s.jurisdiction) + ' · ' + FC.esc(FC.siteType(s.type));
    if (s.image) {
      var photo = /wikimedia/i.test(s.imageCredit || '');
      var credit = photo ? 'Photo: ' + s.imageCredit + '; cropped and darkened.' : 'Aerial view: ' + s.imageCredit + '.';
      var alt = photo ? 'Front of ' + s.name + ', seen from the plaza' : 'Aerial view of ' + s.name + ' and its parking areas';
      return '<figure class="sd-hero sd-hero--photo">' +
        '<div class="sd-hero__frame"><img src="' + FC.esc(s.image) + '" alt="' + FC.esc(alt) + '" width="720" height="840" decoding="async"></div>' +
        '<figcaption class="sd-hero__credit footnote">' + FC.esc(credit) + '</figcaption></figure>';
    }
    return '<div class="sd-hero sd-hero--plain">' +
      '<span class="sd-hero__glyph" aria-hidden="true">' + FC.icon('location', { size: 34, strokeWidth: 1.7 }) + '</span>' +
      '<span class="sd-hero__place">' + place + '</span>' +
      '<span class="sd-hero__nophoto">No photo is published for this site.</span></div>';
  }

  function portsHTML(s) {
    var placeholder = s.tierKey === 'special';
    var extra = Math.max(0, s.pathway - s.starter);
    var pips = '';
    for (var i = 0; i < s.pathway; i++) {
      var now = i < s.starter;
      pips += '<span class="sd-pip ' + (now ? (placeholder ? 'sd-pip--placeholder' : 'sd-pip--now') : 'sd-pip--future') + '">' +
        (now && !placeholder ? FC.icon('bolt', { size: 14, strokeWidth: 2 }) : '') + '</span>';
    }
    var summary;
    if (placeholder) summary = s.starter + ' placeholder ports, not a recommendation. Do not advance a public buildout until the use case is confirmed.';
    else if (extra > 0) summary = 'Install ' + s.starter + ' now and prepare for ' + s.pathway + ' in total: room for ' + extra + ' more.';
    else summary = 'Plan for ' + s.starter + ' ports. No added pathway capacity.';

    var visual = '<li class="hig-list-row sd-ports"><div class="hig-list-row__content"><span class="hig-list-row__body sd-ports__body">' +
      '<span class="sd-pips" aria-hidden="true">' + pips + '</span>' +
      '<span class="sd-ports__summary">' + FC.esc(summary) + '</span></span></div></li>';

    var key1 = '<span class="sd-key sd-key--' + (placeholder ? 'placeholder' : 'now') + '" aria-hidden="true"></span>';
    var key2 = '<span class="sd-key sd-key--future" aria-hidden="true"></span>';
    var rows = visual +
      simpleRow(key1 + '<span>Starter ports</span>', placeholder ? 'Placeholder, counted in the plan total' : 'Install now',
        '<span class="hig-list-row__detail num">' + s.starter + ' now</span>') +
      simpleRow(key2 + '<span>Future-ready ports</span>', 'Pathway capacity to prepare for',
        '<span class="hig-list-row__detail num">' + (extra > 0 ? s.pathway + ' future-ready' : 'No added capacity') + '</span>');
    return sectionHTML('Ports', rows,
      'Future-ready ports are capacity to prepare for (conduit, panel space, layout), not chargers to install now. Right-sizing must be checked against engineering, utility and permitting review.');
  }

  /* Score breakdown: each weighted part in points, adding up to the published score (data/scoring.json), then the
     rank range and chance of first place once the stability check is published (data/stability.json). */
  function breakdownHTML(s) {
    var sc = S.scoring, b = S.scoreById[s.id];
    if (!sc || !sc.parts || !b) return '';
    var rows = sc.parts.map(function (p) {
      var pts = b.parts[p.key];
      if (pts == null) return '';
      var f = Math.max(0, Math.min(1, pts / p.weight));
      var sub = fmt1(pts) + ' of ' + p.weight + ' possible points' +
        (p.key === 'demand' && b.demandAccessFactor ? '. Counted at ' + Math.round(b.demandAccessFactor * 100) + ' percent because public access is limited' : '');
      return '<li class="hig-list-row hig-list-row--subtitle sd-part"><div class="hig-list-row__content"><span class="hig-list-row__body sd-part__body">' +
        '<span class="sd-part__top"><span class="hig-list-row__text"><span class="hig-list-row__title">' + FC.esc(p.name) + '</span>' +
        '<span class="hig-list-row__subtitle">' + FC.esc(sub) + '</span></span>' +
        '<span class="sd-part__pts num">' + fmt1(pts) + '</span></span>' +
        '<span class="sd-part__bar" aria-hidden="true"><span class="sd-part__fill" style="width:' + (f * 100).toFixed(1) + '%"></span></span>' +
        '</span></div></li>';
    }).join('');
    rows += simpleRow('<strong>Readiness score</strong>', '', '<span class="hig-list-row__detail sd-part__total num">' + fmt1(s.score) + '</span>', { cls: 'sd-part-total' });

    var st = FC.stabilityFor(S.stab, s.id);
    var draws = S.stab && S.stab.method && S.stab.method.draws ? Number(S.stab.method.draws).toLocaleString('en-US') + ' ' : '';
    if (st && st.chanceFirst != null) {
      rows += simpleRow('Chance of ranking first', 'Share of ' + draws + 'random weightings that put this site first',
        '<span class="hig-list-row__detail num">' + (Math.round(st.chanceFirst * 10) / 10).toFixed(1) + '%</span>');
    }
    if (st && st.rankLow != null && st.rankHigh != null) {
      rows += simpleRow('Rank as the weights shift', 'Its rank in 9 of 10 of those weightings',
        '<span class="hig-list-row__detail num">' + (st.rankLow === st.rankHigh ? 'Always ' + st.rankLow : st.rankLow + ' to ' + st.rankHigh) + '</span>');
    }
    if (st && st.capacityRange) {
      var cr = st.capacityRange;
      rows += simpleRow('Rank if electrical capacity varied', 'Capacity is unconfirmed. From no credit to full credit; a range, not a probability',
        '<span class="hig-list-row__detail num">' + (cr.bestRank === cr.worstRank ? cr.bestRank : cr.bestRank + ' to ' + cr.worstRank) + '</span>');
    }
    var foot = 'Each part is its own score out of 100 times its weight, rounded so the parts add up to the score. ';
    if (s.rank <= 2 && S.topNote) foot += FC.esc(S.topNote) + ' ';
    foot += '<a href="method.html#scoring">How the weights work</a>' + (s.rank <= 2 ? ' · <a href="method.html#stability">How stable the ranks are</a>' : '') + '.';
    return sectionHTML('Score Breakdown', rows, foot);
  }

  function waitRow(title, subtitle, m) {
    var w = waitInfo(m);
    var trailing = '<span class="sd-wait"><span class="sd-wait__value num">' + fmt1(m) + ' min</span>' +
      '<span class="sd-status sd-status--' + w.key + '">' + FC.icon(w.icon, { size: 15, strokeWidth: 2 }) + '<span>' + w.word + '</span></span></span>';
    return simpleRow(title, subtitle, trailing, { cls: 'sd-wait-row' });
  }

  function detailHTML(s) {
    var total = S.sites.length;
    var h = heroHTML(s);
    h += '<header class="sd-head">' +
      '<p class="sd-eyebrow num">' + FC.esc(s.id) + ' · Rank ' + s.rank + ' of ' + total + '</p>' +
      '<h2 class="sd-title" id="sd-title" tabindex="-1">' + FC.esc(s.name) + '</h2>' +
      '<p class="sd-sub">' + FC.esc(s.jurisdiction) + ' · ' + FC.esc(FC.siteType(s.type)) + '</p>' +
      '<div class="sd-tier">' + FC.tier(s.tierKey, { pill: true, long: true }) + '</div>' +
      '</header>';

    var notes = '';
    if (s.id === 'PWC004') {
      notes += notice('info.circle', 'info', 'Closed for renovation in June 2026',
        'Chinn Park Regional Library was closed for renovation when the site data were gathered in June 2026. Its rank and port plan assume it reopens much as it was.');
    }
    if (s.tierKey === 'special') {
      notes += notice('exclamationmark.triangle', 'special', 'Special use: do not advance',
        'This site should not advance as a general-public charging buildout without a changed public-access or fleet-use case. Its ' + s.starter + ' starter ports are counted in the plan total as a placeholder, not recommended.');
    }
    if (notes) h += '<div class="sd-notices">' + notes + '</div>';

    var list = '';
    /* Readiness */
    list += sectionHTML('Readiness',
      '<li class="hig-list-row sd-ready"><div class="hig-list-row__content"><span class="hig-list-row__body sd-ready__body">' +
        '<span class="sd-gauge-wrap tier--' + s.tierKey + '">' + gaugeHTML(s.score) + '</span>' +
        '<span class="sd-ready__text">' +
          '<span class="sd-ready__rank num">Rank ' + s.rank + ' of ' + total + '</span>' +
          '<span class="sd-ready__score num">Score ' + fmt1(s.score) + ' out of 100</span>' +
          '<span class="sd-ready__hint">Higher is stronger. Scores compare sites against fixed anchors; they are not a feasibility finding.</span>' +
        '</span></span></div></li>');

    /* Score breakdown */
    list += breakdownHTML(s);

    /* Ports */
    list += portsHTML(s);

    /* Waits */
    var waitRows = waitRow('Mean wait', 'Simulated, base case', s.waitMean) +
      waitRow('Peak-window wait', 'Erlang queue model, busiest window', s.waitPeak);
    if (s.id === 'PWC002') {
      waitRows += simpleRow('Why this site needs high review',
        'Its ' + Math.round(s.waitPeak) + '-minute peak-window wait is the reason it is a high-review candidate. Resolve implementation questions early.',
        '', { icon: 'exclamationmark.triangle', iconTone: 'long', cls: 'sd-flag' });
    }
    list += sectionHTML('Waits', waitRows,
      'Modelled waits; no site has been observed in operation. Under 2 minutes is short, 2 to 15 minutes is moderate, over 15 minutes is long and needs review.');

    /* Model note */
    list += sectionHTML('Model Note', '<li class="hig-list-row"><div class="hig-list-row__content"><span class="hig-list-row__body"><span class="hig-list-row__text"><span class="hig-list-row__title sd-note">' + FC.esc(s.note) + '</span></span></span></div></li>');

    /* Data confidence */
    list += sectionHTML('Data Confidence',
      simpleRow('Data confidence', '', '<span class="hig-list-row__detail">' + FC.esc(s.confidence) + '</span>', { icon: 'exclamationmark.triangle', iconTone: 'warn' }) +
      simpleRow('Electrical capacity', '', '<span class="hig-list-row__detail">Unverified placeholder</span>', { icon: 'questionmark.circle', iconTone: 'muted' }),
      'No one has confirmed that the electrical service here could support chargers. This is a planning-support prototype: the site is not approved, and every decision remains subject to electrical, ADA, fire/AHJ, stormwater and permitting review.');

    /* Related */
    list += sectionHTML('See Also',
      linkRow('explore.html', 'View on Map', 'map') +
      linkRow('compare.html', 'Compare All Sites', 'chart.bar') +
      linkRow('method.html#scoring', 'How Scores Are Made', 'list.bullet'), '', 'sd-section--links');

    h += '<div class="hig-list hig-list--ios hig-list--insetGrouped sd-list">' + list + '</div>';
    return h;
  }

  function renderDetail(animate) {
    var s = S.byId[S.sel];
    if (!s) return;
    if (S.rendered !== s.id) {
      gaugeSeq = 0;
      E.sd.innerHTML = detailHTML(s);
      E.sd.className = 'sd tier--' + s.tierKey;
      S.rendered = s.id;
      if (animate) {
        E.sd.classList.remove('is-entering');
        void E.sd.offsetWidth;
        E.sd.classList.add('is-entering');
      }
    }
    E.pager.hidden = false;
    updatePager();
    updateTitle();
  }

  function updatePager() {
    if (!S.sel) return;
    var order = stepOrder();
    var i = order.findIndex(function (s) { return s.id === S.sel; });
    var prev = i > 0 ? order[i - 1] : null;
    var next = i >= 0 && i < order.length - 1 ? order[i + 1] : null;
    E.prev.disabled = !prev; E.barPrev.disabled = !prev;
    E.next.disabled = !next; E.barNext.disabled = !next;
    E.prevName.textContent = prev ? prev.name : 'Start of list';
    E.nextName.textContent = next ? next.name : 'End of list';
    E.prev.setAttribute('aria-label', prev ? 'Previous Site: ' + prev.name : 'Previous Site');
    E.next.setAttribute('aria-label', next ? 'Next Site: ' + next.name : 'Next Site');
    E.barPrev.setAttribute('aria-label', prev ? 'Previous Site: ' + prev.name : 'Previous Site');
    E.barNext.setAttribute('aria-label', next ? 'Next Site: ' + next.name : 'Next Site');
  }

  function updateTitle() {
    var s = S.byId[S.sel];
    var showing = s && (WIDE.matches || S.view === 'detail');
    document.title = showing ? s.name + ' · ' + BASE_TITLE : BASE_TITLE;
  }

  /* ---------- Views and URL ---------- */
  function idFromHash() {
    var h = '';
    try { h = decodeURIComponent(location.hash.slice(1)); } catch (e) { h = ''; }
    h = h.trim().toUpperCase();
    return S.byId[h] ? h : null;
  }
  function setHash(id, push) {
    var url = id ? '#' + id : location.pathname + location.search;
    try {
      if (push) history.pushState({ fcSite: id, pushed: true }, '', url);
      else history.replaceState(id ? { fcSite: id, pushed: !!(history.state && history.state.pushed) } : null, '', url);
    } catch (e) { /* file:// or sandboxed: the view still updates */ }
  }

  function setView(v) {
    var prev = S.view;
    if (prev === v) return;
    S.view = v;
    E.root.setAttribute('data-view', v);
    if (v === 'detail' && prev === 'list') {
      S.listScroll = window.scrollY;
      window.scrollTo(0, 0);
      E.detail.classList.remove('is-pushing'); void E.detail.offsetWidth; E.detail.classList.add('is-pushing');
    } else if (v === 'list' && prev === 'detail') {
      E.master.classList.remove('is-popping'); void E.master.offsetWidth; E.master.classList.add('is-popping');
      window.scrollTo(0, S.listScroll || 0);
    }
    updateTitle();
  }

  function select(id, animate) {
    if (!S.byId[id]) return;
    var changed = S.sel !== id;
    S.sel = id;
    markSelection();
    renderDetail(animate && changed);
  }

  function sync() {
    var id = idFromHash();
    /* A link to an ID that does not exist: say so above the list rather than failing silently. */
    if (!id && location.hash.length > 1) {
      var bad = location.hash.slice(1);
      try { bad = decodeURIComponent(bad); } catch (e) { /* keep it as typed */ }
      setHash(null, false);
      E.count.textContent = 'No site has the ID \u201c' + bad + '\u201d.';
    }
    if (WIDE.matches) {
      var target = id || S.sel || (visible()[0] || ordered()[0]).id;
      select(target, S.view === 'split');
      setView('split');
      revealRow(target);
    } else if (id) {
      select(id, false);
      setView('detail');
    } else {
      var from = S.sel;
      setView('list');
      if (from) focusRow(from);
    }
  }

  /* Wide: keep the selected row inside the list column's own scroll box without moving the page. */
  function revealRow(id) {
    if (!WIDE.matches) return;
    var li = E.rows.querySelector('.sites-row[data-id="' + id + '"]');
    if (!li) return;
    var box = E.master.getBoundingClientRect(), r = li.getBoundingClientRect();
    if (r.top < box.top + 8) E.master.scrollTop -= (box.top + 8 - r.top);
    else if (r.bottom > box.bottom - 8) E.master.scrollTop += (r.bottom - box.bottom + 8);
  }

  function topOfDetail() {
    var top = E.root.getBoundingClientRect().top + window.scrollY;
    if (window.scrollY > top) window.scrollTo(0, Math.max(0, top - 8));
  }
  function focusTitle() {
    var t = $('sd-title');
    if (t) { try { t.focus({ preventScroll: true }); } catch (e) { t.focus(); } }
  }
  function focusRow(id) {
    var a = E.rows.querySelector('a[data-id="' + id + '"]');
    if (a) { try { a.focus({ preventScroll: !WIDE.matches }); } catch (e) { a.focus(); } }
  }

  /* Open a site from the list. */
  function open(id, focusDetail) {
    if (WIDE.matches) {
      setHash(id, false);
      var changed = S.sel !== id;
      select(id, true);
      if (changed) topOfDetail();
      if (focusDetail) focusTitle();
    } else {
      setHash(id, true);
      select(id, false);
      setView('detail');
      focusTitle();
    }
  }

  function step(d, fromEl) {
    var order = stepOrder();
    var i = order.findIndex(function (s) { return s.id === S.sel; });
    var t = order[i + d];
    if (!t) return;
    setHash(t.id, false);
    select(t.id, true);
    if (WIDE.matches) { topOfDetail(); revealRow(t.id); } else window.scrollTo(0, 0);
    if (fromEl && fromEl.disabled) focusTitle();
  }

  function back() {
    /* Pushed from the list in this visit: go back in history so Back and Forward stay in step. A deep link has nothing to pop. */
    if (history.state && history.state.pushed) { history.back(); return; }
    setHash(null, false);
    sync();
  }

  /* ---------- Events ---------- */
  function bind() {
    E.rows.addEventListener('click', function (e) {
      var a = e.target.closest('a[data-id]');
      if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      open(a.getAttribute('data-id'), false);
    });
    E.rows.addEventListener('keydown', function (e) {
      var links = rowLinks();
      var cur = links.indexOf(document.activeElement);
      if (cur < 0) return;
      var n = null;
      if (e.key === 'ArrowDown') n = Math.min(links.length - 1, cur + 1);
      else if (e.key === 'ArrowUp') n = Math.max(0, cur - 1);
      else if (e.key === 'Home') n = 0;
      else if (e.key === 'End') n = links.length - 1;
      else if (e.key === 'Enter' && WIDE.matches) {
        e.preventDefault();
        open(links[cur].getAttribute('data-id'), true);
        return;
      } else return;
      e.preventDefault();
      if (n === cur) return;
      links.forEach(function (a, j) { a.tabIndex = j === n ? 0 : -1; });
      links[n].focus();
      if (WIDE.matches) { open(links[n].getAttribute('data-id'), false); revealRow(links[n].getAttribute('data-id')); }
    });

    var qTimer = null;
    E.q.addEventListener('input', function () {
      S.q = E.q.value;
      E.qClear.hidden = !E.q.value;
      E.search.classList.toggle('has-value', !!E.q.value);
      clearTimeout(qTimer);
      qTimer = setTimeout(renderList, 60);
    });
    E.q.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && E.q.value) { e.preventDefault(); clearSearch(); }
      else if (e.key === 'ArrowDown') {
        var first = rowLinks()[0];
        if (first) { e.preventDefault(); first.focus(); }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        var v = visible();
        if (v.length === 1) open(v[0].id, true);
      }
    });
    E.qClear.addEventListener('mousedown', function (e) { e.preventDefault(); });
    E.qClear.addEventListener('click', clearSearch);
    E.emptyClear.addEventListener('click', function () { clearSearch(); if (S.jur !== 'all') { jurCtl.set('all'); S.jur = 'all'; renderList(); } E.q.focus(); });

    var jurCtl = FC.segmented(E.jur, function (v) { S.jur = v; renderList(); });
    FC.segmented(E.sort, function (v) { S.sort = v; renderList(); });

    E.back.addEventListener('click', back);
    E.prev.addEventListener('click', function () { step(-1, E.prev); });
    E.next.addEventListener('click', function () { step(1, E.next); });
    E.barPrev.addEventListener('click', function () { step(-1, E.barPrev); });
    E.barNext.addEventListener('click', function () { step(1, E.barNext); });

    window.addEventListener('popstate', sync);
    window.addEventListener('hashchange', sync);
    var onWide = function () { S.view = null; markSelection(); sync(); };
    if (WIDE.addEventListener) WIDE.addEventListener('change', onWide); else if (WIDE.addListener) WIDE.addListener(onWide);
  }

  function clearSearch() {
    E.q.value = ''; S.q = '';
    E.qClear.hidden = true;
    E.search.classList.remove('has-value');
    renderList();
    E.q.focus();
  }

  /* ---------- Boot ---------- */
  function init() {
    E.root = $('sites'); E.master = $('sites-master'); E.detail = $('sites-detail');
    E.rows = $('sites-rows'); E.list = $('sites-list'); E.empty = $('sites-empty'); E.emptyText = $('sites-empty-text');
    E.emptyClear = $('sites-empty-clear'); E.count = $('sites-count');
    E.q = $('sites-q'); E.qClear = $('sites-q-clear'); E.search = E.q.closest('.hig-search-field');
    E.jur = $('sites-jur'); E.sort = $('sites-sort');
    E.sd = $('sd'); E.pager = $('sd-pager'); E.prev = $('sd-prev'); E.next = $('sd-next');
    E.prevName = $('sd-prev-name'); E.nextName = $('sd-next-name');
    E.back = $('sites-back'); E.barPrev = $('sites-bar-prev'); E.barNext = $('sites-bar-next');

    Promise.all([FC.data(), FC.optional('data/scoring.json'), FC.optional('data/stability.json')]).then(function (all) {
      var d = all[0];
      S.scoring = all[1]; S.stab = all[2]; S.scoreById = {};
      ((S.scoring && S.scoring.sites) || []).forEach(function (b) { S.scoreById[b.id] = b; });
      S.topNote = FC.topGapText(d.sites);
      S.sites = (d.sites || []).map(function (s) {
        s._hay = norm([s.name, s.id, s.jurisdiction, FC.siteType(s.type), s.type.replace(/_/g, ' '), (FC.TIERS[s.tierKey] || {}).short].join(' '));
        S.byId[s.id] = s;
        return s;
      });
      bind();
      renderList();
      sync();
    }).catch(function (err) {
      E.count.textContent = '';
      E.sd.innerHTML = '';
      E.list.hidden = true;
      E.empty.hidden = false;
      E.empty.querySelector('.sites-empty__title').textContent = 'The site data could not be loaded.';
      E.empty.querySelector('.sites-empty__body').textContent = (err && err.message ? err.message + ' ' : '') + 'Check your connection, then reload the page.';
      E.emptyClear.querySelector('.hig-button__label').textContent = 'Reload';
      E.emptyClear.onclick = function () { location.reload(); };
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
