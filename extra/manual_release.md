::: {.example}
::: {.exampleMarkup}
    ```{.html .cb.code include_file=python.html include_regex="<header.*?/header>"}
    ```
:::

::: {.exampleOutput}
``` {.sourceError}
SOURCE ERROR in "extra/manual.md" near line 1:
Cannot include nonexistent file "python.html"
```
:::
:::

`maniphono` is a library for the manipulation of phonological units,
designed as a solution historical phonology. While offering two standard
models for operation, one modified from the IPA but following as much as
possible its descriptors and one using distinctive features which is
designed for machine learning, it is designed to support custom
phonological models, trying as much as possible to be agnostic about the
theoretical background. It also gives particular attention since design
stage to the role of suprasegmentals.

`maniphono` operates on a hierarchy of phonological abstractions, all
which are related in some way to a "phonological model" that serves as
the basis of all operations. This hierarchy is:

-   a "phonological model" comprises a set of features operating in a
    many-valued logic system: each `feature` may be either undefined or
    defined by defined by one and only one "feature value" (or
    `favalue`) and a map of sounds (given by their graphemes) and the
    feature values that define them
-   a "sound" is a bundle of zero or more feature values and is intended
    to mostly map individual abstract acoustic performances
-   a "segment" is a unit of analysis, as decided by the user; the most
    common segment is, by far, a "sound segment", which is a segment
    composed of one (monosonic segment) or more (polysonic segment)
    sounds
-   a "sequence" is an ordered collection of segments and a set of
    information on suprasegmental properties, such as syllable breaks,
    tones, etc.

Each unit is described in more detail in the subsequent sections. As as
set of examples, however:

-   `model_mipa` is the standard phonological model in `maniphono`,
    comprised (at the time of writing) of 20 features (such as `manner`
    and `length`), 64 fvalues (such as `affricate` and `approximant`,
    values of the `manner` feature, and `half-long` and `long`, values
    of the `length` feature), and 231 graphemes (such as `a`, defined as
    an `open front unrounded vowel`)
-   sounds are to a large extend phonological abstractions represented
    by a single IPA glyph (potentially with diacritics), such as
    `open front unrounded vowel` (that is, /a/) or
    `voiced alveolar non-sibilant lateral affricate consonant` (that is,
    /dɮ/). Sounds can also be "partial", in the sense that they are not
    fully defined and thus represent what is normally called a "class"
    of sounds, such as `glottal consonant` (represented by `H`)
-   a sound segment is intended as a unit of analysis, contingent to the
    user decisions. For example, a bisonic segment can be used to
    represent a diphthong in case they are supposed to be treated as a
    single unit of analysis (such as `/a+j/`, in `maniphono`'s
    notation), which is different from a sequence of two monosonic
    segments (that is, `/a j/`)
-   a sequence is a list of segments, such as `[p a p a+j]`, which is a
    sequence of four segments (the last of which is composed of two
    sounds). It can carry additional information, such as word
    boundaries as in `[# p a p a+j #]`, syllable breaks as in
    `[# p a . p a+j #]`, and tonal information as in
    `[# p a ˧˩ . p a+j ˨˦ #]`

## PhonoModel

By design, a "PhonoModel" works in a way independent

## Description

Mostly text based models, so it can be used in other systems and
programming languages.

bundle

segment

grapheme

model

The central concepts of a model are "features" and "values". A feature
is a set of one or more values that can be used to describe a sound or a
group of sounds (a "sound class"). For example, the "centrality"
feature, used to describe the horizontal position of the tongue in vowel
production in the IPA, can take five different values: front,
near-front, central, near-back, back. All values within the same feature
are exclusive, meaning that no bundle can be carry two or more values
from the same feature; in most operations, applying a value from a
feature that is already set overrides the said value. For models derived
from binary distinctive features, (discuss three-value), each feature
feature will usually have two values, corresponding to the presence or
absence, such as feature "dorsal" with the potential values "-dorsal"
(or "non-dorsal") and "+dorsal" (or just "dorsal").

Value names are globally unique within a model, including those of
different features. Valid names are.... Each value is associated with
additional properties that are used to manipulate and render sounds or
bounds. Note that all these properties are related to values and not
features, meaning that different values of the same feature might have
different weights, implications, etc. (even though in most cases all
values of the same feature will share weights and implications).

-   The weight specifies the "importance" of the value in relation to
    other values. The definition is importance is loose and depends on
    the context, but in most cases it references to what takes
    precedence when generating some output: for example, the most
    important feature in the IPA model is the type of the sound, meaning
    either a consonant or a vowel, as correspondigly the generated
    English names will have the noun "vowel" or "consonant" at the end.
    Note that the weight is inversely related to the importance: the
    lower the weight, the more important the value.

