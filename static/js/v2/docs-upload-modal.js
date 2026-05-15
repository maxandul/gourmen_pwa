/**
 * Upload-Modal Oeffnen/Schliessen + Dropzone (Drive-Browser Phase 9).
 */
(function () {
  'use strict';
  const modal = document.querySelector('[data-docs-upload-modal]');
  const trigger = document.querySelector('[data-docs-upload-trigger]');
  if (!modal || !trigger) return;

  const closers = modal.querySelectorAll('[data-docs-upload-close]');
  const fileInput = modal.querySelector('input[type="file"][name="file"]');
  const filenameEl = modal.querySelector('[data-docs-filename]');
  const titleInput = modal.querySelector('#docs-upload-title');
  const dropzone = modal.querySelector('[data-docs-dropzone]');
  const folderHidden = modal.querySelector('#docs-upload-drive-folder-id');
  const folderLabel = modal.querySelector('#docs-upload-folder-label');
  const maxMb = parseInt(modal.getAttribute('data-max-mb') || '100', 10);
  const allowedMimeTypes = new Set(JSON.parse(modal.getAttribute('data-allowed-mimes') || '[]'));
  const defaultFolder = modal.getAttribute('data-default-folder-id') || '';

  function syncDefaultFolder() {
    if (folderHidden && defaultFolder && !folderHidden.value) {
      folderHidden.value = defaultFolder;
    }
    if (folderLabel && folderHidden && folderHidden.value === defaultFolder) {
      folderLabel.textContent = 'Dokumente (Root)';
    }
  }

  function openModal() {
    syncDefaultFolder();
    if (typeof modal.showModal === 'function') modal.showModal(); else modal.setAttribute('open', 'open');
  }
  function closeModal() {
    if (typeof modal.close === 'function') modal.close(); else modal.removeAttribute('open');
  }

  trigger.addEventListener('click', openModal);
  closers.forEach(function (btn) { btn.addEventListener('click', closeModal); });

  const maxBytes = maxMb * 1024 * 1024;

  function handleFile(file) {
    if (!file) return;
    if (file.size > maxBytes) {
      window.alert('Datei ist grösser als das Limit von ' + maxMb + ' MB.');
      fileInput.value = '';
      return;
    }
    if (file.type && allowedMimeTypes.size && !allowedMimeTypes.has(file.type)) {
      window.alert('Dateityp «' + file.type + '» ist nicht erlaubt.');
      fileInput.value = '';
      return;
    }
    if (filenameEl) filenameEl.textContent = file.name;
    if (titleInput && !titleInput.value) {
      titleInput.value = file.name.replace(/\.[^.]+$/, '');
    }
  }

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      handleFile(fileInput.files && fileInput.files[0]);
    });
  }

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.add('docs-upload-modal__dropzone--active');
      });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.remove('docs-upload-modal__dropzone--active');
      });
    });
    dropzone.addEventListener('drop', function (e) {
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        try {
          fileInput.files = files;
        } catch (err) {
          /* ältere Browser */
        }
        handleFile(files[0]);
      }
    });
  }
})();
