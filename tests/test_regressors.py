#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_regressor
===============

Tests for the various regressors and mroe computationally intensive
tests, that we don't need to execute every single time.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono


class TestRegressor(unittest.TestCase):
    """
    Suite of tests for regressors and other ML methods.
    """

    def test_distance(self):
        dist1 = maniphono.model_mipa.distance("a", "a")
        dist2 = maniphono.model_mipa.distance("a", "e")
        dist3 = maniphono.model_mipa.distance("a", "ʒ")

        assert dist1 == 0.0
        assert dist2 > dist1
        assert dist3 > dist2


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRegressor)
    unittest.TextTestRunner(verbosity=2).run(suite)
