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
from .segment import Segment


class Sequence:
    def __init__(self, segments, boundaries=True):
        self.segments = segments
        self.boundaries = boundaries

        # Initialize index for iteration
        self._iter_idx = None

    def __len__(self):
        return len(self.segments)

    def __getitem__(self, idx):
        return self.segments[idx]

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx == len(self.segments):
            raise StopIteration

        ret = self.segments[self._iter_idx]
        self._iter_idx += 1

        return ret

    def __str__(self):
        graphemes = [str(seg) for seg in self.segments]
        if self.boundaries:
            graphemes = ["#"] + graphemes + ["#"]

        return "[" + " ".join(graphemes) + "]"

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(tuple(self.segments, self.boundaries))


# TODO: this is a temporary holder that assumes monosonic segments separated by
# spaces; a proper parser is later needed for alteruphono
def parse_sequence(seq):
    seq = seq.strip()
    seq = seq.replace("g", "ɡ")

    segments = []
    for grapheme in seq.split():
        segments.append(Segment([Sound(grapheme)]))

    return Sequence(segments)
