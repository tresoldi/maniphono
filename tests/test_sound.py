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
        snd = maniphono.Sound(maniphono.IPA, "p")
        snd += "voiced;aspirated"

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

        print(snd.values)

        assert str(snd) == "b"

    def test_operation(self):
        pass


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSound)
    unittest.TextTestRunner(verbosity=2).run(suite)
