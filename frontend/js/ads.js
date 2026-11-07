// ==========================================================================
// SnapWave - Advertising Engine & Anti-Malvertising Sandbox
// ==========================================================================

const AdConfig = {
  ENABLE_ADS: false,
  DIRECT_AD_URL: '',
  slots: {
    leaderboard: {
      id: 'ad-leaderboard',
      format: '728x90',
      width: '728',
      height: '90',
      active: true
    },
    rectangle: {
      id: 'ad-rect',
      format: '300x250',
      width: '300',
      height: '250',
      active: true
    }
  }
};

function isSafeHttpUrl(value) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

const AdManager = {
  init() {
    if (!AdConfig.ENABLE_ADS) {
      return;
    }
    this.injectSandboxedAds();
  },

  createSandboxedIframe(containerEl, width, height, adHtmlContent) {
    if (!containerEl) return;
    containerEl.innerHTML = '';

    const iframe = document.createElement('iframe');
    iframe.width = width;
    iframe.height = height;
    iframe.style.border = 'none';
    iframe.style.overflow = 'hidden';
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'no-referrer';
    iframe.setAttribute('sandbox', 'allow-scripts allow-popups allow-popups-to-escape-sandbox');
    iframe.srcdoc = `<!DOCTYPE html><html><head><base target="_blank"><style>body{margin:0;padding:0;display:flex;align-items:center;justify-content:center;overflow:hidden;}</style></head><body>${adHtmlContent}</body></html>`;
    containerEl.appendChild(iframe);
  },

  injectSandboxedAds() {
    // Insert network snippets via createSandboxedIframe when ads are enabled.
  },

  onDownloadClick() {
    if (AdConfig.ENABLE_ADS && isSafeHttpUrl(AdConfig.DIRECT_AD_URL)) {
      try {
        const win = window.open(AdConfig.DIRECT_AD_URL, '_blank', 'noopener,noreferrer');
        if (win) win.opener = null;
      } catch (e) {
        console.warn('[SnapWave Ads] Popunder was blocked by browser security.', e);
      }
    }
  }
};

window.AdManager = AdManager;
window.AdConfig = AdConfig;
window.isSafeHttpUrl = isSafeHttpUrl;
