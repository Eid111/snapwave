# -*- coding: utf-8 -*-
"""
SnapWave - Public Online Launcher via Cloudflare Secure Edge
Zero Cost ($0) - No Credit Cards Required - Instant Public HTTPS
"""
import os
import re
import sys
import time
import subprocess
import webbrowser
import urllib.request

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(WORKSPACE_DIR, "cloudflared.exe")
PYTHON_EXE = sys.executable

def p(text="", **kwargs):
    print(text, flush=True, **kwargs)

def print_banner():
    p("=" * 65)
    p("       ⚡ SNAPWAVE - تشغيل الموقع أونلاين للعلن ⚡")
    p("       مجاني 100% | حماية سحابية HTTPS | بدون كروت بنكية")
    p("=" * 65)

def wait_for_backend(timeout=15):
    p("[1/3] 🚀 جاري إطلاق خادم SnapWave السريع...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health", timeout=2) as resp:
                if resp.status == 200:
                    p("  [✓] الخادم المحلي جاهز ويعمل بنجاح على المنفذ 8000.")
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print_banner()

    if not os.path.exists(CLOUDFLARED_EXE):
        p(f"[!] خطأ: أداة cloudflared.exe غير موجودة في: {CLOUDFLARED_EXE}")
        input("اضغط Enter للخروج...")
        return

    # 1. Start Uvicorn process
    server_cmd = [
        PYTHON_EXE, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=WORKSPACE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        if not wait_for_backend():
            p("[!] فشل بدء الخادم المحلي. يرجى التحقق من توفر المنفذ 8000.")
            return

        # 2. Start Cloudflare Tunnel
        p("[2/3] 🌐 جاري إنشاء نفق سحابي مشفر عبر شبكة Cloudflare...")
        tunnel_cmd = [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:8000"]
        tunnel_proc = subprocess.Popen(
            tunnel_cmd,
            cwd=WORKSPACE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        public_url = None
        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

        start_tunnel_wait = time.time()
        for line in tunnel_proc.stdout:
            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                break
            if time.time() - start_tunnel_wait > 30:
                break

        if not public_url:
            p("[!] تعذر الحصول على الرابط السحابي في الوقت المحدد.")
            return

        p("[3/3] 🎉 تم إطلاق موقعك بنجاح على الإنترنت!")
        p("-" * 65)
        p("🔗 رابط موقعك المباشر للجمهور (مشفر بـ HTTPS):")
        p(f"👉 {public_url}")
        p()
        p("⚙️ لوحة تحكم الإدارة (Admin Dashboard):")
        p(f"👉 {public_url}/admin")
        p("-" * 65)
        p("💡 ملاحظات هامة:")
        p("  • الرابط شغال عالمياً من أي موبايل أو لابتوب في أي مكان بالعالم.")
        p("  • لإنهاء تشغيل الموقع وإيقافه، اضغط Ctrl + C أو أغلق هذه النافذة.")
        p("=" * 65)

        # Automatically open in browser
        try:
            webbrowser.open(public_url)
        except Exception:
            pass

        # Keep alive
        tunnel_proc.wait()

    except KeyboardInterrupt:
        p("\n[i] جاري إيقاف الخادم والنفق السحابي بنجاح...")
    finally:
        try:
            server_proc.terminate()
            server_proc.wait(timeout=3)
        except Exception:
            pass
        try:
            tunnel_proc.terminate()
            tunnel_proc.wait(timeout=3)
        except Exception:
            pass
        p("[✓] تم إيقاف الموقع بنجاح. مع السلامة!")

if __name__ == "__main__":
    main()