-   The implies lists the conditions for a value to be set, that is,
    which values must be present or are implied by another. For example,
    all value of feature "manner", the manner of articulation for
    consonants, such as plosive or trill, imply the feature "consonant"
    and cannot in the IPA model be applied to vowels. implies are not
    mandatory, and more than one might be listed, separating them with
    vertical bars (but nested ones are not allowed)

-   Prefix and suffix list the substring preceding and following a
    grapheme string so it can be modified; for example, in the IPA
    model, the feature aspiration has no prefix but a `ʰ` suffix, so
    that an "aspirated voiceless plosive consonant" (\[p\]) is rendered
    as the base sound listed \[p\] "voiceless plosive consonant" plus
    the suffix. Prefixes and suffixes are added to a grapheme string in
    order of their weight, defaulting to alphabetical value name in case
    of two or more values with the same weight (guaranteeing
    reproducibility). If a value lists no prefix or suffix, the
    information is added to the grapheme with a full list of the values
    between brackets; if we did not list one for aspiration, the
    "aspirated voiceless plosive consonant" would be rendered as
    "p\[aspirated\]" (this can of grapheme can be parsed by the system)

# maniphono

`maniphono` is a library for the symbolic manipulation of phonological
units.

The main components of the library are `PhonoModels`, which define
different models and sounds, and actual abstractions.

Models have two main components: the description of features and values
and the description of sounds.

The actual abstractions are organized in levels of nested complexity, as
follows:

    - `Sounds` are the basic units, defined as lists of features
    - `Segments` are collections of one or more sounds
    - `Sequences` are collections of one or more segments

## Usage

The library is intended to be used as normal Python package, trying to
follow the conventions and expectations of its programming language. A
few decisions on implementation might fall short in this principle, but
they are justified by the future plans of offering an equivalent
interface in different programming languages that can easily used on
client browser connections and/or compiled to machine code for easier
parallel processing.

The library is imported as expected. It is currently distributed with
two models, `mipa` and `tresoldi`, which offer a modified version of IPA
and one of full binary distinctive features that is intended mostly for
machine learning approaches. In all cases, the `mipa` model is used as
default.

``` {.python .numberLines startFrom="1"}
import maniphono
print(maniphono.model_mipa)
print(maniphono.model_tresoldi)
```

``` {.stdout}
[`mipa` model (20 features, 64 fvalues, 231 graphemes)]
[`tresoldi` model (30 features, 60 fvalues, 570 graphemes)]
```

### Sounds

A `Sound` can be initialized either with a grapheme, by default, or a
description. Descriptions can be either a list of values or a string
listing different values and separated by a standard delimiter such as
spaces or commas. A model must also be provided, defaulting to `mipa` as
mentioned above. Segments can be "visualized" with `str()`, returning a
graphemic representation, or with `repr()`, returned a descriptive
representation.

``` {.python}
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

The easiest way to manipulate sounds is using the add (`+`) and sub
(`-`) operators, which accept both single and multiple values. If a
value from a feature that is already set is added, it will be replaced.

``` {.python}
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

``` {.python}
>>> snd2.feature_dict()
{'phonation': 'voiceless', 'manner': 'plosive', 'type': 'consonant', 'place': 'velar', 'labialization': 'labialized'}
```

If a grapheme is not available, either because the sound is not complete
or because no diacritic is offered in the model, the library will try to
be explicit about its representation.

``` {.python}
>>> snd4 = maniphono.Sound(description="voiceless consonant")
>>> str(snd4), repr(snd4)
('C̥', 'voiceless consonant')
```

While the results are technically correct, the library still needs work
for always returning good representations when it computes the grapheme.

``` {.python}
>>> snd5 = maniphono.Sound("kʰʷ[voiced]")
>>> str(snd5), repr(snd5)
('ɡʰʷ', 'labialized aspirated voiced velar plosive consonant')
```

### Segments

Segments can combine sounds of different models. The decision of what
makes up a segment is entirely up to the user; the class can be
initialized with a `Sound`, in case of monosonic segments, or with an
ordered list of sounds.

Segments can be represented with `__str__` and can include a delimiter,
by default a `+` sign.

