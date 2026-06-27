import unittest

from pyixapi.core.util import Hashabledict, cat


class HashabledictTestCase(unittest.TestCase):
    def test_equal_dicts_share_hash(self) -> None:
        self.assertEqual(hash(Hashabledict({"k": "v"})), hash(Hashabledict({"k": "v"})))

    def test_hash_is_keys_only_but_equality_is_by_value(self) -> None:
        # Hash depends on keys only; value differences are caught by __eq__, so
        # same-keys/different-values dicts remain distinct set members.
        a = Hashabledict({"k": "v1"})
        b = Hashabledict({"k": "v2"})
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, b)
        self.assertEqual(len({a, b}), 2)


class CatTestCase(unittest.TestCase):
    def test_basic_concatenation(self) -> None:
        self.assertEqual(cat("a", "b", "c"), "a/b/c")

    def test_coerces_non_strings(self) -> None:
        self.assertEqual(cat("a", 1, "b", 2), "a/1/b/2")

    def test_edge_separators_stripped(self) -> None:
        self.assertEqual(cat("a", "/b/", "c/"), "a/b/c")

    def test_empty_parts_skipped(self) -> None:
        self.assertEqual(cat("a", "", "b"), "a/b")

    def test_custom_separator(self) -> None:
        self.assertEqual(cat("a", "b", "c", separator="_"), "a_b_c")

    def test_custom_trailing(self) -> None:
        self.assertEqual(cat("a", "b", "c", trailing="/"), "a/b/c/")
