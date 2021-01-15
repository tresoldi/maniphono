"""
Utility functions for `maniphono`.
"""

from pathlib import Path
import re
import csv
import unicodedata

# Pattern for unicode codepoint replacement
RE_CODEPOINT = re.compile(r"[Uu]\+[0-9A-Fa-f]{4}")

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_FVALUE = re.compile(r"^[a-z][-_a-z]*$")


def normalize(grapheme):
    """
    Normalize the string representation of a grapheme.

    Currently, normalization involves NFD Unicode normalization and stripping
    any leading and trailing white spaces. As these might change in the future, it
    is suggested to always use this functions instead of reimplementing it in code.

    Parameters
    ----------
    grapheme : str
        The grapheme to be normalized.

    Return
    ------
    grapheme : str
        The normalized version of the grapheme.
    """

    return unicodedata.normalize("NFD", grapheme).strip()


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

        if not re.match(RE_FVALUE, value_name):
            raise ValueError(f"Invalid value name `{value_name}` in constraint")

    # In case of an empty string, there is nothing to parse
    if not constraints_str:
        return []

    # Obtain all constraints and check for disjunctions
    constraints = []
    for constr_str in _split_fvalues(constraints_str):
        constr_group = []
        for constr in constr_str.split("|"):
            if constr[0] in "-!":
                _assert_valid_name(constr[1:])
                constr_group.append({"type": "absence", "fvalue": constr[1:]})
            elif constr[0] == "+":
                _assert_valid_name(constr[1:])
                constr_group.append({"type": "presence", "fvalue": constr[1:]})
            else:
                _assert_valid_name(constr)
                constr_group.append({"type": "presence", "fvalue": constr})

        # Collect constraint group
        constraints.append(constr_group)

    # Check for duplicates/inconsistencies
    # TODO: we can have a simple check for duplicates when groups have only
    # one entry, but it would be difficult to check when allowing disjunction

    return constraints


def _split_fvalues(fvalues):
    """
    Split a string with multiple feature values or constraints.

    This function, intended for internal usage, allows to use different
    delimiters and guarantees that all methods will allow all delimiters.

    Delimiters can be white spaces, commas, semicolons, forward slashes,
    and the " and " substring.

    Parameters
    ----------
    fvalues : str
        The string with the list of feature values to be split.

    Returns
    -------
    fvalue_list : list
        A list of strings with the feature values.
    """

    # We internally convert everything to spaces
    for delimiter in [" and ", ",", ";", "/"]:
        fvalues = fvalues.replace(delimiter, " ")

    fvalues = re.sub(r"\s+", " ", fvalues.strip())

    return fvalues.split()


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


def match_initial(string, candidates):
    """
    Returns the longest match at the initial position among a list of candidates.

    The function will check if any candidate among the list is found at the beginning
    of the string, making sure to match longer candidates first (so that it will
    match "abc" before "ab").

    Parameters
    ----------
    string : str
        The string to matched at the beginning.
    candidates : list of str
        A list of string candidates for initial match. The list does not need to
        be sorted in any way.

    Return
    ------
    string : str
        The original string stripped of the initial match, if any. If no candidate
        matched the beginning of the string, it will be a copy of the original one.
    cand : str or None
        The candidate that was matched at the beginning of the string, or `None` if
        no match could be found.
    """

    # Sort the candidates by inverse length -- this is a bit expensive computationally,
    # but it is better to perform it each time to make the function more general.
    # Note that we make sure to remove any empty string inadvertedly passed among the
    # `candidates`.
    candidates = sorted([cand for cand in candidates if cand], reverse=True, key=len)
    for cand in candidates:
        if string.startswith(cand):
            return string[len(cand) :], cand

    return string, None
