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


# def test_build_write_load_regressor():
#     # We load a different copy of MIPA, so as not to interfere with the
#     # other tests.
#     model_a = maniphono.PhonoModel("mipa")
#     model_b = maniphono.PhonoModel("mipa")
#     model_c = maniphono.PhonoModel("mipa")
#
#     # We load a temporary file name. Note that the reusage of the name is
#     # not guaranteed in all platforms, but should always work on Linux
#     handler = tempfile.NamedTemporaryFile()
#     tempname = handler.name
#     handler.close()
#
#     # Build regressor, save, and load
#     model_a.build_regressor()
#     model_a.write_regressor(tempname)
#     model_b.build_regressor(filename=tempname)
#
#     assert model_a.distance("a", "e") == pytest.approx(model_b.distance("a", "e"))
#
#     with pytest.raises(RuntimeError):
#         model_c.build_regressor(filename="dummyfilename")
