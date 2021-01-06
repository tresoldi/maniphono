# __init__.py

"""
maniphono __init__.py
"""

# Version of the lpngram package
__version__ = "0.1.3"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from maniphono.phonomodel import PhonoModel, model_mipa, model_tresoldi
from maniphono.sound import Sound
from maniphono.segment import Segment
from maniphono.sequence import Sequence
from maniphono.utils import codepoint2glyph, replace_codepoints, read_distance_matrix
