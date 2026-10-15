// Flatpickr with Month + Year dropdowns in the header and Clear / Today links at the bottom.
// Usage: var fp = initDropdownPicker('#el', 2015, { dateFormat: 'Y-m-d', ...flatpickr options });
function initDropdownPicker(sel, minYear, opts) {
  return flatpickr(sel, Object.assign({
    monthSelectorType: 'dropdown', maxDate: 'today',
    minDate: minYear + '-01-01', disableMobile: true, allowInput: false,
    onReady: function (selected, str, fp) {
      var sy = document.createElement('select');
      sy.className = 'fp-year'; sy.setAttribute('aria-label', 'Year');
      for (var y = new Date().getFullYear(); y >= minYear; y--) {
        var o = document.createElement('option'); o.value = o.textContent = y; sy.appendChild(o);
      }
      sy.addEventListener('change', function () { fp.changeYear(parseInt(this.value, 10)); });
      fp.currentYearElement.parentNode.parentNode.appendChild(sy);
      fp._fpYear = sy;
      var ft = document.createElement('div'); ft.className = 'fp-footer';
      ft.innerHTML = '<button type="button" data-a="clear">Clear</button><button type="button" data-a="today">Today</button>';
      ft.addEventListener('click', function (e) {
        var a = e.target.getAttribute('data-a');
        if (a === 'clear') { fp.clear(); fp.close(); }
        if (a === 'today') { fp.setDate(new Date(), true); fp.close(); }
      });
      fp.calendarContainer.appendChild(ft);
      fp.calendarContainer.classList.add('hasFooter');
      sy.value = fp.currentYear;
    },
    onOpen: function (s, d, fp) { fp._fpYear.value = fp.currentYear; },
    onMonthChange: function (s, d, fp) { fp._fpYear.value = fp.currentYear; },
    onYearChange: function (s, d, fp) { fp._fpYear.value = fp.currentYear; }
  }, opts));
}
