import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import jwt

host = "https://api.example.net/v1/"
def_args = (
    "-GnNlMD8hBuxSSUJmpbfUkss9dyOKfTV1SnZibNyyr4",
    "XKq8M6NVh5lCbPJ2Ml1h7V93QNIMsGVBfM6g2nRZF-E",
)

# JWT with a fixed exp claim, for asserting the decoded expiry.
sample_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJPbmxpbmUgSldUIEJ1aWxkZXIiLCJpYXQiOjE2NjM5NjE0MDAsImV4cCI6MTY2Mzk2MjMwMCwiYXVkIjoid3d3LmV4YW1wbGUuY29tIiwic3ViIjoidGVzdEBleGFtcGxlLmNvbSJ9.jPZ4TMh9mFGu2Ebgz-UO3bd5wrAJDyOjJaul1tq0AoI"  # noqa: E501
sample_jwt_exp = 1663962300


class Response(object):
    def __init__(
        self,
        status_code: int = 200,
        ok: bool = True,
        content: Any = None,
        url: str = "",
        text: str = "",
        reason: str = "",
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.text = text
        self.reason = reason
        self.content = json.dumps(content) if content is not None else ""
        self.ok = ok

    def json(self) -> Any:
        return json.loads(self.content)


def make_jwt(expires_in: int = 3600, issued_ago: int = 0) -> str:
    """
    Build a signed JWT whose ``exp`` claim is ``expires_in`` seconds from now.

    Use a positive ``expires_in`` for a valid token and a negative one for an
    already-expired token. This keeps auth tests deterministic instead of
    relying on hardcoded tokens whose expiry drifts into the past.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int((now - timedelta(seconds=issued_ago)).timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
        "sub": "test@example.com",
    }
    # 32+ byte key so PyJWT does not emit an InsecureKeyLengthWarning (tests only).
    return jwt.encode(payload, "pyixapi-test-signing-key-not-secret", algorithm="HS256")


def auth_response(access_expires_in: int = 3600, refresh_expires_in: int = 86400) -> Response:
    """Build a :class:`Response` mimicking the ``/auth/token`` payload."""
    return Response(
        content={
            "access_token": make_jwt(access_expires_in),
            "refresh_token": make_jwt(refresh_expires_in),
        }
    )


def mock_api() -> MagicMock:
    """
    Create a MagicMock API with the standard attributes pre-configured.

    The returned mock has a mock http_session suitable for verifying HTTP calls
    made by Request._make_call() without patching the Request class itself.
    """
    api = MagicMock()
    api.http_session = MagicMock()
    api.access_token = MagicMock()
    api.access_token.encoded = "fake-token"
    api.user_agent = "pyixapi/test"
    api.proxies = None
    return api


def mock_endpoint(
    name: str = "test",
    url: str = "https://api.example.net/v2/test",
) -> MagicMock:
    """Create a MagicMock Endpoint with name and url attributes."""
    endpoint = MagicMock()
    endpoint.name = name
    endpoint.url = url
    return endpoint
