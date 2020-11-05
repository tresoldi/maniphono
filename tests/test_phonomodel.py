#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_phonomodel
===============

Tests for the PhonoModel class of the `maniphono` package.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono


class TestPhonoModel(unittest.TestCase):
    """
    Suite of tests for phonological models.
    """

    def test_parse_constraints(self):
        """
        Test constraint parsing and exceptions.
        """

        # Test single value
        ret = maniphono.model.parse_constraints("consonant")
        assert ret["presence"] == {"consonant"}
        assert len(ret["absence"]) == 0

        # Test multiple values with positive and negative
        ret = maniphono.model.parse_constraints("+cons;plos/-voiceless;!front")
        assert tuple(sorted(ret["presence"])) == ("cons", "plos")
        assert tuple(sorted(ret["absence"])) == ("front", "voiceless")

        # Test invalid value names
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("a123")
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("+a123")
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("-a123")

        # Test duplicates
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("abc/+abc")
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("-abc/!abc")

        # Test inconsistency
        with self.assertRaises(ValueError):
            maniphono.model.parse_constraints("abc/-abc")

    # TODO add more IPA assertions, including sounds
    def test_ipa(self):
        """
        Test the IPA model.
        """

        # Note that these will already be indirectly tested when running the other
        # tests, but it is still good to have a single test for this, doing
        # it "manually".
        _ipa = maniphono.PhonoModel("ipa")

        assert len(_ipa.features) == 17
        assert "length" in _ipa.features
        assert "long" in _ipa.features["length"]

        assert _ipa.values["vowel"]["rank"] == 1

    # TODO add more TRESOLDI assertions, including sounds
    def test_tresoldi(self):
        """
        Test the TRESOLDI model.
        """

        # Note that these will already be indirectly tested when running the other
        # tests, but it is still good to have a single test for this, doing
        # it "manually".
        _tresoldi = maniphono.PhonoModel("tresoldi")

        assert len(_tresoldi.features) == 30
        assert "anterior" in _tresoldi.features
        assert "non-anterior" in _tresoldi.features["anterior"]

        assert _tresoldi.values["click"]["rank"] == 12


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhonoModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
