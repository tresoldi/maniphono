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

# TODO: add test with disjunctions
@pytest.mark.parametrize(
    "constraint,parsed_len,test_type,test_fvalue",
    [
        ["consonant", 1, "presence", "consonant"],
        ["+cons;plos/-voiceless;!front", 4, "absence", "front"],
    ],
)
def test_parse_constraints(constraint, parsed_len, test_type, test_fvalue):
    """
    Test constraint parsing and exceptions.
    """

    parsed = maniphono.phonomodel.parse_constraints(constraint)
    assert len(parsed) == parsed_len
    assert len(parsed[0]) == 1
    assert {"type": test_type, "fvalue": test_fvalue} in [entry[0] for entry in parsed]


@pytest.mark.parametrize(
    "constraint",
    [
        ["a123"],
        ["+a123"],
        ["-a123"],
    ],
)
def test_parse_contraints_errors(constraint):
    """
    Test if bad constraint strings are correctly handled.
    """

    # Test invalid value names
    with pytest.raises(ValueError):
        maniphono.phonomodel.parse_constraints(constraint)


# TODO add more MIPA assertions, including sounds
def test_mipa():
    """
    Test the MIPA model.
    """

    # Note that these will already be indirectly tested when running the other
    # tests, but it is still good to have a single test for this, doing
    # it "manually".
    _mipa = maniphono.HumanModel("mipa")

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
    _tresoldi = maniphono.HumanModel("tresoldi")

    assert len(_tresoldi.features) == 30
    assert "anterior" in _tresoldi.features
    assert "non-anterior" in _tresoldi.features["anterior"]
    assert _tresoldi.fvalues["click"]["rank"] == 12


def test_encoder():
    """
    Test the ENCODER model.
    """

    _encoder = maniphono.MachineModel("encoder")

    vector, _ = _encoder.parse_grapheme("a")
    grapheme, _ = _encoder.closest_grapheme(vector)

    assert grapheme == "a"


def test_custom_human_models():
    """
    Test the custom models.
    """

    # Valid model
    model_a = maniphono.HumanModel("A", TEST_DIR / "test_models" / "a")
    assert len(model_a.features) == 5

    # Invalid feature name
    with pytest.raises(ValueError):
        maniphono.HumanModel("B", TEST_DIR / "test_models" / "b")

    # Invalid value name
    with pytest.raises(ValueError):
        maniphono.HumanModel("C", TEST_DIR / "test_models" / "c")

    # Duplicate value name
    with pytest.raises(ValueError):
        maniphono.HumanModel("D", TEST_DIR / "test_models" / "d")

    # Invalid rank value
    with pytest.raises(ValueError):
        maniphono.HumanModel("E", TEST_DIR / "test_models" / "e")

    # Invalid value name in constraint
    with pytest.raises(ValueError):
        maniphono.HumanModel("F", TEST_DIR / "test_models" / "f")

    # Duplicate description in sounds
    with pytest.raises(ValueError):
        maniphono.HumanModel("G", TEST_DIR / "test_models" / "g")

    # Invalid fvalue name in sound description
    with pytest.raises(ValueError):
        maniphono.HumanModel("H", TEST_DIR / "test_models" / "h")

    # Constraint not met in sound description
    with pytest.raises(ValueError):
        maniphono.HumanModel("I", TEST_DIR / "test_models" / "i")


# TODO: add example with the `tresoldi` model
# fmt: off
@pytest.mark.parametrize(
    "model,fvalues,expected",
    [
        [
            maniphono.model_mipa,
            "+vowel +front -close +nasalized",
            ("ã", "ẽ", "æ̃", "ø̃", "œ̃", "ɛ̃", "ɪ̃", "ɶ̃", "ʏ̃"),
        ],
        [
            maniphono.model_tresoldi,
            "+syllabic +non-high +anterior +long",
            ("aː", "ãː", "eː", "ẽː", "æː", "æ̃ː", "øː", "ø̃ː", "œː", "œ̃ː", "ɛː", "ɛ̃ː", "ɶː", "ɶ̃ː"),
        ],
    ],
)
# fmt: on
def test_values2graphemes(model, fvalues, expected):
    graphemes = model.fvalues2graphemes(fvalues)
    assert tuple(graphemes) == expected


