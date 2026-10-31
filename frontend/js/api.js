// ==========================================================================
// SnapWave - API Client Layer
// ==========================================================================

const API_BASE = '/api/v1';

const Api = {
  /**
   * Health ping to check extraction engine status and measure latency.
   */
  async ping() {
    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error('Health check failed');
      const data = await res.json();
      const latency = Math.round(performance.now() - t0);
      return { ok: true, latency, data };
    } catch (e) {
      return { ok: false, latency: 19, error: e };
    }
  },

  /**
   * Inspect and extract formats for a given URL.
   */
  async extract(link) {
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url: link })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'تعذر استخراج بيانات الفيديو من الرابط');
    }
    return data;
  },

  /**
   * Builds the stream download URL with query parameters.
   */
  buildDownloadUrl(fmtId, targetUrl, title, referer) {
    const params = new URLSearchParams({
      url: targetUrl,
      quality: fmtId,
      title: title || 'video',
      referer: referer || ''
    });
    return `${API_BASE}/download?${params.toString()}`;
  }
};

window.Api = Api;
