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


class Sequence:
    def __init__(self, segments):
        self.segments = segments

    def __len__(self):
        return len(self.segments)

    def __str__(self):
        return "[" + " ".join([str(seg) for seg in self.segments]) + "]"
