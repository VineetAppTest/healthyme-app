"""
WakeMe script for HealthyMe.

Pings deployed HealthyMe URL(s) to reduce idle sleep.
Uses only Python standard library.

Environment variable:
  WAKEME_URLS="https://your-app.streamlit.app"
or multiple:
  WAKEME_URLS="https://app1.streamlit.app,https://app2.streamlit.app"
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request
import urllib.error


def ping_url(url: str, timeout: int = 25) -> tuple[bool, str]:
    url = url.strip()
    if not url:
        return False, "Empty URL skipped."

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HealthyMe-WakeMe/1.0",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return True, f"{url} -> HTTP {getattr(response, 'status', None)}"
    except urllib.error.HTTPError as exc:
        # Any HTTP response means the endpoint was reached.
        return True, f"{url} -> HTTP {exc.code}"
    except Exception as exc:
        return False, f"{url} -> ERROR: {exc}"


def main() -> int:
    raw_urls = os.getenv("WAKEME_URLS", "").strip()

    if not raw_urls:
        print("WAKEME_URLS is not set. Nothing to ping.")
        print("Set GitHub secret or variable WAKEME_URLS to your deployed app URL.")
        return 0

    urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
    if not urls:
        print("No valid URL found in WAKEME_URLS.")
        return 0

    print(f"WakeMe started for {len(urls)} URL(s).")

    failures = 0
    for url in urls:
        ok = False
        for attempt in range(1, 4):
            ok, message = ping_url(url)
            print(f"Attempt {attempt}: {message}")
            if ok:
                break
            time.sleep(5)
        if not ok:
            failures += 1

    if failures:
        print(f"WakeMe completed with {failures} failed URL(s). Temporary delays are tolerated.")
        return 0

    print("WakeMe completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
