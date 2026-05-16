"""
HealthyMe WakeMe local/manual tester.

Usage:
  set WAKEME_URLS=https://your-app.streamlit.app
  python scripts/wakeme.py

This mirrors the GitHub workflow logic closely.
"""

from __future__ import annotations

import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error


def add_cache_buster(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("wakeme", str(int(time.time()))))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def ping(url: str, timeout: int = 30) -> tuple[bool, str]:
    target = add_cache_buster(url)
    req = urllib.request.Request(
        target,
        headers={
            "User-Agent": "HealthyMe-WakeMe/3.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            elapsed = round(time.time() - started, 2)
            return True, f"HTTP {getattr(response, 'status', None)} in {elapsed}s"
    except urllib.error.HTTPError as exc:
        elapsed = round(time.time() - started, 2)
        return True, f"HTTP {exc.code} in {elapsed}s"
    except Exception as exc:
        elapsed = round(time.time() - started, 2)
        return False, f"ERROR after {elapsed}s: {exc}"


def main() -> int:
    raw = os.getenv("WAKEME_URLS", "").strip()
    if not raw:
        print("ERROR: WAKEME_URLS is not set.")
        return 0

    urls = [u.strip() for u in raw.split(",") if u.strip()]
    failures = 0

    for url in urls:
        print(f"Target: {url}")
        ok = False
        for attempt in range(1, 6):
            ok, msg = ping(url)
            print(f"Attempt {attempt}/5: {msg}")
            if ok:
                break
            time.sleep(min(5 * attempt, 20))
        if not ok:
            failures += 1

    print("WakeMe completed." if not failures else f"WakeMe completed with {failures} failed target(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
