/* ============================================================
   CRICKBUSS Admin Shell JavaScript
   - Sidebar open/close (mobile)
   - Toast notification system (window.admToast)
   - Confirm dialog (window.admConfirm)
   - Auto-convert Django messages to toasts
   - Convert data-confirm buttons to custom dialog
   ============================================================ */

(function () {
  'use strict';

  /* ── 1. Sidebar toggle (mobile) ─────────────────────────── */
  const sidebar    = document.getElementById('admSidebar');
  const overlay    = document.getElementById('admOverlay');
  const openBtn    = document.getElementById('sidebarOpenBtn');
  const closeBtn   = document.getElementById('sidebarCloseBtn');

  function openSidebar()  {
    if (!sidebar) return;
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('visible');
    document.body.style.overflow = '';
  }

  if (openBtn)  openBtn.addEventListener('click', openSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
  if (overlay)  overlay.addEventListener('click', closeSidebar);

  /* ── 2. Toast system ────────────────────────────────────── */
  const TOAST_ICONS = {
    success: '<i class="fa-solid fa-circle-check"></i>',
    error:   '<i class="fa-solid fa-circle-xmark"></i>',
    warning: '<i class="fa-solid fa-triangle-exclamation"></i>',
    info:    '<i class="fa-solid fa-circle-info"></i>',
  };
  const TOAST_TITLES = {
    success: 'Success',
    error:   'Error',
    warning: 'Warning',
    info:    'Info',
  };

  window.admToast = function (message, type = 'success', duration = 3500) {
    const stack = document.getElementById('admToastStack');
    if (!stack) return;

    const toast = document.createElement('div');
    toast.className = `adm-toast ${type}`;
    toast.innerHTML = `
      <span class="adm-toast-icon">${TOAST_ICONS[type] || TOAST_ICONS.info}</span>
      <div class="adm-toast-body">
        <div class="adm-toast-title">${TOAST_TITLES[type] || 'Notice'}</div>
        <div class="adm-toast-msg">${message}</div>
      </div>
      <button class="adm-toast-close" aria-label="Dismiss">
        <i class="fa-solid fa-xmark"></i>
      </button>`;

    stack.prepend(toast);

    const closeToast = () => {
      toast.classList.add('hiding');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    };

    toast.querySelector('.adm-toast-close').addEventListener('click', closeToast);
    setTimeout(closeToast, duration);
  };

  // Backwards compat: existing code uses window.showToast
  window.showToast = window.admToast;

  /* ── 3. Auto-convert Django messages banner → toasts ─────── */
  document.querySelectorAll('[data-server-toast]').forEach(el => {
    const msg  = el.dataset.serverToast;
    const type = el.dataset.toastType || 'info';
    // Map Django tags to our types
    const mapped = type === 'success' ? 'success'
                 : type === 'error'   ? 'error'
                 : type === 'warning' ? 'warning'
                 : 'info';
    window.admToast(msg, mapped);
    // Also hide the banner alert to avoid duplication
    el.style.display = 'none';
  });

  /* ── 4. Confirm dialog ──────────────────────────────────── */
  const confirmOverlay = document.getElementById('admConfirmOverlay');
  const confirmTitle   = document.getElementById('admConfirmTitle');
  const confirmBody    = document.getElementById('admConfirmBody');
  const confirmIcon    = document.getElementById('admConfirmIcon');
  const confirmOk      = document.getElementById('admConfirmOk');
  const confirmCancel  = document.getElementById('admConfirmCancel');

  let _confirmResolve = null;

  window.admConfirm = function ({
    title   = 'Are you sure?',
    body    = 'This action cannot be undone.',
    okLabel = 'Confirm',
    okClass = '',          // 'ok-success' for green
    type    = 'danger',    // 'danger' | 'warning' | 'info'
  } = {}) {
    return new Promise(resolve => {
      if (!confirmOverlay) { resolve(window.confirm(body)); return; }

      confirmTitle.textContent = title;
      confirmBody.textContent  = body;
      confirmOk.textContent    = okLabel;
      confirmOk.className      = `adm-confirm-ok ${okClass}`;
      confirmIcon.className    = `adm-confirm-icon ${type}`;
      confirmOverlay.hidden    = false;
      _confirmResolve          = resolve;
      confirmOk.focus();
    });
  };

  function closeConfirm(result) {
    if (confirmOverlay) confirmOverlay.hidden = true;
    if (_confirmResolve) { _confirmResolve(result); _confirmResolve = null; }
  }

  if (confirmOk)     confirmOk.addEventListener('click',     () => closeConfirm(true));
  if (confirmCancel) confirmCancel.addEventListener('click',  () => closeConfirm(false));
  if (confirmOverlay) {
    confirmOverlay.addEventListener('click', e => {
      if (e.target === confirmOverlay) closeConfirm(false);
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && !confirmOverlay.hidden) closeConfirm(false);
    });
  }

  /* ── 5. Wire up data-adm-confirm buttons ────────────────── */
  // Usage: <button data-adm-confirm="Delete this player?" data-adm-confirm-type="danger"
  //                data-adm-confirm-ok="Delete" form="formId" type="submit">Delete</button>
  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('[data-adm-confirm]');
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    const ok = await window.admConfirm({
      title:   btn.dataset.admConfirmTitle   || 'Are you sure?',
      body:    btn.dataset.admConfirm        || 'This action cannot be undone.',
      okLabel: btn.dataset.admConfirmOk      || 'Confirm',
      okClass: btn.dataset.admConfirmOkClass || '',
      type:    btn.dataset.admConfirmType    || 'danger',
    });

    if (!ok) return;

    // Submit the nearest form or the form referenced by [form] attr
    const formId = btn.getAttribute('form');
    const form   = formId ? document.getElementById(formId)
                          : btn.closest('form');
    if (form) {
      // If button had a name/value, carry it
      if (btn.name) {
        const h = document.createElement('input');
        h.type = 'hidden'; h.name = btn.name; h.value = btn.value || '';
        form.appendChild(h);
      }
      form.submit();
    }
  });

  /* ── 6. Step-form wizard helper ─────────────────────────── */
  window.StepWizard = function (containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const panels  = Array.from(container.querySelectorAll('.step-panel'));
    const steps   = Array.from(container.querySelectorAll('.step-item'));
    const fill    = container.querySelector('.step-progress-fill');
    let   current = 0;

    function render() {
      panels.forEach((p, i) => p.classList.toggle('active', i === current));
      steps.forEach((s, i) => {
        s.classList.toggle('active', i === current);
        s.classList.toggle('done',   i < current);
      });
      if (fill) {
        const pct = panels.length > 1 ? (current / (panels.length - 1)) * 100 : 0;
        fill.style.width = pct + '%';
      }
    }

    this.next = () => { if (current < panels.length - 1) { current++; render(); } };
    this.prev = () => { if (current > 0) { current--; render(); } };
    this.goto = (n) => { current = Math.max(0, Math.min(n, panels.length - 1)); render(); };

    // Wire buttons
    container.addEventListener('click', e => {
      if (e.target.closest('[data-step-next]')) this.next();
      if (e.target.closest('[data-step-prev]')) this.prev();
    });

    render();
    return this;
  };

})();
