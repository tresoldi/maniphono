# Maniphono

`maniphono` is a library for the manipulation of phonological units, designed as a solution
historical phonology. While offering two standard models for operation, one modified from the
IPA but following as much as possible its descriptors and one using distinctive
features which is designed for machine learning, it is designed to support custom
phonological models, trying as much as possible to be agnostic about the theoretical
background. It also gives particular attention since design stage to the role of
suprasegmentals.

`maniphono` operates on a hierarchy of phonological abstractions, all which are
related in some way to a "phonological model" that serves as the basis of all
operations. This hierarchy is:

  * a "phonological model" comprises a set of features operating in a many-valued
    logic system: each `feature` may be either undefined or defined by defined by
    one and only one "feature value" (or `favalue`) and a map of sounds (given by
    their graphemes) and the feature values that define them
  * a "sound" is a bundle of zero or more feature values and is intended to
    mostly map individual abstract acoustic performances
  * a "segment" is a unit of analysis, as decided by the user; the most common
    segment is, by far, a "sound segment", which is a segment composed of one
    (monosonic segment) or more (polysonic segment) sounds
  * a "sequence" is an ordered collection of segments and a set of information
    on suprasegmental properties, such as syllable breaks, tones, etc.
    
Each unit is described in more detail in the subsequent sections. As as set
of examples, however:

  * `model_mipa` is the standard phonological model in `maniphono`, comprised (at
    the time of writing) of 20 features (such as `manner` and `length`),
    64 fvalues (such as `affricate` and `approximant`, values of the `manner`
    feature, and `half-long` and `long`, values of the `length` feature), and 231
    graphemes (such as `a`, defined as an `open front unrounded vowel`)
  * sounds are to a large extend phonological abstractions represented by a
    single IPA glyph (potentially with diacritics), such as
    `open front unrounded vowel` (that is, /a/) or
    `voiced alveolar non-sibilant lateral affricate consonant` (that is, /dɮ/).
    Sounds can also be "partial", in the sense that they are not fully
    defined and thus represent what is normally called a "class" of sounds,
    such as `glottal consonant` (represented by `H`)
  * a sound segment is intended as a unit of analysis, contingent
    to the user decisions. For example, a bisonic segment can be
    used to represent a diphthong in case they are supposed to be treated
    as a single unit of analysis (such as `/a+j/`, in `maniphono`'s
    notation), which is different from a sequence of two monosonic
    segments (that is, `/a j/`)
  * a sequence is a list of segments, such as `[p a p a+j]`, which is a
    sequence of four segments (the last of which is composed of two sounds). It can
    carry additional information, such as word boundaries as in
    `[# p a p a+j #]`, syllable breaks as in `[# p a . p a+j #]`,
    and tonal information as in `[# p a ˧˩ . p a+j ˨˦ #]`


## PhonoModel


By design, a "PhonoModel" works in a way independent 



## Description

Mostly text based models, so it can be used in other systems and programming languages.

bundle

segment

grapheme

model

The central concepts of a model are "features" and "values". A feature is a set of one or more values that can be used to describe a sound or a group of
sounds (a "sound class"). For example, the "centrality" feature, used to describe the horizontal position of the tongue in vowel production
in the IPA, can take five different values: front, near-front, central, near-back, back. All values within the same feature are exclusive,
meaning that no bundle can be carry two or more values from the same feature; in most operations, applying a value from a feature that is
already set overrides the said value. For models derived from binary distinctive features, (discuss three-value), each feature feature will
usually have two values, corresponding to the presence or absence, such as feature "dorsal" with the potential values "-dorsal" (or "non-dorsal")
and "+dorsal" (or just "dorsal").

Value names are globally unique within a model, including those of different features. Valid names are.... Each value is associated with additional
properties that are used to manipulate and render sounds or bounds. Note that all these properties are related to values and not features,
meaning that different values of the same feature might have different weights, implications, etc. (even though in most cases all
values of the same feature will share weights and implications).

  - The weight specifies the "importance" of the value
in relation to other values. The definition is importance is loose and depends on the context, but in most cases it references to what takes
precedence when generating some output: for example, the most important feature in the IPA model is the type of the sound, meaning either a
consonant or a vowel, as correspondigly the generated English names will have the noun "vowel" or "consonant" at the end. Note that the weight
is inversely related to the importance: the lower the weight, the more important the value.

  - The implies lists the conditions for a value to be set, that is, which values must be present or are implied by another. For example,
  all value of feature "manner", the manner of articulation for consonants, such as plosive or trill, imply the feature "consonant" and
  cannot in the IPA model be applied to vowels. implies are not mandatory, and more than one might be listed, separating them with
  vertical bars (but nested ones are not allowed)

  - Prefix and suffix list the substring preceding and following a grapheme string so it can be modified; for example, in the IPA model, the
    feature aspiration has no prefix but a `ʰ` suffix, so that an "aspirated voiceless plosive consonant" ([p]) is rendered as the
    base sound listed [p] "voiceless plosive consonant" plus the suffix. Prefixes and suffixes are added to a grapheme string in
    order of their weight, defaulting to alphabetical value name in case of two or more values with the same weight (guaranteeing
    reproducibility). If a value lists no prefix or suffix, the information is added to the grapheme with a full list of the
    values between brackets; if we did not list one for aspiration, the "aspirated voiceless plosive consonant" would be rendered
    as "p[aspirated]" (this can of grapheme can be parsed by the system)
