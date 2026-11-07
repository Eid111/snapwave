# -*- coding: utf-8 -*-
import ipaddress
import socket
import threading
import time
import urllib.parse
from collections import defaultdict
from typing import Optional

import requests
from fastapi import HTTPException, Request
from requests.adapters import HTTPAdapter

from backend.core.config import TRUST_PROXY

MAX_URL_LENGTH = 2048
BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::1]",
    "metadata.google.internal",
    "metadata.google.com",
    "169.254.169.254",
    "metadata",
}


def get_client_ip(request: Request) -> str:
    if TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip() or "0.0.0.0"
    return request.client.host if request.client else "127.0.0.1"


def _parse_ip(hostname: str):
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        pass
    if hostname.isdigit():
        try:
            return ipaddress.IPv4Address(int(hostname))
        except (ValueError, OverflowError):
            return None
    return None


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        return _is_blocked_ip(ip.ipv4_mapped)
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_reserved
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return True
    return str(ip) in {"169.254.169.254", "fd00:ec2::254"}


def validate_public_url(raw_url: Optional[str]) -> str:
    """Reject non-web protocols, oversized links, and private/metadata targets."""
    if raw_url is None:
        raise HTTPException(status_code=400, detail="Missing link.")

    url = str(raw_url).strip().strip('"').strip("'")
    if not url:
        raise HTTPException(status_code=400, detail="Empty link.")
    if len(url) > MAX_URL_LENGTH:
        raise HTTPException(status_code=400, detail="Link is too long.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid link protocol. Only http:// and https:// links are supported.",
        )

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed URL structure.")

    if not hostname:
        raise HTTPException(status_code=400, detail="Missing hostname in link.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URLs with embedded credentials are not allowed.")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        raise HTTPException(
            status_code=403,
            detail="Access to local or internal network targets is strictly forbidden.",
        )

    ip = _parse_ip(hostname)
    if ip is not None:
        if _is_blocked_ip(ip):
            raise HTTPException(
                status_code=403,
                detail="Access to private or reserved IP ranges is prohibited.",
            )
        return url

    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Hostname could not be resolved.")
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed URL structure.")

    if not infos:
        raise HTTPException(status_code=400, detail="Hostname could not be resolved.")

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except (ValueError, IndexError):
            continue
        if _is_blocked_ip(ip):
            raise HTTPException(
                status_code=403,
                detail="Access to private or reserved IP ranges is prohibited.",
            )

    return url


def _resolve_public_address(hostname: str) -> str:
    ip = _parse_ip(hostname)
    if ip is not None:
        if _is_blocked_ip(ip):
            raise requests.exceptions.InvalidURL("Private or reserved address is not allowed.")
        return str(ip)

    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise requests.exceptions.ConnectionError("Hostname could not be resolved.") from exc

    addresses = []
    for info in infos:
        try:
            address = ipaddress.ip_address(info[4][0])
        except (ValueError, IndexError):
            continue
        if _is_blocked_ip(address):
            raise requests.exceptions.InvalidURL(
                "Private or reserved address is not allowed."
            )
        addresses.append(str(address))
    if not addresses:
        raise requests.exceptions.ConnectionError("Hostname could not be resolved.")
    return addresses[0]


class _PinnedAddressAdapter(HTTPAdapter):
    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        if proxies:
            raise requests.exceptions.InvalidURL("Proxy connections are not allowed.")
        parsed = urllib.parse.urlsplit(request.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise requests.exceptions.InvalidURL("Invalid web URL.")

        address = _resolve_public_address(parsed.hostname)
        host_params, pool_kwargs = self.build_connection_pool_key_attributes(
            request, verify, cert
        )
        host_params["host"] = address
        if parsed.scheme == "https":
            pool_kwargs["assert_hostname"] = parsed.hostname
            pool_kwargs["server_hostname"] = parsed.hostname
        return self.poolmanager.connection_from_host(
            **host_params, pool_kwargs=pool_kwargs
        )

    def get_connection(self, url, proxies=None):
        if proxies:
            raise requests.exceptions.InvalidURL("Proxy connections are not allowed.")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise requests.exceptions.InvalidURL("Invalid web URL.")

        address = _resolve_public_address(parsed.hostname)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pool_kwargs = {}
        if parsed.scheme == "https":
            pool_kwargs = {
                "assert_hostname": parsed.hostname,
                "server_hostname": parsed.hostname,
            }
        return self.poolmanager.connection_from_host(
            host=address,
            port=port,
            scheme=parsed.scheme,
            pool_kwargs=pool_kwargs,
        )


def request_public_url(
    method: str, raw_url: str, *, follow_redirects: bool = True, **kwargs
) -> requests.Response:
    """Make a web request while validating each URL before following redirects."""
    url = validate_public_url(raw_url)
    with requests.Session() as session:
        session.trust_env = False
        session.mount("http://", _PinnedAddressAdapter())
        session.mount("https://", _PinnedAddressAdapter())
        for redirect_count in range(6):
            response = session.request(
                method, url, allow_redirects=False, **kwargs
            )
            if (
                not follow_redirects
                or response.status_code not in {301, 302, 303, 307, 308}
            ):
                return response

            location = response.headers.get("Location")
            if not location:
                return response
            response.close()
            if redirect_count == 5:
                raise requests.TooManyRedirects("Too many redirects.")

            url = validate_public_url(urllib.parse.urljoin(url, location))
    raise requests.TooManyRedirects("Too many redirects.")


class SimpleRateLimiter:
    def __init__(self, max_requests: int = 25, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_unlocked(self, now: float) -> None:
        stale = [
            ip
            for ip, stamps in self.clients.items()
            if not stamps or now - stamps[-1] >= self.window_seconds
        ]
        for ip in stale:
            self.clients.pop(ip, None)
        self._last_cleanup = now

    def check_rate_limit(self, client_ip: str) -> None:
        now = time.time()
        with self._lock:
            stamps = [t for t in self.clients[client_ip] if now - t < self.window_seconds]
            if len(stamps) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - stamps[0]))
                self.clients[client_ip] = stamps
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit reached. Too many requests. Please wait {max(retry_after, 1)} seconds.",
                )
            stamps.append(now)
            self.clients[client_ip] = stamps
            if now - self._last_cleanup > 60 or len(self.clients) > 8000:
                self._cleanup_unlocked(now)


extract_limiter = SimpleRateLimiter(max_requests=25, window_seconds=60)
download_limiter = SimpleRateLimiter(max_requests=8, window_seconds=60)
login_limiter = SimpleRateLimiter(max_requests=8, window_seconds=900)
