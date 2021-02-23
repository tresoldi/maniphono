# __init__.py

"""
maniphono __init__.py
"""

__version__ = "0.3"
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Build the namespace
from maniphono.phonomodel import (
    PhonoModel,
    model_mipa,
    model_tresoldi,
)  # pyflakes.ignore
from maniphono.sound import Sound  # noqa: F401
from maniphono.segment import (
    Segment,
    SoundSegment,
    BoundarySegment,
    parse_segment,
)  # noqa: F401
from maniphono.segsequence import SegSequence, parse_sequence  # noqa: F401
from maniphono.utils import (
    codepoint2glyph,
    replace_codepoints,
    read_distance_matrix,
    parse_constraints,
    split_fvalues_str,
)  # pyflakes.ignore
