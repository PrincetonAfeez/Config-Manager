"""Tests for coercion and validation modules"""

import unittest

from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.coercion import coerce_value
from config_manager.validation import collect_validation_issues


class CoercionTests(unittest.TestCase):
    def test_bool_from_int(self):
        self.assertTrue(coerce_value(1, Field(bool)))
        self.assertFalse(coerce_value(0, Field(bool)))

    def test_int_from_whole_float(self):
        self.assertEqual(coerce_value(5432.0, Field(int)), 5432)

    def test_combined_coercion_and_validation_errors(self):
        schema = Schema(
            {
                "app": {
                    "name": Field(str, required=True),
                    "port": Field(int),
                }
            }
        )
        with self.assertRaises(ConfigInvalidError) as ctx:
            load(
                schema,
                env={"MYAPP_APP__NAME": "Demo", "MYAPP_APP__PORT": "bad"},
                prefix="MYAPP",
            )
        paths = {issue.path for issue in ctx.exception.issues}
        self.assertIn("app.port", paths)


class ValidationTests(unittest.TestCase):
    def test_regex_uses_fullmatch(self):
        schema = Schema({"app": {"code": Field(str, regex=r"^[a-z]+$")}})
        issues = collect_validation_issues(
            {"app": {"code": "abc123"}},
            {"app": {"code": "abc123"}},
            schema,
            strict=True,
        )
        self.assertTrue(issues)

    def test_validator_rejects_falsy(self):
        schema = Schema({"app": {"name": Field(str, validator=lambda v: len(v) > 2)}})
        issues = collect_validation_issues(
            {"app": {"name": "ab"}},
            {"app": {"name": "ab"}},
            schema,
            strict=True,
        )
        self.assertTrue(issues)

    def test_secret_values_redacted_in_issue_format(self):
        schema = Schema({"database": {"password": Field(str, secret=True, min_length=8)}})
        issues = collect_validation_issues(
            {"database": {"password": "short"}},
            {"database": {"password": "short"}},
            schema,
            strict=True,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("********", issues[0].format())
        self.assertNotIn("short", issues[0].format())


if __name__ == "__main__":
    unittest.main()
