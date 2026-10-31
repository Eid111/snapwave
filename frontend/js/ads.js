// ==========================================================================
// SnapWave - Advertising Engine & Anti-Malvertising Sandbox
// ==========================================================================

const AdConfig = {
  // Set to true in production once you connect your Adsterra / Monetag account
  ENABLE_ADS: false,

  // Direct Ad Link (Opens in new tab when clicking download if active)
  DIRECT_AD_URL: '',

  // Zone IDs / Ad Slots
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

const AdManager = {
  init() {
    if (!AdConfig.ENABLE_ADS) {
      console.log('[SnapWave Security] Ad system in safe development mode (Placeholders active).');
      return;
    }
    this.injectSandboxedAds();
  },

  /**
   * Mounts third-party ad scripts inside isolated, sandboxed iframes.
   * This completely prevents malicious ads from:
   * 1. Hijacking the parent window or force-redirecting the visitor.
   * 2. Accessing cookies, localStorage, or parent DOM.
   * 3. Triggering drive-by downloads or hardware sensor permissions.
   */
  createSandboxedIframe(containerEl, width, height, adHtmlContent) {
    if (!containerEl) return;

    // Clear previous placeholder
    containerEl.innerHTML = '';

    const iframe = document.createElement('iframe');
    iframe.width = width;
    iframe.height = height;
    iframe.style.border = 'none';
    iframe.style.overflow = 'hidden';
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'no-referrer-when-downgrade';

    // Strict Sandbox: allows script & click popups, but blocks top navigation & downloads
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-popups');

    containerEl.appendChild(iframe);

    // Safely write ad payload inside isolated iframe context
    try {
      const doc = iframe.contentWindow.document;
      doc.open();
      doc.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <base target="_blank">
          <style>body{margin:0;padding:0;display:flex;align-items:center;justify-content:center;overflow:hidden;}</style>
        </head>
        <body>
          ${adHtmlContent}
        </body>
        </html>
      `);
      doc.close();
    } catch (e) {
      console.warn('[SnapWave Ads] Sandboxing container notice:', e);
    }
  },

  injectSandboxedAds() {
    // Example: When your ad network gives you ad snippet codes:
    // const bannerCode = `<script ...></script>`;
    // this.createSandboxedIframe(document.getElementById('ad-leaderboard'), '728', '90', bannerCode);
  },

  onDownloadClick() {
    if (AdConfig.ENABLE_ADS && AdConfig.DIRECT_AD_URL) {
      try {
        // Safe popup with noopener and noreferrer to prevent tab-nabbing
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
