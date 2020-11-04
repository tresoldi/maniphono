# __init__.py

"""
maniphono __init__.py
"""

# Version of the lpngram package
__version__ = "0.1"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from maniphono.model import PhonoModel
from maniphono.sound import Sound
from maniphono.segment import Segment
