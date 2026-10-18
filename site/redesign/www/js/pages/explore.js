/* Explore the Data: a view picker and one content frame for the seven published Tableau Public views.
   Privacy: no request goes to public.tableau.com until the person presses "Load Interactive View".
   That choice is kept for this browser session only (sessionStorage), and can be turned off again. */
(function () {
  'use strict';

  var WORKBOOK = 'EV_Charging_Site_Readiness_M2_Canonical';
  var BASE = 'https://public.tableau.com/views/' + WORKBOOK + '/';
  var EMBED = '?:showVizHome=no&:embed=yes&:toolbar=yes&:tabs=no';
  var CONSENT_KEY = 'fc.explore.tableau';

  var VIEWS = [
    { key: 'SiteMap', label: 'Site Map', icon: 'map',
      desc: 'Where the 12 candidate sites are, across Fairfax and Prince William County. Use the map to connect scores back to real places.' },
    { key: 'ReadinessbySite', label: 'Readiness by Site', icon: 'chart.bar',
      desc: 'The readiness score and rank of each site in the canonical milestone2_v3 model. Start here and compare sites before anything else; every score rests on placeholder capacity.' },
    { key: 'StartervsPathwayPorts', label: 'Starter vs Pathway Ports', icon: 'square.grid.2x2',
      desc: 'The starter install at each site next to the pathway it could grow into. Look for where future capacity grows beyond the starter install.' },
    { key: 'PortsAcrossHorizons', label: 'Ports Across Horizons', icon: 'calendar',
      desc: 'How recommended port counts change across the planning horizons and scenarios.' },
    { key: 'LifecycleCostbyHorizon', label: 'Lifecycle Cost by Horizon', icon: 'tag',
      desc: 'Lifecycle cost across the planning horizons. These are screening-class figures for comparing sites, never budgets, quotes or engineering estimates.' },
    { key: 'NetCO2ebyHorizon', label: 'Avoided CO2e by Horizon', icon: 'globe',
      desc: 'Avoided carbon dioxide equivalent (CO2e) across the planning horizons. Higher is better.',
      note: { title: 'A rising line is a good outcome', body: 'The published sheet is titled “Net CO2e”. It shows avoided CO2e, so higher values mean more emissions avoided.' } },
    { key: 'PeakWaitsbySite', label: 'Peak Waits by Site', icon: 'clock',
      desc: 'Modelled queue waits at peak for each site under the base case. No site has been observed in operation.' }
  ];

  var root = document.getElementById('explorer');
  if (!root || !window.FC) return;
  var FC = window.FC;
  var esc = FC.esc;

  function storage(fn) { try { return fn(window.sessionStorage); } catch (e) { return null; } }
  function hasConsent() { return storage(function (s) { return s.getItem(CONSENT_KEY) === '1'; }) === true; }
  function setConsent(on) { storage(function (s) { if (on) s.setItem(CONSENT_KEY, '1'); else s.removeItem(CONSENT_KEY); }); }
  var consent = hasConsent();

  function indexOfKey(k) {
    for (var i = 0; i < VIEWS.length; i++) if (VIEWS[i].key === k) return i;
    return -1;
  }
  function openURL(v) { return BASE + v.key; }
  function embedURL(v) { return BASE + v.key + EMBED; }

  /* iOS-style large spinner (8 capsule spokes), as the design system's ProgressIndicator draws it. */
  function spinner() {
    var op = [1, 0.15, 0.27, 0.39, 0.51, 0.63, 0.75, 0.87];
    var s = '<svg class="hig-progress__spinner hig-progress__spinner--large" viewBox="0 0 35 35" width="35" height="35" aria-hidden="true" focusable="false">';
    op.forEach(function (o, i) {
      s += '<rect x="15" y="0" width="5" height="13" rx="2.5" fill="currentColor" opacity="' + o + '" transform="rotate(' + (i * 45) + ' 17.5 17.5)"/>';
    });
    return s + '</svg>';
  }

  /* ---------- Build ---------- */
  var html = '<div class="ex__layout">' +
    '<div class="ex-picker">' +
    '<p class="ex-picker__label" id="ex-picker-label" aria-hidden="true">Views</p>' +
    '<div class="ex-tabs" role="tablist" aria-label="Tableau views" aria-orientation="horizontal">';
  VIEWS.forEach(function (v, i) {
    html += '<button type="button" class="ex-tab" role="tab" id="ex-tab-' + v.key + '" aria-controls="ex-panel" aria-selected="false" tabindex="-1" data-key="' + v.key + '">' +
      '<span class="ex-tab__icon" aria-hidden="true">' + FC.icon(v.icon, { size: 18 }) + '</span>' +
      '<span class="ex-tab__label">' + esc(v.label) + '</span></button>';
  });
  html += '</div></div>' +
    '<div class="ex-panel" id="ex-panel" role="tabpanel" tabindex="-1">' +
      '<div class="ex-panel__head">' +
        '<div class="ex-panel__top"><span class="ex-panel__eyebrow" id="ex-eyebrow"></span>' +
        '<a class="ex-panel__open" id="ex-open" target="_blank" rel="noopener" href="#"></a></div>' +
        '<h2 class="ex-panel__title" id="ex-title"></h2>' +
        '<p class="ex-panel__desc" id="ex-desc"></p>' +
        '<div id="ex-note"></div>' +
      '</div>' +
      '<div class="ex-frame" id="ex-frame"></div>' +
      '<div class="ex-panel__foot" id="ex-foot" hidden>' +
        '<span>Interactive views are on until you close this tab.</span>' +
        '<button type="button" class="hig-button hig-focus hig-pressable hig-button--ios hig-button--borderless hig-button--small" id="ex-off">' +
        '<span class="hig-button__label">Turn Off</span></button>' +
      '</div>' +
      '<p class="hig-visually-hidden" id="ex-status" role="status" aria-live="polite"></p>' +
    '</div></div>';
  root.innerHTML = html;

  var tabs = Array.prototype.slice.call(root.querySelectorAll('.ex-tab'));
  var tablist = root.querySelector('.ex-tabs');
  var panel = document.getElementById('ex-panel');
  var frame = document.getElementById('ex-frame');
  var foot = document.getElementById('ex-foot');
  var status = document.getElementById('ex-status');
  var current = -1;

  function say(msg) { status.textContent = ''; window.setTimeout(function () { status.textContent = msg; }, 60); }

  function renderGate(v) {
    frame.innerHTML =
      '<div class="ex-frame__gate">' +
        '<span class="ex-frame__glyph" aria-hidden="true">' + FC.icon(v.icon, { size: 28 }) + '</span>' +
        '<p class="ex-frame__gate-title">This view loads from Tableau Public</p>' +
        '<p class="ex-frame__gate-body">Loading the view contacts public.tableau.com, a third-party service. Tableau receives your IP address and browser details and may set its own cookies under its own privacy policy. This site sends it nothing else.</p>' +
        '<p class="ex-frame__gate-body ex-frame__compact-hint">On a small screen the view is cramped here. Tableau Public gives it the full screen.</p>' +
        '<div class="ex-frame__actions">' +
        '<button type="button" class="hig-button hig-focus hig-pressable hig-button--ios hig-button--large" id="ex-load">' +
        '<span class="hig-button__label">Load Interactive View</span></button>' +
        '<a class="hig-button hig-focus hig-pressable hig-button--ios hig-button--large" id="ex-open-gate" href="' + openURL(v) + '" target="_blank" rel="noopener">' +
        '<span class="hig-button__label">Open in Tableau Public</span><span class="hig-visually-hidden"> (new tab)</span></a>' +
        '</div>' +
        '<p class="ex-frame__gate-foot">Your choice applies to all seven views until you close this tab. You can turn it off at any time.</p>' +
      '</div>';
    foot.hidden = true;
    applyEmphasis();
    document.getElementById('ex-load').addEventListener('click', function () {
      consent = true;
      setConsent(true);
      renderViz(VIEWS[current], true);
    });
  }

  function renderViz(v, moveFocus) {
    frame.innerHTML =
      '<div class="ex-frame__loading" id="ex-loading">' + spinner() + '<span>Contacting Tableau Public…</span></div>';
    var ifr = document.createElement('iframe');
    ifr.src = embedURL(v);
    ifr.title = v.label + ': interactive Tableau Public view';
    ifr.setAttribute('allowfullscreen', '');
    ifr.addEventListener('load', function () {
      var l = document.getElementById('ex-loading');
      if (l) l.hidden = true;
      say(v.label + ' loaded.');
    });
    frame.insertBefore(ifr, frame.firstChild);
    foot.hidden = false;
    say('Loading ' + v.label + ' from Tableau Public.');
    if (moveFocus) { try { panel.focus({ preventScroll: true }); } catch (e) { panel.focus(); } }
  }

  function select(i, opts) {
    opts = opts || {};
    if (i < 0 || i >= VIEWS.length) i = 0;
    var v = VIEWS[i];
    var changed = i !== current;
    current = i;
    tabs.forEach(function (t, j) {
      var on = j === i;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', 'ex-tab-' + v.key);
    document.getElementById('ex-eyebrow').textContent = 'View ' + (i + 1) + ' of ' + VIEWS.length;
    document.getElementById('ex-title').textContent = v.label;
    document.getElementById('ex-desc').textContent = v.desc;
    var open = document.getElementById('ex-open');
    open.href = openURL(v);
    open.innerHTML = 'Open in Tableau Public' + FC.icon('chevron.right', { size: 14, strokeWidth: 2.2 }) +
      '<span class="hig-visually-hidden"> (opens ' + esc(v.label) + ' in a new tab)</span>';
    var note = document.getElementById('ex-note');
    note.innerHTML = v.note ?
      '<div class="notice notice--positive" role="note"><span class="notice__icon">' + FC.icon('info.circle', { size: 20 }) + '</span>' +
      '<div><p class="notice__title">' + esc(v.note.title) + '</p><p class="notice__body">' + esc(v.note.body) + '</p></div></div>' : '';

    if (changed || opts.force) {
      if (consent) renderViz(v, false); else renderGate(v);
    }
    if (opts.updateHash !== false && location.hash !== '#' + v.key) {
      try { history.replaceState(null, '', '#' + v.key); } catch (e) { /* file:// or sandboxed: leave the URL alone */ }
    }
    var tab = tabs[i];
    if (opts.focus) tab.focus();
    revealTab(tab);
  }

  /* Keep the selected chip visible in the scrolling row without scrolling the page. */
  function revealTab(tab) {
    if (tablist.scrollWidth <= tablist.clientWidth) return;
    var left = tab.offsetLeft - tablist.offsetLeft;
    var target = left - (tablist.clientWidth - tab.offsetWidth) / 2;
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try { tablist.scrollTo({ left: Math.max(0, target), behavior: reduce ? 'auto' : 'smooth' }); } catch (e) { tablist.scrollLeft = Math.max(0, target); }
  }

  /* ---------- Interaction ---------- */
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(i); });
    t.addEventListener('keydown', function (e) {
      var n = null;
      var rtl = getComputedStyle(tablist).direction === 'rtl';
      var cur = tabs.indexOf(document.activeElement);
      if (cur < 0) return;
      if (e.key === 'ArrowDown' || e.key === (rtl ? 'ArrowLeft' : 'ArrowRight')) n = (cur + 1) % tabs.length;
      else if (e.key === 'ArrowUp' || e.key === (rtl ? 'ArrowRight' : 'ArrowLeft')) n = (cur - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') n = 0;
      else if (e.key === 'End') n = tabs.length - 1;
      if (n === null) return;
      e.preventDefault();
      /* Manual activation: arrows move focus; Enter or Space opens the view (avoids loading a view per keypress). */
      tabs.forEach(function (x, j) { x.tabIndex = j === n ? 0 : -1; });
      tabs[n].focus();
      revealTab(tabs[n]);
    });
  });
  /* When focus leaves the tab list, the selected tab is again its single tab stop. */
  tablist.addEventListener('focusout', function (e) {
    if (tablist.contains(e.relatedTarget)) return;
    tabs.forEach(function (x, j) { x.tabIndex = j === current ? 0 : -1; });
  });

  document.getElementById('ex-off').addEventListener('click', function () {
    consent = false;
    setConsent(false);
    renderGate(VIEWS[current]);
    say('Interactive views turned off. Nothing more loads from Tableau Public.');
    var b = document.getElementById('ex-load');
    if (b) b.focus();
  });

  window.addEventListener('hashchange', function () {
    var i = indexOfKey(location.hash.slice(1));
    if (i >= 0 && i !== current) select(i, { updateHash: false });
  });

  /* Orientation follows the layout: a vertical list when the container is wide, a chip row when compact. */
  function syncOrientation() {
    var w = root.clientWidth;
    tablist.setAttribute('aria-orientation', w >= 800 ? 'vertical' : 'horizontal');
    /* Phones: a narrow column, or a short landscape window. */
    var compact = w < 560 || (window.matchMedia && window.matchMedia('(max-height: 500px)').matches);
    if (compact !== root.classList.contains('is-compact')) { root.classList.toggle('is-compact', compact); applyEmphasis(); }
  }
  /* One prominent control at a time: on phones, where embeds are cramped, opening in Tableau Public is the
     prominent action; on wider screens, loading the view in place is. */
  function applyEmphasis() {
    var compact = root.classList.contains('is-compact');
    var load = document.getElementById('ex-load');
    var open = document.getElementById('ex-open-gate');
    if (!load || !open) return;
    load.classList.toggle('hig-button--bordered-prominent', !compact);
    load.classList.toggle('hig-button--bordered', compact);
    open.classList.toggle('hig-button--bordered-prominent', compact);
    open.classList.toggle('hig-button--bordered', !compact);
  }
  if (window.ResizeObserver) new ResizeObserver(syncOrientation).observe(root);
  window.addEventListener('resize', syncOrientation);
  syncOrientation();

  var start = indexOfKey(location.hash.slice(1));
  select(start >= 0 ? start : 0, { updateHash: start >= 0 });
})();
