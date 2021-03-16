---
title: Maniphono
---

`maniphono` is a library for the symbolic manipulation of phonological
units, designed as a solution historical phonology. While offering two
standard models for operation, one modified from the IPA but following
as much as possible its descriptors and one using distinctive features
which is designed for machine learning, it is designed to support custom
phonological models, trying as much as possible to be agnostic about the
theoretical background. For example, contrary to most computational
systems, it does not force consonants and vowels to be separated, and in
fact allows pure systems of distinctive features where all possible
sounds are expressed using the same matrix. It also gives particular
attention since design stage to the role of suprasegmentals.

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

As mentioned above, a "phonological model" is composed of two main
sources:

-   a feature definition
-   a sound definition

### Feature definition

Features are defined in a tabular file named `model.csv` with contents
similar to the snippet below:

  FEATURE      FVALUE       RANK   PREFIX   SUFFIX   CONSTRAINTS
  ------------ ------------ ------ -------- -------- -------------------------------
  aspiration   aspirated    6               ʰ        consonant
  centrality   back         2               U+0320   vowel
  centrality   central      2               U+0308   vowel
  centrality   front        2               U+031F   vowel
  centrality   near-back    2                        vowel
  centrality   near-front   2                        vowel
  ejection     ejective     5                        plosive\|fricative\|affricate

The most important field for each row, and the only one that needs to be
unique in the row, is the "FVALUE" one, as each row reports one
"fvalue". The "fvalue" labels have names in all lower-case letters, with
optional dashes, and must be unique across the entire model. There
cannot be repeated fvalue names, even if they cannot apply to the same
sound: as a consequence, for example, the MIPA model has a feature
"nasal" which applies to consonants only, and a feature "nasalized"
which applies to vowels only.

The "FEATURE" column reports the feature in the model to which the
fvalue refers to. Each sound in `maniphono` can have at most one fvalue
per feature set, so that it is possible to ask questions such as "which
is fvalue for 'centrality' in sound X" or "is 'front' the fvalue for
'centrality' in sound Y".

"RANK", "PREFIX", and "SUFFIX" are properties mostly used for converting
from and to graphemic representations, such as making sure that
'voiceless bilabial plosive consonant' is converted to "p". The first is
an integer number that informs, in descending order, how "important" a
value is, so that, when presenting information to the user, our results
are reproducible and we always obtain 'voiceless bilabial plosive
consonant' and not 'voiceless bilabial consonant plosive' (which is,
however, accepted as an input). Note that ranks are determined per
fvalue and not per feature basis, as giving more fine-grained options
about how to build the names. "PREFIX" and "SUFFIX" are, as expected,
substrings that will attached to base graphemes in order to modify them;
the order of addition follows the "RANK" property, so here as well the
results are reproducible. Both "PREFIX" and "SUFFIX" can be given as
Unicode charpoints. If an affix is needed when building a graphemic
representation and it is not available, the library will fall back to
adding the corresponding fvalue as a modifier.

"CONSTRAINTS" is a non-mandatory field which allows a detailed
specification of which fvalues must or must not be set for a given
fvalue to be present in a sound. They can be used internally for a
variety of purposes, such as making sure that sounds or groups of sounds
considered impossible are not accepted (such "sibilant laryngeals", in
the `mipa` model) and that some fvalues are automatically added when
necessary (such as automatically marking all "sibilants" as "fricatives"
in the same `mipa` model). The restriction that each can have at most
one fvalue per feature can be interpreted as a list of constraints
automatically added, where each fvalue implies the' absence of the
fvalues of the same feature. The syntax for the "CONSTRAINTS" field can
express many nuances and interdependencies, and is explained in
subsection X.

#### Sound definition

Sounds are defined in a tabular file named `sounds.csv` with contents
similar to the snippet below:

  GRAPHEME   DESCRIPTION                            CLASS
  ---------- -------------------------------------- -------
  V          vowel                                  True
  F          fricative consonant                    True
  a          open front unrounded vowel             False
  ã          open front unrounded vowel nasalized   False
  b          voiced bilabial plosive consonant      False

