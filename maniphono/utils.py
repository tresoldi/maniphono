"""
Utility functions for `maniphono`.
"""


def codepoint2glyph(codepoint):
    """
    Convert a Unicode codepoint, given as a string, to its glyph.

    Parameters
    ----------
    codepoint : str
        A string with the codepoint, such as "U+0283", "u+0283", "u0283", or "0283".

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
