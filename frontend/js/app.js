// ==========================================================================
// SnapWave - Main Application Controller
// ==========================================================================

(() => {
  const state = {
    data: null,
    tab: 'video',
    busy: false
  };

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function isUrl(str) {
    try {
      const u = new URL(str.trim());
      return /^https?:$/.test(u.protocol) && u.hostname.includes('.');
    } catch {
      return false;
    }
  }

  function syncClearButton() {
    const urlInput = UI.elements.url();
    const clearBtn = UI.elements.clear();
    const hasVal = !!urlInput.value;
    clearBtn.classList.toggle('hidden', !hasVal);
    clearBtn.classList.toggle('flex', hasVal);
  }

  async function pasteFromClipboard() {
    try {
      const txt = await navigator.clipboard.readText();
      if (!txt) return;
      const urlInput = UI.elements.url();
      urlInput.value = txt.trim();
      syncClearButton();
      UI.showToast(I18n.t('pasted'));
      if (isUrl(urlInput.value)) {
        $('#form').requestSubmit();
      }
    } catch {
      UI.setMsg(I18n.t('denied'), 'err');
      UI.elements.url().focus();
    }
  }

  async function handleDownload(btn) {
    if (!btn || btn.dataset.busy || !state.data) return;
    const fmt = state.data.formats.find(f => f.id === btn.dataset.id);
    if (!fmt) return;

    const lbl = $('.lbl', btn);
    const scan = $('.scan', btn);
    btn.dataset.busy = '1';
    lbl.textContent = I18n.t('prep');
    btn.classList.add('opacity-90');

    // Trigger Monetization / Ad hook
    AdManager.onDownloadClick();

    // Trigger Stream Download via Anchor
    const dlUrl = Api.buildDownloadUrl(
      fmt.id,
      state.data.target_url,
      state.data.title,
      state.data.referer
    );

    const a = document.createElement('a');
    a.href = dlUrl;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Simulate UX progress animation on button scanner
    for (let p = 20; p <= 100; p += 25) {
      scan.style.width = p + '%';
      lbl.textContent = Math.round(p) + '%';
      await sleep(90);
    }

    btn.classList.replace('bg-ember', 'bg-emerald-600');
    btn.classList.remove('hover:bg-ember-hi');
    lbl.textContent = I18n.t('done');
    scan.style.width = '0';
    UI.showToast(I18n.t('started') + ': ' + fmt.res + ' ' + fmt.container);

    setTimeout(() => {
      delete btn.dataset.busy;
      btn.classList.remove('opacity-90');
      btn.classList.replace('bg-emerald-600', 'bg-ember');
      btn.classList.add('hover:bg-ember-hi');
      lbl.textContent = I18n.t('dl');
    }, 2200);
  }

  function initEventListeners() {
    const urlInput = UI.elements.url();

    // Input events
    urlInput.addEventListener('input', () => {
      syncClearButton();
      if (UI.elements.msg().classList.contains('text-red-600')) {
        UI.setMsg(I18n.t('hint'));
      }
    });

    UI.elements.clear().addEventListener('click', () => {
      urlInput.value = '';
      syncClearButton();
      UI.setMsg(I18n.t('hint'));
      urlInput.focus();
    });

    UI.elements.paste().addEventListener('click', pasteFromClipboard);

    urlInput.addEventListener('paste', () => {
      setTimeout(() => {
        syncClearButton();
        if (isUrl(urlInput.value)) $('#form').requestSubmit();
      }, 0);
    });

    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v' &&
          document.activeElement !== urlInput &&
          !/input|textarea/i.test(document.activeElement.tagName)) {
        e.preventDefault();
        pasteFromClipboard();
      }
    });

    // Language toggle
    UI.elements.langBtn().addEventListener('click', () => {
      const next = I18n.getLang() === 'ar' ? 'en' : 'ar';
      I18n.setLang(next);
      UI.applyTranslations();
      UI.setMsg(I18n.t('hint'));
      if (state.data) UI.renderRows(state.data, state.tab);
    });

    // Tab toggle (Video / Audio)
    $$('.tab').forEach(b => {
      b.addEventListener('click', () => {
        state.tab = b.dataset.tab;
        if (state.data) UI.renderRows(state.data, state.tab);
      });
    });

    // Download click delegation
    UI.elements.rows().addEventListener('click', e => {
      const btn = e.target.closest('.dl');
      if (btn) handleDownload(btn);
    });

    // Form submission
    const form = $('#form');
    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (state.busy) return;

      const link = urlInput.value.trim();
      if (!link) {
        UI.setMsg(I18n.t('empty'), 'err');
        urlInput.focus();
        return;
      }
      if (!isUrl(link)) {
        UI.setMsg(I18n.t('invalid'), 'err');
        urlInput.focus();
        return;
      }

      UI.setMsg(I18n.t('hint'));
      state.busy = true;
      UI.elements.go().disabled = true;
      UI.elements.barProg().classList.remove('hidden');
      UI.elements.result().classList.add('hidden');
      UI.elements.loading().classList.remove('hidden');

      // Stage cycling animation
      let stageIdx = 0;
      const stages = I18n.t('stages');
      UI.elements.stage().textContent = stages[0];
      const stageTimer = setInterval(() => {
        stageIdx = Math.min(stageIdx + 1, stages.length - 1);
        UI.elements.stage().textContent = stages[stageIdx];
      }, 450);

      try {
        const data = await Api.extract(link);
        state.data = data;
        state.tab = 'video';
        UI.renderResult(data, state.tab);
      } catch (err) {
        UI.setMsg(err.message || I18n.t('fail'), 'err');
        UI.elements.result().classList.add('hidden');
      } finally {
        clearInterval(stageTimer);
        state.busy = false;
        UI.elements.go().disabled = false;
        UI.elements.barProg().classList.add('hidden');
        UI.elements.loading().classList.add('hidden');
      }
    });
  }

  // Application Bootstrap
  async function init() {
    UI.applyTranslations();
    UI.renderPlatforms();
    initEventListeners();
    AdManager.init();

    // Check backend health & ping
    const res = await Api.ping();
    const pingEl = UI.elements.ping();
    if (pingEl) {
      pingEl.textContent = `${res.latency} ms`;
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
