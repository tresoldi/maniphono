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

from typing import List

from .segment import Segment, SoundSegment, BoundarySegment
from .sound import Sound


class SegSequence:
    def __init__(self, segments: List[Segment], boundaries: bool = True):
        """
        @param segments:
        @param boundaries:
        """

        self.segments = segments
        self.boundaries = boundaries

        self._update()

    # makes sure that, when the list of segments change, boundaries are added/removed
    # if necessary
    # TODO: could return a boolean on whether it was changed
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

    def __len__(self) -> int:
        return len(self.segments)

    def __getitem__(self, idx) -> Segment:
        return self.segments[idx]

    def __iter__(self):
        _iter_idx = 0
        while _iter_idx < len(self.segments):
            yield self.segments[_iter_idx]
            _iter_idx += 1

    def __str__(self) -> str:
        graphemes = [str(seg) for seg in self.segments]

        return " ".join(graphemes)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(tuple(self.segments)) ^ hash(self.boundaries)

    # TODO: make sure it is a copy
    def __add__(self, other):
        if isinstance(other, SegSequence):
            self.segments += other.segments
        else:
            self.segments.append(other)


# TODO: this is a temporary holder that assumes monosonic segments separated by
# spaces; a proper parser is later needed for alteruphono
def parse_sequence(seq, boundaries=True):
    seq = seq.strip()
    seq = seq.replace("g", "ɡ")

    segments = []
    for grapheme in seq.split():
        segments.append(SoundSegment([Sound(grapheme)]))

    return SegSequence(segments, boundaries=boundaries)
