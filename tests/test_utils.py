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
        assert maniphono.codepoint2glyph("U+0283") == "ʃ"

    def test_replace_codepoints(self):
        assert maniphono.replace_codepoints("aU+0283o") == "aʃo"

    def test_read_distance_matrix(self):
        dm = maniphono.read_distance_matrix()
        assert len(dm) == 181
        self.assertAlmostEqual(dm["a"]["b"], 9.42, places=2)


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
