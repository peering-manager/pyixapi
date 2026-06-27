import unittest
import warnings
from datetime import datetime, timedelta, timezone

from pyixapi.core.token import InvalidTokenException, Token, TokenException

from .util import sample_jwt, sample_jwt_exp


class TokenTestCase(unittest.TestCase):
    def test_from_jwt_valid(self) -> None:
        token = Token.from_jwt(sample_jwt)

        self.assertEqual(token.encoded, sample_jwt)
        self.assertEqual(token.expires_at, datetime.fromtimestamp(sample_jwt_exp, tz=timezone.utc))

    def test_from_jwt_invalid_format(self) -> None:
        with self.assertRaises(TokenException):
            Token.from_jwt("not-a-valid-jwt")

    def test_from_jwt_missing_exp(self) -> None:
        token_str = (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
            "eyJpc3MiOiJPbmxpbmUgSldUIEJ1aWxkZXIifQ.m5rN8mF8H3fC9CYWJLQEWh0m5J0wQ4H1qv-LrK9Cq6M"
        )
        with self.assertRaises(InvalidTokenException):
            Token.from_jwt(token_str)

    def test_repr(self) -> None:
        token = Token.from_jwt(sample_jwt)
        repr_str = repr(token)
        self.assertIn("Token", repr_str)
        self.assertIn("ttl=", repr_str)

    def test_ttl_future(self) -> None:
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        token = Token("test_token", future_time)

        self.assertGreater(token.ttl, 3500)
        self.assertLess(token.ttl, 3700)

    def test_ttl_past(self) -> None:
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token = Token("test_token", past_time)

        self.assertEqual(token.ttl, 0)

    def test_is_expired_false(self) -> None:
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        token = Token("test_token", future_time)
        self.assertFalse(token.is_expired)

    def test_is_expired_true(self) -> None:
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token = Token("test_token", past_time)
        self.assertTrue(token.is_expired)

    def test_issued_at_deprecated(self) -> None:
        token = Token.from_jwt(sample_jwt)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            issued = token.issued_at
            self.assertIsInstance(issued, datetime)
            self.assertTrue(len(w) > 0)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[0].message))
