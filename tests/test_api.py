import unittest
from unittest.mock import patch

import pyixapi

from .util import Response

host = "https://api.example.net/v1/"

def_args = (
    "-GnNlMD8hBuxSSUJmpbfUkss9dyOKfTV1SnZibNyyr4",
    "XKq8M6NVh5lCbPJ2Ml1h7V93QNIMsGVBfM6g2nRZF-E",
)


class ApiTestCase(unittest.TestCase):
    @patch(
        "requests.sessions.Session.post",
        return_value=Response(fixture="api/authenticate.json"),
    )
    def test_authenticate(self, *_):
        api = pyixapi.api(host, *def_args)
        r = api.authenticate()

        self.assertIsNotNone(r)
        self.assertIsNotNone(api.access_token)
        self.assertIsNotNone(api.refresh_token)

    @patch(
        "requests.sessions.Session.post",
        return_value=Response(fixture="api/refresh_authentication.json"),
    )
    def test_refresh_authentication(self, *_):
        api = pyixapi.api(host, *def_args)
        api.authenticate()
        r = api.refresh_authentication()

        self.assertIsNotNone(r)
        self.assertIsNotNone(api.access_token)
        self.assertIsNotNone(api.refresh_token)


class ApiVersionTestCase(unittest.TestCase):
    class ResponseWithFailure:
        ok = False
        status_code = 404
        url = host
        text = "Not found"

    class ResponseWithSuccess:
        ok = True

        def json(self):
            return {"status": "pass", "version": 2}

    @patch(
        "requests.sessions.Session.get",
        return_value=ResponseWithFailure(),
    )
    def test_api_version_1(self, *_):
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.version, 1)

    @patch(
        "requests.sessions.Session.get",
        return_value=ResponseWithSuccess(),
    )
    def test_api_version(self, *_):
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.version, 2)


class ApiHealthTestCase(unittest.TestCase):
    class ResponseWithHealth:
        ok = True

        def json(self):
            return {"status": "pass", "version": "2"}

    @patch(
        "requests.sessions.Session.get",
        return_value=ResponseWithHealth(),
    )
    def test_api_status(self, *_):
        api = pyixapi.api(host, *def_args)
        self.assertEqual(api.health()["status"], "pass")
