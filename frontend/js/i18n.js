// ==========================================================================
// SnapWave - Localization Engine (i18n)
// ==========================================================================

const T = {
  en: {
    engine: 'v2.6 engine online',
    ad: 'Advertisement',
    h1: 'Media, in a snap.',
    sub: 'Paste your link. Choose your format. Download instantly.',
    label: 'Video link',
    paste: 'Paste',
    go: 'Get formats',
    hint: 'Paste a public link. Private or DRM-protected videos can’t be downloaded.',
    by: 'By',
    video: 'Video',
    audio: 'Audio',
    plat: 'Works with the links you already have',
    platSub: 'SnapWave reads the page, finds the media stream and hands it back in the format you choose.',
    s1t: 'Streamed, not stored',
    s1d: 'Media is streamed to your browser and isn’t kept on our servers.',
    s2t: 'Pick your format',
    s2d: 'See the formats and estimated sizes available for each link before you download.',
    s3t: 'No sign-up',
    s3d: 'Free to use, with no account and nothing to install.',
    faq: 'Questions',
    legal: 'Download only content you own or have permission to save.',
    empty: 'Paste a link first.',
    invalid: 'That doesn’t look like a web link. It should start with http:// or https://',
    pasted: 'Pasted from clipboard',
    denied: 'Clipboard access was blocked. Press Ctrl+V in the field instead.',
    fail: 'Couldn’t read that link. Check that the video is public and try again.',
    found: 'formats found',
    dl: 'Download',
    prep: 'Preparing',
    done: 'Saved',
    retry: 'Retry',
    started: 'Download started',
    stages: ['resolving host…', 'fetching manifest…', 'probing streams…', 'estimating sizes…'],
    faqs: [
      ['Do you store the videos I download?', 'No. The file is streamed to your browser and isn’t retained on our servers.'],
      ['Which quality should I pick?', '1080p MP4 plays everywhere. Choose 4K or 1440p only if your screen and storage can use them. For music or podcasts, pick Audio and 256 kbps or higher.'],
      ['Why do formats differ between links?', 'Available formats and qualities depend on the source. You’ll see what’s offered for each link before you download.'],
      ['Can I download m3u8 playlists?', 'Direct HLS (m3u8) links work when the stream isn’t DRM-protected. Availability depends on the source.']
    ]
  },
  ar: {
    engine: 'المحرك v2.6 متصل',
    ad: 'إعلان',
    h1: 'وسائطك، في لحظة.',
    sub: 'الصق الرابط. اختر الصيغة. حمّل فورًا.',
    label: 'رابط الفيديو',
    paste: 'لصق',
    go: 'عرض الصيغ',
    hint: 'الصق رابطًا عامًا. الفيديوهات الخاصة أو المحمية بـ DRM لا يمكن تحميلها.',
    by: 'بواسطة',
    video: 'فيديو',
    audio: 'صوت',
    plat: 'يعمل مع الروابط التي لديك بالفعل',
    platSub: 'يقرأ SnapWave الصفحة ويجد مسار الوسائط ويعيده إليك بالصيغة التي تختارها.',
    s1t: 'بثّ لا تخزين',
    s1d: 'يُبثّ الملف إلى متصفحك ولا يُحفظ على خوادمنا نهائياً.',
    s2t: 'اختر الصيغة',
    s2d: 'اعرض الصيغ والأحجام التقديرية المتاحة لكل رابط قبل التحميل.',
    s3t: 'بدون تسجيل',
    s3d: 'مجاني بدون حساب وبدون تثبيت أي برامج إضافية.',
    faq: 'أسئلة شائعة',
    legal: 'حمّل فقط المحتوى الذي تملكه أو لديك إذن بحفظه.',
    empty: 'الصق رابطًا أولًا.',
    invalid: 'هذا لا يبدو رابط ويب. يجب أن يبدأ بـ http:// أو https://',
    pasted: 'تم اللصق من الحافظة',
    denied: 'تم حظر الوصول إلى الحافظة. اضغط Ctrl+V داخل الحقل.',
    fail: 'تعذّرت قراءة الرابط. تأكد أن الفيديو عام وحاول مرة أخرى.',
    found: 'صيغة متاحة',
    dl: 'تحميل',
    prep: 'جارٍ التحضير',
    done: 'تم الحفظ',
    retry: 'إعادة',
    started: 'بدأ التحميل',
    stages: ['جارٍ تحديد المضيف…', 'جارٍ جلب القائمة…', 'جارٍ فحص المسارات…', 'جارٍ تقدير الأحجام…'],
    faqs: [
      ['هل تحتفظون بالفيديوهات التي أحمّلها؟', 'لا. يُبثّ الملف إلى متصفحك ولا يُحتفظ به على خوادمنا نهائياً.'],
      ['ما الجودة التي أختارها؟', 'صيغة 1080p MP4 تعمل على كل الأجهزة. اختر 4K أو 1440p فقط إذا كانت شاشتك ومساحتك تستفيد منها. للموسيقى والبودكاست اختر صوت بجودة 256 kbps أو أعلى.'],
      ['لماذا تختلف الصيغ من رابط لآخر؟', 'تعتمد الصيغ والجودات المتاحة على المصدر. سترى المتاح لكل رابط قبل التحميل.'],
      ['هل يمكن تحميل قوائم m3u8؟', 'تعمل روابط HLS (m3u8) المباشرة عندما لا يكون البث محميًا بـ DRM. وتعتمد الإتاحة على المصدر.']
    ]
  }
};

let currentLang = 'ar';

function t(key) {
  return T[currentLang][key] || key;
}

function getLang() {
  return currentLang;
}

function setLang(lang) {
  if (T[lang]) {
    currentLang = lang;
  }
}

window.I18n = { T, t, getLang, setLang };
