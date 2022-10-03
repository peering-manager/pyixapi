from datetime import datetime

import jwt


class TokenException(Exception):
    pass


class InvalidTokenException(Exception):
    pass


class Token(object):
    """
    A token is at the core of the authentication mechanism of IX-API.

    To make a query, a set of tokens (access and refresh) must be issued. The access
    token is used for requests authorisation while the refresh token is used to renew
    the period of validity for a token.

    A token as an issued time as well as an expiration time. These time values are
    useful to know when an new authentication or token renewal must be performed to
    continue using the API.
    """

    def __init__(self, token, issued_at, expires_at):
        self.encoded = token  # Cache signed token data
        self.issued_at = issued_at
        self.expires_at = expires_at

    def __str__(self):
        return self.encoded

    def __repr__(self):
        return f"<Token issued_at={self.issued_at} ttl={self.ttl}s>"

    @property
    def ttl(self):
        """
        TTL is the number of seconds, from now, before the token expires.
        """
        seconds = (self.expires_at - datetime.now()).total_seconds()
        return max(0, seconds)

    @property
    def is_expired(self):
        """
        Tell if a token is expired or not (TTL equals to 0).
        """
        return self.ttl == 0

    @classmethod
    def from_jwt(cls, token):
        """
        Create a new token from a JWT, decoding it and caching it issued and
        expiration times.

        :param token: (str) String containing the original encoded token which is the
            result of a POST request to the authentication endpoint.
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise TokenException(e)

        try:
            issued_at = datetime.fromtimestamp(payload["iat"])
            expires_at = datetime.fromtimestamp(payload["exp"])
            return cls(token, issued_at, expires_at)
        except Exception as e:
            raise InvalidTokenException(e)
