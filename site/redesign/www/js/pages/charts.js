/* Small SVG chart helper shared by compare.html and outlook.html.
   Modeled on the HIG Native Chart component (components/src/Chart.jsx): the same figure / header / area / legend
   anatomy and class names (so hig.css styles it), Caption 2 axis labels in label-secondary, separator grid lines,
   bars at most 24px thick with a 4px rounded data end and a 2px gap between grouped bars, 2px lines, 8px symbols
   with a surface ring, a callout on hover or keyboard selection, an overview for assistive technology and a data
   table for every value. Colors are token names resolved by CSS (fill: var(--token)); never color alone: every
   series has a shape, a texture or a word as well.

   FCChart.create(mountEl, spec) -> { set(spec), destroy() }
   spec = {
     kind: 'hbar' | 'columns' | 'line',
     id, title, subtitle, summary,                  // summary joins the accessible overview
     categories: [{ label, lead?, mark?: {shape, color} }],
     series: [{ name, color: 'accent', shape?: 'circle', texture?: bool, dash?: bool }],
     values: [[...per category] per series],        // null = no value
     colorAt?(si, ci) -> token,                     // per-mark color (tiers)
     format(v, si, ctx) -> string,                  // ctx: 'mark' | 'callout' | 'table'
     formatAxis?(v) -> string, unit?, catTitle, valueTitle,
     cap?: number,                                  // hbar: values above it are drawn broken at the axis end
     refLines?: [{ value, label }],                 // line: reference lines
     legend?: [{ label, color, shape?, texture?, line?, dash? }],
     tableExtra?: [{ title, value(ci) -> string }], height?, barMax?, valueLabels?
   } */
