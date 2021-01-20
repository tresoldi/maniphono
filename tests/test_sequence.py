#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_sequence
=============

Tests for the Sequence class of the `maniphono` package.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono


class TestSequence(unittest.TestCase):
    """
    Suite of tests for sequences.
    """

    def test_from_segments(self):
        # Define the sounds that will be used
        snd1 = maniphono.Sound("p")
        snd2 = maniphono.Sound("a")
        snd3 = maniphono.Sound("w")

        # Define the segments that will be used
        seg1 = maniphono.SoundSegment(snd1)
        seg2 = maniphono.SoundSegment(snd2)
        seg3 = maniphono.SoundSegment([snd2, snd3])

        # Test single-sound sequence
        seq1 = maniphono.Sequence([seg1])
        assert len(seq1) == 1
        assert str(seq1) == "[# p #]"

        # Test two-sound sequence (without diphthong)
        seq2 = maniphono.Sequence([seg1, seg2])
        assert len(seq2) == 2
        assert str(seq2) == "[# p a #]"

        # Test two-sound sequence (with diphthong)
        seq3 = maniphono.Sequence([seg1, seg3])
        assert len(seq3) == 2
        assert str(seq3) == "[# p a+w #]"

        # Test complex sequence
        seq4 = maniphono.Sequence([seg1, seg2, seg1, seg3])
        assert len(seq4) == 4
        assert str(seq4) == "[# p a p a+w #]"


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequence)
    unittest.TextTestRunner(verbosity=2).run(suite)
