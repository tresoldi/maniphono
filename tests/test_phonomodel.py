"""
test_phonomodel
===============

Tests for the PhonoModel class of the `maniphono` package.
"""

# Import Python libraries
from pathlib import Path
import pytest

# Import the library itself
import maniphono

TEST_DIR = Path(__file__).parent.absolute()

# TODO: add test with disjunctions, fix other tests
def test_parse_constraints():
    """
    Test constraint parsing and exceptions.
    """

    # Test single value
    ret = maniphono.phonomodel.parse_constraints("consonant")
    assert len(ret) == 1
    assert len(ret[0]) == 1
    assert ret[0][0] == {"type": "presence", "fvalue": "consonant"}

    # Test multiple values with positive and negative
    ret = maniphono.phonomodel.parse_constraints("+cons;plos/-voiceless;!front")
    assert len(ret) == 4
    assert len(ret[0]) == 1
    assert ret[3][0] == {"type": "absence", "fvalue": "front"}

    # Test invalid value names
    with pytest.raises(ValueError):
        maniphono.phonomodel.parse_constraints("a123")
    with pytest.raises(ValueError):
        maniphono.phonomodel.parse_constraints("+a123")
    with pytest.raises(ValueError):
        maniphono.phonomodel.parse_constraints("-a123")


# TODO add more MIPA assertions, including sounds
def test_mipa():
    """
    Test the MIPA model.
    """

    # Note that these will already be indirectly tested when running the other
    # tests, but it is still good to have a single test for this, doing
    # it "manually".
    _mipa = maniphono.PhonoModel("mipa")

    assert len(_mipa.features) == 20
    assert "length" in _mipa.features
    assert "long" in _mipa.features["length"]

    assert _mipa.fvalues["vowel"]["rank"] == 1


# TODO add more TRESOLDI assertions, including sounds
def test_tresoldi():
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

    assert _tresoldi.fvalues["click"]["rank"] == 12


def test_custom_models():
    """
    Test the custom models.
    """

    # Valid model
    model_a = maniphono.PhonoModel("A", TEST_DIR / "test_models" / "a")
    assert len(model_a.features) == 5

    # Invalid feature name
    with pytest.raises(ValueError):
        maniphono.PhonoModel("B", TEST_DIR / "test_models" / "b")

    # Invalid value name
    with pytest.raises(ValueError):
        maniphono.PhonoModel("C", TEST_DIR / "test_models" / "c")

    # Duplicate value name
    with pytest.raises(ValueError):
        maniphono.PhonoModel("D", TEST_DIR / "test_models" / "d")

    # Invalid rank value
    with pytest.raises(ValueError):
        maniphono.PhonoModel("E", TEST_DIR / "test_models" / "e")

    # Invalid value name in constraint
    with pytest.raises(ValueError):
        maniphono.PhonoModel("F", TEST_DIR / "test_models" / "f")

    # Duplicate description in sounds
    with pytest.raises(ValueError):
        maniphono.PhonoModel("G", TEST_DIR / "test_models" / "g")

    # Invalid fvalue name in sound description
    with pytest.raises(ValueError):
        maniphono.PhonoModel("H", TEST_DIR / "test_models" / "h")

    # Constraint not met in sound description
    with pytest.raises(ValueError):
        maniphono.PhonoModel("I", TEST_DIR / "test_models" / "i")


def test_values2graphemes():
    s = maniphono.model_mipa.fvalues2graphemes("+vowel +front -close")
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


# TODO: add test with other models
def test_minimal_matrix():
    mtx = maniphono.model_mipa.minimal_matrix(["t", "d"])
    assert len(mtx) == 2
    assert len(mtx["voiceless", "alveolar", "plosive", "consonant"]) == 1  # /t/
    assert (
        mtx["voiceless", "alveolar", "plosive", "consonant"]["phonation"] == "voiceless"
    )  # /t/
    assert "manner" not in mtx["voiced", "alveolar", "plosive", "consonant"]  # /d/

    vct = maniphono.model_mipa.minimal_matrix(["t", "d"], vector=True)
    assert len(vct) == 2
    assert tuple(vct[0].items()) == (("phonation", "voiceless"),)

    mtx = maniphono.model_mipa.minimal_matrix(["t", "d", "s"])
    assert len(mtx) == 3
    assert len(mtx["voiceless", "alveolar", "plosive", "consonant"]) == 2  # /t/
    assert (
        mtx["voiceless", "alveolar", "plosive", "consonant"]["phonation"] == "voiceless"
    )  # /t/
    assert "manner" in mtx["voiced", "alveolar", "plosive", "consonant"]  # /d/


# TODO: add test with other models
def test_class_features():
    cf = maniphono.model_mipa.class_features(["t", "d"])
    assert len(cf) == 3
    assert cf["place"] == "alveolar"

    cf = maniphono.model_mipa.class_features(["t", "d", "s"])
    assert len(cf) == 2
    assert cf["type"] == "consonant"


# TODO: add test with other models
def test_value_vector():
    fnames, vec = maniphono.model_mipa.fvalue_vector("a")
    assert len(fnames) == 64
    assert fnames[0] == "aspiration_aspirated"
    assert vec[0] is False

    fnames, vec = maniphono.model_mipa.fvalue_vector("a", categorical=True)
    assert len(fnames) == 20
    assert fnames[0] == "aspiration"
    assert vec[0] is None


def test_parse_grapheme():
    TESTS = {
        "a": ("unrounded", "open", "front", "vowel"),
        "b": ("voiced", "bilabial", "plosive", "consonant"),
        "p[voiced]": ("voiced", "bilabial", "plosive", "consonant"),
        "b[voiceless]": ("voiceless", "bilabial", "plosive", "consonant"),
    }
    for grapheme, ref in TESTS.items():
        ret, partial = maniphono.model_mipa.parse_grapheme(grapheme)
        assert ref == ret
        assert partial is False


def test_str():
    assert (
        str(maniphono.model_mipa)
        == "[`mipa` model (20 features, 64 fvalues, 226 graphemes)]"
    )
    assert (
        str(maniphono.model_tresoldi)
        == "[`tresoldi` model (30 features, 60 fvalues, 570 graphemes)]"
    )
