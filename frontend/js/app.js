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
    if (scan) scan.style.width = '40%';

    AdManager.onDownloadClick();

    const dlUrl = Api.buildDownloadUrl(
      fmt.id,
      state.data.target_url,
      state.data.title,
      state.data.referer
    );

    const a = document.createElement('a');
    a.href = dlUrl;
    a.rel = 'noopener';
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    await sleep(400);
    if (scan) scan.style.width = '100%';
    lbl.textContent = I18n.t('started');
    UI.showToast(I18n.t('started') + ': ' + fmt.res + ' ' + fmt.container);

    setTimeout(() => {
      delete btn.dataset.busy;
      btn.classList.remove('opacity-90');
      lbl.textContent = I18n.t('dl');
      if (scan) scan.style.width = '0';
    }, 1800);
  }

  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.style.colorScheme = savedTheme;
    UI.updateThemeIcon(savedTheme);
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.style.colorScheme = next;
    localStorage.setItem('theme', next);
    UI.updateThemeIcon(next);
  }

  function initEventListeners() {
    const urlInput = UI.elements.url();

    // Theme toggle
    document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);

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
    initTheme();

    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(e => console.error('SW register failed', e));
      });
    }

    // Check backend health & ping
    // Check backend health & ping
    const res = await Api.ping();
    const pingEl = UI.elements.ping();
    if (pingEl) {
      pingEl.textContent = `${res.latency} ms`;
    }

    // Load live site configuration from admin panel
    try {
      const cfg = await Api.getConfig();
      if (cfg) {
        // 1. Render announcement banner if active
        if (cfg.announcement_active && cfg.announcement_text) {
          const banner = document.getElementById('announcementBanner');
          const textEl = document.getElementById('announcementText');
          if (banner && textEl) {
            textEl.textContent = cfg.announcement_text;
            banner.classList.remove('hidden');
          }
        }
        // 2. Synchronize Ads settings from dashboard
        if (window.AdConfig) {
          AdConfig.ENABLE_ADS = !!cfg.enable_ads;
          AdConfig.DIRECT_AD_URL = (cfg.direct_ad_url && isSafeHttpUrl(cfg.direct_ad_url))
            ? cfg.direct_ad_url
            : '';
        }
      }
    } catch (e) {
      console.warn('Failed to fetch site config', e);
    }

    AdManager.init();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
