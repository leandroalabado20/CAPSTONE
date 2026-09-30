/* PESO CSJDM — dark mode toggle
   Initial theme is applied by an inline snippet in <head> (before first paint)
   to avoid a flash of the wrong theme. This file only wires up the toggle
   button(s) and keeps their icon in sync. */
(function () {
  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function applyIcon(btn) {
    var dark = isDark();
    var icon = btn.querySelector('i');
    if (icon) icon.className = dark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    var label = dark ? 'Switch to light mode' : 'Switch to dark mode';
    btn.setAttribute('aria-label', label);
    btn.setAttribute('title', label);
  }

  function setTheme(dark) {
    var root = document.documentElement;
    if (dark) {
      root.setAttribute('data-theme', 'dark');
      root.setAttribute('data-bs-theme', 'dark');
      root.setAttribute('data-coreui-theme', 'dark');
    } else {
      root.removeAttribute('data-theme');
      root.removeAttribute('data-bs-theme');
      root.removeAttribute('data-coreui-theme');
    }
    try { localStorage.setItem('peso-theme', dark ? 'dark' : 'light'); } catch (e) {}
    document.querySelectorAll('.theme-toggle-btn').forEach(applyIcon);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.theme-toggle-btn').forEach(function (btn) {
      applyIcon(btn);
      btn.addEventListener('click', function () { setTheme(!isDark()); });
    });
  });
})();
