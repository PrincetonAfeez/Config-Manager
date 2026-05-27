"""Tests for paths module"""

import unittest

from config_manager.paths import get_path, has_path, iter_leaf_paths


class PathsTests(unittest.TestCase):
    def test_get_path_supports_bracket_segments(self):
        data = {"items": [{"extra": "x", "id": 1}]}
        self.assertEqual(get_path(data, "items[0].extra"), "x")
        self.assertEqual(get_path(data, "items[0].id"), 1)

    def test_get_path_bracket_out_of_range(self):
        data = {"items": [{"extra": "x"}]}
        self.assertIsNone(get_path(data, "items[1].extra"))

    def test_has_path_with_brackets(self):
        data = {"items": [{"extra": "x"}]}
        self.assertTrue(has_path(data, "items[0].extra"))
        self.assertFalse(has_path(data, "items[0].missing"))

    def test_iter_leaf_paths_value_available_via_get_path(self):
        data = {"items": [{"extra": "surprise"}]}
        for path in iter_leaf_paths(data):
            self.assertIsNotNone(get_path(data, path))

    def test_scalar_list_paths(self):
        self.assertEqual(iter_leaf_paths({"features": ["a", "b"]}), ["features[0]", "features[1]"])


if __name__ == "__main__":
    unittest.main()