(function () {
  'use strict';

  var GAP = 2;          // narrow strip of surface between grouped bars (HIG)
  var RADIUS = 4;       // rounded data end, square at the baseline
  var LINE_W = 2;
  var SYMBOL = 8;
  var RING = 2;
  var LABEL_GAP = 6;
  var TICK_PX = 11;     // iOS Caption 2
  var seq = 0;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function f2(n) { return (Math.round(n * 100) / 100).toString(); }

  var ctx2d = null;
  function textWidth(str, px, weight, family) {
    try {
      if (!ctx2d) ctx2d = document.createElement('canvas').getContext('2d');
      ctx2d.font = (weight || 400) + ' ' + px + 'px ' + (family || 'sans-serif');
      return ctx2d.measureText(String(str)).width;
    } catch (e) { return String(str).length * px * 0.6; }
  }
  function ellipsize(str, px, weight, family, max) {
    str = String(str);
    if (textWidth(str, px, weight, family) <= max) return str;
    var lo = 0, hi = str.length;
    while (lo < hi) {
      var mid = Math.ceil((lo + hi) / 2);
      if (textWidth(str.slice(0, mid).trim() + '…', px, weight, family) <= max) lo = mid; else hi = mid - 1;
    }
    return str.slice(0, lo).trim() + '…';
  }

  /* Familiar tick sequences only: steps of 1, 2 or 5 x 10^n (HIG Charts). */
  function niceStep(range, count) {
    var raw = range / Math.max(1, count);
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var n = raw / mag;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * mag;
  }
  function tidy(v) { return Number(v.toFixed(10)); }
  function ticksFor(lo, hi, count) {
    if (!(hi > lo)) hi = lo + (Math.abs(lo) || 1);
    var step = niceStep(hi - lo, count);
    var a = Math.floor(tidy(lo / step)) * step;
    var b = Math.ceil(tidy(hi / step)) * step;
    var ticks = [];
    for (var v = a; v <= b + step * 1e-6; v += step) ticks.push(tidy(v));
    return { lo: tidy(a), hi: tidy(b), ticks: ticks };
  }

  /* Series symbols (Swift Charts order) and the site's tier marks. */
  function poly(pts) { return 'M' + pts.map(function (p) { return f2(p[0]) + ' ' + f2(p[1]); }).join('L') + 'Z'; }
  function regular(n, r, x, y) {
    var out = [];
    for (var i = 0; i < n; i++) { var a = (i * 2 * Math.PI) / n; out.push([x + r * Math.sin(a), y - r * Math.cos(a)]); }
    return out;
  }
  function shapePath(shape, x, y, s) {
    var r = s / 2;
    switch (shape) {
      case 'square': return poly([[x - s * 0.44, y - s * 0.44], [x + s * 0.44, y - s * 0.44], [x + s * 0.44, y + s * 0.44], [x - s * 0.44, y + s * 0.44]]);
      case 'triangle': return poly(regular(3, s * 0.64, x, y + s * 0.1));
      case 'diamond': return poly(regular(4, s * 0.64, x, y));
      case 'dash': return 'M' + f2(x - r) + ' ' + f2(y - 2) + 'h' + s + 'v4h' + (-s) + 'Z';
      default: return 'M' + f2(x - r) + ' ' + f2(y) + 'a' + r + ' ' + r + ' 0 1 0 ' + s + ' 0a' + r + ' ' + r + ' 0 1 0 ' + (-s) + ' 0Z';
    }
  }
  function symbol(shape, x, y, s, color, ring) {
    return '<path d="' + shapePath(shape, x, y, s) + '"' + (ring ? ' class="hig-chart__ringed" stroke-width="' + RING * 2 + '" stroke-linejoin="round"' : '') +
      ' style="fill:var(--' + color + ')"/>';
  }

  /* Bars: square at the baseline, 4px rounded data end. */
  function hbarPath(x, y, w, h, r) {
    if (w <= 0.01) return '';
    var rr = Math.max(0, Math.min(r, h / 2, w));
    return 'M' + f2(x) + ' ' + f2(y) + 'H' + f2(x + w - rr) + 'A' + rr + ' ' + rr + ' 0 0 1 ' + f2(x + w) + ' ' + f2(y + rr) +
      'V' + f2(y + h - rr) + 'A' + rr + ' ' + rr + ' 0 0 1 ' + f2(x + w - rr) + ' ' + f2(y + h) + 'H' + f2(x) + 'Z';
  }
  function vbarPath(x, w, yBase, yEnd, r) {
    var h = yBase - yEnd;
    if (h <= 0.01 || w <= 0) return '';
    var rr = Math.max(0, Math.min(r, w / 2, h));
    return 'M' + f2(x) + ' ' + f2(yBase) + 'V' + f2(yEnd + rr) + 'A' + rr + ' ' + rr + ' 0 0 1 ' + f2(x + rr) + ' ' + f2(yEnd) +
      'H' + f2(x + w - rr) + 'A' + rr + ' ' + rr + ' 0 0 1 ' + f2(x + w) + ' ' + f2(yEnd + rr) + 'V' + f2(yBase) + 'Z';
  }
  function crisp(v) { return Math.round(v) + 0.5; }

  function mark(d, color, texture, patId) {
    if (!d) return '';
    return '<path d="' + d + '" style="fill:var(--' + color + ')"/>' + (texture ? '<path d="' + d + '" fill="url(#' + patId + ')"/>' : '');
  }

  /* Legend key: a bar swatch (optionally hatched), or a line with its symbol. */
  function swatch(item, uid) {
    if (item.line) {
      return '<svg class="hig-chart__swatch" width="22" height="10" viewBox="0 0 22 10" aria-hidden="true">' +
        '<path d="M1 5H21" stroke-width="' + LINE_W + '" stroke-linecap="round"' + (item.dash ? ' stroke-dasharray="4 3"' : '') +
        ' style="stroke:var(--' + item.color + ')" fill="none"/>' + (item.shape ? symbol(item.shape, 11, 5, SYMBOL, item.color, true) : '') + '</svg>';
    }
    if (item.shape && !item.bar) {
      return '<svg class="hig-chart__swatch" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">' + symbol(item.shape, 5, 5, item.shape === 'dash' ? 10 : 9, item.color) + '</svg>';
    }
    var pid = uid + '-lg';
    return '<svg class="hig-chart__swatch" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">' +
      (item.texture ? '<defs>' + hatch(pid) + '</defs>' : '') +
      '<rect width="12" height="12" rx="3" style="fill:var(--' + item.color + ')"/>' +
      (item.texture ? '<rect width="12" height="12" rx="3" fill="url(#' + pid + ')"/>' : '') + '</svg>';
  }
  function hatch(id) {
    return '<pattern id="' + id + '" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
      '<rect width="2" height="5" class="fc-chart__hatch"/></pattern>';
  }

  function Chart(mount, spec) {
    this.uid = 'fc-chart-' + (++seq);
    this.mount = mount;
    this.sel = -1;
    this.width = 0;
    this.build();
    this.set(spec);
    var self = this;
    if (typeof ResizeObserver !== 'undefined') {
      this.ro = new ResizeObserver(function (entries) {
        var w = Math.round(entries[0].contentRect.width);
        if (w !== self.width) { self.width = w; self.render(); }
      });
      this.ro.observe(this.area);
    } else {
      this.onResize = function () { self.width = self.area.clientWidth; self.render(); };
      window.addEventListener('resize', this.onResize);
    }
  }

  Chart.prototype.build = function () {
    var u = this.uid;
    var fig = document.createElement('figure');
    fig.className = 'hig-chart hig-chart--ios fc-chart';
    fig.setAttribute('aria-labelledby', u + '-title');
    fig.innerHTML =
      '<figcaption class="hig-chart__header fc-chart__header"><div id="' + u + '-title" class="hig-chart__title t-ios-headline"></div>' +
      '<div class="hig-chart__subtitle t-ios-footnote"></div></figcaption>' +
      '<div class="hig-chart__area hig-focus fc-chart__area" tabindex="0" role="group" aria-roledescription="chart">' +
      '<div class="fc-chart__plot"></div><div class="hig-chart__callout" aria-hidden="true" hidden></div>' +
      '<div class="hig-visually-hidden" aria-live="polite"></div></div>' +
      '<div class="hig-chart__legend t-ios-caption-1 fc-chart__legend" aria-hidden="true"></div>' +
      '<div class="fc-chart__foot"><button type="button" class="hig-button hig-button--ios hig-button--small hig-button--borderless fc-chart__toggle" aria-expanded="false" aria-controls="' + u + '-data">' +
      '<span class="hig-button__label">Show Data</span></button></div>' +
      '<div id="' + u + '-data" class="fc-chart__data hig-visually-hidden"></div>';
    this.mount.innerHTML = '';
    this.mount.appendChild(fig);
    this.fig = fig;
    this.titleEl = fig.querySelector('.hig-chart__title');
    this.subEl = fig.querySelector('.hig-chart__subtitle');
    this.area = fig.querySelector('.fc-chart__area');
    this.plot = fig.querySelector('.fc-chart__plot');
    this.callout = fig.querySelector('.hig-chart__callout');
    this.live = fig.querySelector('[aria-live]');
    this.legendEl = fig.querySelector('.fc-chart__legend');
    this.dataEl = fig.querySelector('.fc-chart__data');
    this.toggle = fig.querySelector('.fc-chart__toggle');
    var self = this;

    this.toggle.addEventListener('click', function () {
      var open = self.toggle.getAttribute('aria-expanded') !== 'true';
      self.toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      self.toggle.querySelector('.hig-button__label').textContent = open ? 'Hide Data' : 'Show Data';
      self.dataEl.classList.toggle('hig-visually-hidden', !open);
    });

    var dragging = false;
    this.area.addEventListener('pointermove', function (e) { if (e.pointerType === 'mouse' || dragging) self.select(self.indexAt(e), false); });
    this.area.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'mouse') dragging = true; self.select(self.indexAt(e), false); });
    this.area.addEventListener('pointerup', function () { dragging = false; });
    this.area.addEventListener('pointercancel', function () { dragging = false; });
    this.area.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') self.select(-1, false); });
    this.area.addEventListener('blur', function () { self.select(-1, false); });
    this.area.addEventListener('keydown', function (e) {
      var n = self.spec.categories.length, i = null, s = self.sel;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') i = s < 0 ? 0 : Math.min(n - 1, s + 1);
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') i = s < 0 ? n - 1 : Math.max(0, s - 1);
      else if (e.key === 'Home') i = 0;
      else if (e.key === 'End') i = n - 1;
      else if (e.key === 'Escape' && s >= 0) i = -1;
      if (i === null) return;
      e.preventDefault();
      self.select(i, true);
    });
  };

  Chart.prototype.set = function (spec) {
    this.spec = spec;
    this.sel = -1;
    this.titleEl.textContent = spec.title || '';
    this.subEl.textContent = spec.subtitle || '';
    this.subEl.hidden = !spec.subtitle;
    var axisHint = spec.kind === 'hbar' ? 'Use the Up and Down arrow keys to move between ' : 'Use the Left and Right arrow keys to move between ';
    this.area.setAttribute('aria-label', (spec.title || 'Chart') + '. ' + axisHint + (spec.catNoun || 'values') + '.');
    this.renderLegend();
    this.renderTable();
    this.width = this.area.clientWidth;
    this.render();
  };

  Chart.prototype.fmt = function (v, si, ctx) {
    if (v === null || v === undefined) return 'no value';
    return this.spec.format ? this.spec.format(v, si, ctx) : String(v);
  };

  Chart.prototype.overview = function () {
    var s = this.spec, cats = s.categories;
    var kinds = { hbar: 'Horizontal bar chart', columns: 'Bar chart', line: 'Line chart' };
    var parts = [(kinds[s.kind] || 'Chart') + (s.series.length > 1 ? ' of ' + s.series.length + ' series: ' + s.series.map(function (x) { return x.name; }).join(', ') : '') + '.'];
    if (cats.length) parts.push((s.catTitle || 'Categories') + ': ' + cats[0].label + ' to ' + cats[cats.length - 1].label + '.');
    if (this.domain) parts.push((s.valueTitle || 'Value') + ' axis: ' + this.domain[0] + ' to ' + this.domain[1] + (s.unit ? ' ' + s.unit : '') + '.');
    if (s.summary) parts.push(s.summary);
    parts.push('Every value is in the data table that follows the chart.');
    return parts.join(' ');
  };

  Chart.prototype.renderLegend = function () {
    var s = this.spec, uid = this.uid;
    var items = s.legend || s.series.map(function (x) {
      return { label: x.name, color: x.color, texture: x.texture, shape: s.kind === 'line' ? x.shape : null, line: s.kind === 'line', dash: x.dash };
    });
    this.legendEl.innerHTML = items.map(function (it, i) {
      return '<span class="hig-chart__legend-item">' + swatch(it, uid + '-' + i) + '<span>' + esc(it.label) + '</span></span>';
    }).join('');
    this.legendEl.hidden = !items.length;
  };

  Chart.prototype.renderTable = function () {
    var s = this.spec, self = this;
    var extra = s.tableExtra || [];
    var h = '<div class="hig-table hig-table--ios fc-chart__table" tabindex="0" role="region" aria-label="' + esc((s.title || 'Chart') + ' data') + '">' +
      '<table class="hig-table__grid"><caption class="hig-visually-hidden">' + esc((s.title || 'Chart') + ' data') + '</caption><thead><tr class="hig-table__head-row">' +
      '<th scope="col" class="hig-table__heading hig-table__cell--leading"><span class="hig-table__heading-label">' + esc(s.catTitle || 'Category') + '</span></th>';
    extra.forEach(function (c) { h += '<th scope="col" class="hig-table__heading hig-table__cell--leading"><span class="hig-table__heading-label">' + esc(c.title) + '</span></th>'; });
    s.series.forEach(function (x) { h += '<th scope="col" class="hig-table__heading hig-table__cell--trailing"><span class="hig-table__heading-label">' + esc(x.name) + '</span></th>'; });
    h += '</tr></thead><tbody>';
    s.categories.forEach(function (c, ci) {
      h += '<tr class="hig-table__row"><th scope="row" class="hig-table__cell hig-table__cell--leading">' + esc(c.tableLabel || c.label) + '</th>';
      extra.forEach(function (x) { h += '<td class="hig-table__cell hig-table__cell--leading">' + esc(x.value(ci)) + '</td>'; });
      s.series.forEach(function (x, si) {
        var v = s.values[si][ci];
        h += '<td class="hig-table__cell hig-table__cell--trailing">' + (v === null || v === undefined ? '<span aria-label="no value">-</span>' : esc(self.fmt(v, si, 'table'))) + '</td>';
      });
      h += '</tr>';
    });
    h += '</tbody></table></div>';
    this.dataEl.innerHTML = h;
  };

  Chart.prototype.indexAt = function (e) {
    var L = this.layout;
    if (!L) return -1;
    var r = this.area.getBoundingClientRect();
    var p = L.axis === 'y' ? e.clientY - r.top : e.clientX - r.left;
    for (var i = 0; i < L.bands.length; i++) if (p >= L.bands[i][0] && p < L.bands[i][1]) return i;
    return -1;
  };

  Chart.prototype.describe = function (ci) {
    var s = this.spec, self = this;
    var vals = s.series.map(function (x, si) {
      var v = s.values[si][ci];
      return (s.series.length > 1 ? x.name + ' ' : '') + self.fmt(v, si, 'callout');
    }).filter(Boolean).join(', ');
    return (s.categories[ci].tableLabel || s.categories[ci].label) + ': ' + vals;
  };

  Chart.prototype.select = function (i, viaKeys) {
    if (i === this.sel) return;
    this.sel = i;
    this.render();
    if (viaKeys) this.live.textContent = i < 0 ? '' : this.describe(i);
  };

  Chart.prototype.render = function () {
    var W = this.width || this.area.clientWidth;
    if (!W || !this.spec) return;
    this.family = getComputedStyle(this.area).fontFamily;
    var out = this.spec.kind === 'hbar' ? this.hbar(W) : this.vertical(W);
    this.layout = out;
    this.plot.innerHTML = '<svg class="hig-chart__svg" width="' + W + '" height="' + out.height + '" viewBox="0 0 ' + W + ' ' + out.height +
      '" role="img" aria-label="' + esc(this.overview()) + '" focusable="false"><defs>' + hatch(this.uid + '-hatch') + '</defs>' + out.svg + '</svg>';
    this.area.style.height = out.height + 'px';
    this.placeCallout(W, out);
  };

  /* ---------- Horizontal bars: one row per category, grouped series inside it ---------- */
  Chart.prototype.hbar = function (W) {
    var s = this.spec, fam = this.family, self = this;
    var n = s.categories.length, k = s.series.length;
    var wide = W >= 560;
    var barT = k === 1 ? 18 : 12;
    var groupH = k * barT + (k - 1) * GAP;
    var markW = s.categories.some(function (c) { return c.mark; }) ? 16 : 0;
    var leadW = s.categories.some(function (c) { return c.lead != null; }) ? Math.ceil(Math.max.apply(null, s.categories.map(function (c) { return textWidth(c.lead || '', 13, 600, fam); }))) + 8 : 0;
    var max = 0, valW = 0;
    s.values.forEach(function (row, si) {
      row.forEach(function (v) {
        if (v == null) return;
        max = Math.max(max, v);
        valW = Math.max(valW, textWidth(self.fmt(v, si, 'mark'), 12, 600, fam));
      });
    });
    var capped = s.cap != null && max > s.cap;
    var capExtra = capped ? 18 : 0;
    var labelW = 0, rowH, labelY;
    if (wide) {
      var widest = Math.max.apply(null, s.categories.map(function (c) { return textWidth(c.label, 13, 400, fam); }));
      labelW = Math.min(Math.ceil(widest) + markW + leadW + 16, Math.round(W * 0.36), 320);
      rowH = Math.max(groupH + 16, 34);
    } else {
      rowH = 20 + groupH + 14;
    }
    var plotX0 = labelW;
    var plotX1 = Math.max(plotX0 + 40, W - Math.ceil(valW) - LABEL_GAP - capExtra - 2);
    var t = ticksFor(0, capped ? s.cap : max, Math.max(2, Math.floor((plotX1 - plotX0) / 64)));
    var dmax = t.hi;
    this.domain = [this.fmtAxis(0), this.fmtAxis(dmax)];
    var xS = function (v) { return plotX0 + (Math.min(v, dmax) / dmax) * (plotX1 - plotX0); };
    var top = 2;
    var axisY = top + n * rowH;
    var height = axisY + 6 + 13 + (s.valueTitle ? 22 : 2);
    var g = '', marks = '', labels = '', bands = [], anchors = [];

    if (this.sel >= 0) g += '<rect class="fc-chart__band" x="0" y="' + (top + this.sel * rowH) + '" width="' + W + '" height="' + rowH + '" rx="8"/>';
    t.ticks.forEach(function (tv) {
      var x = crisp(xS(tv));
      g += '<line class="hig-chart__grid" x1="' + x + '" x2="' + x + '" y1="' + top + '" y2="' + axisY + '"/>';
      labels += '<text class="hig-chart__tick" x="' + f2(Math.max(plotX0 + 4, Math.min(W - 10, xS(tv)))) + '" y="' + (axisY + 6 + 6.5) + '" text-anchor="middle" dominant-baseline="central">' + esc(self.fmtAxis(tv)) + '</text>';
    });

    s.categories.forEach(function (c, ci) {
      var rowY = top + ci * rowH;
      bands.push([rowY, rowY + rowH]);
      var gy = wide ? rowY + (rowH - groupH) / 2 : rowY + 20;
      var ly = wide ? rowY + rowH / 2 : rowY + 10;
      var lx = 0;
      if (c.mark) { labels += symbol(c.mark.shape, lx + 5, ly, c.mark.shape === 'dash' ? 10 : 9, c.mark.color); lx += markW; }
      if (c.lead != null) { labels += '<text class="fc-chart__lead" x="' + lx + '" y="' + f2(ly) + '" dominant-baseline="central">' + esc(c.lead) + '</text>'; lx += leadW; }
      var room = (wide ? labelW - 12 : W) - lx;
      labels += '<text class="fc-chart__label" x="' + lx + '" y="' + f2(ly) + '" dominant-baseline="central">' + esc(ellipsize(c.label, 13, 400, fam, room)) + '</text>';
      var endMax = plotX0;
      s.series.forEach(function (ser, si) {
        var v = s.values[si][ci];
        if (v == null) return;
        var y = gy + si * (barT + GAP);
        var clipped = capped && v > dmax;
        var end = clipped ? plotX1 + capExtra : xS(v);
        var color = s.colorAt ? s.colorAt(si, ci) : ser.color;
        marks += mark(hbarPath(plotX0, y, end - plotX0, barT, RADIUS), color, ser.texture, self.uid + '-hatch');
        if (clipped) {
          // Axis break: two slanted surface-colored cuts across the bar where it leaves the scale.
          var bx = plotX1 + 4;
          marks += '<path class="fc-chart__break" d="M' + f2(bx) + ' ' + f2(y + barT + 2) + 'L' + f2(bx + 5) + ' ' + f2(y - 2) + 'M' + f2(bx + 6) + ' ' + f2(y + barT + 2) + 'L' + f2(bx + 11) + ' ' + f2(y - 2) + '"/>';
        }
        labels += '<text class="fc-chart__value' + (clipped ? ' fc-chart__value--strong' : '') + '" x="' + f2(end + LABEL_GAP) + '" y="' + f2(y + barT / 2) + '" dominant-baseline="central">' + esc(self.fmt(v, si, 'mark')) + '</text>';
        endMax = Math.max(endMax, end + LABEL_GAP + textWidth(self.fmt(v, si, 'mark'), 12, 600, fam));
      });
      anchors.push({ x: endMax, top: rowY, bottom: rowY + rowH });
    });
    if (s.valueTitle) labels += '<text class="hig-chart__axis-title" x="' + f2((plotX0 + plotX1) / 2) + '" y="' + (height - 9) + '" text-anchor="middle" dominant-baseline="central">' + esc(s.valueTitle + (s.unit ? ' (' + s.unit + ')' : '')) + '</text>';
    return { axis: 'y', bands: bands, anchors: anchors, height: height, svg: g + '<g class="hig-chart__marks">' + marks + '</g>' + labels };
  };

  Chart.prototype.fmtAxis = function (v) {
    if (this.spec.formatAxis) return this.spec.formatAxis(v);
    return Math.abs(v) >= 1000 ? new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(v) : String(v);
  };

  /* ---------- Vertical: grouped columns, or lines with symbols, along a category X axis ---------- */
  Chart.prototype.vertical = function (W) {
    var s = this.spec, fam = this.family, self = this;
    var n = s.categories.length, k = s.series.length, line = s.kind === 'line';
    var H = s.height || (W < 520 ? 240 : 300);
    var yTitleH = s.valueTitle ? 20 : 0;
    var plotY0 = yTitleH + 8;
    var plotY1 = H - 4 - 13 - 4;
    var all = [];
    s.values.forEach(function (row) { row.forEach(function (v) { if (v != null) all.push(v); }); });
    (s.refLines || []).forEach(function (r) { all.push(r.value); });
    var lo = line && !s.zero ? Math.min.apply(null, all) : 0;
    var hi = Math.max.apply(null, all);
    var plotH0 = plotY1 - plotY0;
    var count = Math.max(2, Math.round(plotH0 / 50));
    var t = ticksFor(lo, hi, count);
    // Leave headroom for value labels above columns.
    if (!line && s.valueLabels !== false && hi > t.hi * 0.9) t = ticksFor(lo, hi * 1.12, count);
    var yLo = t.lo, yHi = t.hi;
    this.domain = [this.fmtAxis(yLo), this.fmtAxis(yHi)];
    var yS = function (v) { return plotY0 + ((yHi - v) / (yHi - yLo || 1)) * (plotY1 - plotY0); };
    var yW = Math.ceil(Math.max.apply(null, t.ticks.map(function (v) { return textWidth(self.fmtAxis(v), TICK_PX, 400, fam); }))) + LABEL_GAP;
    var plotX0 = 0, plotX1 = W - yW;
    var band = (plotX1 - plotX0) / n;
    var xC = function (ci) { return plotX0 + band * (ci + 0.5); };
    var g = '', marks = '', labels = '', overlay = '', bands = [], anchors = [];

    if (this.sel >= 0) {
      if (line) g += '<line class="hig-chart__rule" x1="' + crisp(xC(this.sel)) + '" x2="' + crisp(xC(this.sel)) + '" y1="' + plotY0 + '" y2="' + plotY1 + '"/>';
      else g += '<rect class="fc-chart__band" x="' + f2(plotX0 + band * this.sel + 2) + '" y="' + (plotY0 - 4) + '" width="' + f2(band - 4) + '" height="' + (plotY1 - plotY0 + 4) + '" rx="8"/>';
    }
    t.ticks.forEach(function (tv) {
      var y = crisp(yS(tv));
      g += '<line class="hig-chart__grid" x1="' + plotX0 + '" x2="' + plotX1 + '" y1="' + y + '" y2="' + y + '"/>';
      labels += '<text class="hig-chart__tick" x="' + (plotX1 + LABEL_GAP) + '" y="' + f2(yS(tv)) + '" dominant-baseline="central">' + esc(self.fmtAxis(tv)) + '</text>';
    });
    if (s.valueTitle) labels += '<text class="hig-chart__axis-title" x="' + W + '" y="9" text-anchor="end" dominant-baseline="central">' + esc(s.valueTitle) + '</text>';
    s.categories.forEach(function (c, ci) {
      bands.push([plotX0 + band * ci, plotX0 + band * (ci + 1)]);
      labels += '<text class="hig-chart__tick" x="' + f2(xC(ci)) + '" y="' + (plotY1 + 4 + 6.5) + '" text-anchor="middle" dominant-baseline="central">' + esc(c.label) + '</text>';
    });

    if (!line) {
      var barMax = s.barMax || 24;
      var bw = Math.max(2, Math.min(barMax, (band * 0.62 - (k - 1) * GAP) / k));
      var showVals = s.valueLabels !== false;
      if (showVals) {
        s.values.forEach(function (row, si) {
          row.forEach(function (v) { if (v != null && textWidth(self.fmt(v, si, 'mark'), 11, 600, fam) > bw + GAP - 1) showVals = false; });
        });
      }
      s.categories.forEach(function (c, ci) {
        var present = [];
        s.series.forEach(function (ser, si) { if (s.values[si][ci] != null) present.push(si); });
        var total = present.length * bw + (present.length - 1) * GAP;
        var topY = plotY1;
        present.forEach(function (si, j) {
          var v = s.values[si][ci], ser = s.series[si];
          var x0 = xC(ci) - total / 2 + j * (bw + GAP);
          var ye = yS(v);
          topY = Math.min(topY, ye);
          marks += mark(vbarPath(x0, bw, yS(Math.max(yLo, 0)), ye, RADIUS), s.colorAt ? s.colorAt(si, ci) : ser.color, ser.texture, self.uid + '-hatch');
          if (showVals) labels += '<text class="fc-chart__value fc-chart__value--small" x="' + f2(x0 + bw / 2) + '" y="' + f2(ye - 8) + '" text-anchor="middle" dominant-baseline="central">' + esc(self.fmt(v, si, 'mark')) + '</text>';
        });
        anchors.push({ x: xC(ci), y: showVals ? topY - 16 : topY });
      });
    } else {
      (s.refLines || []).forEach(function (r) {
        var y = crisp(yS(r.value));
        g += '<line class="fc-chart__ref" x1="' + plotX0 + '" x2="' + plotX1 + '" y1="' + y + '" y2="' + y + '"/>';
        g += '<text class="fc-chart__ref-label" x="' + (plotX0 + 2) + '" y="' + (y - 9) + '" dominant-baseline="central">' + esc(r.label) + '</text>';
      });
      // Dodge coincident points sideways so overlapping series stay visible.
      var pts = s.series.map(function () { return []; });
      s.categories.forEach(function (c, ci) {
        var groups = {};
        s.series.forEach(function (ser, si) {
          var v = s.values[si][ci];
          if (v == null) return;
          (groups[v] = groups[v] || []).push(si);
        });
        Object.keys(groups).forEach(function (v) {
          var list = groups[v];
          list.forEach(function (si, j) { pts[si][ci] = { x: xC(ci) + (j - (list.length - 1) / 2) * (SYMBOL + 3), y: yS(+v) }; });
        });
        var topY = plotY1;
        s.series.forEach(function (ser, si) { if (pts[si][ci]) topY = Math.min(topY, pts[si][ci].y); });
        anchors.push({ x: xC(ci), y: topY - SYMBOL / 2 - RING });
      });
      s.series.forEach(function (ser, si) {
        var d = '', started = false;
        pts[si].forEach(function (p) { if (!p) { started = false; return; } d += (started ? 'L' : 'M') + f2(p.x) + ' ' + f2(p.y); started = true; });
        marks += '<path d="' + d + '" fill="none" stroke-width="' + LINE_W + '" stroke-linecap="round" stroke-linejoin="round"' + (ser.dash ? ' stroke-dasharray="6 4"' : '') + ' style="stroke:var(--' + ser.color + ')"/>';
      });
      s.series.forEach(function (ser, si) {
        pts[si].forEach(function (p, ci) {
          if (!p) return;
          var big = ci === self.sel;
          overlay += symbol(ser.shape || 'circle', p.x, p.y, big ? SYMBOL + 3 : SYMBOL, ser.color, true);
        });
      });
    }
    return { axis: 'x', bands: bands, anchors: anchors, height: H, plotY0: plotY0, plotY1: plotY1,
      svg: g + '<g class="hig-chart__marks">' + marks + '</g><g>' + overlay + '</g>' + labels };
  };

  /* Callout: values lead, labels follow; above the selected marks when there is room, else beside them. */
  Chart.prototype.placeCallout = function (W, L) {
    var c = this.callout, s = this.spec, self = this, i = this.sel;
    if (i < 0) { c.hidden = true; return; }
    var cat = s.categories[i];
    var h = '<div class="hig-chart__callout-x t-ios-caption-1">' + esc(cat.tableLabel || cat.label) + '</div>';
    s.series.forEach(function (ser, si) {
      var v = s.values[si][i];
      if (v == null) return;
      var item = { color: s.colorAt ? s.colorAt(si, i) : ser.color, texture: ser.texture, shape: s.kind === 'line' ? ser.shape : null, line: s.kind === 'line', dash: ser.dash };
      h += '<div class="hig-chart__callout-row">' + (s.series.length > 1 ? swatch(item, self.uid + '-c' + si) : '') +
        '<span class="hig-chart__callout-value t-ios-subheadline-emphasized">' + esc(self.fmt(v, si, 'callout')) + '</span>' +
        (s.series.length > 1 ? '<span class="hig-chart__callout-unit t-ios-caption-1">' + esc(ser.name) + '</span>' : '') + '</div>';
    });
    c.innerHTML = h;
    c.hidden = false;
    var cw = c.offsetWidth, ch = c.offsetHeight, a = L.anchors[i], left, top;
    var clampX = function (x) { return Math.max(0, Math.min(W - cw, x)); };
    if (L.axis === 'y') {
      left = a.x + 8 + cw <= W ? a.x + 8 : W - cw;
      top = a.bottom + ch + 4 <= L.height ? a.bottom - 2 : a.top - ch + 2;
      if (left === a.x + 8) top = Math.max(0, Math.min(L.height - ch, (a.top + a.bottom) / 2 - ch / 2));
    } else if (a.y - L.plotY0 >= ch + 6) {
      left = clampX(a.x - cw / 2); top = a.y - ch - 6;
    } else {
      left = a.x + 14 + cw <= W ? a.x + 14 : clampX(a.x - 14 - cw); top = L.plotY0;
    }
    c.style.left = Math.round(Math.max(0, left)) + 'px';
    c.style.top = Math.round(top) + 'px';
  };

  Chart.prototype.destroy = function () {
    if (this.ro) this.ro.disconnect();
    if (this.onResize) window.removeEventListener('resize', this.onResize);
    this.mount.innerHTML = '';
  };

  window.FCChart = {
    create: function (mount, spec) { return new Chart(mount, spec); },
    ticksFor: ticksFor,
    swatch: function (item) { return swatch(item, 'fc-sw-' + (++seq)); }
  };
})();