"GRAPHEME" is a base grapheme representation, and it is recommended that
it follows the IPA as close as possible. As the "PREFIX" and "AFFIX"
fields in model, this field accepts Unicode charpoints. Note, that
internally the graphemes will always be normalized and returned
following the NFD, that is, the Normalization Form Canonical
Decomposition, when characters are decomposed by canonical equivalence,
and multiple combining characters are arranged in a specific order. For
more information, see subsection X.

The "DESCRIPTION" is a list of one or more fvalues that define the
corresponding grapheme. It is not necessary for them to follow the ranks
of the fvalues. While it is recommended to separate the fvalues by a
single white space, there is some flexibility in terms of the syntax
defining an "fvalue list" (see subsection X).

The "CLASS" column reports a boolean information on whether the sound is
partial (`True`) or not (`False`). Sound partiality is an attribute
mostly used internally for forward and backward operation when applying
a sound change, and for most common purposes the sounds that can be
represented in IPA can be considered non-partial. It is recommended,
following the practice in the literature, that partial sounds are
defined with capital letters.

As expected, there can be no duplicates in terms of graphemes (the same
grapheme specified with two equivalent flists) and of fvalue lists (two
equivalent flists mapping to different graphemes). The library will
check for these restrictions when loading a model.

Models can carry additional information related to each sound, both
categorical (such as sound classes) and numerical (such as prosody
values), which are not mandatory but might be needed by different
methods and functionalities. In case this information is needed for a
sound not in the list of sounds (such as one extended with a diacritic),
the system will internally find the closest sound and repeat that
information (this is what happens, for example, with sound classes).
This also happens in case of empty cells (common, for example, for
partial sounds). The MIPA model carries information on sound classes
(derived from SCA \[cite list\]) and prosody (derived from \[cite
list\]).

Sound can be created from graphemes or from descriptions, which are
lists of fvalues (provided either as a single string or as an actual
Python iterable). All sounds have an implied model, which default to
MIPA.

### fvalue list syntax

lorem ipsum

### Constraint syntax

lorem ipsum

### Unicode normalization

lorem ipsum

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

``` {.python .numberLines startFrom="7"}
import maniphono
print(maniphono.model_mipa)
print(maniphono.model_tresoldi)
```

### Sounds

A `Sound` can be initialized either with a grapheme, by default, or a
description. Descriptions can be either a list of values or a string
listing different values and separated by a standard delimiter such as
spaces or commas. A model must also be provided, defaulting to `mipa` as
mentioned above. Segments can be "visualized" with `str()`, returning a
graphemic representation, or with `repr()`, returned a descriptive
representation.

``` {.python .numberLines startFrom="10"}
snd1 = maniphono.Sound("p")
str(snd1), repr(snd1)
snd2 = maniphono.Sound(description="voiceless bilabial plosive consonant")
str(snd2), repr(snd2)
snd3 = maniphono.Sound("a", model=maniphono.model_tresoldi)
str(snd3), repr(snd3)
```

The easiest way to manipulate sounds is using the add (`+`) and sub
(`-`) operators, which accept both single and multiple values. If a
value from a feature that is already set is added, it will be replaced.

``` {.python .numberLines startFrom="16"}
snd1 += 'voiced'
str(snd1), repr(snd1)
snd2 += 'velar,aspirated,labialized'
str(snd2), repr(snd2)
snd2 -= 'aspirated'
str(snd2), repr(snd2)
```

A dictionary of features and values can be easily obtained:

``` {.python .numberLines startFrom="22"}
snd2.feature_dict()
```

If a grapheme is not available, either because the sound is not complete
or because no diacritic is offered in the model, the library will try to
be explicit about its representation.

``` {.python .numberLines startFrom="23"}
snd4 = maniphono.Sound(description="voiceless consonant")
str(snd4), repr(snd4)
```

