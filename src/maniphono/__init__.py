"""
maniphono __init__.py
"""

# Package information
__version__ = "0.3.3"  # remember to sync with setup.py
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Import from the various modules
from maniphono.phonomodel import PhonoModel, model_mipa, model_tresoldi
from maniphono.sound import Sound
from maniphono.segment import BoundarySegment, SoundSegment, parse_segment
from maniphono.segsequence import SegSequence, parse_sequence
from maniphono.common import (
    codepoint2glyph,
    replace_codepoints,
    parse_constraints,
    parse_fvalues,
)
from maniphono.metrics import DistanceRegressor

# Build the exported namespace; note that functions from
# the common/utils module are not included (but they are available
# with full qualified usage, like `maniphono.codepoint2glyph`)
__all__ = [
    "PhonoModel",
    "model_mipa",
    "model_tresoldi",
    "Sound",
    "SoundSegment",
    "SegSequence",
    "parse_sequence",
    "DistanceRegressor",
]
