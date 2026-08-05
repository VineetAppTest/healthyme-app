import asyncio
import gzip
from importlib.metadata import version
from pathlib import Path

from streamlit.web.server.starlette.starlette_gzip_middleware import (
    MediaAwareGZipMiddleware,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT_FILES = (
    ROOT / "requirements.txt",
    ROOT / "production_cutover" / "requirements.txt",
)
EXPECTED_STARLETTE_PIN = "starlette==1.3.1"


def test_all_deployment_requirements_pin_the_verified_starlette_release():
    for requirement_file in REQUIREMENT_FILES:
        requirements = requirement_file.read_text(encoding="utf-8").splitlines()
        assert EXPECTED_STARLETTE_PIN in requirements

    assert version("starlette") == "1.3.1"


def test_streamlit_media_aware_gzip_handles_a_real_response():
    body = b"healthyme-gzip-regression-contract" * 64
    messages = []

    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    middleware = MediaAwareGZipMiddleware(app, minimum_size=500)
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/_stcore/health",
        "headers": [(b"accept-encoding", b"gzip")],
    }
    asyncio.run(middleware(scope, receive, send))

    start, response = messages
    headers = dict(start["headers"])
    assert headers[b"content-encoding"] == b"gzip"
    assert gzip.decompress(response["body"]) == body
