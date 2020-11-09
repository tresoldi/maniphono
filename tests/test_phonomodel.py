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

    # TODO: add test with disjunctions, fix other tests
    def test_parse_constraints(self):
        """
        Test constraint parsing and exceptions.
        """

        # Test single value
        ret = maniphono.phonomodel.parse_constraints("consonant")
        assert len(ret) == 1
        assert len(ret[0]) == 1
        assert ret[0][0] == {"type": "presence", "value": "consonant"}

        # Test multiple values with positive and negative
        ret = maniphono.phonomodel.parse_constraints("+cons;plos/-voiceless;!front")
        assert len(ret) == 4
        assert len(ret[0]) == 1
        assert ret[3][0] == {"type": "absence", "value": "front"}

        # Test invalid value names
        with self.assertRaises(ValueError):
            maniphono.phonomodel.parse_constraints("a123")
        with self.assertRaises(ValueError):
            maniphono.phonomodel.parse_constraints("+a123")
        with self.assertRaises(ValueError):
            maniphono.phonomodel.parse_constraints("-a123")

    # TODO add more IPA assertions, including sounds
    def test_ipa(self):
        """
        Test the IPA model.
        """

        # Note that these will already be indirectly tested when running the other
        # tests, but it is still good to have a single test for this, doing
        # it "manually".
        _mipa = maniphono.PhonoModel("mipa")

        assert len(_mipa.features) == 20
        assert "length" in _mipa.features
        assert "long" in _mipa.features["length"]

        assert _mipa.values["vowel"]["rank"] == 1

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

    def test_values2sounds(self):
        s = maniphono.model_mipa.values2sounds("+vowel +front -close")
        assert tuple(s) == (
            "a",
            "ã",
            "e",
            "ẽ",
            "æ",
            "æ̃",
            "ø",
            "ø̃",
            "œ",
            "œ̃",
            "ɛ",
            "ɛ̃",
            "ɪ",
            "ɪ̃",
            "ɶ",
            "ɶ̃",
            "ʏ",
            "ʏ̃",
        )

    def test_minimal_matrix(self):
        mtx = maniphono.model_mipa.minimal_matrix(["t", "d"])
        assert len(mtx) == 2
        assert len(mtx["t"]) == 1
        assert mtx["t"]["phonation"] == "voiceless"
        assert "manner" not in mtx["d"]

        mtx = maniphono.model_mipa.minimal_matrix(["t", "d", "s"])
        assert len(mtx) == 3
        assert len(mtx["t"]) == 2
        assert mtx["t"]["phonation"] == "voiceless"
        assert "manner" in mtx["d"]


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhonoModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
