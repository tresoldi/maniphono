"""
Utility functions for `maniphono`.
"""

from pathlib import Path
import re
import csv

# Pattern for unicode codepoint replacement
RE_CODEPOINT = re.compile("U\+[0-9A-F]{4}")


def codepoint2glyph(codepoint):
    """
    Convert a Unicode codepoint, given as a string, to its glyph.

    Parameters
    ----------
    codepoint : str
        A string with the codepoint in the format "U+XXXX", such
        as "U+0283".

    Returns
    -------
    glyph : str
        The correponding glyph (such as "ʃ").
    """

    codepoint = codepoint.lower()
    if codepoint.startswith("u+") or codepoint.startswith("x+"):
        value = int(codepoint[2:], 16)
    elif codepoint[0] in "ux":
        value = int(codepoint[1:], 16)
    else:
        value = int(codepoint, 16)

    return chr(value)


def replace_codepoints(text):
    """
    Replaces Unicode codepoints in a string with the corresponding glyphs.

    Multiple codepoints can be specified in the same string. Characters
    which are not part of codepoint annotation are kept.

    Parameters
    ----------
    text : str
        The text with codepoint annotations to be replaced.

    Returns
    -------
    ret : str
        The text with codepoint annotations replaced.
    """

    # Internal function used for calling codepoint2glyph() on a match
    def _match_repr(match):
        return codepoint2glyph(match.group())

    return RE_CODEPOINT.sub(_match_repr, text)


def read_distance_matrix(filepath=None):
    """
    Read a distance matrix, used to seed a regressor.

    Parameters
    ==========
    filepath : str
        Path to the TSV file containing the distance matrix used to
        seed the regressor. If not provided, will default to one derived
        from data presented in Mielke (2012) and included in the library.

    Returns
    =======
    matrix : dict
        A dictionary of dictionaries with the distances as floating-point
        values.
    """

    if not filepath:
        filepath = Path(__file__).parent.parent / "distances" / "default.tsv"
        filepath = filepath.as_posix()

    matrix = {}
    with open(filepath) as tsvfile:
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            grapheme = row.pop("GRAPHEME")
            matrix[grapheme] = {gr: float(dist) for gr, dist in row.items()}

    return matrix
