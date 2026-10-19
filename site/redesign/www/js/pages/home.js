/* Overview (index.html). The page ships with static text that matches data/sites.json, so it reads correctly
   without JavaScript. When the data loads, every figure is recomputed from it and the top candidates are rebuilt,
   so the page can never drift from the published contract. Markup follows HIG Native Widget, Gauge and List. */
(function () {
  'use strict';

  var FC = window.FC;

  /* ---------- Gauge (circular, gaugeStyle capacity): geometry from Gauge.jsx (iOS 27 kit, 58pt dial) ---------- */
  var D = 58, SW = 5.52, R = +((D - SW) / 2).toFixed(3), C = D / 2;
  function pt(a) { var t = (a * Math.PI) / 180; return [C + R * Math.sin(t), C - R * Math.cos(t)]; }
  function arc(a0, a1) {
    var p0 = pt(a0), p1 = pt(a1);
    return 'M' + p0[0].toFixed(3) + ' ' + p0[1].toFixed(3) + 'A' + R + ' ' + R + ' 0 ' + (a1 - a0 > 180 ? 1 : 0) + ' 1 ' +
      p1[0].toFixed(3) + ' ' + p1[1].toFixed(3);
  }
  var TINT = { 'tier1': 'system-green', 'high-review': 'system-orange', 'tier2': 'system-teal', 'tier3': 'system-gray', 'special': 'system-red' };

  function gauge(o) {
    var min = o.min || 0, max = o.max, span = (max - min) || 1;
    var f = Math.max(0, Math.min(1, (o.value - min) / span));
    var full = f >= 0.9995;
    var fillPath = !full && f > 0 ? arc(0, 360 * f) : null;
    var solid = o.tint ? ' style="stroke: var(--' + o.tint + ')"' : '';
    var svg = '<svg class="hig-gauge__dial" viewBox="0 0 ' + D + ' ' + D + '" width="' + D + '" height="' + D + '" aria-hidden="true" focusable="false">' +
      '<defs><mask id="' + o.id + '" maskUnits="userSpaceOnUse" x="0" y="0" width="' + D + '" height="' + D + '">' +
      '<rect width="' + D + '" height="' + D + '" fill="#fff"/>' +
      (fillPath ? '<path d="' + fillPath + '" fill="none" stroke="#000" stroke-width="' + SW + '" stroke-linecap="round"/>' : '') +
      '</mask></defs>' +
      (!full ? '<circle class="hig-gauge__track hig-gauge__track--capacity" cx="' + C + '" cy="' + C + '" r="' + R + '" fill="none" stroke-width="' + SW + '" mask="url(#' + o.id + ')"/>' : '') +
      (f > 0 ? (full
        ? '<circle class="hig-gauge__fill" cx="' + C + '" cy="' + C + '" r="' + R + '" fill="none" stroke-width="' + SW + '"' + solid + '/>'
        : '<path class="hig-gauge__fill" d="' + fillPath + '" fill="none" stroke-width="' + SW + '" stroke-linecap="round"' + solid + '/>') : '') +
      '</svg>';
    var vt = o.valueText || String(o.value);
    return '<div class="hig-gauge hig-gauge--circular hig-gauge--style-capacity hig-gauge--ios' + (o.tint ? ' hig-gauge--tinted' : '') + '"' +
      ' role="meter" aria-valuenow="' + o.value + '" aria-valuemin="' + min + '" aria-valuemax="' + max + '"' +
      ' aria-valuetext="' + FC.esc(vt + ' out of ' + max) + '" aria-label="' + FC.esc(o.label) + '">' + svg +
      '<span class="hig-gauge__value" aria-hidden="true">' + FC.esc(vt) + '</span></div>';
  }

  /* ---------- Top-candidate card ---------- */
  function ordinal(n) { return ['', 'first', 'second', 'third'][n] || ('number ' + n); }
  function candidateCard(s) {
    var aerial = /USGS/.test(s.imageCredit || '');
    var alt = aerial ? 'Aerial view of ' + s.name : s.name + ', main entrance';
    return '<article class="home-cand" aria-labelledby="cand-' + s.id + '">' +
      (s.image ? '<div class="home-cand__media"><img src="' + FC.esc(s.image) + '" alt="' + FC.esc(alt) + '" width="720" height="840" loading="lazy" decoding="async"></div>' : '') +
      '<div class="home-cand__body">' +
        '<p class="home-cand__rank num">Rank ' + s.rank + '</p>' +
        '<h3 class="home-cand__name" id="cand-' + s.id + '"><a class="home-cand__link" href="sites.html#' + encodeURIComponent(s.id) + '">' + FC.esc(s.name) + '</a></h3>' +
        '<p class="home-cand__meta">' + FC.esc(s.id) + ' · ' + FC.esc(s.jurisdiction) + ' · ' + FC.esc(FC.siteType(s.type)) + '</p>' +
        '<div class="home-cand__stats">' +
          gauge({ id: 'gauge-mask-' + s.id, value: s.score, min: 0, max: 100, tint: TINT[s.tierKey], valueText: s.score.toFixed(1), label: 'Readiness score' }) +
          '<div class="home-cand__facts">' +
            FC.tier(s.tierKey, { pill: true }) +
            '<p class="home-cand__ports num"><span class="hig-visually-hidden">Ports: </span>' + s.starter + ' now · ' + s.pathway + ' future</p>' +
          '</div>' +
        '</div>' +
        (s.imageCredit ? '<p class="home-cand__credit">Image: ' + FC.esc(s.imageCredit) + '</p>' : '') +
      '</div></article>';
  }

  /* ---------- Render from data ---------- */
  function setText(key, value) {
    document.querySelectorAll('[data-k="' + key + '"]').forEach(function (el) { el.textContent = value; });
  }
  function sum(list, field) { return list.reduce(function (t, s) { return t + (+s[field] || 0); }, 0); }
  function byId(list, id) { return list.filter(function (s) { return s.id === id; })[0]; }

  function render(d) {
    var sites = (d.sites || []).slice().sort(function (a, b) { return a.rank - b.rank; });
    if (!sites.length) return;
    var n = sites.length;

    // Widget: sites screened, split by jurisdiction in the order they first appear.
    var juris = [], counts = {};
    sites.forEach(function (s) { if (!(s.jurisdiction in counts)) { juris.push(s.jurisdiction); counts[s.jurisdiction] = 0; } counts[s.jurisdiction]++; });
    juris.sort();
    setText('sites', n);
    setText('juris', juris.map(function (j) { return counts[j] + ' ' + j; }).join(' · '));

    // Widget: ports now vs future-ready (pathway).
    var starter = sum(sites, 'starter'), pathway = sum(sites, 'pathway');
    setText('starter', starter);
    setText('pathway', pathway);
    var meter = document.querySelector('[data-k-meter="ports"]');
    if (meter && pathway > 0) {
      meter.style.setProperty('--hig-gauge-f', (starter / pathway).toFixed(4));
      meter.setAttribute('aria-valuenow', starter);
      meter.setAttribute('aria-valuemax', pathway);
      meter.setAttribute('aria-valuetext', starter + ' of ' + pathway);
    }

    // Widget: Tier 1.
    var t1 = sites.filter(function (s) { return s.tierKey === 'tier1'; });
    setText('tier1', t1.length);
    setText('tier1-ids', t1.map(function (s) { return s.id; }).join(' · '));

    // Widget: data confidence.
    var low = sites.filter(function (s) { return s.confidence === 'Low'; }).length;
    setText('low', low);
    setText('total', n);
    setText('conf', low === n ? 'Low' : 'Mixed');

    // Top candidates: the top three by rank.
    var top = document.getElementById('top-candidates');
    if (top) top.innerHTML = sites.slice(0, 3).map(candidateCard).join('');

    // Takeaway rows: rank and score beside each site.
    document.querySelectorAll('[data-meta]').forEach(function (el) {
      var s = byId(sites, el.getAttribute('data-meta'));
      if (!s) return;
      el.innerHTML = FC.tier(s.tierKey) + '<span class="home-list__facts num">' + FC.esc(s.id) + ' · Rank ' + s.rank + ' · ' + s.score.toFixed(1) + '</span>';
    });
    var garage = byId(sites, 'PWC002');
    if (garage) { setText('pwc002-peak', garage.waitPeak.toFixed(1)); setText('pwc002-mean', garage.waitMean.toFixed(1)); }

    // Ranking note: the canonical order.
    var first = sites[0], ffx002 = byId(sites, 'FFX002');
    if (first) { setText('first-id', first.id); setText('first-score', first.score.toFixed(1)); }
    if (ffx002) { setText('ffx002-rank', ordinal(ffx002.rank)); setText('ffx002-score', ffx002.score.toFixed(1)); }
  }

  /* Official versus earlier (legacy_v2) results, from data/versions.json. Official totals stay summed from sites.json. */
  function renderVersions(v, d) {
    if (!v || !v.official || !v.earlier) return;
    var old = v.earlier, off = v.official;
    if (old.first) { setText('earlier-first-id', old.first.id); setText('earlier-first-score', Number(old.first.score).toFixed(1)); }
    var basis = document.getElementById('ports-basis');
    if (basis && off.portPlanBasis && off.portPlanBasis !== old.model && old.pathway != null) {
      var sites = (d && d.sites) || [];
      basis.textContent = 'Port totals are the official plan (' + off.portPlanBasis + ', ' + sum(sites, 'starter') + ' now and ' + sum(sites, 'pathway') +
        ' future-ready). ' + old.label + ': ' + old.starter + ' now and ' + old.pathway + ' future-ready, superseded.';
    }
  }

  window.FCHome = { gauge: gauge, candidateCard: candidateCard };
  if (typeof document === 'undefined' || !document.getElementById || !document.getElementById('top-candidates')) return;
  FC.data().then(function (d) {
    render(d);
    return FC.optional('data/versions.json').then(function (v) { renderVersions(v, d); });
  }).catch(function () {
    // The static figures already on the page match the published data, so they stay as they are.
    var note = document.getElementById('data-status');
    if (note) note.textContent = 'Live data could not be loaded, so the figures shown are the published values.';
  });
})();
