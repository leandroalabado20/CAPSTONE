/* PESO CSJDM — client-side form guard
   Stops a form from submitting when any field is invalid (empty required field,
   wrong type/format, out-of-range number, etc.) so the user never loses what
   they already typed. Highlights the invalid fields (Bootstrap .was-validated),
   scrolls to the first problem, focuses it, and shows the native message.
   Add data-no-validate to a <form> to opt out. */
(function () {
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form || form.tagName !== 'FORM') return;
    if (form.hasAttribute('data-no-validate')) return;

    if (!form.checkValidity()) {
      e.preventDefault();
      e.stopPropagation();
      form.classList.add('was-validated');
      var bad = form.querySelector(':invalid');
      if (bad) {
        bad.scrollIntoView({ behavior: 'smooth', block: 'center' });
        try { bad.focus({ preventScroll: true }); } catch (err) { bad.focus(); }
        if (typeof bad.reportValidity === 'function') bad.reportValidity();
      }
    }
  }, true);
})();

/* Input masks.  data-mask="mobile"  -> digits only, max 11, must be 09XXXXXXXXX
                 data-mask="tin"     -> digits only, auto dashes: 000-000-000-000
   Pasted values are cleaned too (spaces, dashes, +63 / 63 prefix on mobile numbers). */
(function () {
  var TIN_MAX = 12;
  function digits(s) { return String(s || '').replace(/\D/g, ''); }
  function fmtMobile(s) {
    var d = digits(s);
    if (d.indexOf('639') === 0) d = '0' + d.slice(2);   // +63 9XX... -> 09XX...
    else if (d.charAt(0) === '9') d = '0' + d;          // 9XX... -> 09XX...
    return d.slice(0, 11);
  }
  function fmtTin(s) {
    var d = digits(s).slice(0, TIN_MAX), out = [], i;
    for (i = 0; i < d.length; i += 3) out.push(d.substr(i, 3));
    return out.join('-');
  }
  var FORMAT = { mobile: fmtMobile, tin: fmtTin };

  function check(el, kind) {
    var v = el.value, ok = true, msg = '';
    if (kind === 'mobile') {
      ok = !v || /^09\d{9}$/.test(v);
      msg = 'Enter an 11-digit mobile number starting with 09 (e.g. 09171234567).';
    } else {
      ok = !v || /^\d{3}-\d{3}-\d{3}(-\d{3})?$/.test(v);
      msg = 'Enter a complete TIN: 000-000-000 or 000-000-000-000.';
    }
    el.setCustomValidity(ok ? '' : msg);
  }

  function reformat(el, kind) {
    var fmt = FORMAT[kind];
    var pos = el.selectionStart, before = el.value;
    var digitsBeforeCaret = digits(before.slice(0, pos)).length;
    var next = fmt(before);
    if (next !== before) el.value = next;
    // put the caret after the same number of digits it followed before reformatting
    var p = 0, seen = 0;
    while (p < next.length && seen < digitsBeforeCaret) { if (/\d/.test(next.charAt(p))) seen++; p++; }
    try { el.setSelectionRange(p, p); } catch (e) { /* not supported on this input type */ }
    check(el, kind);
  }

  function setup(el) {
    var kind = el.getAttribute('data-mask');
    if (!FORMAT[kind]) return;
    el.setAttribute('inputmode', 'numeric');
    el.setAttribute('autocomplete', 'off');
    if (kind === 'mobile') {
      el.maxLength = 11;
      el.pattern = '09[0-9]{9}';
      el.title = '11-digit mobile number starting with 09 (e.g. 09171234567)';
      if (!el.placeholder) el.placeholder = '09XXXXXXXXX';
    } else {
      el.maxLength = 15;
      el.pattern = '[0-9]{3}-[0-9]{3}-[0-9]{3}(-[0-9]{3})?';
      el.title = 'TIN in the format 000-000-000-000';
      if (!el.placeholder) el.placeholder = '000-000-000-000';
    }
    // Block letters and symbols as they are typed (shortcuts like Ctrl+V still work).
    el.addEventListener('keydown', function (e) {
      if (e.ctrlKey || e.metaKey || e.altKey || e.key.length !== 1) return;
      if (!/\d/.test(e.key)) e.preventDefault();
    });
    // Backspace / Delete next to a dash removes the digit beside it instead of getting stuck.
    el.addEventListener('keydown', function (e) {
      if (kind !== 'tin' || el.selectionStart !== el.selectionEnd) return;
      var pos = el.selectionStart;
      if (e.key === 'Backspace' && el.value.charAt(pos - 1) === '-') el.setSelectionRange(pos - 1, pos - 1);
      if (e.key === 'Delete' && el.value.charAt(pos) === '-') el.setSelectionRange(pos + 1, pos + 1);
    });
    // Paste: keep only the digits (and turn +63 9XX... into 09XX...) before the length limit cuts it.
    el.addEventListener('paste', function (e) {
      var t = (e.clipboardData || window.clipboardData).getData('text');
      e.preventDefault();
      var a = el.selectionStart, b = el.selectionEnd;
      var add = kind === 'mobile' && a === 0 && b === el.value.length ? fmtMobile(t) : digits(t);
      el.value = el.value.slice(0, a) + add + el.value.slice(b);
      var c = a + add.length;
      el.setSelectionRange(c, c);
      reformat(el, kind);
    });
    el.addEventListener('input', function () { reformat(el, kind); });
    el.addEventListener('blur', function () { check(el, kind); });
    if (el.value) { el.value = FORMAT[kind](el.value); check(el, kind); }
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('[data-mask]'), setup);
  });
})();


/* Double-submit guard.  Once a valid POST form is on its way, its buttons are disabled and show a spinner,
   and a second submit (double-click, Enter + click, two quick taps) is swallowed. Everything is restored if the
   browser comes back from history (bfcache) or the server has not answered after 30 s.
   Opt out with data-no-lock on the <form>. GET forms (searches) are left alone. */
(function () {
  var RESTORE_AFTER_MS = 30000;

  function buttons(form) {
    return Array.prototype.slice.call(form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]'));
  }
  function unlock(form) {
    if (!form || form.dataset.locked !== '1') return;
    delete form.dataset.locked;
    buttons(form).forEach(function (b) {
      if (b.dataset.origHtml !== undefined) { b.innerHTML = b.dataset.origHtml; delete b.dataset.origHtml; }
      b.disabled = false;
      b.removeAttribute('aria-busy');
    });
  }
  function lock(form) {
    form.dataset.locked = '1';
    buttons(form).forEach(function (b) {
      if (b.tagName === 'BUTTON' && b.dataset.origHtml === undefined) {
        b.dataset.origHtml = b.innerHTML;
        b.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' + b.textContent.trim();
      }
      b.disabled = true;
      b.setAttribute('aria-busy', 'true');
    });
    setTimeout(function () { unlock(form); }, RESTORE_AFTER_MS);
  }

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form || form.tagName !== 'FORM') return;
    if (form.hasAttribute('data-no-lock')) return;
    if ((form.method || 'get').toLowerCase() !== 'post') return;
    if (form.target && form.target !== '_self') return;           // opens elsewhere: page stays interactive
    if (form.dataset.locked === '1') { e.preventDefault(); return; }     // second submit while the first is in flight
    // Run after the validation guard and any inline onsubmit/confirm() had their say
    setTimeout(function () { if (!e.defaultPrevented) lock(form); }, 0);
  });

  window.addEventListener('pageshow', function () {
    Array.prototype.forEach.call(document.querySelectorAll('form[data-locked="1"]'), unlock);
  });
})();
