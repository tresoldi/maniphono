#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_maniphono
==============

Tests for the `maniphono` package.
"""

# Import Python libraries
import unittest

# Import the library itself
# TODO: don't import with *
from maniphono import *


class TestManiphono(unittest.TestCase):
    """
    Suite of tests for the `maniphono` library.
    """

    def test_dummy(self):
        assert 1 == 1


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManiphono)
    unittest.TextTestRunner(verbosity=2).run(suite)
