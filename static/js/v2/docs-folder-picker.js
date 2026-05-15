/**
 * Lazy Folder-Picker fuer Drive-Browser (Phase 9).
 */
(function () {
  'use strict';

  const dlg = document.getElementById('docs-folder-picker-dialog');
  const tree = document.querySelector('[data-docs-folder-picker-tree]');
  const applyBtn = document.querySelector('[data-docs-folder-picker-apply]');
  if (!dlg || !tree || !applyBtn) return;

  let selectedId = null;
  let selectedName = null;
  let targetInput = null;
  let targetLabel = null;

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function closeDlg() {
    if (typeof dlg.close === 'function') dlg.close(); else dlg.removeAttribute('open');
  }

  document.querySelectorAll('[data-docs-folder-picker-close]').forEach(function (btn) {
    btn.addEventListener('click', closeDlg);
  });

  function setSelection(id, name) {
    selectedId = id;
    selectedName = name;
    applyBtn.disabled = !id;
    tree.querySelectorAll('.docs-folder-picker__row--selected').forEach(function (el) {
      el.classList.remove('docs-folder-picker__row--selected');
    });
    const hit = tree.querySelector('[data-folder-id="' + id + '"]');
    if (hit) hit.classList.add('docs-folder-picker__row--selected');
  }

  function fetchJson(url) {
    return fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) throw new Error('Netzwerkfehler');
      return r.json();
    });
  }

  function renderChildren(container, parentId, depth) {
    const wrap = document.createElement('div');
    wrap.className = 'docs-folder-picker__children';
    wrap.setAttribute('data-parent-loaded', parentId);
    container.appendChild(wrap);

    fetchJson('/docs/api/folder/' + encodeURIComponent(parentId) + '/children')
      .then(function (data) {
        const folders = data.folders || [];
        folders.forEach(function (f) {
          const row = document.createElement('div');
          row.className = 'docs-folder-picker__row';
          row.setAttribute('data-folder-id', f.id);
          row.style.paddingLeft = (depth * 12) + 'px';

          const toggle = document.createElement('button');
          toggle.type = 'button';
          toggle.className = 'docs-folder-picker__toggle';
          toggle.setAttribute('aria-label', 'Unterordner laden');
          toggle.textContent = '+';

          const label = document.createElement('button');
          label.type = 'button';
          label.className = 'docs-folder-picker__choose';
          label.textContent = f.name;

          row.appendChild(toggle);
          row.appendChild(label);

          toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            const loaded = wrap.querySelector('[data-parent-loaded="' + f.id + '"]');
            if (loaded) {
              loaded.remove();
              toggle.textContent = '+';
              return;
            }
            toggle.textContent = '–';
            renderChildren(wrap, f.id, depth + 1);
          });

          label.addEventListener('click', function () {
            setSelection(f.id, f.name);
          });

          wrap.appendChild(row);
        });
      })
      .catch(function () {
        wrap.textContent = 'Ordnerliste konnte nicht geladen werden.';
      });
  }

  function openPicker(btn) {
    const selInput = btn.getAttribute('data-target-input');
    const selLabel = btn.getAttribute('data-target-label');
    targetInput = selInput ? document.querySelector(selInput) : null;
    targetLabel = selLabel ? document.querySelector(selLabel) : null;
    selectedId = null;
    selectedName = null;
    applyBtn.disabled = true;
    tree.innerHTML = '';

    fetchJson('/docs/api/root').then(function (root) {
      const row = document.createElement('div');
      row.className = 'docs-folder-picker__row';
      row.setAttribute('data-folder-id', root.id);

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'docs-folder-picker__toggle';
      toggle.textContent = '+';

      const label = document.createElement('button');
      label.type = 'button';
      label.className = 'docs-folder-picker__choose';
      label.textContent = root.name || 'Dokumente';

      row.appendChild(toggle);
      row.appendChild(label);

      label.addEventListener('click', function () {
        setSelection(root.id, label.textContent || 'Dokumente');
      });

      toggle.addEventListener('click', function () {
        const loaded = tree.querySelector('[data-parent-loaded="' + root.id + '"]');
        if (loaded) {
          loaded.remove();
          toggle.textContent = '+';
          return;
        }
        toggle.textContent = '–';
        renderChildren(tree, root.id, 1);
      });

      tree.appendChild(row);

      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', 'open');
    });
  }

  document.querySelectorAll('[data-docs-folder-picker-open]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      openPicker(btn);
    });
  });

  applyBtn.addEventListener('click', function () {
    if (!selectedId || !targetInput) {
      closeDlg();
      return;
    }
    targetInput.value = selectedId;
    if (targetLabel) targetLabel.textContent = selectedName || selectedId;
    closeDlg();
  });
})();
