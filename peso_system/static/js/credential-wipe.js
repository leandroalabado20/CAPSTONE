/* Clears credential fields when the page is left or restored from history (Back/Forward / bfcache),
   so emails and passwords never sit pre-filled in a form the user navigated away from. */
(function () {
  var SELECTOR = 'input[type="password"], input[name="email"], input[name="confirm_email"]';

  function wipe() {
    Array.prototype.forEach.call(document.querySelectorAll(SELECTOR), function (el) {
      el.value = '';
      el.defaultValue = '';                       // also drops a server-rendered value from the "reset" state
      el.classList.remove('is-invalid');
      if (el.type === 'password') el.type = 'password';   // un-reveal if the eye toggle had shown it
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-wipe-msg]'), function (n) {
      n.textContent = ''; n.style.display = 'none';
    });
  }

  // Leaving the page: empty the fields so the bfcache snapshot / browser form restore holds nothing.
  window.addEventListener('pagehide', wipe);
  // Coming back via Back/Forward (restored page or browser form-restore): empty again.
  window.addEventListener('pageshow', function (e) {
    var nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {};
    if (e.persisted || nav.type === 'back_forward') wipe();
  });
})();
