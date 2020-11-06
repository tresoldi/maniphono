#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_utils
==========

Tests for the `utils` module of the `maniphono` package.
"""

# Import Python libraries
import unittest

# Import the library itself
import maniphono


class TestUtils(unittest.TestCase):
    """
    Suite of tests for utility functions.
    """

    def test_codepoint2glyph(self):
        assert maniphono.codepoint2glyph("0283") == "ʃ"
        assert maniphono.codepoint2glyph("u0283") == "ʃ"
        assert maniphono.codepoint2glyph("X+0283") == "ʃ"


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
