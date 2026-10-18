/* Shared behavior for every page: icons, navigation, data, and the small set of controls the pages use.
   Pages call FC.* after this script loads. No framework; markup follows the HIG Native component classes. */
(function () {
  'use strict';

  /* ---------- Icons (HIG Native glyphs, plus three drawn for this site in the same 24x24, 1.8 stroke style) ---------- */
  var ICONS = window.HIG_ICONS || {};
  ICONS['chart.bar'] = [['path', { d: 'M5 20V12M10 20V6M15 20v-9M20 20V9' }], ['path', { d: 'M3 20.5h18', sw: 0.8 }]];
  ICONS['bolt'] = [['path', { d: 'M13.5 3L5.5 13.5h6l-1 7.5 8-10.5h-6z' }]];
  ICONS['map'] = [['path', { d: 'M3.5 6.5l5.5-2.5 6 2.5 5.5-2.5v13.5l-5.5 2.5-6-2.5-5.5 2.5z' }], ['path', { d: 'M9 4v13.5M15 6.5V20' }]];
  ICONS['bubble'] = [['path', { d: 'M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8.5a1.5 1.5 0 0 1-1.5 1.5H10l-4.5 3.5V17H5A1.5 1.5 0 0 1 3.5 15.5V7A1.5 1.5 0 0 1 5 5.5z' }]];
  ICONS['books'] = [['path', { d: 'M4.5 5h4v14h-4zM8.5 5h4v14h-4z' }], ['path', { d: 'M13.2 6.2l3.9-1 3.4 13.6-3.9 1z' }]];
  var RTL = window.HIG_RTL_FLIP || new Set();

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  var maskSeq = 0;
  function icon(name, opts) {
    opts = opts || {};
    var shapes = ICONS[name];
    if (!shapes) return '';
    var size = opts.size || 20;
    var sw = opts.strokeWidth || 1.8;
    var knock = shapes.filter(function (s) { return s[1].knock; });
    var mid = knock.length ? 'fc-icon-mask-' + (++maskSeq) : null;
    var attrs = function (a) {
      return Object.keys(a).filter(function (k) { return ['fill', 'knock', 'sw'].indexOf(k) < 0; })
        .map(function (k) { return k + '="' + esc(a[k]) + '"'; }).join(' ');
    };
    var body = '';
    if (mid) {
      body += '<mask id="' + mid + '"><rect x="0" y="0" width="24" height="24" fill="#fff"/>' + knock.map(function (s) {
        return '<' + s[0] + ' ' + attrs(s[1]) + ' fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
      }).join('') + '</mask>';
    }
    shapes.forEach(function (s) {
      var a = s[1];
      if (a.knock) return;
      if (a.fill) body += '<' + s[0] + ' ' + attrs(a) + ' fill="currentColor" stroke="none"' + (mid ? ' mask="url(#' + mid + ')"' : '') + '/>';
      else body += '<' + s[0] + ' ' + attrs(a) + ' fill="none" stroke="currentColor" stroke-width="' + (a.sw ? sw * a.sw : sw) + '" stroke-linecap="round" stroke-linejoin="round"/>';
    });
    var label = opts.title ? ' role="img" aria-label="' + esc(opts.title) + '"' : ' aria-hidden="true"';
    return '<svg class="hig-icon' + (opts.className ? ' ' + opts.className : '') + '" viewBox="0 0 24 24" width="' + size + '" height="' + size + '"' + label +
      (RTL.has(name) ? ' data-rtl-flip=""' : '') + ' focusable="false">' + body + '</svg>';
  }
  /* Replace <i data-icon="name" data-size="20"></i> placeholders written in static markup. */
  function hydrateIcons(root) {
    (root || document).querySelectorAll('i[data-icon]').forEach(function (el) {
      var t = document.createElement('span');
      t.innerHTML = icon(el.getAttribute('data-icon'), { size: +el.getAttribute('data-size') || 20, title: el.getAttribute('data-title') || undefined });
      var svg = t.firstChild;
      if (svg) el.replaceWith(svg); else el.remove();
    });
  }

  /* ---------- Navigation ---------- */
  var NAV = [
    { title: 'Results', items: [
      { key: 'home', href: 'index.html', label: 'Overview', icon: 'house' },
      { key: 'sites', href: 'sites.html', label: 'Sites', icon: 'location', badge: '12' },
      { key: 'compare', href: 'compare.html', label: 'Compare', icon: 'chart.bar' },
      { key: 'outlook', href: 'outlook.html', label: 'Outlook', icon: 'calendar' },
      { key: 'explore', href: 'explore.html', label: 'Explore Data', icon: 'map' }
    ] },
    { title: 'Approach', items: [
      { key: 'method', href: 'method.html', label: 'Method', icon: 'list.bullet' },
      { key: 'standards', href: 'standards.html', label: 'Standards', icon: 'books' }
    ] },
    { title: 'Project', items: [
      { key: 'assistant', href: 'assistant.html', label: 'Assistant', icon: 'bubble' },
      { key: 'about', href: 'about.html', label: 'About', icon: 'info.circle' },
      { key: 'privacy', href: 'privacy.html', label: 'Privacy', icon: 'lock' }
    ] }
  ];
  var TABS = [
    { key: 'home', href: 'index.html', label: 'Overview', icon: 'house' },
    { key: 'sites', href: 'sites.html', label: 'Sites', icon: 'location' },
    { key: 'compare', href: 'compare.html', label: 'Compare', icon: 'chart.bar' },
    { key: 'method', href: 'method.html', label: 'Method', icon: 'list.bullet' },
    { key: 'more', href: 'more.html', label: 'More', icon: 'ellipsis' }
  ];
  var MORE_KEYS = ['outlook', 'explore', 'standards', 'assistant', 'about', 'privacy'];

  function renderNav() {
    var page = document.body.getAttribute('data-page') || '';
    var tabKey = TABS.some(function (t) { return t.key === page; }) ? page : (MORE_KEYS.indexOf(page) >= 0 ? 'more' : page);

    var side = document.createElement('nav');
    side.className = 'nav-sidebar hig-sidebar hig-sidebar--ios hig-sidebar--floating hig-glass hig-glass--regular';
    side.setAttribute('aria-label', 'Site');
    var html = '<div class="hig-sidebar__top"><a class="nav-brand" href="index.html">' +
      '<span class="nav-brand__mark">' + icon('bolt', { size: 22, strokeWidth: 2 }) + '</span>' +
      '<span class="nav-brand__text"><span class="nav-brand__title">EV Site Readiness</span>' +
      '<span class="nav-brand__sub">Future City Fellowship</span></span></a></div>';
    NAV.forEach(function (sec, si) {
      html += '<div class="hig-sidebar__section" role="group" aria-labelledby="nav-sec-' + si + '">' +
        '<div class="hig-sidebar__header" id="nav-sec-' + si + '"><span class="hig-sidebar__header-title">' + esc(sec.title) + '</span></div>' +
        '<ul class="hig-sidebar__list" role="list">';
      sec.items.forEach(function (it) {
        var sel = it.key === page;
        html += '<li class="hig-sidebar__li"><a class="hig-sidebar__row hig-focus hig-pressable' + (sel ? ' is-selected' : '') + '" href="' + it.href + '"' +
          (sel ? ' aria-current="page"' : '') + '><span class="hig-sidebar__icon" aria-hidden="true">' + icon(it.icon, { size: '1.15em', strokeWidth: 1.6 }) + '</span>' +
          '<span class="hig-sidebar__text"><span class="hig-sidebar__label">' + esc(it.label) + '</span></span>' +
          (it.badge ? '<span class="hig-sidebar__badge">' + esc(it.badge) + '</span>' : '') + '</a></li>';
      });
      html += '</ul></div>';
    });
    html += '<p class="nav-sidebar__foot">Planning-support prototype. Not engineering advice.</p>';
    side.innerHTML = html;

    var tab = document.createElement('nav');
    tab.className = 'nav-tabbar hig-tab-bar hig-tab-bar--ios';
    tab.setAttribute('aria-label', 'Site');
    var th = '<div class="hig-tab-bar__list hig-tab-bar__list--fill"><div class="hig-tab-bar__tabs hig-glass hig-glass--small hig-shape--capsule">';
    TABS.forEach(function (t) {
      var sel = t.key === tabKey;
      th += '<a class="hig-tab-bar__tab hig-focus' + (sel ? ' is-selected' : '') + '" href="' + t.href + '"' + (sel ? ' aria-current="page"' : '') + '>' +
        (sel ? '<span class="hig-tab-bar__selection" aria-hidden="true"></span>' : '') +
        '<span class="hig-tab-bar__icon" aria-hidden="true">' + icon(t.icon, { size: '1.15em', strokeWidth: 2.1 }) + '</span>' +
        '<span class="hig-tab-bar__label">' + esc(t.label) + '</span></a>';
    });
    th += '</div></div>';
    tab.innerHTML = th;

    var mount = document.getElementById('nav') || document.body;
    mount.appendChild(side);
    mount.appendChild(tab);
  }

  /* ---------- Data ---------- */
  var dataPromise = null;
  function data() {
    if (!dataPromise) {
      dataPromise = fetch('data/sites.json', { cache: 'no-cache' }).then(function (r) {
        if (!r.ok) throw new Error('The site data could not be loaded (HTTP ' + r.status + ').');
        return r.json();
      });
    }
    return dataPromise;
  }
  var TIERS = {
    'tier1': { short: 'Tier 1', label: 'Tier 1: advance to site screening' },
    'high-review': { short: 'High review', label: 'High-review candidate' },
    'tier2': { short: 'Tier 2', label: 'Tier 2: promising, refine data' },
    'tier3': { short: 'Tier 3', label: 'Tier 3: lower priority, monitor' },
    'special': { short: 'Special use', label: 'Special use: do not advance' }
  };
  function tier(key, opts) {
    opts = opts || {};
    var t = TIERS[key] || { short: key, label: key };
    return '<span class="tier tier--' + esc(key) + (opts.pill ? ' tier--pill' : '') + '"><span class="tier__mark" aria-hidden="true"></span>' +
      esc(opts.long ? t.label : t.short) + '</span>';
  }
  var TYPES = { office: 'Government office', library: 'Library', garage: 'Commuter garage', public_safety: 'Public safety training' };
  function siteType(t) { return TYPES[t] || t; }
  function fmtUSD(n) { return '$' + Math.round(n).toLocaleString('en-US'); }
  function fmtUSDk(n) { return n >= 1e6 ? '$' + (n / 1e6).toFixed(2) + 'M' : '$' + Math.round(n / 1e3) + 'K'; }

  /* ---------- Segmented control: enhance markup written as HIG SegmentedControl (iOS) ---------- */
  /* <div class="hig-segmented hig-segmented--ios hig-segmented--small" role="radiogroup" aria-label="...">
       <button class="hig-segmented__segment hig-focus" role="radio" data-value="a"><span class="hig-segmented__label" data-label="A">A</span></button> ... */
  function segmented(root, onChange) {
    var segs = Array.prototype.slice.call(root.querySelectorAll('.hig-segmented__segment'));
    if (!root.querySelector('.hig-segmented__knob')) {
      var k = document.createElement('span');
      k.className = 'hig-segmented__knob'; k.setAttribute('aria-hidden', 'true');
      k.innerHTML = '<span class="hig-segmented__lens hig-glass hig-glass--clear"></span>';
      root.insertBefore(k, root.firstChild);
    }
    root.style.setProperty('--hig-seg-n', segs.length);
    function set(i, focus, silent) {
      segs.forEach(function (s, j) {
        var on = i === j;
        s.classList.toggle('hig-segmented__segment--selected', on);
        s.setAttribute('aria-checked', on ? 'true' : 'false');
        s.tabIndex = on ? 0 : -1;
      });
      root.style.setProperty('--hig-seg-i', i);
      if (focus) segs[i].focus();
      if (!silent && onChange) onChange(segs[i].getAttribute('data-value'), i);
    }
    var start = segs.findIndex(function (s) { return s.getAttribute('aria-checked') === 'true'; });
    set(start < 0 ? 0 : start, false, true);
    segs.forEach(function (s, i) {
      s.type = 'button';
      s.addEventListener('click', function () { set(i, false); });
      s.addEventListener('keydown', function (e) {
        var rtl = getComputedStyle(root).direction === 'rtl';
        var cur = segs.indexOf(document.activeElement); if (cur < 0) return;
        var n = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') n = (cur + ((e.key === 'ArrowRight' && rtl) ? -1 : 1) + segs.length) % segs.length;
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') n = (cur + ((e.key === 'ArrowLeft' && rtl) ? 1 : -1) + segs.length) % segs.length;
        else if (e.key === 'Home') n = 0; else if (e.key === 'End') n = segs.length - 1;
        if (n === null) return;
        e.preventDefault(); set(n, true);
      });
    });
    return { set: function (v) { var i = segs.findIndex(function (s) { return s.getAttribute('data-value') === v; }); if (i >= 0) set(i, false, true); } };
  }

  /* ---------- Footer ---------- */
  function renderFooter() {
    var main = document.querySelector('.main');
    if (!main || document.querySelector('.site-foot')) return;
    var f = document.createElement('footer');
    f.className = 'site-foot footnote';
    f.innerHTML = '<p>Planning-support prototype. Not engineering advice, a permit, or a utility interconnection decision. No site shown here is approved. ' +
      'Electrical capacity is an unverified placeholder at all twelve sites.</p>' +
      '<p class="num">Canonical contract v1.0.0 (generated 2026-07-19) · site inputs 2026-06-24 · emissions factor EPA eGRID2023 Rev 2, SRVC, 596.3 lb CO2e/MWh (accessed 2026-07-19; refreshed annually)</p>' +
      '<p>Future City Fellowship Phase 2 prototype · Built by Andy Yaro, George Mason University · <a href="about.html">About this site</a> · <a href="privacy.html">Privacy</a> · <a href="devices.html">Device Preview</a></p>';
    main.appendChild(f);
  }

  window.FC = { icon: icon, hydrateIcons: hydrateIcons, esc: esc, data: data, tier: tier, TIERS: TIERS, siteType: siteType,
    fmtUSD: fmtUSD, fmtUSDk: fmtUSDk, segmented: segmented, NAV: NAV };

  function boot() {
    if (document.body.getAttribute('data-nav') !== 'none') { renderNav(); renderFooter(); }
    hydrateIcons(document);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
