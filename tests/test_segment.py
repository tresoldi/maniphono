"""
test_segment
============

Tests for the Segment class of the `maniphono` package.
"""

# Import Python libraries
import pytest

# Import the library itself
import maniphono


def test_boundary_seg():
    seg = maniphono.BoundarySegment()
    assert str(seg) == "#"
    assert repr(seg) == "boundary_seg:#"


def test_from_sounds():
    # Define the sounds that will be used
    snd1 = maniphono.Sound("w")
    snd2 = maniphono.Sound("a")
    snd3 = maniphono.Sound("j", model=maniphono.model_tresoldi)

    # Test single-sound segment
    seg1 = maniphono.SoundSegment(snd2)
    assert len(seg1) == 1
    assert str(seg1) == "a"
    assert repr(seg1) == "sound_seg:a"

    # Test two-sound segment
    seg2 = maniphono.SoundSegment([snd2, snd3])
    assert len(seg2) == 2
    assert str(seg2) == "a+j"
    assert repr(seg2) == "sound_seg:a+j"

    # Test three-sound segment
    seg3 = maniphono.SoundSegment([snd1, snd2, snd3])
    assert len(seg3) == 3
    assert str(seg3) == "w+a+j"
    assert repr(seg3) == "sound_seg:w+a+j"


def test_add():
    snd1 = maniphono.Sound("p")
    snd2 = maniphono.Sound("a")
    seg1 = maniphono.SoundSegment([snd1])
    seg2 = maniphono.SoundSegment([snd1, snd2])

    seg1.add_fvalues("voiced")
    with pytest.raises(ValueError):
        seg2.add_fvalues("voiced")


def test_getitem():
    snd1 = maniphono.Sound("p")
    snd2 = maniphono.Sound("a")
    seg = maniphono.SoundSegment([snd1, snd2])

    assert str(seg[1]) == "a"


def test_hash():
    snd1 = maniphono.Sound("p")
    snd2 = maniphono.Sound("a")

    seg1 = maniphono.SoundSegment([snd1])
    seg2 = maniphono.SoundSegment([snd1, snd2])

    assert hash(seg1) != hash(seg2)


def test_eq_and_neq():
    snd1 = maniphono.Sound("p")
    snd2 = maniphono.Sound("a")

    seg1 = maniphono.SoundSegment([snd1])
    seg2 = maniphono.SoundSegment([snd1])
    seg3 = maniphono.SoundSegment([snd2])
    seg4 = maniphono.SoundSegment([snd1, snd2])

    assert seg1 == seg2
    assert seg1 != seg3
    assert seg1 != seg4


def test_parse_segment():
    assert repr(maniphono.parse_segment("#")) == "boundary_seg:#"
    assert str(maniphono.parse_segment("a")) == "a"
    assert str(maniphono.parse_segment("C")) == "C"
    assert str(maniphono.parse_segment("SVL")) == "SVL"
