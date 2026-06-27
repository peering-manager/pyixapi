import unittest
from unittest.mock import patch

import pyixapi
from pyixapi.core.endpoint import Endpoint
from pyixapi.core.query import RequestError
from pyixapi.core.response import Record
from pyixapi.models import Connection

from .util import Response, auth_response, def_args, host


class EndpointTestCase(unittest.TestCase):
    @patch("requests.sessions.Session.post", return_value=auth_response())
    def setUp(self, *_) -> None:
        self.api = pyixapi.api(host, *def_args)
        self.api.authenticate()

    def test_str(self) -> None:
        endpoint = Endpoint(self.api, "connections")
        self.assertEqual(str(endpoint), f"{host}connections")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(
            content=[
                {"id": "CONN-001", "name": "Connection 1"},
                {"id": "CONN-002", "name": "Connection 2"},
            ]
        ),
    )
    def test_all(self, *_) -> None:
        result = list(self.api.connections.all())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "CONN-001")
        self.assertEqual(result[1].id, "CONN-002")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(
            content=[
                {"id": "CONN-001", "name": "Connection 1"},
            ]
        ),
    )
    def test_filter(self, *_) -> None:
        result = list(self.api.connections.filter(name="Connection 1"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "CONN-001")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(
            content=[
                {"id": "CONN-001", "name": "Connection 1"},
                {"id": "CONN-002", "name": "Connection 2"},
            ]
        ),
    )
    def test_all_len_then_iterate(self, *_) -> None:
        # Exercises the real Request.get() -> count -> RecordSet.__len__ path.
        recordset = self.api.connections.all()
        self.assertEqual(len(recordset), 2)
        self.assertEqual([r.id for r in recordset], ["CONN-001", "CONN-002"])

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content={"id": "CONN-001", "name": "Connection 1"}),
    )
    def test_get_by_id(self, *_) -> None:
        result = self.api.connections.get("CONN-001")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "CONN-001")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content=[{"id": "CONN-001", "name": "Connection 1"}]),
    )
    def test_get_by_id_with_single_element_list_response(self, *_) -> None:
        # A by-id lookup wrapped in a one-element list still resolves to one record.
        result = self.api.connections.get("CONN-001")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "CONN-001")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content=[{"id": "CONN-001", "name": "Connection 1"}]),
    )
    def test_get_by_kwargs(self, *_) -> None:
        result = self.api.connections.get(name="Connection 1")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "CONN-001")

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(content=[]),
    )
    def test_get_not_found(self, *_) -> None:
        result = self.api.connections.get(name="Nonexistent")
        self.assertIsNone(result)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(
            content=[
                {"id": "CONN-001", "name": "Connection 1"},
                {"id": "CONN-002", "name": "Connection 2"},
            ]
        ),
    )
    def test_get_multiple_results_raises_error(self, *_) -> None:
        with self.assertRaises(ValueError) as context:
            self.api.connections.get(state="active")
        self.assertIn("returned more than one result", str(context.exception))

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=404, ok=False),
    )
    def test_get_404_returns_none(self, mock_get) -> None:
        mock_response = mock_get.return_value
        mock_response.url = f"{host}connections/NOTFOUND"
        mock_response.text = "Not Found"
        result = self.api.connections.get("NOTFOUND")
        self.assertIsNone(result)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(status_code=500, ok=False),
    )
    def test_get_500_raises_error(self, mock_get) -> None:
        mock_response = mock_get.return_value
        mock_response.url = f"{host}connections/ERROR"
        mock_response.text = "Internal Server Error"
        mock_response.reason = "Internal Server Error"
        with self.assertRaises(RequestError):
            self.api.connections.get("ERROR")

    @patch(
        "requests.sessions.Session.post",
        return_value=Response(content={"id": "CONN-003", "name": "New Connection"}),
    )
    def test_create_with_dict(self, *_) -> None:
        result = self.api.connections.create({"name": "New Connection"})
        self.assertEqual(result.id, "CONN-003")
        self.assertEqual(result.name, "New Connection")

    @patch(
        "requests.sessions.Session.post",
        return_value=Response(content={"id": "CONN-004", "name": "Another Connection"}),
    )
    def test_create_with_kwargs(self, *_) -> None:
        result = self.api.connections.create(name="Another Connection")
        self.assertEqual(result.id, "CONN-004")
        self.assertEqual(result.name, "Another Connection")

    def test_return_obj_defaults_to_record(self) -> None:
        endpoint = Endpoint(self.api, "test-endpoint")
        self.assertEqual(endpoint.return_obj, Record)

    def test_return_obj_with_model(self) -> None:
        endpoint = Endpoint(self.api, "connections", model=Connection)
        self.assertEqual(endpoint.return_obj, Connection)

    @patch(
        "requests.sessions.Session.get",
        return_value=Response(
            content=[
                {"id": "CONN-001", "name": "Connection 1"},
            ]
        ),
    )
    def test_filter_passes_kwargs(self, mock_get) -> None:
        list(self.api.connections.filter(state="active", name="Connection 1"))
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]["params"]["state"], "active")
        self.assertEqual(call_args[1]["params"]["name"], "Connection 1")

    @patch("requests.sessions.Session.get", return_value=Response(content=[{"id": "CONN-001"}]))
    def test_request_carries_authenticated_token(self, mock_get) -> None:
        list(self.api.connections.all())
        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], f"Bearer {self.api.access_token.encoded}")
