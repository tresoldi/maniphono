# TODO: add sound class export (depend on clts?)


class Segment:
    def __init__(self, sounds):
        self.sounds = sounds

    def __len__(self):
        return len(self.sounds)

    def __str__(self, delimiter="+"):
        return delimiter.join([str(snd) for snd in self.sounds])
