/* PESO CSJDM - styled autocomplete
   The browser's native <datalist> popup can't be styled, so:
   - every <input list="..."> is upgraded automatically to a custom dropdown, and
   - window.PesoAC.attach(input, getItems) turns any input into one whose options
     come from a function (used by the Province > City > Barangay selector).
   The menu matches the input's width, filters as you type, and supports mouse,
   touch and keyboard (up/down/enter/esc). If anything fails the native datalist stays. */
(function () {
  function attach(input, getItems) {
    var wrap = input.parentNode;
    if (!wrap.classList.contains('ac-wrap')) {
      wrap = document.createElement('div');
      wrap.className = 'ac-wrap';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
    }
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');

    var menu = document.createElement('ul');
    menu.className = 'ac-menu';
    menu.setAttribute('role', 'listbox');
    menu.hidden = true;
    wrap.appendChild(menu);

    var shown = [], active = -1;

    function close() { menu.hidden = true; active = -1; input.setAttribute('aria-expanded', 'false'); }
    function setActive(i) {
      var lis = menu.children;
      if (active >= 0 && lis[active]) lis[active].classList.remove('active');
      active = i;
      if (i >= 0 && lis[i]) { lis[i].classList.add('active'); lis[i].scrollIntoView({ block: 'nearest' }); }
    }
    function choose(v) {
      input.value = v;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      close();
    }
    function render() {
      if (input.disabled || input.readOnly) { close(); return; }
      var items = getItems() || [];
      var q = input.value.trim().toLowerCase();
      shown = items.filter(function (v) { return !q || v.toLowerCase().indexOf(q) !== -1; });
      menu.innerHTML = '';
      if (!shown.length) { close(); return; }
      shown.forEach(function (v) {
        var li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.textContent = v;
        li.addEventListener('mousedown', function (e) { e.preventDefault(); choose(v); });
        menu.appendChild(li);
      });
      menu.hidden = false;
      active = -1;
      input.setAttribute('aria-expanded', 'true');
    }

    input.addEventListener('focus', render);
    input.addEventListener('click', function () { if (menu.hidden) render(); });
    input.addEventListener('input', render);
    input.addEventListener('blur', close);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (menu.hidden) render(); setActive(Math.min(active + 1, shown.length - 1)); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(Math.max(active - 1, 0)); }
      else if (e.key === 'Enter' && !menu.hidden && active >= 0) { e.preventDefault(); choose(shown[active]); }
      else if (e.key === 'Escape') { close(); }
    });
  }

  function upgradeDatalist(input) {
    var dl = document.getElementById(input.getAttribute('list'));
    if (!dl) return;
    var items = Array.prototype.map.call(dl.options, function (o) { return o.value; });
    if (!items.length) return;
    input.removeAttribute('list');
    attach(input, function () { return items; });
  }

  window.PesoAC = { attach: attach };

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('input[list]'), function (el) {
      try { upgradeDatalist(el); } catch (err) { /* keep native datalist */ }
    });
  });
})();
