"""
Module for segment abstractions and operations.

This module holds the code for the segment model. According to our proposal,
a segment is a sequential list of one or more sounds, as defined by
analysis. In most contexts, diphthongs and longer multivowel objects
will be the only multisound segments, as potential consonantal
equivalents such as affricates and clicks are first-class citizens of
the phonological model, with their own features. Nonetheless, the model
is designed for extensibility and, as such, does not prevent the
user of specifying as many sounds as desired as building a single,
"atomic" segment.

According to this proposal, however, the class tries as much as possible
to behave as a Sound class when it is composed of a single sound.
"""

# TODO: add sound class export (depend on clts?)
# TODO: allow to initialize sounds with strings (graphemes/descs)
# TODO: allow to parse segments/sounds
# TODO: allow add/sub operations, and most from Sound
# TODO: should allow gaps? i.e., zero-sounds segments?

from .sound import Sound


class Segment:
    def __init__(self):
        self.type = None

    # Each subclass with implement it, if necessary
    def add_fvalues(self, fvalues):
        pass

    def __repr__(self):
        return f"{self.type}:{str(self)}"


# TODO: different boundaries: start/end/any
class BoundarySegment(Segment):
    def __init__(self):
        self.type = "boundary"

    def __str__(self):
        return "#"


class SoundSegment(Segment):
    def __init__(self, sounds):
        self.type = "soundsegment"

        if isinstance(sounds, Sound):
            self.sounds = [sounds]
        elif isinstance(sounds, str):  # TODO: assume it is a grpaheme, good enoguh?
            self.sounds = [Sound("a")]
        else:
            self.sounds = sounds

    def add_fvalues(self, fvalues):
        if len(self.sounds) == 1:
            self.sounds[0].add_fvalues(fvalues)

    def __len__(self):
        return len(self.sounds)

    def __getitem__(self, idx):
        return self.sounds[idx]

    def __iter__(self):
        _iter_idx = 0
        while _iter_idx < len(self.sounds):
            yield self.sounds[_iter_idx]
            _iter_idx += 1

    def __str__(self):
        return "+".join([str(snd) for snd in self.sounds])

    def __hash__(self):
        return hash(tuple(self.sounds))

    # TODO: comment that if self.sounds holds a single sound, and `other` is a sound,
    # we try to match
    def __eq__(self, other):
        if len(self.sounds) == 1 and isinstance(other, Sound):
            return self.sounds[0] == other

        return hash(self) == hash(other)

    def __ne__(self, other):
        if len(self.sounds) == 1 and isinstance(other, Sound):
            return self.sounds[0] != other

        return hash(self) != hash(other)


# TODO: holder that only accepts monosonic segments
def parse_segment(grapheme):
    # look for negation, if there is one
    # TODO: use `negate`
    if grapheme[0] == "!":
        negate = True
        grapheme = grapheme[1:]
    else:
        negate = False

    ## TODO: temporary holders for complex classes in alteruphno
    if grapheme == "SVL":
        return SoundSegment(
            Sound(description="voiceless plosive consonant", partial=True)
        )
    elif grapheme == "R":  # TODO: how to deal with resonant=-stop?
        return SoundSegment(Sound(description="fricative consonant", partial=True))
    elif grapheme == "SV":
        return SoundSegment(Sound(description="voiced plosive consonant", partial=True))
    elif grapheme == "VN":
        return SoundSegment(Sound(description="nasalized vowel", partial=True))
    elif grapheme == "VL":
        return SoundSegment(Sound(description="long vowel", partial=True))
    elif grapheme == "CV":
        return SoundSegment(Sound(description="voiced consonant", partial=True))

    grapheme = grapheme.replace("g", "ɡ")

    return SoundSegment(Sound(grapheme))
