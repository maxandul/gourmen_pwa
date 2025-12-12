// Merch Order Edit (V2)
// - Nutzt JSON-Payload aus #merch-order-edit-data
// - Kein Inline-JS/Handler; Events per Delegation
// - Entfernen durch Menge 0

(function () {
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    const dataEl = document.getElementById('merch-order-edit-data');
    const form = document.getElementById('merch-order-form');
    if (!dataEl || !form) return;

    let data;
    try {
      data = JSON.parse(dataEl.textContent || '{}');
    } catch (err) {
      console.error('Merch Edit: JSON parse fehlgeschlagen', err);
      return;
    }

    const articles = Array.isArray(data.articles) ? data.articles : [];
    if (!articles.length) return;

    const articleMap = buildArticleMap(articles);

    // Prefill bestehende Rows: setze preselect attributes for colors/sizes
    form.querySelectorAll('.variant-row').forEach((row) => {
      const colorSelect = row.querySelector('.color-select');
      const sizeSelect = row.querySelector('.size-select');
      const qtyInput = row.querySelector('.quantity-input');
      if (colorSelect && sizeSelect && qtyInput) {
        // Falls Größe schon gesetzt, sicherstellen, dass Optionen korrekt sind
        handleColorChange(colorSelect, articleMap, true);
        if (colorSelect.value && sizeSelect.value) {
          handleSizeChange(sizeSelect, articleMap);
        }
      }
    });

    // Delegation: Add variant
    form.addEventListener('click', (event) => {
      const addBtn = event.target.closest('.js-add-variant');
      if (addBtn) {
        const articleId = parseInt(addBtn.dataset.articleId, 10);
        addVariantRow(articleId, articleMap);
        updateSummary();
      }
    });

    // Delegation: selects/inputs
    form.addEventListener('change', (event) => {
      const target = event.target;
      if (target.classList.contains('color-select')) {
        handleColorChange(target, articleMap, false);
      } else if (target.classList.contains('size-select')) {
        handleSizeChange(target, articleMap);
      } else if (target.classList.contains('quantity-input')) {
        updateSummary();
      }
    });

    form.addEventListener('input', (event) => {
      if (event.target.classList.contains('quantity-input')) {
        updateSummary();
      }
    });

    updateSummary();
  }

  function buildArticleMap(articles) {
    const map = {};
    articles.forEach((article) => {
      const variantsMap = {};
      (article.variants || []).forEach((v) => {
        variantsMap[`${v.color}_${v.size}`] = v;
      });
      map[article.id] = {
        colors: article.available_colors || [],
        variantsMap,
      };
    });
    return map;
  }

  function addVariantRow(articleId, articleMap) {
    const container = document.getElementById(`variants_container_${articleId}`);
    const article = articleMap[articleId];
    if (!container || !article) return;

    const newIndex = container.querySelectorAll('.variant-row').length;
    const row = document.createElement('div');
    row.className = 'form-row variant-row';
    row.dataset.articleId = articleId;
    row.dataset.rowIndex = newIndex;
    row.innerHTML = renderRow(articleId, article.colors, newIndex);
    container.appendChild(row);
  }

  function renderRow(articleId, colors, rowIndex) {
    const colorOptions = (colors || [])
      .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
      .join('');

    return `
      <div class="form-field">
        <label class="form-field__label">Farbe</label>
        <select name="color_${articleId}[]" 
                class="form-field__select color-select"
                data-article-id="${articleId}"
                data-row-index="${rowIndex}">
          <option value="">Farbe wählen</option>
          ${colorOptions}
        </select>
      </div>
      <div class="form-field">
        <label class="form-field__label">Größe</label>
        <select name="size_${articleId}[]" 
                class="form-field__select size-select"
                data-article-id="${articleId}"
                data-row-index="${rowIndex}"
                disabled>
          <option value="">Zuerst Farbe wählen</option>
        </select>
      </div>
      <div class="form-field">
        <label class="form-field__label">Anzahl</label>
        <input type="number" 
               name="quantity_${articleId}[]" 
               min="0" 
               max="10" 
               value="0" 
               class="form-field__input quantity-input"
               data-article-id="${articleId}"
               data-row-index="${rowIndex}"
               disabled>
      </div>
      <div class="form-field">
        <label class="form-field__label">Preis</label>
        <div class="info-row__value price-value">-</div>
      </div>
    `;
  }

  function handleColorChange(select, articleMap, isInitial) {
    const row = select.closest('.variant-row');
    const articleId = select.dataset.articleId;
    const article = articleMap[articleId];
    if (!row || !article) return;

    const sizeSelect = row.querySelector('.size-select');
    const qty = row.querySelector('.quantity-input');
    const priceEl = row.querySelector('.price-value');

    resetRow(sizeSelect, qty, priceEl);

    const selectedColor = select.value;
    if (!selectedColor) return;

    const sizes = new Set();
    Object.values(article.variantsMap).forEach((v) => {
      if (v.color === selectedColor) sizes.add(v.size);
    });
    sizeSelect.innerHTML = '<option value="">Größe wählen</option>';
    sizes.forEach((size) => {
      const opt = document.createElement('option');
      opt.value = size;
      opt.textContent = size;
      sizeSelect.appendChild(opt);
    });
    sizeSelect.disabled = false;

    // Bei Initialisierung ggf. preselect Size und Preis setzen
    if (isInitial && select.dataset.preselectSize) {
      sizeSelect.value = select.dataset.preselectSize;
      handleSizeChange(sizeSelect, articleMap);
      delete select.dataset.preselectSize;
    }
  }

  function handleSizeChange(select, articleMap) {
    const row = select.closest('.variant-row');
    const articleId = select.dataset.articleId;
    const article = articleMap[articleId];
    if (!row || !article) return;

    const colorSelect = row.querySelector('.color-select');
    const qty = row.querySelector('.quantity-input');
    const priceEl = row.querySelector('.price-value');

    const color = colorSelect.value;
    const size = select.value;

    resetRow(null, qty, priceEl);

    if (color && size) {
      const variant = article.variantsMap[`${color}_${size}`];
      if (variant) {
        qty.disabled = false;
        qty.dataset.price = variant.price;
        priceEl.textContent = (variant.price / 100).toFixed(2) + ' CHF';
      }
    }
    updateSummary();
  }

  function resetRow(sizeSelect, qty, priceEl) {
    if (sizeSelect) {
      sizeSelect.disabled = true;
      sizeSelect.innerHTML = '<option value="">Größe wählen</option>';
    }
    if (qty) {
      qty.disabled = true;
      qty.value = 0;
      delete qty.dataset.price;
    }
    if (priceEl) priceEl.textContent = '-';
  }

  function updateSummary() {
    const qtyInputs = document.querySelectorAll('.quantity-input');
    let totalItems = 0;
    let totalPrice = 0;

    qtyInputs.forEach((input) => {
      if (input.disabled || !input.dataset.price) return;
      const qty = parseInt(input.value, 10) || 0;
      const price = parseInt(input.dataset.price, 10) || 0;
      totalItems += qty;
      totalPrice += qty * price;
    });

    const selectedEl = document.getElementById('selected-items');
    const totalEl = document.getElementById('total-price');
    if (selectedEl) selectedEl.textContent = totalItems;
    if (totalEl) totalEl.textContent = (totalPrice / 100).toFixed(2) + ' CHF';
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
})();