While the results are technically correct, the library still needs work
for always returning good representations when it computes the grapheme.

``` {.python .numberLines startFrom="25"}
snd5 = maniphono.Sound("kʰʷ[voiced]")
str(snd5), repr(snd5)
```

### Segments

Segments can combine sounds of different models. The decision of what
makes up a segment is entirely up to the user; the class can be
initialized with a `Sound`, in case of monosonic segments, or with an
ordered list of sounds.

Segments can be represented with `__str__` and can include a delimiter,
by default a `+` sign.

``` {.python .numberLines startFrom="27"}
snd1 = maniphono.Sound("w")
snd2 = maniphono.Sound("a")
snd3 = maniphono.Sound("j", model=maniphono.model_tresoldi)
seg1 = maniphono.Segment(snd1)
seg2 = maniphono.Segment([snd2, snd3])
seg3 = maniphono.Segment([snd1, snd2, snd3])
str(seg1), str(seg2), str(seg3)
```

### Sequences

Sequences combine segments in order.

Sequences can be represented with `__str__` and always use a white space
as a delimiter (following CLDF convention) as well as leading and
trailing square brackets (`[` and `]`).

``` {.python .numberLines startFrom="34"}
snd1, snd2, snd3 = maniphono.Sound("p"), maniphono.Sound("a"), maniphono.Sound("w")
seg1, seg2, seg3 = maniphono.Segment(snd1), maniphono.Segment(snd2), maniphono.Segment([snd3])
seg4 = maniphono.Segment([snd2, snd3])
str(seg1), str(seg2), str(seg3), str(seg4)
seq1 = maniphono.SegSequence([seg1, seg2])
seq2 = maniphono.SegSequence([seg1, seg2, seg3])
seq3 = maniphono.SegSequence([seg1, seg4])
seq4 = maniphono.SegSequence([seg1, seg2, seg3, seg1, seg4])
str(seq1), str(seq2), str(seq3), str(seq4)
```

### Operations

`PhonoModel` offers a number of auxiliary methods.

The `.values2sounds()` method will take a list of value constraints,
both in terms of presence and absence, and returned an order list of all
graphemes defined in the model that satisfy the constraint.

``` {.python .numberLines startFrom="43"}
>>> maniphono.model_mipa.values2graphemes("+vowel +front -close")
```

``` {.stderr}
  File "source.py", line 43
    >>> maniphono.model_mipa.values2graphemes("+vowel +front -close")
    ^
SyntaxError: invalid syntax
```

The `.minimal_matrix()` method will take a list of graphemes and return
a dictionary with the minimum set of features in which they differ.

``` {.python .numberLines startFrom="44"}
maniphono.model_mipa.minimal_matrix(["t", "d"])
dict(maniphono.model_mipa.minimal_matrix(["t", "d", "s"]))
```

Similarly, the `.class_features()` method will take a list of graphemes
and return a dictionary of features and values the graphemes have in
common. It can be used to discover what features make up a class with
these sounds.

``` {.python .numberLines startFrom="46"}
maniphono.model_mipa.class_features(["t", "d"])
maniphono.model_mipa.class_features(["t", "d", "s"])
```

The `.value_vector()` method will take a grapheme and return a list of
feature names and a boolean vector of presence/absence. It is mostly
intended for machine learning projects; for human explorations or
categorical machine learning, there is an option to return non-binary
vectors.

``` {.python .numberLines startFrom="48"}
maniphono.model_mipa.value_vector("a")
maniphono.model_mipa.value_vector("a", binary=False)
```

All models allow to compute a distance between two sounds, with the
distance between a sound and itself set, by design, to zero. In some
cases this experimental method will compute and cache and `sklearn`
regressor, which can take a while.

``` {.python .numberLines startFrom="50"}
maniphono.model_mipa.distance("a", "a")
maniphono.model_mipa.distance("a", "e")
maniphono.model_mipa.distance("a", "ʒ")
```
