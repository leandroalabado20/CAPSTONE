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
