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

  /* ---------- Figures in the prose (data-k), recomputed from the published data ---------- */
  function setText(key, value) {
    document.querySelectorAll('[data-k="' + key + '"]').forEach(function (el) { el.textContent = value; });
  }
  function fmtPts(v) { return String(Math.round(v * 100) / 100); }
  function one(v) { return Number(v).toFixed(1); }

  function renderFigures(sites, scoring) {
    var starter = 0, pathway = 0;
    sites.forEach(function (s) { starter += s.starter; pathway += s.pathway; });
    setText('starter', starter);
    setText('pathway', pathway);
    var t = FC.topTwo(sites);
    if (t) {
      setText('first-id', t.first.id); setText('first-score', one(t.first.score));
      setText('second-id', t.second.id); setText('second-score', one(t.second.score));
    }
    if (scoring && scoring.sites) {
      // The feasibility points most sites share: the mark of the placeholder electrical capacity.
      var counts = {};
      scoring.sites.forEach(function (s) { var k = one(s.parts.feasibility); counts[k] = (counts[k] || 0) + 1; });
      var top = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })[0];
      if (top && counts[top] > 1) { setText('feas-shared', counts[top]); setText('feas-shared-pts', top); }
      if (scoring.meta && scoring.meta.accessFactor) setText('access-pct', Math.round(scoring.meta.accessFactor * 100));
    }
  }

  /* ---------- Weights table, rebuilt from data/scoring.json so it can never drift from the model ---------- */
  function renderWeights(scoring) {
    var table = document.getElementById('m-weights');
    if (!table || !scoring || !scoring.parts) return;
    var e = FC.esc;
    table.querySelectorAll('tbody').forEach(function (tb) { tb.remove(); });
    var html = scoring.parts.map(function (p) {
      return '<tbody><tr class="m-weights__part"><th scope="rowgroup" colspan="2">' + e(p.name) + '</th><td class="m-weights__num">' + p.weight + '</td></tr>' +
        p.drivers.map(function (d) {
          return '<tr><th scope="row"><span class="m-weights__name">' + e(d.name) + '</span>' +
            (d.note ? '<span class="m-weights__note">' + e(d.note) + '</span>' : '') + '</th>' +
            '<td class="m-weights__num">' + d.share + '%</td><td class="m-weights__num">' + fmtPts(d.points) + '</td></tr>';
        }).join('') + '</tbody>';
    }).join('');
    var tfoot = table.querySelector('tfoot');
    if (tfoot) tfoot.insertAdjacentHTML('beforebegin', html); else table.insertAdjacentHTML('beforeend', html);
    var cards = document.querySelectorAll('#m-parts .m-dim');
    scoring.parts.forEach(function (p, i) {
      var w = cards[i] && cards[i].querySelector('.m-dim__weight');
      if (w) w.innerHTML = p.weight + '<span class="m-dim__unit"> points</span>';
    });
  }

  /* ---------- Rank stability, from data/stability.json (generated by tools/build_stability.py from the engine's
     reference output). Shown only once its status is "final"; until then the page keeps the text it ships with. ---------- */
  function pct1(v) { return (Math.round(v * 10) / 10).toFixed(1) + '%'; }
  function words(n) { return ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n] || String(n); }
  function cap1(t) { return t.charAt(0).toUpperCase() + t.slice(1); }

  function oatSentences(st, names) {
    var rows = st.oneAtATime || [], step = (st.method && st.method.step) || 5;
    var flips = rows.filter(function (r) { return r.topChanged; });
    var t = 'Each part’s weight was moved ' + step + ' points up, then ' + step + ' points down. ' + ((st.method && st.method.rescale) || '') + ' ';
    if (!flips.length) t += 'None of the ' + words(rows.length) + ' changes puts a different site first. ';
    else t += cap1(flips.length === 1 ? 'only one' : words(flips.length)) + ' of the ' + words(rows.length) + ' changes ' + (flips.length === 1 ? 'puts' : 'put') + ' a different site first: ' +
      flips.map(function (r) { return step + (r.change > 0 ? ' more' : ' fewer') + ' points of ' + (names[r.part] || r.part) + ' puts ' + r.first + ' first'; }).join('; ') + '. ';
    // The closest call among the cases that keep the published leader.
    var close = rows.filter(function (r) { return !r.topChanged && r.firstScore != null && r.secondScore != null; })
      .sort(function (x, y) { return (x.firstScore - x.secondScore) - (y.firstScore - y.secondScore); })[0];
    if (close && close.firstScore - close.secondScore <= 0.5) {
      var gap = Math.round((close.firstScore - close.secondScore) * 10) / 10;
      t += step + (close.change > 0 ? ' more' : ' fewer') + ' points of ' + (names[close.part] || close.part) + ' leaves ' + close.first + ' first by ' +
        (gap === 0.1 ? 'a tenth of a point' : gap.toFixed(1) + ' points') + ' (' + one(close.firstScore) + ' against ' + one(close.secondScore) + '). ';
    }
    var f = st.smallestFlip;
    if (f) t += 'The smallest single change that puts a different site first is ' + (names[f.part] || f.part) + (f.to > f.from ? ' rising' : ' falling') +
      ' from ' + Math.round(f.from) + ' to about ' + one(f.to) + ' points.';
    return t.trim();
  }

  function renderStability(st, sites, scoring) {
    if (!FC.stabilityReady(st)) return;
    var e = FC.esc;
    var names = {};
    ((scoring && scoring.parts) || []).forEach(function (p) { names[p.key] = p.name; });
    var byId = {};
    sites.forEach(function (s) { byId[s.id] = s; });
    var t = FC.topTwo(sites);

    var oatText = document.getElementById('m-oat-text');
    if (oatText) oatText.textContent = oatSentences(st, names);

    var oat = document.getElementById('m-oat');
    var rows = (st.oneAtATime || []).filter(function (r) { return r.first; });
    if (oat && rows.length) {
      var step = (st.method && st.method.step) || 5;
      var h = '<table class="m-oat"><caption>Each weight moved ' + step + ' points</caption><thead><tr>' +
        '<th scope="col">Change</th><th scope="col">First</th><th scope="col">Second</th></tr></thead><tbody>';
      rows.forEach(function (r) {
        var flip = !!r.topChanged;
        var label = (names[r.part] || r.part) + ' ' + (r.change > 0 ? '+' : '−') + Math.abs(r.change);
        h += '<tr><th scope="row">' + e(label) + '</th>' +
          '<td' + (flip ? ' class="m-oat__flip"' : '') + '>' + e(r.first) + (flip ? '<span class="hig-visually-hidden"> (a different leader)</span>' : '') + (r.firstScore != null ? '<span class="m-oat__score">' + one(r.firstScore) + '</span>' : '') + '</td>' +
          '<td>' + e(r.second || '') + (r.secondScore != null ? '<span class="m-oat__score">' + one(r.secondScore) + '</span>' : '') + '</td></tr>';
      });
      h += '</tbody></table>';
      if (t) h += '<p class="footnote m-stab__foot">Bold marks a change that puts a site other than ' + e(t.first.id) + ' first.</p>';
      oat.innerHTML = h;
    }

    var chText = document.getElementById('m-chance-text');
    if (chText && st.method && st.method.draws) {
      chText.textContent = 'The four weights were also drawn at random ' + Number(st.method.draws).toLocaleString('en-US') + ' times around their published values' +
        (st.method.spread ? ' (' + st.method.spread + ', in 9 of 10 draws)' : '') + ', and the sites were rescored every time. ' +
        'A site’s chance of first place is the share of those weightings in which it came first. It is a share of plausible weightings, not the chance that a site is the right place to build.';
    }

    var chance = document.getElementById('m-chance');
    var ranked = (st.sites || []).filter(function (s) { return s.chanceFirst != null; });
    if (chance && ranked.length) {
      var shown = ranked.filter(function (s) { return s.chanceFirst > 0; }).sort(function (a, b) { return b.chanceFirst - a.chanceFirst; });
      var never = ranked.length - shown.length;
      var c = '<ul class="m-chance" role="list" aria-label="Chance of first place">' + shown.map(function (s) {
        var site = byId[s.id] || { name: s.id };
        var bits = [site.name];
        if (s.chanceTop3 != null) bits.push('top three in ' + Math.round(s.chanceTop3) + '%');
        if (s.rankLow != null && s.rankHigh != null) bits.push(s.rankLow === s.rankHigh ? 'rank ' + s.rankLow : 'rank ' + s.rankLow + ' to ' + s.rankHigh);
        return '<li class="m-chance__row"><a class="m-chance__site" href="sites.html#' + e(s.id) + '">' + e(s.id) +
          '<span>' + e(bits.join(' · ')) + '</span></a>' +
          '<span class="m-chance__value">' + pct1(s.chanceFirst) + '</span>' +
          '<span class="m-chance__bar" aria-hidden="true"><span class="m-chance__fill" style="width:' + Math.max(0, Math.min(100, s.chanceFirst)) + '%"></span></span></li>';
      }).join('') + '</ul>';
      var foot = [];
      if (never) foot.push('The other ' + never + ' sites never came first.');
      if (st.method && st.method.rangeNote) foot.push('Rank range: ' + st.method.rangeNote.charAt(0).toLowerCase() + st.method.rangeNote.slice(1));
      if (foot.length) c += '<p class="footnote m-stab__foot">' + e(foot.join(' ')) + '</p>';
      chance.innerHTML = c;
    }

    // What the check does not cover: unconfirmed electrical capacity, as a range rather than a probability.
    var capEl = document.getElementById('m-cap-text'), inp = st.inputs;
    if (capEl && inp && inp.capacityPoints != null && inp.feasibilityShared) {
      var fs = inp.feasibilityShared, n = inp.sites || sites.length;
      var same = ((scoring && scoring.sites) || []).filter(function (x) { return x.id === fs.ids[0]; })[0];
      var txt = 'Spare capacity is an unverified placeholder at all ' + n + ' sites and is worth up to ' + fmtPts(inp.capacityPoints) + ' points, so ' + fs.count +
        ' sites share exactly the same feasibility points' + (same ? ' (' + one(same.parts.feasibility) + ')' : '') + '. ';
      if (inp.capacityCouldBeFirst != null) {
        txt += 'If capacity alone ran anywhere from no credit to full credit, ' + inp.capacityCouldBeFirst + ' of the ' + n + ' sites could rank first';
        if (inp.unconfirmedCouldBeFirst != null) txt += '; with every unconfirmed input allowed to move, ' + (inp.unconfirmedCouldBeFirst === n ? 'any of the ' + n : inp.unconfirmedCouldBeFirst) + ' could';
        txt += '. That is a range of what could happen, not a probability. ';
      }
      txt += 'Confirming capacity is the step that would firm up the order most.';
      capEl.innerHTML = '<strong>Placeholder electrical capacity.</strong> ' + e(txt);
    }
  }

  /* ---------- Official versus earlier (legacy_v2) results, from data/versions.json ----------
     Official port totals are always summed from data/sites.json. versions.json says which ranking the port plan
     follows and carries the earlier result, kept apart and labelled. */
  function resultBadge(gaps) {
    return gaps > 0
      ? '<span class="m-result m-result--gap">' + FC.icon('exclamationmark.triangle', { size: 18 }) + gaps + (gaps === 1 ? ' gap' : ' gaps') + '</span>'
      : '<span class="m-result m-result--ok">' + FC.icon('checkmark.circle', { size: 18 }) + 'No gaps</span>';
  }
  function gapList(list, label) {
    if (!list || !list.length) return '';
    return '<ul class="m-gaps__list" role="list" aria-label="' + FC.esc(label) + '">' + list.map(function (g) {
      return '<li><a class="m-gaps__site" href="sites.html#' + FC.esc(g.id) + '">' + FC.esc(g.id) + '</a><span class="m-gaps__amt num">Gap of ' + g.ports + (g.ports === 1 ? ' port' : ' ports') + '</span></li>';
    }).join('') + '</ul>';
  }
  var CHECK_LABELS = [['sites', 'Candidate sites evaluated'], ['tier1', 'Tier 1 starter candidates'], ['categories', 'Decision categories applied'],
    ['exports', 'Tableau-ready data exports'], ['errors', 'Blocking validation errors'], ['warnings', 'Warnings'], ['reviewFlags', 'Review flags to confirm'], ['info', 'Info items']];
  function metrics(m) {
    return '<dl class="m-metrics">' + CHECK_LABELS.filter(function (l) { return m[l[0]] != null; }).map(function (l) {
      return '<div class="m-metric"><dt class="metric__label">' + l[1] + '</dt><dd class="metric__value">' + FC.esc(m[l[0]]) + '</dd></div>';
    }).join('') + '</dl>';
  }

  function renderVersions(v, sites) {
    if (!v || !v.official || !v.earlier) return;
    var e = FC.esc, off = v.official, old = v.earlier;
    var starter = 0, pathway = 0;
    sites.forEach(function (s) { starter += s.starter; pathway += s.pathway; });

    // Port plan: once the official plan no longer follows the earlier ranking, say so and show the earlier totals apart.
    if (off.portPlanBasis && off.portPlanBasis !== old.model) {
      var basis = document.getElementById('m-basis');
      if (basis) basis.innerHTML = '<strong>It follows the official <code>' + e(off.portPlanBasis) + '</code> ranking.</strong> Its totals of ' +
        starter + ' install-now and ' + pathway + ' future-ready ports are the official plan, the same ranking the results pages show.';
      var pe = document.getElementById('m-plan-earlier');
      if (pe && old.pathway != null) {
        pe.innerHTML = '<p class="m-earlier__label">' + e(old.label) + '</p>' +
          '<p class="m-earlier__value"><span class="num">' + old.starter + '</span> install-now and <span class="num">' + old.pathway + '</span> future-ready ports</p>' +
          '<p class="m-earlier__lead">The study’s accepted <code>' + e(old.model) + '</code> ranking, as first presented. Shown for the record only.</p>' +
          '<p class="m-earlier__state">' + FC.icon('xmark', { size: 16 }) + 'Superseded</p>';
        pe.hidden = false;
      }
    }

    // Scenario sweep: the official result when published, the earlier one always labelled.
    var so = document.getElementById('m-scen-official');
    if (so && off.scenarios && off.scenarios.length) {
      so.innerHTML = '<p class="m-official__label">' + e(off.label) + ' (' + e(off.model) + ')</p>' +
        '<ul class="m-earlier__rows" role="list">' + off.scenarios.map(function (s) {
          return '<li><span>' + e(s.name) + '</span>' + resultBadge(s.gaps) + '</li>';
        }).join('') + '</ul>' + gapList(off.gapSites, 'Capacity gaps in the official result');
      so.hidden = false;
    }
    var rowsEl2 = document.getElementById('m-scen-earlier-rows');
    if (rowsEl2 && old.scenarios) {
      rowsEl2.innerHTML = old.scenarios.map(function (s) { return '<li><span>' + e(s.name) + '</span>' + resultBadge(s.gaps) + '</li>'; }).join('');
    }
    var gapsEl = document.getElementById('m-scen-earlier-gaps');
    if (gapsEl && old.gapSites) gapsEl.outerHTML = gapList(old.gapSites, 'Combined-stress capacity gaps in the earlier result') || '';

    // Baseline check: the official run's counts lead when published; the earlier counts stay labelled below.
    var co = document.getElementById('m-check-official');
    if (co && off.baselineCheck) {
      co.innerHTML = '<p class="m-official__label">' + e(off.label) + ' (' + e(off.model) + ')</p>' + metrics(off.baselineCheck);
      co.hidden = false;
      if (off.baselineCheck.reviewFlags != null) setText('review-flags', off.baselineCheck.reviewFlags);
    }
    var ce = document.getElementById('m-check-earlier');
    if (ce && old.baselineCheck) {
      ce.innerHTML = '<p class="m-earlier__label">' + e(old.label) + '</p>' + metrics(old.baselineCheck);
    }
  }

  Promise.all([FC.data(), FC.optional('data/scoring.json'), FC.optional('data/stability.json'), FC.optional('data/versions.json')]).then(function (all) {
    var d = all[0], scoring = all[1], st = all[2], v = all[3];
    var sites = (d && d.sites) || [];
    renderFigures(sites, scoring);
    renderWeights(scoring);
    renderStability(st, sites, scoring);
    renderVersions(v, sites);
    if (rowsEl) renderPlan(sites);
    renderMembership(sites);
  }).catch(function () {
    if (rowsEl) {
      rowsEl.innerHTML = '<p class="m-plan__status footnote">The per-site port plan could not be loaded. The totals above still apply. Reload the page to try again.</p>';
    }
  });
})();
