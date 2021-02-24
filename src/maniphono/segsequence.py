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

# Import Python standard libraries
from typing import List

# Import local modules
from .segment import Segment, SoundSegment, BoundarySegment
from .sound import Sound

# TODO: accept a SeqSequence where it is accepting a List[Segment]?
class SegSequence:
    def __init__(self, segments: List[Segment], boundaries: bool = True) -> None:
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
    def _update(self) -> None:
        """
        Internal method for automatic update of boundaries.

        This method makes sure that, when the list of segments change, boundaries are
        added or removed as necessary, following the value of `self.boundaries`.
        All operations that alter `self.segments` must call this method once they are
        done.
        """
        # self.boundaries can be None
        if self.boundaries is True:
            if not isinstance(self.segments[0], BoundarySegment):
                self.segments = [BoundarySegment()] + self.segments
            if not isinstance(self.segments[-1], BoundarySegment):
                self.segments.append(BoundarySegment())
        elif self.boundaries is False:
            if isinstance(self.segments[0], BoundarySegment):
                self.segments = self.segments[1:]
            if isinstance(self.segments[-1], BoundarySegment):
                self.segments = self.segments[:-1]

    def __len__(self) -> int:
        return len(self.segments)

    def __getitem__(self, idx) -> Segment:
        return self.segments[idx]

    # TODO: properly organize __iter__ and __next__, following the Segment implementation
    def __iter__(self):
        _iter_idx = 0
        while _iter_idx < len(self.segments):
            yield self.segments[_iter_idx]
            _iter_idx += 1

    def __str__(self) -> str:
        return " ".join([str(seg) for seg in self.segments])

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


# TODO: write a proper parser accepting multisonic segments
def parse_sequence(seq: str, boundaries: bool = True) -> SegSequence:
    """
    Parses a string sequence as a SegSequence.

    @param seq: A textual representation of the sequence to be parsed.
    @param boundaries: Whether the SegSequence should use boundaries (default: True)
    @return: The parsed SegSequence.
    """
    # TODO: can this reuse the common pre-processing functions?
    seq = seq.strip()

    segments = []
    for grapheme in seq.split():
        if grapheme == "#":
            segments.append(BoundarySegment())
        else:
            segments.append(SoundSegment([Sound(grapheme)]))

    return SegSequence(segments, boundaries=boundaries)
