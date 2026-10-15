/* PESO CSJDM - cascading Province > City/Municipality > Barangay selector.
   Markup: a container [data-location data-psgc-base="<static url>/data/psgc/"] holding three
   text inputs marked data-loc="province" | "city" | "barangay" (their saved values are the names).
   Data: static/data/psgc/provinces.json + one file per province (built by tools/build_psgc.py).
   City stays disabled until a province is chosen, Barangay until a city is chosen. */
(function () {
  var cache = {};
  function getJSON(url) {
    if (!cache[url]) {
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).catch(function (err) { delete cache[url]; throw err; });   // let the next attempt retry instead of reusing the failure
    }
    return cache[url];
  }
  function norm(s) { return String(s || '').toLowerCase().replace(/\s+/g, ' ').trim(); }
  function loose(s) { return norm(s).replace(/^city of /, '').replace(/ city$/, ''); }
  function find(list, val) {
    var n = norm(val), l = loose(val), i;
    if (!n) return '';
    for (i = 0; i < list.length; i++) if (norm(list[i]) === n) return list[i];
    for (i = 0; i < list.length; i++) if (loose(list[i]) === l) return list[i];
    return '';
  }

  function init(box) {
    var base = box.getAttribute('data-psgc-base');
    var elP = box.querySelector('[data-loc="province"]');
    var elC = box.querySelector('[data-loc="city"]');
    var elB = box.querySelector('[data-loc="barangay"]');
    if (!base || !elP || !elC || !elB || !window.PesoAC) return;

    var provinces = [], provNames = [], data = null;
    var state = { prov: '', city: '' };

    function lock(el, hint) { el.value = ''; el.disabled = true; el.placeholder = hint; }
    function unlock(el, hint) { el.disabled = false; el.placeholder = hint; }
    function resetBrgy() { lock(elB, 'Select city / municipality first'); }
    function resetCity() { state.city = ''; data = null; lock(elC, 'Select province first'); resetBrgy(); }

    function loadProvince(name) {
      var p = provinces.filter(function (x) { return x.n === name; })[0];
      if (!p) return Promise.resolve(null);
      return getJSON(base + p.c + '.json').then(function (d) { data = d; return d; });
    }
    function setProvince(raw) {
      var v = find(provNames, raw);
      elP.value = v;
      if (!v) { state.prov = ''; resetCity(); return Promise.resolve(); }
      if (v === state.prov && data) return Promise.resolve();
      state.prov = v;
      state.city = '';
      lock(elC, 'Loading...');
      resetBrgy();
      return loadProvince(v).then(function () { unlock(elC, 'Type to search'); });
    }
    function setCity(raw) {
      var v = data ? find(Object.keys(data), raw) : '';
      elC.value = v;
      if (!v) { state.city = ''; resetBrgy(); return; }
      if (v === state.city) return;
      state.city = v;
      lock(elB, '');
      unlock(elB, 'Type to search');
    }
    function setBarangay(raw) {
      var list = (data && state.city && data[state.city]) || [];
      elB.value = find(list, raw);
    }

    window.PesoAC.attach(elP, function () { return provNames; });
    window.PesoAC.attach(elC, function () { return data ? Object.keys(data) : []; });
    window.PesoAC.attach(elB, function () { return (data && state.city && data[state.city]) || []; });

    elP.addEventListener('change', function () { setProvince(elP.value); });
    elC.addEventListener('change', function () { setCity(elC.value); });
    elB.addEventListener('change', function () { setBarangay(elB.value); });

    // Start locked, then restore any saved values once the province list is in.
    var saved = { p: elP.value, c: elC.value, b: elB.value };
    resetCity();
    elP.disabled = true;
    elP.placeholder = 'Loading...';
    // Exposed so other scripts (e.g. the profile draft restore) can wait for / drive the cascade.
    box.pesoSet = function (p, c, b) { return setProvince(p).then(function () { setCity(c); setBarangay(b); }); };
    box.pesoReady = getJSON(base + 'provinces.json').then(function (list) {
      provinces = list;
      provNames = list.map(function (x) { return x.n; });
      unlock(elP, 'Type to search');
      if (!saved.p) return;
      return setProvince(saved.p).then(function () {
        setCity(saved.c);
        setBarangay(saved.b);
        box.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }).catch(function () {
      // Data unavailable: fall back to plain text boxes so the form still works.
      [elP, elC, elB].forEach(function (el) { el.disabled = false; el.placeholder = ''; });
      elP.value = saved.p;
      elC.value = saved.c;
      elB.value = saved.b;
      box.pesoSet = function (p, c, b) { elP.value = p; elC.value = c; elB.value = b; return Promise.resolve(); };
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('[data-location]'), init);
  });
})();
