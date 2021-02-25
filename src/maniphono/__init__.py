"""
maniphono __init__.py
"""

# Package information
__version__ = "0.3.1"  # remember to sync with setup.py
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Import from the various modules
from maniphono.phonomodel import PhonoModel, model_mipa, model_tresoldi
from maniphono.sound import Sound
from maniphono.segment import SoundSegment
from maniphono.segsequence import SegSequence, parse_sequence
from maniphono.utils import (
    codepoint2glyph,
    replace_codepoints,
    parse_constraints,
    split_fvalues_str,
)
from maniphono.metrics import DistanceRegressor

# Build the exported namespace; note that functions from
# the common/utils module are not included (but they are available
# with full qualified usage, like `maniphono.codepoint2glyph`)
__all__ = ["PhonoModel", "model_mipa", "model_tresoldi",
           "Sound", "SoundSegment", "SegSequence", "parse_sequence",
           "DistanceRegressor"]