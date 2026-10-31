# -*- coding: utf-8 -*-
import time
import ipaddress
import urllib.parse
from collections import defaultdict
from fastapi import HTTPException, Request

# ==============================================================================
# SSRF Protection: Prevent querying local, loopback, or private networks
# ==============================================================================

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}

def validate_public_url(raw_url: str) -> str:
    """
    Validates that a URL is a legitimate public web address and prevents SSRF attacks.
    """
    url = raw_url.strip().strip('"').strip("'")
    
    # Enforce safe web protocols only
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid link protocol. Only http:// and https:// links are supported."
        )

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed URL structure.")

    if not hostname:
        raise HTTPException(status_code=400, detail="Missing hostname in link.")

    # Check against known local hostnames
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        raise HTTPException(
            status_code=403,
            detail="Access to local or internal network targets is strictly forbidden."
        )

    # Check if the hostname resolves to a private IP
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise HTTPException(
                status_code=403,
                detail="Access to private or reserved IP ranges is prohibited."
            )
    except ValueError:
        # Hostname is a domain name (e.g., youtube.com), which is normal
        pass

    return url


# ==============================================================================
# Lightweight In-Memory Rate Limiter (Anti-Flood / Anti-DDoS)
# ==============================================================================

class SimpleRateLimiter:
    """
    Tracks request timestamps per client IP.
    Allows up to `max_requests` per `window_seconds`.
    """
    def __init__(self, max_requests: int = 25, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)

    def check_rate_limit(self, client_ip: str):
        now = time.time()
        timestamps = self.clients[client_ip]

        # Prune old timestamps
        self.clients[client_ip] = [t for t in timestamps if now - t < self.window_seconds]

        if len(self.clients[client_ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.clients[client_ip][0]))
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached. Too many requests. Please wait {max(retry_after, 1)} seconds."
            )

        self.clients[client_ip].append(now)

# Global limiter instance: 25 requests per minute per IP
extract_limiter = SimpleRateLimiter(max_requests=25, window_seconds=60)
