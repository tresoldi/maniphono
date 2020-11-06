# TODO: accept sounds instead of segments, perhaps generating segments on the fly?
# TODO: add method for sylabification (including syll breaks)
# TODO: tone, stress and other (=general) suprasegmentals? it should probably be a
#       vector, with representation computed on the fly for __str__


class Sequence:
    def __init__(self, segments):
        self.segments = segments

    def __str__(self):
        return "[" + " ".join([str(seg) for seg in self.segments]) + "]"