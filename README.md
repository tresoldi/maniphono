# maniphono


[![PyPI](https://img.shields.io/pypi/v/maniphono.svg)](https://pypi.org/project/maniphono)
![build](https://github.com/tresoldi/maniphono/workflows/Python%20package/badge.svg)

Python library for the symbolic manipulation of phoneme representations

## Installation

In any standard Python environment, `maniphono` can be installed with:

```bash
$ pip install maniphono
```

## Introduction
`maniphono` is a library for the symbolic manipulation of phonological units.

The main components of the library are `PhonoModels`, which define different models and
sounds, and actual abstractions.

Models have two main components: the description of features and values and the
description of sounds.

The actual abstractions are organized in levels of nested complexity, as follows:

    - `Sounds` are the basic units, defined as lists of features
    - `Segments` are collections of one or more sounds
    - `Sequences` are collections of one or more segments

## Usage

The library is intended to be used as normal Python package, trying to follow the
conventions and expectations of its programming language. A few decisions on
implementation might fall short in this principle, but they are justified by the future
plans of offering an equivalent interface in different programming languages that can
easily used on client browser connections and/or compiled to machine code for easier
parallel processing.

The library is imported as expected. It is currently distributed with two models,
`mipa` and `tresoldi`, which offer a modified version of IPA and one of full binary
distinctive features that is intended mostly for machine learning approaches. In all
cases, the `mipa` model is used as default.

```python
>>> import maniphono
>>> print(maniphono.model_mipa)
[`mipa` model (20 features, 63 values, 224 graphemes)]
>>> print(maniphono.model_tresoldi)
[`tresoldi` model (30 features, 60 values, 570 graphemes)]
```

### Sounds

A `Sound` can be initialized either with a grapheme, by default, or a description.
Descriptions can be either a list of values or a string listing different values and
separated by a standard delimiter such as spaces or commas. A model must also be
provided, defaulting to `mipa` as mentioned above. Segments can be "visualized"
with `str()`, returning a graphemic representation, or with `repr()`, returned a
descriptive representation.

```python
>>> snd1 = maniphono.Sound("p")
>>> str(snd1), repr(snd1)
('p', 'voiceless bilabial plosive consonant')
>>> snd2 = maniphono.Sound(description="voiceless bilabial plosive consonant")
>>> str(snd2), repr(snd2)
('p', 'voiceless bilabial plosive consonant')
>>> snd3 = maniphono.Sound("a", model=maniphono.model_tresoldi)
>>> str(snd3), repr(snd3)
('a', 'low non-back non-high non-sibilant non-strident distributed anterior non-constricted non-spread voice dorsal non-labial non-click coronal place non-lateral laryngeal syllabic tense non-consonantal non-nasal approximant continuant sonorant')
```

The easiest way to manipulate sounds is using the add (`+`) and sub (`-`) operators, which
accept both single and multiple values. If a value from a feature that
is already set is added, it will be replaced.

```python
>>> snd1 += 'voiced'
>>> str(snd1), repr(snd1)
('b', 'voiced bilabial plosive consonant')
>>> snd2 += 'velar,aspirated,labialized'
>>> str(snd2), repr(snd2)
('kʰʷ', 'labialized aspirated voiceless velar plosive consonant')
>>> snd2 -= 'aspirated'
>>> str(snd2), repr(snd2)
('kʷ', 'labialized voiceless velar plosive consonant')
```

A dictionary of features and values can be easily obtained:

```python
>>> snd2.feature_dict()
{'phonation': 'voiceless', 'manner': 'plosive', 'type': 'consonant', 'place': 'velar', 'labialization': 'labialized'}
```

If a grapheme is not available, either because the sound is not complete or because no
diacritic is offered in the model, the library will try to be explicit about its
representation.

```python
>>> snd4 = maniphono.Sound(description="voiceless consonant")
>>> str(snd4), repr(snd4)
('C̥', 'voiceless consonant')
```

While the results are technically correct, the library still needs work for
always returning good representations when it computes the grapheme.

```python
>>> snd5 = maniphono.Sound("kʰʷ[voiced]")
>>> str(snd5), repr(snd5)
('ɡʰʷ', 'labialized aspirated voiced velar plosive consonant')
```

### Segments

Segments can combine sounds of different models. The decision of what makes up a
segment is entirely up to the user; the class can be initialized with a `Sound`,
in case of monosonic segments, or with an ordered list of sounds.

Segments can be represented with `__str__` and can include a delimiter, by default
a `+` sign.

```python
>>> snd1 = maniphono.Sound("w")
>>> snd2 = maniphono.Sound("a")
>>> snd3 = maniphono.Sound("j", model=maniphono.model_tresoldi)
>>> seg1 = maniphono.Segment(snd1)
>>> seg2 = maniphono.Segment([snd2, snd3])
>>> seg3 = maniphono.Segment([snd1, snd2, snd3])
>>> str(seg1), str(seg2), str(seg3)
('w', 'a+j', 'w+a+j')
```

### Sequences

Sequences combine segments in order.

Sequences can be represented with `__str__` and always use a white space as a delimiter
(following CLDF convention) as well as leading and trailing square brackets (`[` and `]`).

```python
>>> snd1, snd2, snd3 = maniphono.Sound("p"), maniphono.Sound("a"), maniphono.Sound("w")
>>> seg1, seg2, seg3 = maniphono.Segment(snd1), maniphono.Segment(snd2), maniphono.Segment([snd3])
>>> seg4 = maniphono.Segment([snd2, snd3])
>>> str(seg1), str(seg2), str(seg3), str(seg4)
('p', 'a', 'w', 'a+w')
>>> seq1 = maniphono.Sequence([seg1, seg2])
>>> seq2 = maniphono.Sequence([seg1, seg2, seg3])
>>> seq3 = maniphono.Sequence([seg1, seg4])
>>> seq4 = maniphono.Sequence([seg1, seg2, seg3, seg1, seg4])
>>> str(seq1), str(seq2), str(seq3), str(seq4)
('[p a]', '[p a w]', '[p a+w]', '[p a w p a+w]')
```

### Operations

`PhonoModel` offers a number of auxiliary methods.

The `.values2sounds()` method will take a list of value constraints, both in terms of
presence and absence, and returned an order list of all graphemes defined in the model
that satisfy the constraint.

```python
>>> maniphono.model_mipa.values2graphemes("+vowel +front -close")
['a', 'ã', 'e', 'ẽ', 'æ', 'æ̃', 'ø', 'ø̃', 'œ', 'œ̃', 'ɛ', 'ɛ̃', 'ɪ', 'ɪ̃', 'ɶ', 'ɶ̃', 'ʏ', 'ʏ̃']
```

The `.minimal_matrix()` method will take a list of graphemes and return a dictionary
with the minimum set of features in which they differ.

```python
>>> maniphono.model_mipa.minimal_matrix(["t", "d"])
{'t': {'phonation': 'voiceless'}, 'd': {'phonation': 'voiced'}}
>>> dict(maniphono.model_mipa.minimal_matrix(["t", "d", "s"]))
{'t': {'manner': 'plosive', 'phonation': 'voiceless'}, 'd': {'manner': 'plosive', 'phonation': 'voiced'}, 's': {'manner': 'fricative', 'phonation': 'voiceless'}}
```

Similarly, the `.class_features()` method will take a list of graphemes and return a
dictionary of features and values the graphemes have in common. It can be used to
discover what features make up a class with these sounds.

```python
>>> maniphono.model_mipa.class_features(["t", "d"])
{'place': 'alveolar', 'type': 'consonant', 'manner': 'plosive'}
>>> maniphono.model_mipa.class_features(["t", "d", "s"])
{'place': 'alveolar', 'type': 'consonant'}
```

The `.value_vector()` method will take a grapheme and return a list of feature names
and a boolean vector of presence/absence. It is mostly intended for machine learning
projects; for human explorations or categorical machine learning, there is an option
to return non-binary vectors.

```python
>>> maniphono.model_mipa.value_vector("a")
(['aspiration_aspirated', 'centrality_back', 'centrality_central', 'centrality_front', 'centrality_near-back', 'centrality_near-front', 'ejection_ejective', 'height_close', 'height_close-mid', 'height_mid', 'height_near-close', 'height_near-open', 'height_open', 'height_open-mid', 'labialization_labialized', 'laterality_lateral', 'length_half-long', 'length_long', 'manner_affricate', 'manner_approximant', 'manner_click', 'manner_flap', 'manner_fricative', 'manner_implosive', 'manner_plosive', 'manner_trill', 'nasality_nasal', 'nasalization_nasalized', 'palatalization_palatalized', 'pharyngealization_pharyngealized', 'phonation_voiced', 'phonation_voiceless', 'place_alveolar', 'place_alveolo-palatal', 'place_bilabial', 'place_dental', 'place_epiglottal', 'place_glottal', 'place_labial', 'place_labio-alveolar', 'place_labio-coronal', 'place_labio-dental', 'place_labio-palatal', 'place_labio-velar', 'place_linguo-labial', 'place_palatal', 'place_palato-velar', 'place_pharyngeal', 'place_post-alveolar', 'place_retroflex', 'place_uvular', 'place_uvulo-epiglottal', 'place_velar', 'roundness_rounded', 'roundness_unrounded', 'sibilancy_non-sibilant', 'sibilancy_sibilant', 'syllabicity_non-syllabic', 'syllabicity_syllabic', 'type_consonant', 'type_vowel', 'uvularization_uvularized', 'velarization_velarized'], [False, False, False, True, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, True, False, False])
>>> maniphono.model_mipa.value_vector("a", binary=False)
(['aspiration', 'centrality', 'ejection', 'height', 'labialization', 'laterality', 'length', 'manner', 'nasality', 'nasalization', 'palatalization', 'pharyngealization', 'phonation', 'place', 'roundness', 'sibilancy', 'syllabicity', 'type', 'uvularization', 'velarization'], [None, 'front', None, 'open', None, None, None, None, None, None, None, None, None, None, 'unrounded', None, None, 'vowel', None, None])
```

All models allow to compute a distance between two sounds, with the distance between a sound and
itself set, by design, to zero. In some cases this experimental method will compute and cache
and `sklearn` regressor, which can take a while.

```python
>>> maniphono.model_mipa.distance("a", "a")
0.0
>>> maniphono.model_mipa.distance("a", "e")
3.7590891821444608
>>> maniphono.model_mipa.distance("a", "ʒ")
30.419280377524366
```
