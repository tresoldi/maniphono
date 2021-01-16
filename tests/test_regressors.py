#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_regressor
===============

Tests for the various regressors and more computationally intensive
tests, that we don't need to execute every single time.
"""

# Import Python libraries
import unittest
from pathlib import Path
import tempfile

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

    def test_build_write_load_regressor(self):
        # We load a different copy of MIPA, so as not to interfere with the
        # other tests.
        model_a = maniphono.PhonoModel("mipa")
        model_b = maniphono.PhonoModel("mipa")
        model_c = maniphono.PhonoModel("mipa")

        # We load a temporary file name. Note that the reusage of the name is
        # not guaranteed in all platforms, but should always work on Linux
        handler = tempfile.NamedTemporaryFile()
        tempname = handler.name
        handler.close()

        # Build regressor, save, and load
        model_a.build_regressor()
        model_a.write_regressor(tempname)
        model_b.build_regressor(filename=tempname)

        self.assertAlmostEqual(
            model_a.distance("a", "e"), model_b.distance("a", "e"), places=4
        )

        with self.assertRaises(RuntimeError):
            model_c.build_regressor(filename="dummyfilename")


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRegressor)
    unittest.TextTestRunner(verbosity=2).run(suite)
