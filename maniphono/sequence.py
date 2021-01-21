"""
Module for sequence abstractions and operations.

This module holds the code for the sequence model.
"""

# TODO: extend documentation
# TODO: accept sounds instead of segments, perhaps generating segments on the fly?
# TODO: add method for sylabification (including syll breaks)
# TODO: tone, stress and other (=general) suprasegmentals? it should probably be a
#       vector, with representation computed on the fly for __str__
# TODO: add method to syllabify
# TODO: add suprasegmentals

from .sound import Sound
from .segment import SoundSegment, BoundarySegment


class Sequence:
    def __init__(self, segments, boundaries=True):
        self.boundaries = boundaries

        self.segments = segments
        self._update()

    # makes sure that, when the list of segments change, boundaries are added/removed
    # if necessary
    def _update(self):
        # self.boundaries can be None
        if self.boundaries is True:
            if self.segments[0].type != "boundary":
                self.segments = [BoundarySegment()] + self.segments
            if self.segments[-1].type != "boundary":
                self.segments.append(BoundarySegment())
        elif self.boundaries is False:
            if self.segments[0].type == "boundary":
                self.segments = self.segments[1:]
            if self.segments[-1].type == "boundary":
                self.segments = self.segments[:-1]

    def __len__(self):
        return len(self.segments)

    def __getitem__(self, idx):
        return self.segments[idx]

    def __iter__(self):
        _iter_idx = 0
        while _iter_idx < len(self.segments):
            yield self.segments[_iter_idx]
            _iter_idx += 1

    def __str__(self):
        graphemes = [str(seg) for seg in self.segments]

        return " ".join(graphemes)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(tuple(self.segments, self.boundaries))

    def __add__(self, material):
        if isinstance(material, Sequence):
            self.segments += material.segments
        else:
            self.segments.append(material)


# TODO: this is a temporary holder that assumes monosonic segments separated by
# spaces; a proper parser is later needed for alteruphono
def parse_sequence(seq, boundaries=True):
    seq = seq.strip()
    seq = seq.replace("g", "ɡ")

    segments = []
    for grapheme in seq.split():
        segments.append(SoundSegment([Sound(grapheme)]))

    return Sequence(segments, boundaries=boundaries)
