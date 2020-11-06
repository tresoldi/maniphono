"""
Utility functions for `maniphono`.
"""

import re

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
