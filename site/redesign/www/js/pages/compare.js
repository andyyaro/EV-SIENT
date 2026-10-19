/* Compare Sites: one chart switched by a segmented control (Readiness | Ports | Waits), a sortable table of all
   12 sites that links each row to sites.html#ID, and a client-side CSV of exactly the table's columns. */
(function () {
  'use strict';

  var TIER_ORDER = ['tier1', 'high-review', 'tier2', 'tier3', 'special'];
  var TIER_MARK = {
    'tier1': { shape: 'circle', color: 'system-green' },
    'high-review': { shape: 'diamond', color: 'system-orange' },
    'tier2': { shape: 'square', color: 'system-teal' },
    'tier3': { shape: 'dash', color: 'system-gray' },
    'special': { shape: 'triangle', color: 'system-red' }
  };

  function sum(list, key) { return list.reduce(function (a, s) { return a + s[key]; }, 0); }
  function one(v) { return Number(v).toFixed(1); }

  function boot(data) {
    var sites = data.sites.slice().sort(function (a, b) { return a.rank - b.rank; });
    var totalStarter = sum(sites, 'starter');
    var totalPathway = sum(sites, 'pathway');
    var cats = sites.map(function (s) {
      return { label: s.name, lead: String(s.rank), mark: TIER_MARK[s.tierKey], tableLabel: s.rank + '. ' + s.name + ' (' + s.id + ')' };
    });
    var tierShort = function (k) { return (FC.TIERS[k] || { short: k }).short; };

    /* ---------- Chart views ---------- */
    var top = sites[0], last = sites[sites.length - 1];
    var tierCounts = {};
    sites.forEach(function (s) { tierCounts[s.tierKey] = (tierCounts[s.tierKey] || 0) + 1; });
    var readiness = {
      kind: 'hbar', title: 'Readiness Score',
      subtitle: 'Sites in rank order. Each bar is colored and marked by its tier; the legend names the tiers.',
      summary: 'Scores run from ' + one(top.score) + ' for ' + top.name + ' (rank 1) to ' + one(last.score) + ' for ' + last.name + ' (rank ' + last.rank + '). ' +
        TIER_ORDER.filter(function (k) { return tierCounts[k]; }).map(function (k) { return tierCounts[k] + ' ' + tierShort(k); }).join(', ') + '.',
      catTitle: 'Site', catNoun: 'sites', valueTitle: 'Readiness score',
      categories: cats,
      series: [{ name: 'Score', color: 'accent' }],
      values: [sites.map(function (s) { return s.score; })],
      colorAt: function (si, ci) { return TIER_MARK[sites[ci].tierKey].color; },
      format: function (v) { return one(v); },
      formatAxis: function (v) { return String(v); },
      legend: TIER_ORDER.filter(function (k) { return tierCounts[k]; }).map(function (k) {
        return { label: (FC.TIERS[k] || {}).label || k, shape: TIER_MARK[k].shape, color: TIER_MARK[k].color };
      }),
      tableExtra: [{ title: 'Tier', value: function (ci) { return tierShort(sites[ci].tierKey); } }]
    };
    var ports = {
      kind: 'hbar', title: totalStarter + ' Ports Now, ' + totalPathway + ' Future-Ready',
      subtitle: 'Starter ports to install now beside the future-ready pathway each site should be prepared for, in rank order.',
      summary: 'Across the 12 sites: ' + totalStarter + ' starter ports and ' + totalPathway + ' future-ready pathway ports. ' +
        'The largest pathways are ' + sites.filter(function (s) { return s.pathway === Math.max.apply(null, sites.map(function (x) { return x.pathway; })); })
          .map(function (s) { return s.name + ' (' + s.pathway + ')'; }).join(' and ') + '.',
      catTitle: 'Site', catNoun: 'sites', valueTitle: 'Ports',
      categories: cats,
      series: [{ name: 'Starter now', color: 'accent' }, { name: 'Future-ready pathway', color: 'system-orange', texture: true }],
      values: [sites.map(function (s) { return s.starter; }), sites.map(function (s) { return s.pathway; })],
      format: function (v, si, ctx) { return ctx === 'mark' ? String(v) : v + (v === 1 ? ' port' : ' ports'); },
      formatAxis: function (v) { return String(v); }
    };
    // Waits: one site's peak dwarfs the rest. Cut the scale just above every other site's values and draw that
    // site's bars broken, labeled with their full values (no log scale).
    var outlier = sites.reduce(function (a, s) { return s.waitPeak > a.waitPeak ? s : a; }, sites[0]);
    var othersMax = Math.max.apply(null, sites.filter(function (s) { return s !== outlier; }).map(function (s) { return Math.max(s.waitMean, s.waitPeak); }));
    var waits = {
      kind: 'hbar', title: 'Modelled Wait Times',
      subtitle: 'Mean simulated wait and the Erlang peak-window estimate, in minutes. The scale is cut so the other sites stay readable: ' +
        outlier.id + '’s bars are broken and labeled with their full values (' + one(outlier.waitMean) + ' and ' + one(outlier.waitPeak) + ' min).',
      summary: outlier.name + ' (' + outlier.id + ') has the longest waits: ' + one(outlier.waitMean) + ' minutes mean and ' + one(outlier.waitPeak) +
        ' minutes in the peak window. Every other site stays at or under ' + one(othersMax) + ' minutes.',
      catTitle: 'Site', catNoun: 'sites', valueTitle: 'Wait', unit: 'minutes',
      categories: cats,
      series: [{ name: 'Mean wait', color: 'accent' }, { name: 'Peak-window wait', color: 'system-orange', texture: true }],
      values: [sites.map(function (s) { return s.waitMean; }), sites.map(function (s) { return s.waitPeak; })],
      cap: othersMax,
      format: function (v, si, ctx) { return ctx === 'mark' && v <= othersMax ? one(v) : one(v) + ' min'; },
      formatAxis: function (v) { return String(v); }
    };
    var views = { readiness: readiness, ports: ports, waits: waits };
    var keys = {
      readiness: '<strong>' + (tierCounts.tier1 || 0) + '</strong> Tier 1 sites',
      ports: 'The pathway adds <strong>' + (totalPathway - totalStarter) + '</strong> ports beyond the starter build',
      waits: 'Longest peak wait <strong>' + one(outlier.waitPeak) + ' min</strong> (' + FC.esc(outlier.id) + ')'
    };
    var keyEl = document.getElementById('chart-key');
    var chart = FCChart.create(document.getElementById('compare-chart'), readiness);
    keyEl.innerHTML = keys.readiness;
    FC.segmented(document.getElementById('view-picker'), function (v) {
      chart.set(views[v]);
      keyEl.innerHTML = keys[v];
    });

    /* ---------- Table ---------- */
    var COLS = [
      { key: 'rank', title: 'Rank', align: 'trailing', get: function (s) { return s.rank; }, csv: function (s) { return s.rank; } },
      { key: 'site', title: 'Site', get: function (s) { return s.name; }, csv: function (s) { return s.name + ' (' + s.id + ')'; } },
      { key: 'jurisdiction', title: 'Jurisdiction', get: function (s) { return s.jurisdiction; }, csv: function (s) { return s.jurisdiction; } },
      { key: 'type', title: 'Type', get: function (s) { return FC.siteType(s.type); }, csv: function (s) { return FC.siteType(s.type); } },
      { key: 'score', title: 'Score', align: 'trailing', get: function (s) { return s.score; }, csv: function (s) { return one(s.score); } },
      { key: 'tier', title: 'Tier', get: function (s) { return TIER_ORDER.indexOf(s.tierKey); }, csv: function (s) { return tierShort(s.tierKey); } },
      { key: 'starter', title: 'Ports Now', align: 'trailing', get: function (s) { return s.starter; }, csv: function (s) { return s.starter; } },
      { key: 'pathway', title: 'Future-Ready', align: 'trailing', get: function (s) { return s.pathway; }, csv: function (s) { return s.pathway; } },
      { key: 'waitMean', title: 'Mean Wait', csvTitle: 'Mean Wait (min)', align: 'trailing', get: function (s) { return s.waitMean; }, csv: function (s) { return one(s.waitMean); } },
      { key: 'waitPeak', title: 'Peak Wait', csvTitle: 'Peak Wait (min)', align: 'trailing', get: function (s) { return s.waitPeak; }, csv: function (s) { return one(s.waitPeak); } }
    ];
    var sort = { key: 'rank', dir: 'ascending' };
    var tableEl = document.getElementById('site-table');
    var statusEl = document.getElementById('sort-status');

    function sorted() {
      var col = COLS.filter(function (c) { return c.key === sort.key; })[0];
      var d = sort.dir === 'descending' ? -1 : 1;
      return sites.slice().sort(function (a, b) {
        var x = col.get(a), y = col.get(b);
        var r = typeof x === 'number' ? x - y : String(x).localeCompare(String(y), 'en', { numeric: true, sensitivity: 'base' });
        return d * (r || a.rank - b.rank);
      });
    }

    function cell(c, s) {
      var e = FC.esc;
      switch (c.key) {
        case 'rank': return '<span class="site-table__rank">' + s.rank + '</span>';
        case 'site': return '<span class="site-table__site"><a href="sites.html#' + e(s.id) + '">' + e(s.name) + '</a><span class="site-table__id">' + e(s.id) + '</span></span>';
        case 'type': return e(FC.siteType(s.type));
        case 'score': return one(s.score);
        case 'tier': return FC.tier(s.tierKey);
        case 'waitMean': return one(s.waitMean) + ' <span class="site-table__unit">min</span>';
        case 'waitPeak': return one(s.waitPeak) + ' <span class="site-table__unit">min</span>';
        default: return e(s[c.key]);
      }
    }

    function renderTable(focusKey) {
      var rows = sorted();
      var h = '<table class="hig-table__grid"><caption class="hig-visually-hidden">All 12 candidate sites. Sorted by ' +
        FC.esc(COLS.filter(function (c) { return c.key === sort.key; })[0].title) + ', ' + sort.dir + '.</caption><thead><tr class="hig-table__head-row">';
      COLS.forEach(function (c, i) {
        var on = sort.key === c.key;
        var align = c.align || 'leading';
        var sticky = i < 2 ? ' is-sticky is-sticky--' + i : '';
        h += '<th scope="col" aria-sort="' + (on ? sort.dir : 'none') + '" class="hig-table__heading hig-table__cell--' + align + (on ? ' hig-table__heading--sorted' : '') + sticky + '">' +
          '<button type="button" class="hig-table__sort hig-focus" data-key="' + c.key + '"><span class="hig-table__heading-label">' + FC.esc(c.title) + '</span>' +
          '<span class="hig-table__sort-indicator" aria-hidden="true">' + (on ? FC.icon(sort.dir === 'descending' ? 'chevron.down' : 'chevron.up', { size: 16, strokeWidth: 2.4 }) : '') + '</span></button></th>';
      });
      h += '</tr></thead><tbody>';
      rows.forEach(function (s) {
        h += '<tr class="hig-table__row" data-id="' + FC.esc(s.id) + '">';
        COLS.forEach(function (c, i) {
          var tag = c.key === 'site' ? 'th scope="row"' : 'td';
          var sticky = i < 2 ? ' is-sticky is-sticky--' + i : '';
          h += '<' + tag + ' class="hig-table__cell hig-table__cell--' + (c.align || 'leading') + sticky + '">' + cell(c, s) + '</' + tag.split(' ')[0] + '>';
        });
        h += '</tr>';
      });
      h += '</tbody></table>';
      tableEl.innerHTML = h;
      if (focusKey) {
        var b = tableEl.querySelector('.hig-table__sort[data-key="' + focusKey + '"]');
        if (b) b.focus();
      }
    }

    tableEl.addEventListener('click', function (e) {
      var btn = e.target.closest('.hig-table__sort');
      if (btn) {
        var k = btn.getAttribute('data-key');
        sort = { key: k, dir: sort.key === k && sort.dir === 'ascending' ? 'descending' : 'ascending' };
        renderTable(k);
        var col = COLS.filter(function (c) { return c.key === k; })[0];
        statusEl.textContent = 'Sorted by ' + col.title + ', ' + sort.dir + '.';
        return;
      }
      if (e.target.closest('a')) return;
      var tr = e.target.closest('tr[data-id]');
      if (tr && !(window.getSelection && String(window.getSelection()))) window.location.href = 'sites.html#' + encodeURIComponent(tr.getAttribute('data-id'));
    });
    renderTable();

    /* ---------- CSV: exactly the table's columns, in the current sort order ---------- */
    function csvField(v) {
      var s = String(v == null ? '' : v);
      return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }
    var btn = document.getElementById('download-csv');
    btn.disabled = false;
    btn.addEventListener('click', function () {
      var lines = [COLS.map(function (c) { return csvField(c.csvTitle || c.title); }).join(',')];
      sorted().forEach(function (s) { lines.push(COLS.map(function (c) { return csvField(c.csv(s)); }).join(',')); });
      var blob = new Blob([lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'ev-site-readiness-compare.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      statusEl.textContent = 'Downloaded a CSV of all 12 sites.';
    });
  }

  /* ---------- Score breakdown: four weighted parts in points (data/scoring.json), plus rank range and chance of
     first place once the stability check is published (data/stability.json). ---------- */
  function breakdown(data, scoring, st) {
    var el = document.getElementById('breakdown-table');
    if (!el) return;
    if (!scoring || !scoring.parts || !scoring.sites) {
      el.innerHTML = '<p class="footnote">The score breakdown could not be loaded. Reload the page to try again.</p>';
      return;
    }
    var e = FC.esc;
    var byId = {};
    scoring.sites.forEach(function (b) { byId[b.id] = b; });
    var sites = data.sites.slice().sort(function (a, b) { return a.rank - b.rank; });
    var ready = FC.stabilityReady(st);
    var stab = function (id) { return FC.stabilityFor(st, id) || {}; };
    var showRange = ready && sites.some(function (s) { return stab(s.id).rankLow != null; });
    var showChance = ready && sites.some(function (s) { return stab(s.id).chanceFirst != null; });

    var h = '<table class="hig-table__grid"><caption class="hig-visually-hidden">Score breakdown for all ' + sites.length +
      ' sites, in points. Each row’s parts add up to its score.</caption><thead><tr class="hig-table__head-row">';
    var heads = [['Rank', 'trailing'], ['Site', 'leading']].concat(scoring.parts.map(function (p) { return [p.name + ' (' + p.weight + ')', 'trailing']; }))
      .concat([['Score', 'trailing']]).concat(showRange ? [['Rank Range', 'trailing']] : []).concat(showChance ? [['Chance of First', 'trailing']] : []);
    heads.forEach(function (c, i) {
      var sticky = i < 2 ? ' is-sticky is-sticky--' + i : '';
      h += '<th scope="col" class="hig-table__heading hig-table__cell--' + c[1] + sticky + '"><span class="hig-table__heading-label">' + e(c[0]) + '</span></th>';
    });
    h += '</tr></thead><tbody>';
    sites.forEach(function (s) {
      var b = byId[s.id] || { parts: {} }, x = stab(s.id);
      h += '<tr class="hig-table__row">' +
        '<td class="hig-table__cell hig-table__cell--trailing is-sticky is-sticky--0"><span class="site-table__rank">' + s.rank + '</span></td>' +
        '<th scope="row" class="hig-table__cell hig-table__cell--leading is-sticky is-sticky--1"><span class="site-table__site"><a href="sites.html#' + e(s.id) + '">' + e(s.name) + '</a><span class="site-table__id">' + e(s.id) + '</span></span></th>';
      scoring.parts.forEach(function (p) {
        var v = b.parts[p.key];
        h += '<td class="hig-table__cell hig-table__cell--trailing">' + (v == null ? '' : one(v)) +
          (p.key === 'demand' && b.demandAccessFactor ? '<span class="site-table__unit"> *</span>' : '') + '</td>';
      });
      h += '<td class="hig-table__cell hig-table__cell--trailing"><strong>' + one(s.score) + '</strong></td>';
      if (showRange) h += '<td class="hig-table__cell hig-table__cell--trailing">' + (x.rankLow == null ? '' : x.rankLow === x.rankHigh ? x.rankLow : x.rankLow + ' to ' + x.rankHigh) + '</td>';
      if (showChance) h += '<td class="hig-table__cell hig-table__cell--trailing">' + (x.chanceFirst == null ? '' : Math.round(x.chanceFirst) + '%') + '</td>';
      h += '</tr>';
    });
    h += '</tbody></table>';
    el.innerHTML = h;

    // Figures in the notes, recomputed from the data.
    var counts = {};
    scoring.sites.forEach(function (b) { var k = one(b.parts.feasibility); counts[k] = (counts[k] || 0) + 1; });
    var top = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })[0];
    if (top && counts[top] > 1) {
      document.querySelectorAll('[data-k="feas-shared"]').forEach(function (n) { n.textContent = counts[top]; });
      document.querySelectorAll('[data-k="feas-shared-pts"]').forEach(function (n) { n.textContent = top; });
    }
  }

  function fail(err) {
    var msg = '<p class="footnote" role="alert">' + FC.esc(err && err.message ? err.message : 'The site data could not be loaded.') +
      ' Reload the page to try again.</p>';
    document.getElementById('compare-chart').innerHTML = msg;
    document.getElementById('site-table').innerHTML = msg;
  }

  function start() {
    FC.data().then(function (data) {
      boot(data);
      return Promise.all([FC.optional('data/scoring.json'), FC.optional('data/stability.json')]).then(function (all) {
        breakdown(data, all[0], all[1]);
      });
    }).catch(fail);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