# TODO: add test with other models
@pytest.mark.parametrize(
    "graphemes,length,key,feature,fvalue,missing_feature",
    [
        [
            ["t", "d"],
            2,
            ["voiceless", "alveolar", "plosive", "consonant"],
            "phonation",
            "voiceless",
            "manner",
        ],
    ],
)
def test_minimal_matrix(graphemes, length, key, feature, fvalue, missing_feature):
    mtx = maniphono.model_mipa.minimal_matrix(graphemes)
    assert len(mtx) == length
    assert mtx[frozenset(key)][feature] == fvalue
    assert missing_feature not in mtx[frozenset(key)]


# TODO: add test with other models
@pytest.mark.parametrize(
    "graphemes,length,fvalues",
    [
        [["t", "d"], 2, ("phonation", "voiceless")],
    ],
)
def test_minimal_vector(graphemes, length, fvalues):
    vct = maniphono.model_mipa.minimal_vector(graphemes)
    assert len(vct) == length
    assert tuple(vct[0].items()) == (fvalues,)


# TODO: add test with other models
@pytest.mark.parametrize(
    "sounds,length,expected_feature,expected_fvalue",
    [
        [["t", "d"], 3, "place", "alveolar"],
        [["t", "d", "s"], 2, "type", "consonant"],
    ],
)
def test_class_features(sounds, length, expected_feature, expected_fvalue):
    cf = maniphono.model_mipa.class_features(sounds)
    assert len(cf) == length
    assert cf[expected_feature] == expected_fvalue


# TODO: add test with other models
@pytest.mark.parametrize(
    "sound,categorical,length,fname,value",
    [
        ["a", False, 64, "aspiration_aspirated", False],
        ["a", True, 20, "aspiration", None],
    ],
)
def test_value_vector(sound, categorical, length, fname, value):
    fnames, vec = maniphono.model_mipa.fvalue_vector(sound, categorical=categorical)
    assert len(fnames) == length
    assert fnames[0] == fname
    assert vec[0] is value


# TODO: add test with other models
# TODO: add tests with partials
@pytest.mark.parametrize(
    "grapheme,fvalues,ref_partial",
    [
        ["a", ["unrounded", "open", "front", "vowel"], False],
        ["b", ["voiced", "bilabial", "plosive", "consonant"], False],
        ["p[voiced]", ["voiced", "bilabial", "plosive", "consonant"], False],
        ["b[voiceless]", ["voiceless", "bilabial", "plosive", "consonant"], False],
    ],
)
def test_parse_grapheme(grapheme, fvalues, ref_partial):
    ret, partial = maniphono.model_mipa.parse_grapheme(grapheme)
    assert ret == frozenset(fvalues)
    assert partial is ref_partial


# fmt: off
@pytest.mark.parametrize(
    "fvalues,use_rank,expected",
    [
        [["unrounded", "open", "vowel", "front"], True, ("unrounded", "open", "front", "vowel")],
        [["unrounded", "open", "vowel", "front"], False, ("front", "open", "unrounded", "vowel")],
    ],
)
# fmt: on
def test_sort_fvalues(fvalues, use_rank, expected):
    assert (
        tuple(maniphono.model_mipa.sort_fvalues(fvalues, use_rank=use_rank)) == expected
    )


@pytest.mark.parametrize(
    "model,source,field,expected",
    [
        [maniphono.model_mipa, "a", "prosody", "7"],
        [maniphono.model_mipa, "open front unrounded vowel", "prosody", "7"],
        [maniphono.model_mipa, ("vowel", "unrounded", "front", "open"), "prosody", "7"],
        [maniphono.model_mipa, "b", "sca", "P"],
        [maniphono.model_mipa, "c", "dummy_feature", None],
        [maniphono.model_tresoldi, "t", "dolgopolsky", "T"],
    ],
)
def test_get_info(model, source, field, expected):
    assert model.get_info(source, field) == expected


# fmt: off
def test_str():
    assert str(maniphono.model_mipa) == "[`mipa` model (20 features, 64 fvalues, 231 graphemes)]"
    assert str(maniphono.model_tresoldi) == "[`tresoldi` model (30 features, 60 fvalues, 570 graphemes)]"
# fmt: on
