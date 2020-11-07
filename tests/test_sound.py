#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_sound
==========

Tests for the Sound class of the `maniphono` package.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono

# TODO: test more sounds


class TestSound(unittest.TestCase):
    """
    Suite of tests for sounds.
    """

    def test_from_grapheme(self):
        snd1 = maniphono.Sound(maniphono.IPA, "p")
        snd2 = maniphono.Sound(maniphono.Tresoldi, "a")

        assert repr(snd1) == "voiceless bilabial plosive consonant"
        assert (
            repr(snd2)
            == "low non-back non-high non-sibilant non-strident distributed "
            + "anterior non-constricted non-spread voice dorsal non-labial non-click "
            + "coronal place non-lateral laryngeal syllabic tense non-consonantal "
            + "non-nasal approximant continuant sonorant"
        )

    def test_from_description(self):
        snd1 = maniphono.Sound(
            maniphono.IPA, description="voiceless bilabial plosive consonant"
        )
        snd2 = maniphono.Sound(
            maniphono.Tresoldi,
            description="anterior approximant non-back non-click non-consonantal "
            "non-constricted continuant coronal distributed dorsal non-high "
            "non-labial laryngeal non-lateral low non-nasal place non-sibilant "
            "sonorant non-spread non-strident syllabic tense voice",
        )

        assert str(snd1) == "p"
        assert str(snd2) == "a"

    # TODO: test add_value return
    def test_add_value(self):
        snd1 = maniphono.Sound(maniphono.IPA, "p")
        snd1.add_value("voiced")

        assert str(snd1) == "b"

    def test_add_operator(self):
        """
        Single test of the `add` operator.

        This only tests the method; tests of good results are performed in
        `test_operation()`.
        """

        # Test a simple addition
        snd = maniphono.Sound(maniphono.IPA, "p")
        snd += "voiced;aspirated"
        assert str(snd) == "bʰ"

        # Add a value alrady in the sound
        snd += "voiced"
        assert str(snd) == "bʰ"

    def test_sub_operator(self):
        """
        Single test of the `sub` operator.

        This only tests the method; tests of good results are performed in
        `test_operation()`.
        """
        snd = maniphono.Sound(
            maniphono.IPA, description="voiced bilabial aspirated plosive consonant"
        )
        snd -= "aspirated"
        assert str(snd) == "b"

    def test_cache(self):
        """
        Test the Sound cache.
        """

        snd = maniphono.Sound(maniphono.IPA, "b")
        assert str(snd) == "b"
        assert str(snd) == "b"
        assert repr(snd) == "voiced bilabial plosive consonant"
        assert repr(snd) == "voiced bilabial plosive consonant"

    def test_operation(self):
        ADD_TESTS = [
            ["p", "voiced", "b"],
            ["p", "voiced,aspirated", "bʰ"],
            ["m", "alveolar", "n"],
            ["ɴ", "voiceless", "ɴ̥"],
            ["t", "ejective,retroflex", "ʈʼ"],
            ["ɹ", "lateral", "l"],
            ["s", "non-sibilant", "ç[alveolar]"],
            ["i", "back", "ɯ"],
            ["ɜ", "rounded", "ɞ"],
            ["n", "syllabic", "n̩"],
            ["t", "aspirated", "tʰ"],
            ["d", "dental", "b̪"],
            ["d", "labialized", "dʷ"],
            ["d", "velarized", "dˠ"],
            ["a", "pharyngealized", "aˤ"],
            ["d", "palatalized", "dʲ"],
            ["t", "aspirated,labialized", "tʰʷ"],
            #            ["e", "nasalized", "ẽ"],
        ]

        for test in ADD_TESTS:
            source, values, target = test
            snd1 = maniphono.Sound(maniphono.IPA, source)
            snd2 = snd1 + values
            assert target == str(snd2)


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSound)
    unittest.TextTestRunner(verbosity=2).run(suite)
