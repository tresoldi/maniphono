#!/usr/bin/env python3
# encoding: utf-8

"""
__main__.py

Module for command-line execution and phoneme manipulation.
"""

# Import Python standard libraries
from pathlib import Path

# Import our library
import maniphono


def main():
    resource_path = Path(__file__).parent.parent.parent.absolute()
    resource_path = resource_path / "resources"

    ipa_model = resource_path / "ipa.model.csv"
    ipa_sounds = resource_path / "ipa.sounds.csv"
    ipa = maniphono.PhonoModel(ipa_model, ipa_sounds)

    tresoldi_model = resource_path / "tresoldi.model.csv"
    tresoldi_sounds = resource_path / "tresoldi.sounds.csv"
    tresoldi = maniphono.PhonoModel(tresoldi_model, tresoldi_sounds)

    a = maniphono.Bundle(ipa, "unrounded open front vowel")
    t = maniphono.Bundle(ipa, "voiceless alveolar lateral affricate consonant")
    print(a.grapheme(), repr(a))
    print(t.grapheme(), repr(t))

    e = maniphono.Bundle(tresoldi, grapheme="e")
    e.set_description("preaspirated")
    print(e.grapheme(), repr(e))

    pj = maniphono.Bundle(
        ipa, "labialized aspirated voiceless bilabial plosive consonant"
    )
    print(pj.grapheme(), repr(pj))


if __name__ == "__main__":
    main()
