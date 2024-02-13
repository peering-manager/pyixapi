import warnings
from datetime import datetime, timezone

import jwt


class TokenException(Exception):
    pass


class InvalidTokenException(Exception):
    pass


class Token:
    """
    A token is at the core of the authentication mechanism of IX-API.

    To make a query, a set of tokens (access and refresh) must be issued. The access
    token is used for requests authorisation while the refresh token is used to renew
    the period of validity for a token.

    A token as an issued time as well as an expiration time. These time values are
    useful to know when an new authentication or token renewal must be performed to
    continue using the API.
    """

    def __init__(self, token: str, expires_at: datetime) -> None:
        self.encoded: str = token  # Cache signed token data
        self.expires_at: datetime = expires_at

    def __str__(self) -> str:
        return self.encoded

    def __repr__(self) -> str:
        return f"<Token ttl={self.ttl}s>"

    @property
    def issued_at(self) -> datetime:
        warnings.warn(
            "Property 'issued_at' is deprecated and value will always be set to now.",
            DeprecationWarning,
        )
        return datetime.now(tz=timezone.utc)

    @property
    def ttl(self) -> int:
        """
        TTL is the number of seconds, from now, before the token expires.
        """
        seconds = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, seconds)

    @property
    def is_expired(self) -> bool:
        """
        Tell if a token is expired or not (TTL equals to 0).
        """
        return self.ttl == 0

    @classmethod
    def from_jwt(cls, token: str) -> "Token":
        """
        Create a new token from a JWT, decoding it and caching its expiration time.

        :param token: (str) String containing the original encoded token which is the
            result of a POST request to the authentication endpoint.
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise TokenException(e)

        try:
            return cls(
                token=token,
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        except Exception as e:
            raise InvalidTokenException(e)
