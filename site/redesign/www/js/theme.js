/* Map the system appearance to the design system's four themes (light, dark, light-hc, dark-hc).
   The HIG says not to offer an app-specific appearance switch, so this only follows the OS setting.
   Loaded synchronously in <head> so the first paint is already in the right theme. */
(function () {
  var root = document.documentElement;
  var dark = window.matchMedia('(prefers-color-scheme: dark)');
  var more = window.matchMedia('(prefers-contrast: more)');
  function apply() { root.setAttribute('data-theme', (dark.matches ? 'dark' : 'light') + (more.matches ? '-hc' : '')); }
  apply();
  [dark, more].forEach(function (m) {
    if (m.addEventListener) m.addEventListener('change', apply); else if (m.addListener) m.addListener(apply);
  });
})();
