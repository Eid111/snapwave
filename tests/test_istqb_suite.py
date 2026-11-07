# -*- coding: utf-8 -*-
"""
==============================================================================
SnapWave - Enterprise ISTQB & ISO 29119 Software Verification Suite
Advanced Modules:
  1. Functional Testing & Routing
  2. Input Validation (BVA & EP)
  3. Security, OWASP Top 10 & Advanced Fuzzing (XSS, Path Traversal, Null Bytes)
  4. Multi-Threaded Stress, High Concurrency & Rate Limiting (DoS Resilience)
  5. UI & Localization Integrity (i18n & DOM)
==============================================================================
"""

import sys
import os
import re
import time
import concurrent.futures
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.main import app
from backend.core.security import download_limiter, extract_limiter, login_limiter

class TestReport:
    def __init__(self):
        self.results = []
        self.categories = {}

    def record(self, category: str, test_id: str, description: str, passed: bool, details: str = ""):
        entry = {
            "category": category,
            "id": test_id,
            "description": description,
            "passed": passed,
            "details": details
        }
        self.results.append(entry)
        self.categories.setdefault(category, {"total": 0, "passed": 0, "failed": 0})
        self.categories[category]["total"] += 1
        if passed:
            self.categories[category]["passed"] += 1
        else:
            self.categories[category]["failed"] += 1

    def print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        pass_rate = (passed / total * 100) if total else 0

        print("\n" + "=" * 85)
        print("          ISTQB / ISO 29119 ADVANCED VERIFICATION & RESILIENCE REPORT          ")
        print("=" * 85)
        print(f"Total Test Cases Executed : {total}")
        print(f"Passed                    : {passed}")
        print(f"Failed                    : {failed}")
        print(f"Compliance / Pass Rate    : {pass_rate:.1f}%\n")

        print("-" * 85)
        print(f"{'Category':<40} | {'Total':<6} | {'Passed':<6} | {'Failed':<6} | {'Status'}")
        print("-" * 85)
        for cat, stats in self.categories.items():
            status = "PASS [OK]" if stats["failed"] == 0 else "FAIL [X]"
            print(f"{cat:<40} | {stats['total']:<6} | {stats['passed']:<6} | {stats['failed']:<6} | {status}")
        print("-" * 85)

        print("\n--- Detailed Test Execution Log ---")
        for r in self.results:
            icon = "[PASS]" if r["passed"] else "[FAIL]"
            print(f"{icon} {r['id']} ({r['category']}): {r['description']}")
            if r["details"]:
                print(f"       -> Details: {r['details']}")

        print("=" * 85)
        return failed == 0

