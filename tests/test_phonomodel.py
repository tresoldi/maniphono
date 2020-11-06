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

TEST_DIR = Path(__file__).parent.absolute()


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

        assert len(_ipa.features) == 18
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

    def test_custom_models(self):
        """
        Test the custom models.
        """

        # Valid model
        model_a = maniphono.PhonoModel("A", TEST_DIR / "test_models" / "a")
        assert len(model_a.features) == 5

        # Invalid feature name
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("B", TEST_DIR / "test_models" / "b")

        # Invalid value name
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("C", TEST_DIR / "test_models" / "c")

        # Duplicate value name
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("D", TEST_DIR / "test_models" / "d")

        # Invalid rank value
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("E", TEST_DIR / "test_models" / "e")

        # Invalid value name in constraint
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("F", TEST_DIR / "test_models" / "f")

        # Duplicate description in sounds
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("G", TEST_DIR / "test_models" / "g")

        # Invalid value name in sound description
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("H", TEST_DIR / "test_models" / "h")

        # Constraint not met in sound description
        with self.assertRaises(ValueError):
            maniphono.PhonoModel("I", TEST_DIR / "test_models" / "i")


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhonoModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
