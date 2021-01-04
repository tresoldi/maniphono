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
        self.delimiter = delimiter

        if isinstance(sounds, sound.Sound):
            self.sounds = [sounds]
        else:
            self.sounds = sounds

    def __len__(self):
        return len(self.sounds)

    def __str__(self):
        return self.delimiter.join([str(snd) for snd in self.sounds])
