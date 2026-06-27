import json
import unittest
from unittest.mock import MagicMock

from pyixapi.core.query import ContentError, Request, RequestError
from pyixapi.core.token import Token

from .util import make_jwt


class RequestErrorTestCase(unittest.TestCase):
    def test_404_error_message(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://api.example.net/v1/notfound"
        mock_response.text = "Not Found"

        error = RequestError(mock_response)
        self.assertEqual(error.req, mock_response)
        self.assertIn("could not be found", error.message)
        self.assertIn("notfound", str(error))

    def test_401_error_message(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        error = RequestError(mock_response)
        self.assertIn("Authentication credentials are invalid", error.message)

    def test_500_error_with_json(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.json.return_value = {"error": "Database connection failed"}

        error = RequestError(mock_response)
        self.assertIn("500", error.message)
        self.assertIn("Database connection failed", error.message)

    def test_500_error_without_json(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.json.side_effect = ValueError("Invalid JSON")

        error = RequestError(mock_response)
        self.assertIn("details were not found as JSON", error.message)

    def test_error_attribute(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://api.example.net/v1/notfound"
        mock_response.text = "Not Found"

        error = RequestError(mock_response)
        self.assertEqual(error.error, "Not Found")


class ContentErrorTestCase(unittest.TestCase):
    def test_content_error(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "Not JSON content"

        error = ContentError(mock_response)
        self.assertEqual(error.req, mock_response)
        self.assertIn("invalid (non-JSON) data", str(error))


class RequestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.http_session = MagicMock()
        self.token = Token.from_jwt(make_jwt())

    def test_url_construction_with_key(self) -> None:
        request = Request(
            base="https://api.example.net/v1/connections",
            key="CONN-001",
            http_session=self.http_session,
        )
        self.assertEqual(request.url, "https://api.example.net/v1/connections/CONN-001")

    def test_url_construction_without_key(self) -> None:
        request = Request(
            base="https://api.example.net/v1/connections",
            http_session=self.http_session,
        )
        self.assertEqual(request.url, "https://api.example.net/v1/connections")

    def test_get_health(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "pass", "version": "2"}
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1",
            token=self.token,
            http_session=self.http_session,
        )
        result = request.get_health()

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["version"], "2")

    def test_get_version_v2(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "pass", "version": "2"}
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1",
            http_session=self.http_session,
        )
        version = request.get_version()

        self.assertEqual(version, 2)

    def test_get_version_v1_fallback(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1",
            http_session=self.http_session,
        )
        version = request.get_version()

        self.assertEqual(version, 1)

    def test_get_with_list_response(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
        ]
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        result = list(request.get())

        self.assertEqual(len(result), 2)
        self.assertEqual(request.count, 2)

    def test_get_with_single_response(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": "1", "name": "Item 1"}
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items/1",
            http_session=self.http_session,
        )
        result = list(request.get())

        self.assertEqual(len(result), 1)
        # A single object counts as one result, not one-per-field.
        self.assertEqual(request.count, 1)

    def test_get_with_filters(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            filters={"name": "test", "state": "active"},
            http_session=self.http_session,
        )
        list(request.get())

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[1]["params"]["name"], "test")
        self.assertEqual(call_args[1]["params"]["state"], "active")

    def test_write_verbs_send_url_verb_and_body(self) -> None:
        url = "https://api.example.net/v1/items/ITEM-001"
        cases = [
            ("post", lambda r, d: r.post(d)),
            ("put", lambda r, d: r.put(d)),
            ("patch", lambda r, d: r.patch(d)),
        ]
        for verb, call in cases:
            with self.subTest(verb=verb):
                mock_response = MagicMock()
                mock_response.ok = True
                mock_response.json.return_value = {"id": "X"}
                getattr(self.http_session, verb).return_value = mock_response

                request = Request(base=url, http_session=self.http_session)
                data = {"name": "Item"}
                result = call(request, data)

                mock = getattr(self.http_session, verb)
                self.assertEqual(mock.call_args[0][0], url)
                self.assertEqual(mock.call_args[1]["json"], data)
                self.assertEqual(result, {"id": "X"})

    def test_delete_success(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        self.http_session.delete.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items/ITEM-001",
            http_session=self.http_session,
        )
        result = request.delete()

        self.assertTrue(result)
        # A bodyless DELETE must not advertise a JSON request body.
        headers = self.http_session.delete.call_args[1]["headers"]
        self.assertNotIn("Content-Type", headers)
        self.assertIn("accept", headers)

    def test_delete_with_data(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        self.http_session.delete.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        result = request.delete({"ids": ["ITEM-001", "ITEM-002"]})

        self.assertTrue(result)
        # A DELETE carrying a body sets the JSON content type.
        headers = self.http_session.delete.call_args[1]["headers"]
        self.assertEqual(headers["Content-Type"], "application/json;")

    def test_options(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "name": "Item List",
            "actions": {"POST": {}, "GET": {}},
        }
        self.http_session.options.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        result = request.options()

        self.assertIn("actions", result)

    def test_make_call_with_content_error(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = json.JSONDecodeError("Error", "", 0)
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )

        with self.assertRaises(ContentError):
            list(request.get())

    def test_make_call_with_token(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            token=self.token,
            http_session=self.http_session,
        )
        list(request.get())

        call_args = self.http_session.get.call_args
        self.assertIn("Authorization", call_args[1]["headers"])
        self.assertTrue(call_args[1]["headers"]["Authorization"].startswith("Bearer "))

    def test_make_call_with_user_agent(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
            user_agent="TestAgent/1.0",
        )
        list(request.get())

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[1]["headers"]["User-Agent"], "TestAgent/1.0")

    def test_make_call_with_proxies(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        self.http_session.get.return_value = mock_response

        proxies = {"http": "http://proxy:8080", "https": "https://proxy:8443"}
        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
            proxies=proxies,
        )
        list(request.get())

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[1]["proxies"], proxies)

    def test_get_health_failure(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 503
        mock_response.reason = "Service Unavailable"
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1",
            http_session=self.http_session,
        )

        with self.assertRaises(RequestError):
            request.get_health()

    def test_get_health_without_token(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "pass", "version": "2"}
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1",
            http_session=self.http_session,
        )
        request.get_health()

        call_args = self.http_session.get.call_args
        self.assertNotIn("Authorization", call_args[1]["headers"])

    def test_make_call_with_url_override(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": "1"}
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            filters={"name": "test"},
            http_session=self.http_session,
        )
        result = request._make_call(url_override="https://api.example.net/v1/other")
        self.assertEqual(result, {"id": "1"})

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[0][0], "https://api.example.net/v1/other")
        # When url_override is used, params should be empty (filters ignored)
        self.assertEqual(call_args[1]["params"], {})

    def test_get_with_add_params(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [{"id": "1"}]
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        list(request.get(add_params={"from": "2024-01-01"}))

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[1]["params"]["from"], "2024-01-01")

    def test_verb_failures_raise_request_error(self) -> None:
        cases = [
            ("post", lambda r: r.post({"name": "Invalid"})),
            ("put", lambda r: r.put({"name": "Invalid"})),
            ("patch", lambda r: r.patch({"name": "Invalid"})),
            ("delete", lambda r: r.delete()),
            ("options", lambda r: r.options()),
        ]
        for verb, call in cases:
            with self.subTest(verb=verb):
                mock_response = MagicMock()
                mock_response.ok = False
                mock_response.status_code = 400
                mock_response.reason = "Bad Request"
                getattr(self.http_session, verb).return_value = mock_response

                request = Request(base="https://api.example.net/v1/items", http_session=self.http_session)
                with self.assertRaises(RequestError):
                    call(request)

    def test_post_sets_content_type_header(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": "NEW-001"}
        self.http_session.post.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        request.post({"name": "Item"})

        call_args = self.http_session.post.call_args
        self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/json;")

    def test_get_sets_accept_header(self) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = []
        self.http_session.get.return_value = mock_response

        request = Request(
            base="https://api.example.net/v1/items",
            http_session=self.http_session,
        )
        list(request.get())

        call_args = self.http_session.get.call_args
        self.assertEqual(call_args[1]["headers"]["accept"], "application/json;")
