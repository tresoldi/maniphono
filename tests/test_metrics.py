"""
test_regressor
===============

Tests for the various regressors and more computationally intensive
tests, that we don't need to execute every single time.
"""

# Import Python libraries
import tempfile
import pytest

# Import the library itself
import maniphono

# Create and cache a regressor that is used by all tests not
# verifying directly regressor creation
REGRESSOR = maniphono.DistanceRegressor()


@pytest.mark.parametrize(
    "sound_x,sound_y,expected,tol",
    [
        ["a", "a", 0.0, 0.0],
        ["a", "e", 4.15, 1e-1],
        ["a", "ʒ", 28.16, 1e-1],
        ["a", "cː", 18.99, 1e-1],  # not in the model
    ],
)
def test_distance_hardcoded(sound_x, sound_y, expected, tol):
    """
    Test hard-coded distances.
    """
    assert REGRESSOR.distance(sound_x, sound_y) == pytest.approx(expected, abs=tol)


def test_distance():
    R = maniphono.DistanceRegressor()
    dist1 = R.distance("a", "a")
    dist2 = R.distance("a", "e")
    dist3 = R.distance("a", "ʒ")

    assert dist1 == 0.0
    assert dist2 > dist1
    assert dist3 > dist2

    dist4 = R.distance("a", "cː")  # not in the model
    assert dist4 > dist1
    assert dist4 > dist2
    assert dist4 < dist3


def test_distance_no_regressor():
    R = maniphono.DistanceRegressor(regtype=None)
    dist1 = R.distance("a", "a")
    dist2 = R.distance("a", "e")
    dist3 = R.distance("a", "ʒ")

    assert dist1 == 0.0
    assert dist2 > dist1
    assert dist3 > dist2

    with pytest.raises(KeyError):
        R.distance("a", "cː")  # not in the model


def test_build_write_load_regressor():
    # We load a temporary file name. Note that the reusage of the name is
    # not guaranteed in all platforms, but should always work on Linux
    handler = tempfile.NamedTemporaryFile()
    tempname = handler.name
    handler.close()

    # Build regressor, save, and load
    reg1 = maniphono.DistanceRegressor()
    reg1.build_regressor()
    reg1.write_regressor(tempname)

    reg2 = maniphono.DistanceRegressor(regressor_file=tempname)

    assert reg1.distance("a", "e") == pytest.approx(reg2.distance("a", "e"))

    with pytest.raises(RuntimeError):
        maniphono.DistanceRegressor(regressor_file="dummyfilename")
