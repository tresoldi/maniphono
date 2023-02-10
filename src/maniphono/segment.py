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

# TODO: add sound class export (depend on clts?) -- or decision tree?
# TODO: allow to initialize sounds with strings (graphemes/descs)
# TODO: allow to parse segments/sounds
# TODO: allow add/sub operations, and most from Sound
# TODO: should allow gaps? i.e., zero-sounds segments?

# Import Python standard libraries
from typing import Union, List

# Import local modules
from .sound import Sound
from .phonomodel import PhonoModel, model_mipa


class Segment:
    """
    Super class for all segments.
    """

    def __init__(self):
        pass

    # Each subclass with implement it, if necessary
    def add_fvalues(self, fvalues):
        raise NotImplementedError


# TODO: different boundaries: start/end/any
class BoundarySegment(Segment):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "#"

    def __repr__(self) -> str:
        return f"boundary_seg:{str(self)}"


class SoundSegment(Segment):
    def __init__(self, sounds: Union[str, Sound, List[Sound]]) -> None:
        """
        Initialize a sound segment.

        @param sounds:
        """
        super().__init__()

        if isinstance(sounds, Sound):
            self.sounds = [sounds]
        elif isinstance(sounds, str):
            # TODO: write a proper parser, as this assumes that, when a string, `sounds`
            #       carries a single grapheme (dealing with _diacritics might get tricky)
            self.sounds = [Sound(sounds)]
        else:
            # Must be a list of Sounds
            self.sounds = sounds

    def add_fvalues(self, fvalues: Union[str, list]) -> None:
        if len(self.sounds) == 1:
            self.sounds[0].set_fvalues(fvalues)
        else:
            raise ValueError("Not implemented for multisonic segments.")

    def __len__(self) -> int:
        return len(self.sounds)

    def __getitem__(self, idx) -> Sound:
        return self.sounds[idx]

    # TODO: would better rewrite as common __init__/__next__
    def __iter__(self):
        _iter_idx = 0
        while _iter_idx < len(self.sounds):
            yield self.sounds[_iter_idx]
            _iter_idx += 1

    def __str__(self) -> str:
        return "+".join([str(snd) for snd in self.sounds])

    def __repr__(self) -> str:
        return f"sound_seg:{str(self)}"

    def __hash__(self) -> int:
        return hash(tuple(self.sounds))

    # TODO: comment that if self.sounds holds a single sound, and `other` is a sound,
    # we try to match
    def __eq__(self, other: Union[Sound, Segment]) -> bool:
        if len(self.sounds) == 1 and isinstance(other, Sound):
            return self.sounds[0] == other

        return hash(self) == hash(other)

    def __ne__(self, other: Union[Sound, Segment]) -> bool:
        return not self.__eq__(other)

    # TODO: should work with sounds and not modifiers
    def __add__(self, modifier) -> Segment:
        # TODO: work on multisonic segments
        if len(self.sounds) != 1:
            raise ValueError("more than one sound")

        return SoundSegment(self.sounds[0] + modifier)


# TODO: this holder only accepts monosonic segments
def parse_segment(segment: str, model: PhonoModel = model_mipa) -> Segment:
    """
    @param segment:
    @return:
    """

    # TODO: make sure to implement context-specific boundaries (^and $)
    if segment in ["#", "^", "$"]:
        return BoundarySegment()

    # look for negation, if there is one
    # TODO: use `negate`
    if segment[0] == "!":
        negate = True
        segment = segment[1:]
    else:
        negate = False

    # TODO: make sure this is not necessary anymore (mostly for alteruphono)
    segment = segment.replace("g", "ɡ")

    return SoundSegment(Sound(segment))
