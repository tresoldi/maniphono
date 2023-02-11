"""
maniphono __init__.py
"""

# Package information
__version__ = "0.4.1"  # remember to sync with setup.py
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Import from the various modules
from maniphono.phonomodel import (
    HumanModel,
    MachineModel,
    model_mipa,
    model_tresoldi,
    model_encoder,
)
from maniphono.sound import Sound
from maniphono.segment import BoundarySegment, SoundSegment, parse_segment
from maniphono.segsequence import SegSequence, parse_sequence
from maniphono.common import (
    codepoint2glyph,
    replace_codepoints,
    parse_constraints,
    parse_fvalues,
)

# Build the exported namespace; note that functions from
# the common/utils module are not included (but they are available
# with full qualified usage, like `maniphono.codepoint2glyph`)
__all__ = [
    "HumanModel",
    "MachineModel",
    "model_mipa",
    "model_tresoldi",
    "model_encoder",
    "Sound",
    "SoundSegment",
    "SegSequence",
    "parse_sequence",
]
