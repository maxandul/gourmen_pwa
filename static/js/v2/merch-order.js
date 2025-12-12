// Merch Order Form (V2) - entkoppelt von Template-Logik
// - Daten kommen als JSON aus #merch-variants-data (type="application/json")
// - Keine Inline-Handler; Event Delegation auf dem Formular

(function () {
  document.addEventListener('DOMContentLoaded', initMerchOrder);

  function initMerchOrder() {
    const dataEl = document.getElementById('merch-variants-data');
    const form = document.getElementById('merch-order-form');
    if (!dataEl || !form) return;

    let data;
    try {
      data = JSON.parse(dataEl.textContent || '{}');
    } catch (err) {
      console.error('Merch: JSON Parse fehlgeschlagen', err);
      return;
    }

    const articles = Array.isArray(data.articles) ? data.articles : [];
    if (!articles.length) return;

    const articleMap = buildArticleMap(articles);

    // Initiale Rows verdrahten
    form.querySelectorAll('.variant-row').forEach((row) => {
      attachRowListeners(row, articleMap);
    });

    // Event Delegation für Add / Remove Buttons
    form.addEventListener('click', (event) => {
      const addBtn = event.target.closest('.js-add-variant');
      if (addBtn) {
        const articleId = parseInt(addBtn.dataset.articleId, 10);
        addVariantRow(articleId, articleMap);
        updateSummary();
      }
    });

    // Delegation für Selects / Inputs
    form.addEventListener('change', (event) => {
      const target = event.target;
      if (target.classList.contains('color-select')) {
        handleColorChange(target, articleMap);
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
      (article.variants || []).forEach((variant) => {
        variantsMap[`${variant.color}_${variant.size}`] = variant;
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

    const newRowIndex = container.querySelectorAll('.variant-row').length;
    const row = document.createElement('div');
    row.className = 'variant-row';
    row.dataset.articleId = articleId;
    row.dataset.rowIndex = newRowIndex;
    row.innerHTML = renderVariantRow(articleId, article.colors, newRowIndex);

    container.appendChild(row);
    attachRowListeners(row, articleMap);
  }

  function renderVariantRow(articleId, colors, rowIndex) {
    const colorOptions = (colors || [])
      .map((color) => `<option value="${escapeHtml(color)}">${escapeHtml(color)}</option>`)
      .join('');

    return `
      <div class="form-row" data-article-id="${articleId}" data-row-index="${rowIndex}">
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
      </div>
    `;
  }

  function attachRowListeners(row, articleMap) {
    const colorSelect = row.querySelector('.color-select');
    if (colorSelect) {
      colorSelect.addEventListener('change', (e) => handleColorChange(e.target, articleMap));
    }

    const sizeSelect = row.querySelector('.size-select');
    if (sizeSelect) {
      sizeSelect.addEventListener('change', (e) => handleSizeChange(e.target, articleMap));
    }

    const qtyInput = row.querySelector('.quantity-input');
    if (qtyInput) {
      qtyInput.addEventListener('input', updateSummary);
      qtyInput.addEventListener('change', updateSummary);
    }
  }

  function handleColorChange(colorSelect, articleMap) {
    const row = colorSelect.closest('.variant-row');
    const articleId = colorSelect.dataset.articleId;
    const article = articleMap[articleId];
    const sizeSelect = row.querySelector('.size-select');
    const quantityInput = row.querySelector('.quantity-input');
    const priceDisplay = row.querySelector('.price-value');

    resetRow(sizeSelect, quantityInput, priceDisplay);

    const selectedColor = colorSelect.value;
    if (article && selectedColor) {
      const availableSizes = new Set();
      Object.values(article.variantsMap).forEach((variant) => {
        if (variant.color === selectedColor) availableSizes.add(variant.size);
      });
      sizeSelect.innerHTML = '<option value="">Größe wählen</option>';
      availableSizes.forEach((size) => {
        const opt = document.createElement('option');
        opt.value = size;
        opt.textContent = size;
        sizeSelect.appendChild(opt);
      });
      sizeSelect.disabled = false;
    }
    updateSummary();
  }

  function handleSizeChange(sizeSelect, articleMap) {
    const row = sizeSelect.closest('.variant-row');
    const articleId = sizeSelect.dataset.articleId;
    const article = articleMap[articleId];
    const colorSelect = row.querySelector('.color-select');
    const quantityInput = row.querySelector('.quantity-input');
    const priceDisplay = row.querySelector('.price-value');

    resetRow(null, quantityInput, priceDisplay);

    const selectedColor = colorSelect.value;
    const selectedSize = sizeSelect.value;
    if (article && selectedColor && selectedSize) {
      const variant = article.variantsMap[`${selectedColor}_${selectedSize}`];
      if (variant) {
        quantityInput.disabled = false;
        quantityInput.dataset.price = variant.price;
      }
    }
    updateSummary();
  }

  function resetRow(sizeSelect, quantityInput, priceDisplay) {
    if (sizeSelect) {
      sizeSelect.disabled = true;
      sizeSelect.innerHTML = '<option value="">Größe wählen</option>';
    }
    if (quantityInput) {
      quantityInput.disabled = true;
      quantityInput.value = 0;
      delete quantityInput.dataset.price;
    }
    if (priceDisplay) {
      priceDisplay.textContent = '-';
    }
  }

  function updateSummary() {
    const quantityInputs = document.querySelectorAll('.quantity-input');
    let totalItems = 0;
    let totalPrice = 0;

    quantityInputs.forEach((input) => {
      const qty = parseInt(input.value, 10) || 0;
      const priceRappen = parseInt(input.dataset.price || '0', 10);
      const priceDisplay = input.closest('.variant-row')?.querySelector('.price-value');

      if (!input.disabled && qty > 0 && priceRappen > 0) {
        totalItems += qty;
        totalPrice += (priceRappen * qty) / 100;
        if (priceDisplay) {
          priceDisplay.textContent = `${(priceRappen / 100).toFixed(2)} CHF`;
        }
      } else if (priceDisplay) {
        priceDisplay.textContent = '-';
      }
    });

    const selectedItemsSpan = document.getElementById('selected-items');
    const totalPriceSpan = document.getElementById('total-price');
    if (selectedItemsSpan) selectedItemsSpan.textContent = totalItems;
    if (totalPriceSpan) totalPriceSpan.textContent = `${totalPrice.toFixed(2)} CHF`;

    const submitBtn = document.getElementById('submit-order-btn');
    if (submitBtn) submitBtn.disabled = totalItems === 0;
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

