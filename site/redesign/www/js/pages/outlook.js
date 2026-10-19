/* Outlook: summary tiles, scenario explanations, and three charts (ports over time, lifecycle cost, avoided
   emissions), all computed from the horizons, costs and emissions arrays in data/sites.json. */
(function () {
  'use strict';

  var SCEN = {
    baseline: { name: 'Baseline', color: 'system-gray', shape: 'circle',
      text: 'The 2026 starting point: starter ports at today’s modeled demand. Every scenario starts here.' },
    base: { name: 'Base', color: 'accent', shape: 'circle',
      text: 'Demand grows 1.9 times by 2036, 3.0 times by 2046 and 4.0 times by 2056, relative to 2026.' },
    high: { name: 'High growth', color: 'system-orange', shape: 'square',
      text: 'Demand grows 2.6 times by 2036, 4.5 times by 2046 and 6.0 times by 2056.' },
    stress_combined: { name: 'Combined stress', color: 'system-teal', shape: 'triangle', dash: true,
      text: 'High growth plus a further 15 percent at every horizon: the toughest test of the plan.' }
  };
  var GROWTH = ['base', 'high', 'stress_combined'];
  var CASES = {
    DEF: { name: 'Deferred', color: 'accent' },
    OVB: { name: 'Overbuild', color: 'system-orange', texture: true },
    STG: { name: 'Staged', color: 'system-teal' }
  };

  function uniq(list) { return list.filter(function (v, i) { return list.indexOf(v) === i; }); }
  function find(list, pred) { for (var i = 0; i < list.length; i++) if (pred(list[i])) return list[i]; return null; }
  function maxBy(list, f) { return list.reduce(function (a, x) { return f(x) > f(a) ? x : a; }, list[0]); }
  function tonnes(v) { return Math.round(v).toLocaleString('en-US'); }

  function boot(data) {
    var H = data.horizons, C = data.costs, E = data.emissions, esc = FC.esc;
    var base0 = find(H, function (h) { return h.scenario === 'baseline'; });
    var pathway = base0 ? base0.pathway : Math.max.apply(null, H.map(function (h) { return h.pathway; }));
    var years = uniq(H.map(function (h) { return h.year; })).sort();
    var growthYears = years.filter(function (y) { return !base0 || y !== base0.year; });
    var hAt = function (scen, y) { return find(H, function (h) { return h.scenario === scen && h.year === y; }); };
    var firstFull = function (scen) { return find(H.filter(function (h) { return h.scenario === scen; }).sort(function (a, b) { return a.year - b.year; }), function (h) { return h.active >= h.pathway; }); };

    /* ---------- Summary tiles ---------- */
    var t1 = hAt('base', growthYears[0]);
    var t2 = firstFull('high');
    var stg = C.filter(function (c) { return c.case === 'STG'; });
    var t3 = maxBy(stg, function (c) { return c.year; });
    var emStress = E.filter(function (e) { return e.scenario === 'stress_combined'; });
    var t4 = maxBy(emStress, function (e) { return e.year; });
    var tiles = [];
    if (t1) tiles.push({ icon: 'bolt', tint: 'var(--accent)', head: 'Base scenario', value: t1.active + ' <small>ports</small>',
      label: 'active by ' + t1.year + ', up from ' + (base0 ? base0.active : '') + ' in ' + (base0 ? base0.year : '') + '.' });
    if (t2) tiles.push({ icon: 'checkmark.circle', tint: 'var(--system-orange)', head: 'High growth', value: t2.active + ' <small>of ' + t2.pathway + '</small>',
      label: 'pathway ports active by ' + t2.year + ': the full pathway.' });
    if (t3) tiles.push({ icon: 'tag', tint: 'var(--system-teal)', head: 'Staged build', value: esc(FC.fmtUSDk(t3.avoided)),
      label: 'avoided by staging instead of overbuilding (' + t3.year + ').' });
    if (t4) tiles.push({ icon: 'globe', tint: 'var(--system-green)', head: 'Combined stress', value: tonnes(t4.tonnes) + ' <small>t CO<sub>2</sub>e</small>',
      label: 'avoided per year by ' + t4.year + '. Higher is better.' });
    document.getElementById('tiles').innerHTML = tiles.map(function (t) {
      return '<div class="tile" style="--tile-tint:' + t.tint + '"><p class="tile__head">' + FC.icon(t.icon, { size: 16, strokeWidth: 2 }) + esc(t.head) + '</p>' +
        '<p class="tile__value">' + t.value + '</p><p class="tile__label">' + t.label + '</p></div>';
    }).join('');

    /* ---------- Scenario rows ---------- */
    var rows = ['baseline'].concat(GROWTH).map(function (k) {
      var s = SCEN[k], detail;
      if (k === 'baseline') detail = base0 ? base0.active + ' ports in ' + base0.year : '';
      else {
        var full = firstFull(k);
        var lastH = hAt(k, years[years.length - 1]);
        detail = full ? 'All ' + full.pathway + ' ports by ' + full.year : (lastH ? lastH.active + ' of ' + lastH.pathway + ' ports by ' + lastH.year : '');
      }
      var text = s.text;
      var sw = FCChart.swatch({ label: s.name, color: s.color, shape: s.shape, line: k !== 'baseline', dash: s.dash });
      return '<li class="hig-list-row"><div class="hig-list-row__content"><span class="hig-list-row__lead" aria-hidden="true">' + sw + '</span>' +
        '<div class="hig-list-row__body"><div class="hig-list-row__text"><span class="hig-list-row__title">' + esc(s.name) + '</span>' +
        '<span class="hig-list-row__subtitle">' + esc(text) + '</span></div>' +
        '<div class="hig-list-row__trailing"><span class="hig-list-row__detail">' + esc(detail) + '</span></div></div></div></li>';
    });
    document.getElementById('scenario-rows').innerHTML = rows.join('');

    /* ---------- Ports over time ---------- */
    var portsVals = GROWTH.map(function (k) {
      return years.map(function (y) { var h = (base0 && y === base0.year) ? base0 : hAt(k, y); return h ? h.active : null; });
    });
    var same = GROWTH.length > 2 && portsVals[1].every(function (v, i) { return v === portsVals[2][i]; });
    var lastY = years[years.length - 1];
    FCChart.create(document.getElementById('ports-chart'), {
      kind: 'line', title: 'Active Ports by Horizon',
      subtitle: 'All scenarios start from ' + (base0 ? base0.active : '') + ' starter ports in ' + years[0] + '. The dashed line is the ' + pathway + '-port future-ready pathway.' +
        (same ? ' High growth and combined stress follow the same path, so their points sit side by side.' : ''),
      summary: GROWTH.map(function (k, i) { return SCEN[k].name + ' reaches ' + portsVals[i][portsVals[i].length - 1] + ' ports by ' + lastY; }).join('; ') +
        '. The pathway capacity is ' + pathway + ' ports.',
      catTitle: 'Year', catNoun: 'horizons', valueTitle: 'Active ports',
      categories: years.map(function (y) { return { label: String(y) }; }),
      series: GROWTH.map(function (k) { return { name: SCEN[k].name, color: SCEN[k].color, shape: SCEN[k].shape, dash: SCEN[k].dash }; }),
      values: portsVals,
      refLines: [{ value: pathway, label: 'Pathway: ' + pathway + ' ports' }],
      format: function (v, si, ctx) { return ctx === 'mark' ? String(v) : v + ' ports'; },
      legend: GROWTH.map(function (k) { return { label: SCEN[k].name, color: SCEN[k].color, shape: SCEN[k].shape, line: true, dash: SCEN[k].dash }; })
        .concat([{ label: 'Future-ready pathway (' + pathway + ')', color: 'label-secondary', line: true, dash: true }])
    });

    /* ---------- Lifecycle cost ---------- */
    var costYears = uniq(C.map(function (c) { return c.year; })).sort();
    var caseKeys = uniq(C.map(function (c) { return c.case; })).filter(function (k) { return CASES[k]; });
    var cAt = function (k, y) { return find(C, function (c) { return c.case === k && c.year === y; }); };
    FCChart.create(document.getElementById('cost-chart'), {
      kind: 'columns', title: 'Net Present Value by Strategy',
      subtitle: 'Base-case trajectory only. Screening-class planning estimates in US dollars.',
      summary: costYears.map(function (y) {
        return y + ': ' + caseKeys.map(function (k) { var c = cAt(k, y); return CASES[k].name + ' ' + (c ? FC.fmtUSD(c.npv) : 'no value'); }).join(', ');
      }).join('. ') + '.',
      catTitle: 'Horizon', catNoun: 'horizons', valueTitle: 'NPV (USD)',
      categories: costYears.map(function (y) { return { label: String(y) }; }),
      series: caseKeys.map(function (k) { return { name: CASES[k].name + ' (' + k + ')', color: CASES[k].color, texture: CASES[k].texture }; }),
      values: caseKeys.map(function (k) { return costYears.map(function (y) { var c = cAt(k, y); return c ? c.npv : null; }); }),
      barMax: 48,
      format: function (v, si, ctx) { return ctx === 'mark' ? FC.fmtUSDk(v) : FC.fmtUSD(v); },
      formatAxis: function (v) { return v === 0 ? '$0' : v >= 1e6 ? '$' + (v / 1e6) + 'M' : '$' + Math.round(v / 1e3) + 'K'; }
    });
    document.getElementById('savings').innerHTML = stg.slice().sort(function (a, b) { return a.year - b.year; }).map(function (c) {
      return '<div class="saving"><p class="saving__year">' + c.year + '</p><p class="saving__value">' + esc(FC.fmtUSD(c.avoided)) + '</p>' +
        '<p class="saving__label">avoided overbuild cost by staging</p></div>';
    }).join('');

    /* ---------- Avoided emissions ---------- */
    var emYears = uniq(E.map(function (e) { return e.year; })).sort();
    var emScen = ['baseline'].concat(GROWTH).filter(function (k) { return E.some(function (e) { return e.scenario === k; }); });
    var eAt = function (k, y) { return find(E, function (e) { return e.scenario === k && e.year === y; }); };
    var best = maxBy(E, function (e) { return e.tonnes; });
    FCChart.create(document.getElementById('em-chart'), {
      kind: 'columns', title: 'Avoided CO2e per Year',
      subtitle: 'Higher is better. Tonnes of CO2e avoided each year, by horizon and scenario.',
      summary: 'Higher is better. The most avoided is ' + tonnes(best.tonnes) + ' tonnes per year (' + SCEN[best.scenario].name + ', ' + best.year + '). ' +
        emYears.map(function (y) {
          return y + ': ' + emScen.map(function (k) { var e = eAt(k, y); return e ? SCEN[k].name + ' ' + tonnes(e.tonnes) : null; }).filter(Boolean).join(', ');
        }).join('. ') + ' tonnes.',
      catTitle: 'Horizon', catNoun: 'horizons', valueTitle: 'Tonnes CO2e per year',
      categories: emYears.map(function (y) { return { label: String(y) }; }),
      series: emScen.map(function (k) { return { name: SCEN[k].name, color: SCEN[k].color, texture: k === 'high' }; }),
      values: emScen.map(function (k) { return emYears.map(function (y) { var e = eAt(k, y); return e ? e.tonnes : null; }); }),
      barMax: 32,
      format: function (v, si, ctx) { return ctx === 'mark' ? tonnes(v) : ctx === 'table' ? v.toFixed(1) + ' t' : tonnes(v) + ' t per year'; }
    });
    if (data.meta && data.meta.emissions) {
      document.getElementById('em-factor').innerHTML = '<strong>Emissions factor:</strong> ' + esc(data.meta.emissions).replace(/CO2e/g, 'CO<sub>2</sub>e') + '.';
    }
  }

  /* Scenario sweep results: the official one once published, the earlier legacy_v2 one always labelled (data/versions.json). */
  function gapsText(list) {
    return list.map(function (g) { return g.id + ' (' + g.ports + (g.ports === 1 ? ' port)' : ' ports)'); }).join(' and ');
  }
  function sweepText(scen, gapSites) {
    var clear = scen.filter(function (s) { return !s.gaps; }), hit = scen.filter(function (s) { return s.gaps; });
    var t = clear.length === scen.length ? 'No scenario left a future-ready capacity gap.'
      : (clear.length ? clear.length + ' of ' + scen.length + ' scenarios showed no future-ready capacity gaps. ' : '') +
        hit.map(function (s) { return s.name + ' opened ' + s.gaps + (s.gaps === 1 ? ' gap' : ' gaps'); }).join('; ') +
        (gapSites && gapSites.length ? ': ' + gapsText(gapSites) : '') + '.';
    return t;
  }
  function versions(v) {
    if (!v || !v.official || !v.earlier) return;
    var esc = FC.esc, off = v.official, old = v.earlier;
    if (off.scenarios && off.scenarios.length) {
      var o = document.getElementById('scenario-official');
      o.innerHTML = '<p class="earlier__label">' + esc(off.label) + ' (' + esc(off.model) + ')</p><p class="earlier__text">' + esc(sweepText(off.scenarios, off.gapSites)) + '</p>';
      o.hidden = false;
    }
    // The earlier (legacy_v2) paragraph is historical and ships as written in outlook.html.
  }

  function fail(err) {
    document.getElementById('tiles').innerHTML = '<p class="footnote" role="alert">' + FC.esc(err && err.message ? err.message : 'The outlook data could not be loaded.') +
      ' Reload the page to try again.</p>';
  }

  function start() {
    FC.data().then(function (d) {
      boot(d);
      return FC.optional('data/versions.json').then(versions);
    }).catch(fail);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
