"""Shared HTTP helper: throttling + exponential backoff for external APIs.

Every external call in the app goes through request_with_backoff so that a batch
of 20 businesses cannot machine-gun a free-tier endpoint. A per-host minimum
interval enforces basic client-side rate limiting.
"""
import threading
import time

import requests

# Minimum seconds between calls to the same host (client-side throttle).
_DEFAULT_MIN_INTERVAL = 0.6
_last_call = {}
_lock = threading.Lock()


def _throttle(host, min_interval):
    with _lock:
        now = time.monotonic()
        last = _last_call.get(host, 0.0)
        wait = min_interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()


def request_with_backoff(
    method,
    url,
    *,
    min_interval=_DEFAULT_MIN_INTERVAL,
    max_retries=3,
    timeout=20,
    **kwargs,
):
    """Perform an HTTP request with throttling and exponential backoff.

    Retries on 429, 5xx, and connection/timeout errors. Raises the final
    exception (or returns the final non-OK response) after exhausting retries.
    """
    host = url.split("/")[2] if "://" in url else url
    delay = 1.0
    last_exc = None
    for attempt in range(max_retries + 1):
        _throttle(host, min_interval)
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                retry_after = resp.headers.get("Retry-After")
                sleep_for = float(retry_after) if (retry_after and retry_after.isdigit()) else delay
                time.sleep(sleep_for)
                delay *= 2
                continue
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    if last_exc:
        raise last_exc
