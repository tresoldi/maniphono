"""
Utility functions for `maniphono`.
"""

from pathlib import Path
import re
import csv
import unicodedata

# Pattern for unicode codepoint replacement
RE_CODEPOINT = re.compile("[Uu]\+[0-9A-Fa-f]{4}")

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_VALUE = re.compile(r"^[a-z][-_a-z]*$")


def normalize(grapheme):
    """
    Normalize the string representation of a grapheme.
    """

    grapheme = unicodedata.normalize("NFD", grapheme)
    return grapheme.strip()


# TODO: extend documentation
def parse_constraints(constraints_str):
    """
    Parses a string of constraints into a constraint structure.
    """

    def _assert_valid_name(value_name):
        """
        Internal function for asserting that a value name is valid.

        A `ValueError` is raised if the name is not valid, with the function
        passing silently otherwise.
        """

        if not re.match(RE_VALUE, value_name):
            raise ValueError(f"Invalid value name `{value_name}` in constraint")

    # Obtain all constraints and check for disjunctions
    constraints = []
    for constr_str in _split_values(constraints_str):
        constr_group = []
        for constr in constr_str.split("|"):
            if constr[0] in "-!":
                _assert_valid_name(constr[1:])
                constr_group.append({"type": "absence", "value": constr[1:]})
            elif constr[0] == "+":
                _assert_valid_name(constr[1:])
                constr_group.append({"type": "presence", "value": constr[1:]})
            else:
                _assert_valid_name(constr)
                constr_group.append({"type": "presence", "value": constr})

        # Collect constraint group
        constraints.append(constr_group)

    # Check for duplicates/inconsistencies
    # TODO: we can have a simple check for duplicates when groups have only
    # one entry, but it would be difficult to check when allowing disjunction

    return constraints


# TODO: rename as it is used to split contraints as well
def _split_values(values):
    """
    Split a string with multiple values.

    This function, intended for internal usage, allows to use different
    delimiters and guarantees that all methods will allow all delimiters.

    Delimiters can be white spaces, commas, semicolons, forward slashes,
    and the " and " substring.

    Parameters
    ----------
    values : str
        The string with the list of values to be split.

    Returns
    -------
    value_list : list
        A list of strings with the values.
    """

    # We internally convert everything to spaces
    for delimiter in [" and ", ",", ";", "/"]:
        values = values.replace(delimiter, " ")

    values = re.sub(r"\s+", " ", values.strip())

    return values.split()


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
    if codepoint.startswith("u+"):
        value = int(codepoint[2:], 16)
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
