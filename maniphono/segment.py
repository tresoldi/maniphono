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

from . import sound


class Segment:
    def __init__(self, sounds, delimiter="+"):
        self._iter_idx = None

        self.delimiter = delimiter

        if isinstance(sounds, sound.Sound):
            self.sounds = [sounds]
        else:
            self.sounds = sounds

    def __len__(self):
        return len(self.sounds)

    def __getitem__(self, idx):
        return self.sounds[idx]

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx == len(self.sounds):
            raise StopIteration

        ret = self.sounds[self._iter_idx]
        self._iter_idx += 1

        return ret

    def __str__(self):
        return self.delimiter.join([str(snd) for snd in self.sounds])

    def __hash__(self):
        return hash(tuple(self.sounds))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
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
        return Segment(
            sound.Sound(description="voiceless plosive consonant", partial=True)
        )
    elif grapheme == "R":  # TODO: how to deal with resonant=-stop?
        return Segment(sound.Sound(description="fricative consonant", partial=True))
    elif grapheme == "SV":
        return Segment(
            sound.Sound(description="voiced plosive consonant", partial=True)
        )
    elif grapheme == "VN":
        return Segment(sound.Sound(description="nasalized vowel", partial=True))
    elif grapheme == "VL":
        return Segment(sound.Sound(description="long vowel", partial=True))
    elif grapheme == "CV":
        return Segment(sound.Sound(description="voiced consonant", partial=True))

    grapheme = grapheme.replace("g", "ɡ")

    return Segment(sound.Sound(grapheme))