``` {.python}
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

Sequences can be represented with `__str__` and always use a white space
as a delimiter (following CLDF convention) as well as leading and
trailing square brackets (`[` and `]`).

``` {.python}
>> > snd1, snd2, snd3 = maniphono.Sound("p"), maniphono.Sound("a"), maniphono.Sound("w")
>> > seg1, seg2, seg3 = maniphono.Segment(snd1), maniphono.Segment(snd2), maniphono.Segment([snd3])
>> > seg4 = maniphono.Segment([snd2, snd3])
>> > str(seg1), str(seg2), str(seg3), str(seg4)
('p', 'a', 'w', 'a+w')
>> > seq1 = maniphono.SegSequence([seg1, seg2])
>> > seq2 = maniphono.SegSequence([seg1, seg2, seg3])
>> > seq3 = maniphono.SegSequence([seg1, seg4])
>> > seq4 = maniphono.SegSequence([seg1, seg2, seg3, seg1, seg4])
>> > str(seq1), str(seq2), str(seq3), str(seq4)
('[p a]', '[p a w]', '[p a+w]', '[p a w p a+w]')
```

### Operations

`PhonoModel` offers a number of auxiliary methods.

The `.values2sounds()` method will take a list of value constraints,
both in terms of presence and absence, and returned an order list of all
graphemes defined in the model that satisfy the constraint.

``` {.python}
>>> maniphono.model_mipa.values2graphemes("+vowel +front -close")
['a', 'ã', 'e', 'ẽ', 'æ', 'æ̃', 'ø', 'ø̃', 'œ', 'œ̃', 'ɛ', 'ɛ̃', 'ɪ', 'ɪ̃', 'ɶ', 'ɶ̃', 'ʏ', 'ʏ̃']
```

The `.minimal_matrix()` method will take a list of graphemes and return
a dictionary with the minimum set of features in which they differ.

``` {.python}
>>> maniphono.model_mipa.minimal_matrix(["t", "d"])
{'t': {'phonation': 'voiceless'}, 'd': {'phonation': 'voiced'}}
>>> dict(maniphono.model_mipa.minimal_matrix(["t", "d", "s"]))
{'t': {'manner': 'plosive', 'phonation': 'voiceless'}, 'd': {'manner': 'plosive', 'phonation': 'voiced'}, 's': {'manner': 'fricative', 'phonation': 'voiceless'}}
```

Similarly, the `.class_features()` method will take a list of graphemes
and return a dictionary of features and values the graphemes have in
common. It can be used to discover what features make up a class with
these sounds.

``` {.python}
>>> maniphono.model_mipa.class_features(["t", "d"])
{'place': 'alveolar', 'type': 'consonant', 'manner': 'plosive'}
>>> maniphono.model_mipa.class_features(["t", "d", "s"])
{'place': 'alveolar', 'type': 'consonant'}
```

The `.value_vector()` method will take a grapheme and return a list of
feature names and a boolean vector of presence/absence. It is mostly
intended for machine learning projects; for human explorations or
categorical machine learning, there is an option to return non-binary
vectors.

``` {.python}
>>> maniphono.model_mipa.value_vector("a")
(['aspiration_aspirated', 'centrality_back', 'centrality_central', 'centrality_front', 'centrality_near-back', 'centrality_near-front', 'ejection_ejective', 'height_close', 'height_close-mid', 'height_mid', 'height_near-close', 'height_near-open', 'height_open', 'height_open-mid', 'labialization_labialized', 'laterality_lateral', 'length_half-long', 'length_long', 'manner_affricate', 'manner_approximant', 'manner_click', 'manner_flap', 'manner_fricative', 'manner_implosive', 'manner_plosive', 'manner_trill', 'nasality_nasal', 'nasalization_nasalized', 'palatalization_palatalized', 'pharyngealization_pharyngealized', 'phonation_voiced', 'phonation_voiceless', 'place_alveolar', 'place_alveolo-palatal', 'place_bilabial', 'place_dental', 'place_epiglottal', 'place_glottal', 'place_labial', 'place_labio-alveolar', 'place_labio-coronal', 'place_labio-dental', 'place_labio-palatal', 'place_labio-velar', 'place_linguo-labial', 'place_palatal', 'place_palato-velar', 'place_pharyngeal', 'place_post-alveolar', 'place_retroflex', 'place_uvular', 'place_uvulo-epiglottal', 'place_velar', 'roundness_rounded', 'roundness_unrounded', 'sibilancy_non-sibilant', 'sibilancy_sibilant', 'syllabicity_non-syllabic', 'syllabicity_syllabic', 'type_consonant', 'type_vowel', 'uvularization_uvularized', 'velarization_velarized'], [False, False, False, True, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, True, False, False])
>>> maniphono.model_mipa.value_vector("a", binary=False)
(['aspiration', 'centrality', 'ejection', 'height', 'labialization', 'laterality', 'length', 'manner', 'nasality', 'nasalization', 'palatalization', 'pharyngealization', 'phonation', 'place', 'roundness', 'sibilancy', 'syllabicity', 'type', 'uvularization', 'velarization'], [None, 'front', None, 'open', None, None, None, None, None, None, None, None, None, None, 'unrounded', None, None, 'vowel', None, None])
```

All models allow to compute a distance between two sounds, with the
distance between a sound and itself set, by design, to zero. In some
cases this experimental method will compute and cache and `sklearn`
regressor, which can take a while.

``` {.python}
>>> maniphono.model_mipa.distance("a", "a")
0.0
>>> maniphono.model_mipa.distance("a", "e")
3.7590891821444608
>>> maniphono.model_mipa.distance("a", "ʒ")
30.419280377524366
```
