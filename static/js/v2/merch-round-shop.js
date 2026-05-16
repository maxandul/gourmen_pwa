/**
 * Merch Rundenshop: Mengenfeld an gewählte Ausführung (round_item_id) koppeln.
 */
(function syncMerchRoundShopConfig() {
  document.querySelectorAll('[data-merch-config-form]').forEach(function (form) {
    var sel = form.querySelector('select[name="round_item_id"]');
    var qtyInput = form.querySelector('input[name="quantity"]');
    if (!sel || !qtyInput) {
      return;
    }

    function readCartQty(option) {
      if (!option) {
        return 0;
      }
      var raw = option.getAttribute('data-cart-qty');
      var n = parseInt(raw === null || raw === '' ? '0' : raw, 10);
      return Number.isNaN(n) ? 0 : n;
    }

    function sync() {
      var opt = sel.selectedOptions[0];
      qtyInput.value = String(readCartQty(opt));
    }

    sel.addEventListener('change', sync);
    sync();
  });
})();