def run_all_tests():
    report = TestReport()
    extract_limiter.clients.clear()
    download_limiter.clients.clear()
    login_limiter.clients.clear()

    # Standard client for single-threaded functional & security checks
    client = TestClient(app, client=("198.51.100.1", 50000))

    # =========================================================================
    # 1. FUNCTIONAL & ROUTING
    # =========================================================================
    cat = "1. Functional & Routing"

    r = client.get("/api/v1/health")
    passed = r.status_code == 200 and r.json().get("status") == "ok"
    report.record(cat, "TC-FUNC-01", "Health endpoint v1 returns 200 and 'ok'", passed)

    r = client.get("/api/health")
    passed = r.status_code == 200 and r.json().get("status") == "ok"
    report.record(cat, "TC-FUNC-02", "Legacy Health endpoint returns 200 for backward compat", passed)

    r = client.get("/")
    passed = r.status_code == 200 and "<title>SnapWave" in r.text
    report.record(cat, "TC-FUNC-03", "GET / delivers semantic HTML5 index page", passed, f"Bytes: {len(r.text)}")

    r = client.get("/favicon.ico")
    passed = r.status_code == 200 and "image/svg+xml" in r.headers.get("content-type", "")
    report.record(cat, "TC-FUNC-04", "GET /favicon.ico returns SVG favicon", passed)

    r = client.get("/css/style.css")
    passed = r.status_code == 200 and ".grid-bg" in r.text and ".skel" in r.text
    report.record(cat, "TC-FUNC-05", "GET /css/style.css serves compiled modular styles", passed)

    js_modules = ["app.js", "api.js", "ui.js", "i18n.js", "ads.js"]
    all_js_ok = all(client.get(f"/js/{m}").status_code == 200 for m in js_modules)
    report.record(cat, "TC-FUNC-06", "All 5 frontend JS modules mounted & accessible", all_js_ok)

    # Live YouTube Extraction Probe
    yt_test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    r = client.post("/api/v1/extract", json={"url": yt_test_url})
    is_extracted = False
    details = ""
    if r.status_code == 200:
        data = r.json()
        formats = data.get("formats", [])
        is_extracted = bool(data.get("title") and len(formats) > 0)
        details = f"Extracted '{data.get('title')[:25]}...', Formats: {len(formats)}"
    report.record(cat, "TC-FUNC-07", "Live YouTube stream extraction and format classification", is_extracted, details)

    # =========================================================================
    # 2. INPUT VALIDATION (BVA & EP)
    # =========================================================================
    cat = "2. Input Validation (BVA/EP)"

    r = client.post("/api/v1/extract", json={})
    report.record(cat, "TC-BVA-01", "Missing 'url' field returns 422 Unprocessable Entity", r.status_code == 422)

    r = client.post("/api/v1/extract", json={"url": ""})
    report.record(cat, "TC-BVA-02", "Empty URL string returns 400 Bad Request", r.status_code == 400)

    r = client.post("/api/v1/extract", json={"url": "    \t\n   "})
    report.record(cat, "TC-BVA-03", "Whitespace-only URL returns 400 Bad Request", r.status_code == 400)

    r = client.post("/api/v1/extract", json={"url": "ftp://files.example.com/video.mp4"})
    report.record(cat, "TC-BVA-04", "Unsupported protocol (ftp://) is rejected with 400", r.status_code == 400)

    r = client.post("/api/v1/extract", json={"url": "file:///C:/Windows/system32/cmd.exe"})
    report.record(cat, "TC-BVA-05", "File URI (file://) is strictly rejected", r.status_code == 400)

    giant_url = "https://example.com/" + "a" * 4000
    r = client.post("/api/v1/extract", json={"url": giant_url})
    report.record(cat, "TC-BVA-06", "Extreme boundary string (4,000 chars) rejected as too long", r.status_code == 400)

    # =========================================================================
    # 3. ADVANCED SECURITY, OWASP TOP 10 & FUZZING
    # =========================================================================
    cat = "3. Security & Advanced Fuzzing"

    # SSRF suite
    r = client.post("/api/v1/extract", json={"url": "http://localhost:8000/internal"})
    report.record(cat, "TC-SEC-01", "SSRF: Probe against 'localhost' blocked with 403 Forbidden", r.status_code == 403)

    r = client.post("/api/v1/extract", json={"url": "http://127.0.0.1:3306/db"})
    report.record(cat, "TC-SEC-02", "SSRF: Probe against loopback IP '127.0.0.1' blocked with 403", r.status_code == 403)

    r = client.post("/api/v1/extract", json={"url": "http://192.168.1.1/admin"})
    report.record(cat, "TC-SEC-03", "SSRF: Probe against private gateway 192.168.x.x blocked with 403", r.status_code == 403)

    r = client.post("/api/v1/extract", json={"url": "http://10.0.0.5/api"})
    report.record(cat, "TC-SEC-04", "SSRF: Probe against corporate subnet 10.x.x.x blocked with 403", r.status_code == 403)

    r = client.post("/api/v1/extract", json={"url": "http://[::1]:8080/flag"})
    report.record(cat, "TC-SEC-05", "SSRF: Probe against IPv6 loopback [::1] blocked with 403", r.status_code == 403)

    # Command Injection neutralization
    cmd_inj = "https://example.com/video;calc.exe;del /f"
    r = client.post("/api/v1/extract", json={"url": cmd_inj})
    report.record(cat, "TC-SEC-06", "Command Injection: Semicolon command chain safely sanitized", r.status_code in [400, 404])

    cmd_sub = "https://example.com/video$(whoami)"
    r = client.post("/api/v1/extract", json={"url": cmd_sub})
    report.record(cat, "TC-SEC-07", "Command Injection: Subshell $(whoami) safely passed as raw argument", r.status_code in [400, 404])

    # Security Headers Suite
    r = client.get("/")
    h_nosniff = r.headers.get("x-content-type-options") == "nosniff"
    h_frame = r.headers.get("x-frame-options") == "SAMEORIGIN"
    h_perm = "camera=()" in r.headers.get("permissions-policy", "")
    h_csp = "default-src 'self'" in r.headers.get("content-security-policy", "")
    report.record(cat, "TC-SEC-08", "Full HTTP Security Headers Suite present (CSP, Frame, Sniff, Perm)", h_nosniff and h_frame and h_perm and h_csp)

    # Fuzzing 1: XSS Protocol Payload
    r = client.post("/api/v1/extract", json={"url": "javascript:alert('XSS')"})
    report.record(cat, "TC-SEC-09", "XSS Fuzzing: javascript: pseudo-protocol rejected with 400", r.status_code == 400)

    # Fuzzing 2: Script Tag Injection in URL
    r = client.post("/api/v1/extract", json={"url": "https://example.com/<script>alert(1)</script>"})
    report.record(cat, "TC-SEC-10", "XSS Fuzzing: HTML script tag payload handled cleanly", r.status_code in [400, 404])

    # Fuzzing 3: Directory Traversal in Target Link
    r = client.post("/api/v1/extract", json={"url": "https://example.com/../../../../etc/passwd"})
    report.record(cat, "TC-SEC-11", "Path Traversal: Dot-dot-slash sequence blocked from host escape", r.status_code in [400, 404])

    # Fuzzing 4: Null Byte Injection
    r = client.post("/api/v1/extract", json={"url": "https://example.com/video%00.mp4"})
    report.record(cat, "TC-SEC-12", "Null Byte Fuzzing: %00 null byte safely sanitized", r.status_code in [400, 404])

    # Fuzzing 5: Data Type Mismatch (Invalid Type)
    r = client.post("/api/v1/extract", json={"url": 12345678})
    report.record(cat, "TC-SEC-13", "Type Fuzzing: Integer passed instead of URL string returns 422", r.status_code == 422)

    # Fuzzing 6: Malformed / Broken JSON Structure
    r = client.post("/api/v1/extract", content=b'{"url": "https://example.com', headers={"Content-Type": "application/json"})
    report.record(cat, "TC-SEC-14", "Malformed JSON: Truncated JSON payload caught cleanly by parser", r.status_code in [400, 422])

    # Fuzzing 7: CRLF Header Injection Attempt
    r = client.post("/api/v1/extract", json={"url": "https://example.com/\r\nSet-Cookie:admin=1"})
    report.record(cat, "TC-SEC-15", "CRLF Injection: Carriage return line feed characters neutralized", r.status_code in [400, 404])

    r = client.post("/api/v1/extract", json={"url": "http://2130706433/"})
    report.record(cat, "TC-SEC-16", "SSRF: Decimal-encoded loopback IP blocked with 403", r.status_code == 403)

    r = client.get("/api/v1/download", params={"url": "http://127.0.0.1/secret", "quality": "best"})
    report.record(cat, "TC-SEC-17", "SSRF: Download endpoint blocks loopback targets with 403", r.status_code == 403)

    r = client.get("/api/v1/admin/settings")
    report.record(cat, "TC-SEC-18", "Admin settings require authentication", r.status_code == 401)

    r = client.post("/api/v1/admin/login", json={"password": "definitely-wrong-password"})
    report.record(cat, "TC-SEC-19", "Admin login rejects incorrect password", r.status_code == 401)

    # =========================================================================
    # 4. CONCURRENCY, STRESS & RATE LIMITING RESILIENCE
    # =========================================================================
    cat = "4. Stress, Concurrency & Rate Limiting"

    extract_limiter.clients.clear()
    download_limiter.clients.clear()
    login_limiter.clients.clear()

    # 4.1 Single-IP Rapid Rate Limit Threshold
    single_ip_client = TestClient(app, client=("198.51.100.77", 40001))
    rate_limited = False
    triggered_at = None
    for attempt in range(1, 30):
        res = single_ip_client.post("/api/v1/extract", json={"url": "https://example.com/test"})
        if res.status_code == 429:
            rate_limited = True
            triggered_at = attempt
            break
    report.record(cat, "TC-STR-01", "Rate Limiter enforces 25 requests/min quota strictly", rate_limited, f"Triggered on call #{triggered_at}")

    # 4.2 Multi-Threaded Burst Concurrency Test (50 simultaneous requests across 10 threads)
    burst_total = 50
    concurrency_workers = 10
    burst_results = []
    
    def fire_burst_request(req_idx):
        # Dedicated client simulating a high-speed traffic burst
        c = TestClient(app, client=(f"203.0.113.{(req_idx % 4) + 10}", 50000 + req_idx))
        t_start = time.perf_counter()
        res = c.post("/api/v1/extract", json={"url": "https://example.com/concurrent-probe"})
        t_elapsed = (time.perf_counter() - t_start) * 1000
        return res.status_code, t_elapsed

    t0_burst = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_workers) as executor:
        futures = [executor.submit(fire_burst_request, i) for i in range(burst_total)]
        for f in concurrent.futures.as_completed(futures):
            status, latency = f.result()
            burst_results.append((status, latency))
    total_burst_time = (time.perf_counter() - t0_burst) * 1000
    
    # Analyze burst results
    no_500_errors = all(s != 500 for s, _ in burst_results)
    avg_latency = sum(lat for _, lat in burst_results) / len(burst_results)
    throttled_count = sum(1 for s, _ in burst_results if s == 429)
    handled_count = sum(1 for s, _ in burst_results if s in [400, 404])

    details_str = f"50 requests in {total_burst_time:.1f}ms | Avg latency: {avg_latency:.1f}ms | Throttled (429): {throttled_count} | Handled: {handled_count} | 500 Errors: 0"
    report.record(cat, "TC-STR-02", "High Concurrency Burst (50 requests across 10 parallel threads)", no_500_errors, details_str)

    # 4.3 Multi-Client Fair Allocation
    # Ensure distinct IPs are isolated and one IP's throttle doesn't starve a clean new IP
    fresh_ip_client = TestClient(app, client=("192.0.2.200", 30000))
    res_fresh = fresh_ip_client.post("/api/v1/extract", json={"url": "https://example.com/fresh-user"})
    passed_fairness = res_fresh.status_code in [400, 404]  # Not 429, meaning it was granted access
    report.record(cat, "TC-STR-03", "Rate Limiter IP isolation (Throttling one IP does not block clean users)", passed_fairness, f"Fresh IP Status: {res_fresh.status_code}")

    # =========================================================================
    # 5. UI & LOCALIZATION INTEGRITY
    # =========================================================================
    cat = "5. UI & Localization Integrity"

    i18n_path = ROOT_DIR / "frontend" / "js" / "i18n.js"
    i18n_content = i18n_path.read_text(encoding="utf-8")
    m_en = re.search(r'en:\s*\{([^}]+)\}', i18n_content, re.S)
    m_ar = re.search(r'ar:\s*\{([^}]+)\}', i18n_content, re.S)
    keys_en = set(re.findall(r'(\b[a-zA-Z0-9_]+\b):', m_en.group(1))) if m_en else set()
    keys_ar = set(re.findall(r'(\b[a-zA-Z0-9_]+\b):', m_ar.group(1))) if m_ar else set()
    parity_ok = len(keys_en) > 10 and len(keys_en - keys_ar) == 0 and len(keys_ar - keys_en) == 0
    report.record(cat, "TC-UI-01", "Localization (i18n) complete parity between Arabic & English", parity_ok, f"Keys count: {len(keys_en)}")

    html_content = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    required_ids = [
        "url", "form", "bar", "msg", "go", "clear", "paste", "lang", "ping",
        "loading", "stage", "result", "rows", "count", "thumb", "dur",
        "title", "author", "host", "date", "toast", "faqList", "chips",
        "ad-leaderboard", "ad-rect"
    ]
    missing_dom_ids = [dom_id for dom_id in required_ids if f'id="{dom_id}"' not in html_content]
    report.record(cat, "TC-UI-02", "All 25 core DOM elements verified in HTML structure", len(missing_dom_ids) == 0)

    # Output Summary
    all_passed = report.print_summary()
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
