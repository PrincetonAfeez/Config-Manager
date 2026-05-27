""" Tests for dotenv parser module """

import unittest

from config_manager.dotenv import parse_dotenv
from config_manager.errors import ParseError


class DotenvParserTests(unittest.TestCase):
    def test_parse_supported_syntax(self):
        parsed = parse_dotenv(
            """
            # comment
            APP_NAME=Demo
            export DEBUG=true # inline
            PASSWORD="abc#123"
            SINGLE='quoted value'
            MULTI=hello\\
            world
            """
        )
        self.assertEqual(parsed["APP_NAME"], "Demo")
        self.assertEqual(parsed["DEBUG"], "true")
        self.assertEqual(parsed["PASSWORD"], "abc#123")
        self.assertEqual(parsed["SINGLE"], "quoted value")
        self.assertEqual(parsed["MULTI"], "helloworld")

    def test_malformed_line_has_parse_error(self):
        with self.assertRaises(ParseError) as ctx:
            parse_dotenv("DATABASE_PORT")
        self.assertIn("line 1", str(ctx.exception))

    def test_duplicate_key_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse_dotenv("APP_NAME=one\nAPP_NAME=two\n")
        self.assertIn("duplicate key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
