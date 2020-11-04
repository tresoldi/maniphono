#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_maniphono
==============

Tests for the `maniphono` package.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono

# Set home page, for loading resources, etc.
HOME_PATH = Path(__file__).parent.parent.absolute()


class TestModel(unittest.TestCase):
    """
    Suite of tests for phonological models.
    """

    # TODO add more IPA assertions, including sounds
    def test_ipa(self):
        """
        Test the IPA model.
        """

        # Note that these will already be indirectly tested when running the other
        # tests, but it is still good to have a single test for this, doing
        # it "manually".
        _ipa = maniphono.PhonoModel("ipa", HOME_PATH / "models" / "ipa")

        assert len(_ipa.features) == 15
        assert "length" in _ipa.features
        assert "long" in _ipa.features["length"]

        assert _ipa.weights["vowel"] == 1

    # TODO add more TRESOLDI assertions, including sounds
    def test_tresoldi(self):
        """
        Test the TRESOLDI model.
        """

        # Note that these will already be indirectly tested when running the other
        # tests, but it is still good to have a single test for this, doing
        # it "manually".
        _tresoldi = maniphono.PhonoModel("tresoldi", HOME_PATH / "models" / "tresoldi")

        assert len(_tresoldi.features) == 30
        assert "anterior" in _tresoldi.features
        assert "non-anterior" in _tresoldi.features["anterior"]

        assert _tresoldi.weights["click"] == 12


class TestManiphono(unittest.TestCase):
    """
    Suite of tests for the `maniphono` library.
    """

    def test_dummy(self):
        assert 1 == 1


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestModel)
    unittest.TextTestRunner(verbosity=2).run(suite)

    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManiphono)
    unittest.TextTestRunner(verbosity=2).run(suite)
