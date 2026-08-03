from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


BASE_URL = os.getenv(
    "HEALTHYME_PRODUCTION_URL",
    "https://healthymeappbyankita.streamlit.app",
).rstrip("/")
EVIDENCE_PATH = Path(
    os.getenv(
        "HEALTHYME_SMOKE_EVIDENCE_PATH",
        "artifacts/production_entry_smoke.json",
    )
)
ENDPOINTS = ("/", "/Login")
MAX_ATTEMPTS = 6
RETRY_SECONDS = 10
TIMEOUT_SECONDS = 30

TRANSIENT_MARKERS = (
    "this app has gone to sleep",
    "this app is in sleep mode",
    "wake up",
    "please wait while the app wakes",
)
FATAL_MARKERS = (
    "this app does not exist",
    "repository not found",
    "404: not found",
)
SHELL_MARKERS = (
    "streamlit",
    "_stcore",
    "data-testid",
)


def _probe(path: str) -> dict[str, Any]:
    url = urljoin(f"{BASE_URL}/", path.lstrip("/"))
    attempts: list[dict[str, Any]] = []
    final: dict[str, Any] = {
        "path": path,
        "requested_url": url,
        "ok": False,
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.monotonic()
        try:
            response = requests.get(
                url,
                timeout=TIMEOUT_SECONDS,
                allow_redirects=True,
                headers={
                    "User-Agent": (
                        "HealthyMe-Production-Acceptance/1.0 "
                        "(+github-actions)"
                    )
                },
            )
            elapsed_ms = round((time.monotonic() - started) * 1000)
            body = response.text or ""
            lowered = body.lower()
            transient = [marker for marker in TRANSIENT_MARKERS if marker in lowered]
            fatal = [marker for marker in FATAL_MARKERS if marker in lowered]
            shell = [marker for marker in SHELL_MARKERS if marker in lowered]
            attempt_record = {
                "attempt": attempt,
                "status_code": response.status_code,
                "final_url": response.url,
                "elapsed_ms": elapsed_ms,
                "content_length": len(body),
                "sha256_16": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
                "transient_markers": transient,
                "fatal_markers": fatal,
                "shell_markers": shell,
            }
            attempts.append(attempt_record)

            healthy_status = 200 <= response.status_code < 400
            usable_shell = bool(shell) or len(body) >= 500
            ok = healthy_status and usable_shell and not transient and not fatal
            final.update(attempt_record)
            final["ok"] = ok
            if ok:
                break
        except requests.RequestException as exc:
            attempts.append(
                {
                    "attempt": attempt,
                    "error": f"{type(exc).__name__}: {exc}",
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                }
            )
            final.update(attempts[-1])

        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_SECONDS)

    final["attempts"] = attempts
    return final


def main() -> int:
    evidence = {
        "base_url": BASE_URL,
        "purpose": "Unauthenticated production entry acceptance",
        "scope": [
            "deployed hostname resolves from GitHub Actions",
            "root route responds without a fatal Streamlit error",
            "/Login responds without a fatal Streamlit error",
        ],
        "out_of_scope": [
            "authenticated Admin workflow",
            "authenticated Member workflow",
            "business-data mutation",
        ],
        "results": [_probe(path) for path in ENDPOINTS],
    }
    evidence["ok"] = all(result.get("ok") for result in evidence["results"])

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
