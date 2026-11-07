// ==========================================================================
// SnapWave - UI & Rendering Component
// ==========================================================================

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[ch]));
}

const UI = {
  elements: {
    url: () => $('#url'),
    msg: () => $('#msg'),
    bar: () => $('#bar'),
    go: () => $('#go'),
    goTxt: () => $('#goTxt'),
    clear: () => $('#clear'),
    paste: () => $('#paste'),
    langBtn: () => $('#lang'),
    ping: () => $('#ping'),
    loading: () => $('#loading'),
    stage: () => $('#stage'),
    barProg: () => $('#barProg'),
    result: () => $('#result'),
    rows: () => $('#rows'),
    count: () => $('#count'),
    thumb: () => $('#thumb'),
    dur: () => $('#dur'),
    title: () => $('#title'),
    author: () => $('#author'),
    host: () => $('#host'),
    date: () => $('#date'),
    toast: () => $('#toast'),
    faqList: () => $('#faqList'),
    chips: () => $('#chips'),
    year: () => $('#yr')
  },

  toastTimer: null,

  showToast(text) {
    const el = this.elements.toast();
    if (!el) return;
    el.textContent = text;
    el.style.opacity = '1';
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => {
      el.style.opacity = '0';
    }, 2200);
  },

  setMsg(text, kind = 'info') {
    const msgEl = this.elements.msg();
    const barEl = this.elements.bar();
    if (!msgEl || !barEl) return;

    msgEl.textContent = text;
    msgEl.className = 'mt-2.5 min-h-[20px] text-[13px] ' + (kind === 'err' ? 'text-red-600' : 'text-zinc-500');
    barEl.style.borderColor = kind === 'err' ? 'rgba(248,113,113,.7)' : '';
  },

  fmtDur(s) {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const x = s % 60;
    return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(x).padStart(2, '0');
  },

  fmtMB(mb) {
    return mb >= 1000 ? (mb / 1024).toFixed(2) + ' GB' : mb.toFixed(1) + ' MB';
  },

  renderPlatforms() {
    const platforms = [
      ['YouTube', ''],
      ['TikTok', ''],
      ['Instagram', ''],
      ['Facebook', ''],
      ['HLS', 'm3u8 streams']
    ];
    const chipsEl = this.elements.chips();
    if (chipsEl) {
      chipsEl.innerHTML = platforms.map(([n, m]) =>
        `<li class="hair rounded-md bg-panel h-9 px-3 flex items-center gap-2 text-sm text-zinc-200 shadow-[0_1px_0_rgba(255,255,255,.7)]">
           ${esc(n)}${m ? `<span class="font-mono text-[10px] text-zinc-500" dir="ltr">${esc(m)}</span>` : ''}
         </li>`
      ).join('');
    }
    const yrEl = this.elements.year();
    if (yrEl) yrEl.textContent = new Date().getFullYear();
  },

  renderFaqs() {
    const faqs = I18n.t('faqs');
    const faqEl = this.elements.faqList();
    if (faqEl && Array.isArray(faqs)) {
      faqEl.innerHTML = faqs.map(([q, a]) => `
        <details class="group">
          <summary class="flex items-center justify-between gap-4 px-5 py-4 text-sm font-medium hover:bg-raised/60">
            ${esc(q)}
            <svg class="chev shrink-0 text-zinc-500 transition-transform" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <p class="px-5 pb-5 text-sm text-zinc-400 leading-relaxed">${esc(a)}</p>
        </details>
      `).join('');
    }
  },

  renderResult(data, activeTab = 'video') {
    const thumb = this.elements.thumb();
    const src = data.thumbnail || '/assets/favicon.svg';
    thumb.src = (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('/'))
      ? src
      : '/assets/favicon.svg';
    thumb.alt = data.title || '';
    this.elements.dur().textContent = this.fmtDur(data.duration);
    this.elements.title().textContent = data.title;
    this.elements.author().textContent = data.author;
    this.elements.host().textContent = data.host;
    this.elements.date().textContent = data.date;

    this.renderRows(data, activeTab);
    this.elements.result().classList.remove('hidden');
    this.elements.result().scrollIntoView({ behavior: 'smooth', block: 'start' });
  },

  renderRows(data, activeTab) {
    $$('.tab').forEach(b => {
      const on = b.dataset.tab === activeTab;
      b.setAttribute('aria-selected', on);
      b.className = 'tab h-8 px-3.5 rounded-md text-sm font-medium transition-colors ' +
        (on ? 'bg-white text-zinc-100 hair shadow-sm' : 'text-zinc-500 hover:text-zinc-200 border border-transparent');
    });

    const list = data.formats.filter(f => f.type === activeTab);
    this.elements.count().textContent = list.length + ' ' + I18n.t('found');

    this.elements.rows().innerHTML = list.map(f => `
      <div class="row flex items-center gap-3 rounded-lg px-2.5 sm:px-3 py-2.5 hover:bg-raised/70 transition-colors" data-id="${esc(f.id)}">
        <span class="font-mono text-[11px] font-semibold w-11 text-center rounded border ${f.container === 'MP4' ? 'border-ember/40 text-[#B93C00]' : 'border-black/20 text-zinc-300'} py-1" dir="ltr">${esc(f.container)}</span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-mono text-sm font-medium" dir="ltr">${esc(f.res)}</span>
            <span class="text-xs text-zinc-400">${esc(f.tag)}</span>
          </div>
          <div class="font-mono text-[11px] text-zinc-500 mt-0.5" dir="ltr">${esc(f.codec)}</div>
        </div>
        <span class="font-mono text-xs text-zinc-300 tabular-nums w-[72px] text-end" dir="ltr">~${esc(this.fmtMB(f.mb))}</span>
        <button class="dl relative overflow-hidden h-9 min-w-[104px] px-3.5 rounded-lg bg-ember hover:bg-ember-hi text-white text-sm font-semibold transition-colors flex items-center justify-center gap-1.5" data-id="${esc(f.id)}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12m0 0l-5-5m5 5l5-5M5 20h14"/></svg>
          <span class="lbl">${esc(I18n.t('dl'))}</span>
          <span class="scan" style="width:0"></span>
        </button>
      </div>
    `).join('');
  },

  applyTranslations() {
    const lang = I18n.getLang();
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';

    $$('[data-i18n]').forEach(el => {
      const v = I18n.t(el.dataset.i18n);
      if (v) el.textContent = v;
    });

    const langBtn = this.elements.langBtn();
    if (langBtn) {
      langBtn.textContent = lang === 'ar' ? 'English' : 'العربية';
    }

    this.renderFaqs();
  }
};

window.UI = UI;
window.$ = $;
window.$$ = $$;
window.esc = esc;
