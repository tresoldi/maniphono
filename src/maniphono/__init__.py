"""
maniphono __init__.py
"""

__version__ = "0.3.1"
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Import from the various modules
from maniphono.phonomodel import  PhonoModel, model_mipa, model_tresoldi
from maniphono.sound import Sound  # noqa: F401
from maniphono.segment import SoundSegment
from maniphono.segsequence import SegSequence, parse_sequence  # noqa: F401
from maniphono.utils import (
    codepoint2glyph,
    replace_codepoints,
    read_distance_matrix,
    parse_constraints,
    split_fvalues_str,
)  # pyflakes.ignore
