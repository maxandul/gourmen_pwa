const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.env.MERCH_EDIT_TEST_SOURCE || 'static/js/v2/merch-order-edit.js', 'utf8');

function run({ quantity = '3', color = 'Blue', size = 'M', price = 1900 } = {}) {
  const callbacks = {};
  const dataset = () => new Proxy({}, { set(target, key, value) { target[key] = String(value); return true; } });
  function select(options, initial) {
    let value = initial;
    return { options: [...options], disabled: false, dataset: dataset(),
      get value() { return value; },
      set value(next) { value = this.options.includes(String(next)) ? String(next) : ''; },
      set innerHTML(html) { this.options = ['']; value = ''; },
      appendChild(option) { this.options.push(option.value); },
      closest() { return row; }
    };
  }
  const colorSelect = select(['', color], color);
  colorSelect.dataset.articleId = 1;
  colorSelect.dataset.preselectSize = size;
  const sizeSelect = select(['', size], size);
  sizeSelect.dataset.articleId = 1;
  const qty = { value: quantity, disabled: false, dataset: dataset() };
  const priceLabel = { textContent: '' };
  const nodes = { '.color-select': colorSelect, '.size-select': sizeSelect, '.quantity-input': qty, '.price-value': priceLabel };
  const row = { querySelector(key) { return nodes[key]; } };
  const total = { textContent: '' };
  const count = { textContent: '' };
  const elements = {
    'merch-order-edit-data': { textContent: JSON.stringify({ articles: [{ id: 1, available_colors: ['Blue'], variants: [{ id: 1, color: 'Blue', size: 'M', price }] }] }) },
    'merch-order-form': { querySelectorAll() { return [row]; }, addEventListener(name, fn) { callbacks[name] = fn; } },
    'total-price': total, 'selected-items': count
  };
  const document = {
    addEventListener(name, fn) { callbacks[name] = fn; },
    getElementById(id) { return elements[id]; },
    querySelectorAll() { return [qty]; },
    createElement() { return { value: '', textContent: '' }; }
  };
  vm.runInNewContext(source, { document, console });
  callbacks.DOMContentLoaded();
  return { qty, colorSelect, sizeSelect, total, count, priceLabel };
}

test('real initialization retains quantity and bound-price total', () => {
  const state = run();
  assert.equal(state.qty.value, '3');
  assert.equal(state.qty.disabled, false);
  assert.equal(state.total.textContent, '57.00 CHF');
  assert.equal(state.count.textContent, 3);
});

test('free bound item remains editable and totals correctly', () => {
  const state = run({ quantity: '2', price: 0 });
  assert.equal(state.qty.value, '2');
  assert.equal(state.total.textContent, '0.00 CHF');
  assert.equal(state.count.textContent, 2);
});

test('rejected unavailable selection remains correctable after initialization', () => {
  const state = run({ quantity: '7', color: 'Retained invalid color', size: 'XL' });
  assert.equal(state.qty.value, '7');
  assert.equal(state.qty.disabled, false);
  assert.equal(state.colorSelect.value, 'Retained invalid color');
  assert.equal(state.sizeSelect.value, 'XL');
  assert.equal(state.sizeSelect.disabled, false);
});

test('invalid quantity text from server error is not reset', () => {
  assert.equal(run({ quantity: '-1.5' }).qty.value, '-1.5');
});
