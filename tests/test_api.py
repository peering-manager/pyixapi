import unittest
import warnings
from unittest.mock import patch

import pyixapi
from pyixapi.core.token import Token

from .util import Response, auth_response, def_args, host, make_jwt


class ApiInitTestCase(unittest.TestCase):
    def test_url_trailing_slash_stripped(self) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertFalse(api.url.endswith("/"))

    def test_init_with_pre_existing_tokens(self) -> None:
        token = make_jwt(expires_in=-3600)
        api = pyixapi.api(host, *def_args, access_token=token, refresh_token=token)
        self.assertIsNotNone(api.access_token)
        self.assertIsInstance(api.access_token, Token)
        self.assertIsNotNone(api.refresh_token)
        self.assertIsInstance(api.refresh_token, Token)

    def test_init_without_tokens(self) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertIsNone(api.access_token)
        self.assertIsNone(api.refresh_token)

    def test_init_with_custom_user_agent(self) -> None:
        api = pyixapi.api(host, *def_args, user_agent="custom/1.0")
        self.assertEqual(api.user_agent, "custom/1.0")

    def test_init_with_proxies(self) -> None:
        proxies = {"http": "http://proxy:8080"}
        api = pyixapi.api(host, *def_args, proxies=proxies)
        self.assertEqual(api.proxies, proxies)

    def test_default_user_agent(self) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.user_agent, f"pyixapi/{pyixapi.__version__}")


class ApiTestCase(unittest.TestCase):
    @patch("requests.sessions.Session.post", return_value=auth_response())
    def test_authenticate_stores_valid_tokens(self, mock_post) -> None:
        api = pyixapi.api(host, *def_args)
        r = api.authenticate()

        self.assertIsNotNone(r)
        self.assertFalse(api.access_token.is_expired)
        self.assertFalse(api.refresh_token.is_expired)
        self.assertTrue(mock_post.call_args[0][0].endswith("/auth/token"))
        self.assertEqual(mock_post.call_args[1]["json"]["api_key"], def_args[0])
        self.assertEqual(mock_post.call_args[1]["json"]["api_secret"], def_args[1])

    def test_authenticate_returns_none_when_access_token_valid(self) -> None:
        api = pyixapi.api(host, *def_args)
        api.access_token = Token.from_jwt(make_jwt(expires_in=3600))
        with patch("requests.sessions.Session.post") as mock_post:
            result = api.authenticate()
        self.assertIsNone(result)
        mock_post.assert_not_called()

    @patch("requests.sessions.Session.post", return_value=auth_response())
    def test_authenticate_refreshes_when_access_expired_refresh_valid(self, mock_post) -> None:
        api = pyixapi.api(host, *def_args)
        api.access_token = Token.from_jwt(make_jwt(expires_in=-3600))
        api.refresh_token = Token.from_jwt(make_jwt(expires_in=3600))

        result = api.authenticate()

        self.assertIsNotNone(result)
        self.assertTrue(mock_post.call_args[0][0].endswith("/auth/refresh"))

    @patch("requests.sessions.Session.post", return_value=auth_response())
    def test_authenticate_reauthenticates_when_both_tokens_expired(self, mock_post) -> None:
        api = pyixapi.api(host, *def_args)
        api.access_token = Token.from_jwt(make_jwt(expires_in=-3600))
        api.refresh_token = Token.from_jwt(make_jwt(expires_in=-3600))

        result = api.authenticate()

        self.assertIsNotNone(result)
        self.assertTrue(mock_post.call_args[0][0].endswith("/auth/token"))
        self.assertFalse(api.access_token.is_expired)

    @patch("requests.sessions.Session.post", return_value=auth_response())
    def test_refresh_authentication(self, mock_post) -> None:
        api = pyixapi.api(host, *def_args)
        api.authenticate()
        sent_refresh_token = api.refresh_token.encoded
        r = api.refresh_authentication()

        self.assertIsNotNone(r)
        self.assertFalse(api.access_token.is_expired)
        self.assertFalse(api.refresh_token.is_expired)
        self.assertTrue(mock_post.call_args[0][0].endswith("/auth/refresh"))
        self.assertEqual(mock_post.call_args[1]["json"]["refresh_token"], sent_refresh_token)

    def test_refresh_authentication_raises_without_refresh_token(self) -> None:
        api = pyixapi.api(host, *def_args)
        api.refresh_token = None
        with self.assertRaises(ValueError) as ctx:
            api.refresh_authentication()
        self.assertIn("No refresh token", str(ctx.exception))


class ApiVersionTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False, url=host, text="Not found"),
    )
    def test_api_version_1(self, *_) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            api = pyixapi.api(host, *def_args)
            self.assertEqual(api.version, 1)

            assert w
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[-1].message)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"status": "pass", "version": 2}),
    )
    def test_api_version(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.version, 2)

    @patch("requests.sessions.Session.get", return_value=Response(content={"status": "pass", "version": 2}))
    def test_api_version_is_cached(self, mock_get) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.version, 2)
        self.assertEqual(api.version, 2)
        api.accounts
        mock_get.assert_called_once()


class ApiVersionDependentEndpointsTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"status": "pass", "version": 2}),
    )
    def test_accounts_v2(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        endpoint = api.accounts
        self.assertIn("accounts", endpoint.url)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False, url=host, text="Not found"),
    )
    def test_accounts_v1(self, *_) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            api = pyixapi.api(host, *def_args)
            endpoint = api.accounts
            self.assertIn("customers", endpoint.url)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"status": "pass", "version": 2}),
    )
    def test_product_offerings_v2(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        endpoint = api.product_offerings
        self.assertIn("product-offerings", endpoint.url)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False, url=host, text="Not found"),
    )
    def test_product_offerings_v1(self, *_) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            api = pyixapi.api(host, *def_args)
            endpoint = api.product_offerings
            self.assertIn("products", endpoint.url)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"status": "pass", "version": 2}),
    )
    def test_demarcs_raises_on_v2(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        with self.assertRaises(AttributeError):
            api.demarcs

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False, url=host, text="Not found"),
    )
    def test_demarcs_v1(self, *_) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            api = pyixapi.api(host, *def_args)
            endpoint = api.demarcs
            self.assertIn("demarcs", endpoint.url)


class ApiAccountTestCase(unittest.TestCase):
    @patch("requests.sessions.Session.get")
    def test_account(self, mock_get) -> None:
        # Respond by URL so the test does not depend on call order.
        def by_url(url, *args, **kwargs):
            if url.endswith("/account"):
                return Response(content={"id": "ACCT-001", "name": "My Account"})
            return Response(content={"status": "pass", "version": 2})

        mock_get.side_effect = by_url

        api = pyixapi.api(host, *def_args)
        account = api.account()

        self.assertEqual(account.id, "ACCT-001")
        self.assertTrue(any(c.args[0].endswith("/account") for c in mock_get.call_args_list))


class ApiImplementationTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"name": "Test IXP", "version": "2.7.1"}),
    )
    def test_implementation(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        result = api.implementation()
        self.assertEqual(result["name"], "Test IXP")
        self.assertEqual(result["version"], "2.7.1")


class ApiExtensionsTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content=[{"name": "ext1"}, {"name": "ext2"}]),
    )
    def test_extensions(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        result = api.extensions()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "ext1")


class ApiHealthTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"status": "pass", "version": "2"}),
    )
    def test_api_status(self, *_) -> None:
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.health()["status"], "pass")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False, url=host, text="Not found"),
    )
    def test_health_v1_returns_empty_dict(self, *_) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            api = pyixapi.api(host, *def_args)
            result = api.health()
            self.assertEqual(result, {})
