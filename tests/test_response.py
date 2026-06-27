import unittest
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from pyixapi.core.response import Record, RecordSet, get_return

from .util import Response, mock_api, mock_endpoint

if TYPE_CHECKING:
    from pyixapi.core.query import Request


class GetReturnTestCase(unittest.TestCase):
    def test_get_return_with_record(self) -> None:
        record = Record({"id": "TEST-001"}, mock_api(), mock_endpoint())
        result = get_return(record)
        self.assertEqual(result, "TEST-001")

    def test_get_return_with_non_record(self) -> None:
        result = get_return("simple_string")
        self.assertEqual(result, "simple_string")

        result = get_return(42)
        self.assertEqual(result, 42)


class RecordSetTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api = mock_api()
        self.endpoint = mock_endpoint()
        self.endpoint.api = self.api
        self.endpoint.return_obj = Record

    def test_iteration(self) -> None:
        request = MagicMock()
        request.get.return_value = iter(
            [
                {"id": "ITEM-001", "name": "Item 1"},
                {"id": "ITEM-002", "name": "Item 2"},
            ]
        )
        recordset = RecordSet(self.endpoint, request)

        items = list(recordset)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "ITEM-001")
        self.assertEqual(items[1].id, "ITEM-002")

    def test_len_with_count(self) -> None:
        request = MagicMock()
        request.get.return_value = iter([])
        request.count = 5

        recordset = RecordSet(self.endpoint, request)
        self.assertEqual(len(recordset), 5)

    def test_len_with_deferred_count(self) -> None:
        class MockRequest:
            def get(self):
                self.count = 1
                yield {"id": "ITEM-001"}

        request = MockRequest()
        recordset = RecordSet(self.endpoint, cast("Request", request))

        length = len(recordset)
        self.assertEqual(length, 1)

        items = list(recordset)
        self.assertEqual(len(items), 1)

    def test_len_empty(self) -> None:
        request = MagicMock()
        request.get.return_value = iter([])
        del request.count

        recordset = RecordSet(self.endpoint, request)
        self.assertEqual(len(recordset), 0)

    def test_len_then_iterate_uses_cache(self) -> None:
        """When len() is called first, cached items should still be iterable."""

        class MockRequest:
            def get(self):
                self.count = 2
                yield {"id": "ITEM-001"}
                yield {"id": "ITEM-002"}

        request = MockRequest()
        recordset = RecordSet(self.endpoint, cast("Request", request))

        length = len(recordset)
        self.assertEqual(length, 2)

        items = list(recordset)
        self.assertEqual(len(items), 2)
        ids = {item.id for item in items}
        self.assertEqual(ids, {"ITEM-001", "ITEM-002"})


class RecordTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api = mock_api()
        self.endpoint = mock_endpoint(name="connections", url="https://api.example.net/v1/connections")

    def test_str_with_id(self) -> None:
        record = Record({"id": "CONN-001"}, self.api, self.endpoint)
        self.assertEqual(str(record), "CONN-001")

    def test_str_without_id(self) -> None:
        record = Record({}, self.api, self.endpoint)
        self.assertEqual(str(record), str(self.endpoint))

    def test_iteration(self) -> None:
        record = Record(
            {"id": "CONN-001", "name": "Connection 1", "state": "active"},
            self.api,
            self.endpoint,
        )
        items = dict(record)
        self.assertEqual(items["id"], "CONN-001")
        self.assertEqual(items["name"], "Connection 1")
        self.assertEqual(items["state"], "active")

    def test_getitem(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        self.assertEqual(record["id"], "CONN-001")
        self.assertEqual(record["name"], "Connection 1")

    def test_missing_attribute_raises(self) -> None:
        # Absent fields are not lazy-fetched.
        record = Record({"id": "CONN-001"}, self.api, self.endpoint)
        with self.assertRaises(AttributeError):
            record.not_in_response

    def test_equality(self) -> None:
        record1 = Record({"id": "CONN-001"}, self.api, self.endpoint)
        record2 = Record({"id": "CONN-001"}, self.api, self.endpoint)
        record3 = Record({"id": "CONN-002"}, self.api, self.endpoint)

        self.assertEqual(record1, record2)
        self.assertNotEqual(record1, record3)
        self.assertNotEqual(record1, "CONN-001")

    def test_hash(self) -> None:
        record1 = Record({"id": "CONN-001"}, self.api, self.endpoint)
        record2 = Record({"id": "CONN-001"}, self.api, self.endpoint)

        self.assertEqual(hash(record1), hash(record2))

        records = {record1, record2}
        self.assertEqual(len(records), 1)

    def test_serialize_simple(self) -> None:
        record = Record(
            {"id": "CONN-001", "name": "Connection 1", "capacity": 1000},
            self.api,
            self.endpoint,
        )
        serialized = record.serialize()
        self.assertEqual(serialized["id"], "CONN-001")
        self.assertEqual(serialized["name"], "Connection 1")
        self.assertEqual(serialized["capacity"], 1000)

    def test_serialize_nested(self) -> None:
        nested_record = Record({"id": "NESTED-001"}, self.api, self.endpoint)
        record = Record({"id": "CONN-001", "nested": nested_record}, self.api, self.endpoint)

        serialized = record.serialize()
        self.assertEqual(serialized["nested"], "NESTED-001")

    def test_serialize_with_list(self) -> None:
        nested1 = Record({"id": "ITEM-001"}, self.api, self.endpoint)
        nested2 = Record({"id": "ITEM-002"}, self.api, self.endpoint)
        record = Record({"id": "CONN-001", "items": [nested1, nested2]}, self.api, self.endpoint)

        serialized = record.serialize()
        self.assertEqual(serialized["items"], ["ITEM-001", "ITEM-002"])

    def test_serialize_nested_flag(self) -> None:
        record = Record({"id": "CONN-001"}, self.api, self.endpoint)
        serialized = record.serialize(nested=True)
        self.assertEqual(serialized, "CONN-001")

    def test_updates_no_changes(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        updates = record.updates()
        self.assertEqual(updates, {})

    def test_updates_with_changes(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        record.name = "Connection 1 Updated"
        updates = record.updates()
        self.assertIn("name", updates)
        self.assertEqual(updates["name"], "Connection 1 Updated")

    def test_save_patches_only_changed_fields(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        record.name = "Connection 1 Updated"

        self.api.http_session.patch.return_value = Response(content={"id": "CONN-001", "name": "Updated"})
        result = record.save()

        self.assertTrue(result)
        self.api.http_session.patch.assert_called_once()
        self.assertEqual(self.api.http_session.patch.call_args[1]["json"], {"name": "Connection 1 Updated"})

    def test_save_refreshes_from_response(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        record.name = "Connection 1 Updated"

        self.api.http_session.patch.return_value = Response(
            content={"id": "CONN-001", "name": "Normalised", "state": "production"}
        )
        result = record.save()
        self.assertTrue(result)
        self.assertEqual(record.name, "Normalised")
        self.assertEqual(record.state, "production")
        self.assertEqual(record.updates(), {})

    def test_save_no_changes(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        result = record.save()
        self.assertFalse(result)

    def test_save_with_non_dict_response_skips_refresh(self) -> None:
        record = Record({"id": "CONN-001", "name": "Original"}, self.api, self.endpoint)
        record.name = "Modified"

        self.api.http_session.patch.return_value = Response(content=["unexpected"])
        result = record.save()

        self.assertTrue(result)
        self.assertEqual(record.name, "Modified")

    def test_update(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)

        self.api.http_session.patch.return_value = Response(content={"id": "CONN-001", "name": "New Name"})
        result = record.update({"name": "New Name"})

        self.assertTrue(result)
        self.api.http_session.patch.assert_called_once()
        self.assertEqual(self.api.http_session.patch.call_args[1]["json"], {"name": "New Name"})

    def test_delete(self) -> None:
        record = Record({"id": "CONN-001"}, self.api, self.endpoint)

        self.api.http_session.delete.return_value = Response(content=None)
        result = record.delete()

        self.assertTrue(result)
        self.assertTrue(self.api.http_session.delete.call_args[0][0].endswith("/connections/CONN-001"))

    def test_repr(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        repr_str = repr(record)
        self.assertIn("CONN-001", repr_str)
        self.assertIn("Connection 1", repr_str)

    def test_iter_serializes_nested_record(self) -> None:
        class WithNested(Record):
            nested = Record

        record = WithNested(
            {"id": "CONN-001", "nested": {"id": "NESTED-001", "name": "Nested"}}, self.api, self.endpoint
        )
        items = dict(record)
        self.assertIsInstance(items["nested"], dict)
        self.assertEqual(items["nested"]["id"], "NESTED-001")

    def test_iter_serializes_list_of_records(self) -> None:
        record = Record({"id": "CONN-001", "items": [{"id": "ITEM-001"}, {"id": "ITEM-002"}]}, self.api, self.endpoint)
        items = dict(record)
        self.assertIsInstance(items["items"], list)
        self.assertEqual([i["id"] for i in items["items"]], ["ITEM-001", "ITEM-002"])

    def test_key_without_id(self) -> None:
        record = Record({}, self.api, self.endpoint)
        key = record.__key__()
        self.assertEqual(key, ("connections",))

    def test_key_with_id(self) -> None:
        record = Record({"id": "CONN-001"}, self.api, self.endpoint)
        key = record.__key__()
        self.assertEqual(key, ("connections", "CONN-001"))

    def test_parse_values_dict_with_class_attribute_model(self) -> None:
        class CustomRecord(Record):
            nested = Record

        record = CustomRecord(
            {"id": "CONN-001", "nested": {"id": "N-001", "name": "Nested"}},
            self.api,
            self.endpoint,
        )
        self.assertIsInstance(record.nested, Record)
        self.assertEqual(record.nested.id, "N-001")

    def test_parse_values_list_with_dicts_default_model(self) -> None:
        record = Record(
            {"id": "CONN-001", "children": [{"id": "C-001"}, {"id": "C-002"}]},
            self.api,
            self.endpoint,
        )
        self.assertEqual(len(record.children), 2)
        self.assertIsInstance(record.children[0], Record)
        self.assertEqual(record.children[0].id, "C-001")

    def test_parse_values_list_with_class_attribute_model(self) -> None:
        class CustomRecord(Record):
            children = [Record]

        record = CustomRecord(
            {"id": "CONN-001", "children": [{"id": "C-001"}]},
            self.api,
            self.endpoint,
        )
        self.assertIsInstance(record.children[0], Record)
        self.assertEqual(record.children[0].id, "C-001")

    def test_serialize_init(self) -> None:
        record = Record({"id": "CONN-001", "name": "Original"}, self.api, self.endpoint)
        record.name = "Modified"

        serialized = record.serialize(init=True)
        self.assertEqual(serialized["name"], "Original")

        serialized = record.serialize()
        self.assertEqual(serialized["name"], "Modified")

    def test_serialize_init_with_nested_record(self) -> None:
        class WithNested(Record):
            nested = Record

        record = WithNested({"id": "CONN-001", "nested": {"id": "N-001"}}, self.api, self.endpoint)
        # setattr to satisfy the type checker (nested is a class attr).
        setattr(record, "nested", Record({"id": "N-002"}, self.api, self.endpoint))

        self.assertEqual(record.serialize(init=True)["nested"], "N-001")
        self.assertEqual(record.serialize()["nested"], "N-002")

    def test_diff_with_dict_values(self) -> None:
        record = Record(
            {"id": "CONN-001", "meta": {"key": "value"}},
            self.api,
            self.endpoint,
        )
        record.meta = {"key": "changed"}

        diff = record._diff()
        self.assertIn("meta", diff)

    def test_updates_detects_nested_dict_value_change(self) -> None:
        # Value-only change in a nested dict (Hashabledict hashes keys only).
        record = Record({"id": "CONN-001", "meta": {"vlan": 10, "label": "primary"}}, self.api, self.endpoint)
        record.meta = {"vlan": 20, "label": "primary"}

        updates = record.updates()
        self.assertIn("meta", updates)
        self.assertEqual(updates["meta"], {"vlan": 20, "label": "primary"})

    def test_diff_distinguishes_list_with_comma_element(self) -> None:
        # Lists compare structurally, so ["a,b"] differs from ["a", "b"].
        record = Record({"id": "CONN-001", "tags": ["a,b"]}, self.api, self.endpoint)
        record.tags = ["a", "b"]
        self.assertIn("tags", record._diff())

    def test_diff_with_list_values(self) -> None:
        record = Record(
            {"id": "CONN-001", "tags": ["a", "b"]},
            self.api,
            self.endpoint,
        )
        record.tags = ["a", "c"]

        diff = record._diff()
        self.assertIn("tags", diff)

    def test_updates_with_falsy_id(self) -> None:
        record = Record({"id": "", "name": "Test"}, self.api, self.endpoint)
        record.name = "Modified"
        updates = record.updates()
        self.assertEqual(updates, {})

    def test_save_patch_returns_falsy(self) -> None:
        record = Record({"id": "CONN-001", "name": "Original"}, self.api, self.endpoint)
        record.name = "Modified"

        self.api.http_session.patch.return_value = Response(content={})
        result = record.save()
        self.assertFalse(result)

    def test_update_no_changes(self) -> None:
        record = Record({"id": "CONN-001", "name": "Connection 1"}, self.api, self.endpoint)
        result = record.update({"name": "Connection 1"})
        self.assertFalse(result)

    def test_make_request_builds_correct_url(self) -> None:
        self.api.user_agent = "test/1.0"

        record = Record({"id": "CONN-001"}, self.api, self.endpoint)
        request = record._make_request("statistics")

        self.assertIn("CONN-001", request.url)
        self.assertIn("statistics", request.url)
        self.assertIn("connections", request.url)
