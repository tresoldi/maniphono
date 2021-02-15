#!/usr/bin/env python3
# pylint: disable=no-self-use

"""
test_segment
============

Tests for the Segment class of the `maniphono` package.
"""

# Import Python libraries
import unittest
from pathlib import Path

# Import the library itself
import maniphono


class TestSegment(unittest.TestCase):
    """
    Suite of tests for segments.
    """

    def test_from_sounds(self):
        # Define the sounds that will be used
        snd0 = maniphono.Sound("w")
        snd1 = maniphono.Sound("a")
        snd2 = maniphono.Sound("j", model=maniphono.model_tresoldi)

        # Test single-sound segment
        seg1 = maniphono.SoundSegment(snd1)
        assert len(seg1) == 1
        assert str(seg1) == "a"

        # Test two-sound segment
        seg2 = maniphono.SoundSegment([snd1, snd2])
        assert len(seg2) == 2
        assert str(seg2) == "a+j"

        # Test three-sound segment
        seg3 = maniphono.SoundSegment([snd0, snd1, snd2])
        assert len(seg3) == 3
        assert str(seg3) == "w+a+j"


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile it
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSegment)
    unittest.TextTestRunner(verbosity=2).run(suite)
