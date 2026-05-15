/**
 * Gemeinsame Rename/Move/Archive/Restore-Modale fuer Drive-Browser-Listen.
 */
(function () {
  'use strict';

  function openDlg(el) {
    if (!el) return;
    if (typeof el.showModal === 'function') el.showModal(); else el.setAttribute('open', 'open');
  }
  function closeDlg(el) {
    if (!el) return;
    if (typeof el.close === 'function') el.close(); else el.removeAttribute('open');
  }

  function stemFromFilename(name) {
    if (!name) return '';
    var i = name.lastIndexOf('.');
    return i > 0 ? name.slice(0, i) : name;
  }

  function wireCloseButtons(root) {
    root.querySelectorAll('[data-drive-quick-close]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var dlg = btn.closest('dialog');
        closeDlg(dlg);
      });
    });
  }

  wireCloseButtons(document);

  document.addEventListener('click', function (e) {
    var renameBtn = e.target.closest('[data-drive-quick-rename]');
    if (renameBtn) {
      var id = renameBtn.getAttribute('data-doc-id');
      var fname = renameBtn.getAttribute('data-filename') || '';
      var form = document.getElementById('drive-quick-rename-form');
      var dlg = document.getElementById('drive-quick-rename-dialog');
      var inp = document.getElementById('drive-quick-rename-title-input');
      if (form && dlg && inp && id) {
        form.action = '/docs/file/' + encodeURIComponent(id) + '/rename';
        inp.value = stemFromFilename(fname);
        openDlg(dlg);
      }
      return;
    }

    var moveBtn = e.target.closest('[data-drive-quick-move]');
    if (moveBtn) {
      var mid = moveBtn.getAttribute('data-doc-id');
      var mform = document.getElementById('drive-quick-move-form');
      var mdlg = document.getElementById('drive-quick-move-dialog');
      var pid = document.getElementById('drive-quick-move-parent-id');
      var lbl = document.getElementById('drive-quick-move-folder-label');
      if (mform && mdlg && pid && lbl && mid) {
        mform.action = '/docs/file/' + encodeURIComponent(mid) + '/move';
        pid.value = '';
        lbl.textContent = 'Kein Ordner gewählt';
        openDlg(mdlg);
      }
      return;
    }

    var archBtn = e.target.closest('[data-drive-quick-archive]');
    if (archBtn) {
      var aid = archBtn.getAttribute('data-doc-id');
      var aform = document.getElementById('drive-quick-archive-form');
      var adlg = document.getElementById('drive-quick-archive-dialog');
      if (aform && adlg && aid) {
        aform.action = '/docs/file/' + encodeURIComponent(aid) + '/archive';
        openDlg(adlg);
      }
      return;
    }

    var restBtn = e.target.closest('[data-drive-quick-restore]');
    if (restBtn) {
      var rid = restBtn.getAttribute('data-doc-id');
      var rform = document.getElementById('drive-quick-restore-form');
      var rdlg = document.getElementById('drive-quick-restore-dialog');
      var tid = document.getElementById('drive-quick-restore-target-id');
      var rlbl = document.getElementById('drive-quick-restore-folder-label');
      if (rform && rdlg && tid && rlbl && rid) {
        rform.action = '/docs/file/' + encodeURIComponent(rid) + '/restore';
        tid.value = '';
        rlbl.textContent = 'Kein Ordner gewählt';
        openDlg(rdlg);
      }
    }
  });
})();
