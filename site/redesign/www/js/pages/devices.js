/* Device Preview: renders each page of the site in same-origin iframes at real device viewport sizes,
   scaled down to fit. The iframe's own width drives the site's media queries, so every frame shows the
   layout that device actually gets (tab bar below 1024px, floating sidebar from 1024px). */
(function () {
  'use strict';
  var PAGES = [
    ['index.html', 'Overview'], ['sites.html', 'Sites'], ['sites.html#FFX004', 'Sites: FFX004 Detail'], ['compare.html', 'Compare'],
    ['outlook.html', 'Outlook'], ['explore.html', 'Explore Data'], ['method.html', 'Method'], ['standards.html', 'Standards'],
    ['assistant.html', 'Assistant'], ['about.html', 'About'], ['privacy.html', 'Privacy'], ['more.html', 'More'], ['404.html', 'Not Found']
  ];
  var DEVICES = [
    { group: 'phone', name: 'iPhone SE', w: 375, h: 667 },
    { group: 'phone', name: 'iPhone 16', w: 393, h: 852 },
    { group: 'phone', name: 'iPhone 16 Pro Max', w: 440, h: 956 },
    { group: 'phone', name: 'Small Android', w: 360, h: 780 },
    { group: 'tablet', name: 'iPad mini', w: 744, h: 1133 },
    { group: 'tablet', name: 'iPad Air 11-inch', w: 820, h: 1180 },
    { group: 'tablet', name: 'iPad Pro 13-inch', w: 1032, h: 1376 },
    { group: 'computer', name: 'Laptop', w: 1280, h: 800 },
    { group: 'computer', name: 'MacBook Air 13-inch', w: 1470, h: 956 },
    { group: 'computer', name: 'Desktop', w: 1920, h: 1080 }
  ];
  var GROUPS = { phone: 'Phones', tablet: 'Tablets', computer: 'Computers' };
  var TARGET_H = { phone: 560, tablet: 560, computer: 460 };

  var stage = document.getElementById('dv-stage');
  var select = document.getElementById('dv-page');
  var rotateBtn = document.getElementById('dv-rotate');
  var status = document.getElementById('dv-status');
  var state = { page: 'index.html', group: 'all', rotated: false };

  try {
    var saved = JSON.parse(sessionStorage.getItem('fc-devices') || 'null');
    if (saved && typeof saved === 'object') { state.page = saved.page || state.page; state.group = saved.group || state.group; state.rotated = !!saved.rotated; }
  } catch (e) { /* storage unavailable: use defaults */ }
  var fromHash = decodeURIComponent((location.hash || '').slice(1));
  if (fromHash && PAGES.some(function (p) { return p[0] === fromHash; })) state.page = fromHash;

  PAGES.forEach(function (p) {
    var o = document.createElement('option');
    o.value = p[0]; o.textContent = p[1];
    select.appendChild(o);
  });
  select.value = state.page;

  function save() {
    try { sessionStorage.setItem('fc-devices', JSON.stringify(state)); } catch (e) { /* ignore */ }
    history.replaceState(null, '', '#' + encodeURIComponent(state.page));
  }

  function layoutName(w) { return w >= 1024 ? 'Floating sidebar layout' : 'Tab bar layout'; }

  function dims(d) {
    var rot = state.rotated && d.group !== 'computer';
    return { w: rot ? d.h : d.w, h: rot ? d.w : d.h };
  }

  function fit() {
    var avail = stage.clientWidth;
    stage.querySelectorAll('.dv-device').forEach(function (fig) {
      var w = +fig.getAttribute('data-w'), h = +fig.getAttribute('data-h'), g = fig.getAttribute('data-group');
      var bezel = g === 'phone' ? 14 : g === 'tablet' ? 20 : 16;
      var s = Math.min(TARGET_H[g] / h, (avail - bezel) / w, 1);
      var screen = fig.querySelector('.dv-screen');
      var frame = fig.querySelector('iframe');
      screen.style.width = Math.floor(w * s) + 'px';
      screen.style.height = Math.floor(h * s) + 'px';
      fig.style.width = (Math.floor(w * s) + bezel) + 'px';
      frame.style.transform = 'scale(' + s + ')';
      fig.querySelector('.dv-caption__scale').textContent = Math.round(s * 100) + '%';
    });
  }

  function render() {
    stage.textContent = '';
    var label = (PAGES.find(function (p) { return p[0] === state.page; }) || [0, state.page])[1];
    var shown = 0;
    Object.keys(GROUPS).forEach(function (g) {
      if (state.group !== 'all' && state.group !== g) return;
      var sec = document.createElement('section');
      sec.className = 'dv-group';
      sec.setAttribute('aria-labelledby', 'dv-g-' + g);
      sec.innerHTML = '<h2 class="dv-group__title" id="dv-g-' + g + '">' + GROUPS[g] + '</h2><div class="dv-row"></div>';
      var row = sec.querySelector('.dv-row');
      DEVICES.filter(function (d) { return d.group === g; }).forEach(function (d) {
        var z = dims(d);
        var fig = document.createElement('figure');
        fig.className = 'dv-device dv-device--' + g;
        fig.setAttribute('data-w', z.w); fig.setAttribute('data-h', z.h); fig.setAttribute('data-group', g);
        fig.innerHTML =
          '<div class="dv-bezel"><div class="dv-screen"><iframe loading="lazy" width="' + z.w + '" height="' + z.h + '" ' +
          'style="width:' + z.w + 'px;height:' + z.h + 'px" src="' + FC.esc(state.page) + '" ' +
          'title="' + FC.esc(label + ' on ' + d.name + ', ' + z.w + ' by ' + z.h) + '"></iframe></div></div>' +
          '<figcaption class="dv-caption"><span class="dv-caption__name">' + FC.esc(d.name) + '</span>' +
          '<span class="dv-caption__size">' + z.w + ' × ' + z.h + ' · <span class="dv-caption__scale"></span></span>' +
          '<a href="' + FC.esc(state.page) + '" target="_blank" rel="noopener">Open Full Size</a>' +
          '<span class="dv-caption__layout">' + layoutName(z.w) + '</span></figcaption>';
        row.appendChild(fig);
        shown++;
      });
      stage.appendChild(sec);
    });
    status.textContent = 'Showing ' + label + ' on ' + shown + (shown === 1 ? ' device' : ' devices') + (state.rotated ? ', phones and tablets rotated' : '') + '.';
    fit();
  }

  select.addEventListener('change', function () { state.page = select.value; save(); render(); });
  rotateBtn.setAttribute('aria-pressed', state.rotated ? 'true' : 'false');
  rotateBtn.addEventListener('click', function () {
    state.rotated = !state.rotated;
    rotateBtn.setAttribute('aria-pressed', state.rotated ? 'true' : 'false');
    save(); render();
  });
  document.getElementById('dv-reload').addEventListener('click', function () {
    stage.querySelectorAll('iframe').forEach(function (f) { f.src = f.src; });
  });
  var seg = FC.segmented(document.getElementById('dv-group'), function (v) { state.group = v; save(); render(); });
  seg.set(state.group);

  if (window.ResizeObserver) new ResizeObserver(fit).observe(stage);
  else window.addEventListener('resize', fit);
  render();
})();
