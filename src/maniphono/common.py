"""
Utility functions for `maniphono`.
"""

# Import standard modules
from typing import List, Optional, Sequence, Tuple, Iterable
import re
import unicodedata

# Pattern for unicode codepoint replacement
RE_CODEPOINT = re.compile(r"[Uu]\+[0-9A-Fa-f]{4}")

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_FVALUE = re.compile(r"^[a-z][-_a-z]*$")


def euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    """
    Compute the Euclidean distance between two vectors.

    Parameters
    ----------
    a : Sequence[float]
        The first vector.
    b : Sequence[float]
        The second vector.

    Returns
    -------
    float
        The Euclidean distance between the two vectors.
    """

    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def normalize(grapheme: str) -> str:
    """
    Normalize the string representation of a grapheme.

    Currently, normalization involves NFD Unicode normalization and stripping any leading
    and trailing white spaces. As these operations might change in the future, it is
    suggested to always use this function instead of reimplementing it in code
    each time.

    Parameters
    ----------
    grapheme : str
        The grapheme to be normalized.

    Returns
    -------
    str
        The normalized version of the grapheme.
    """

    return unicodedata.normalize("NFD", grapheme).strip()


# TODO: annotate the type of return, which might involve changing it
# TODO: check for duplicates and inconsistencies after the parsing
# TODO: the usage of parse_fvalues might lead to bugs in the future, better to generalize the splitting
def parse_constraints(constraints: List[str]) -> list:
    """
    Parses a list of constraints into a constraint structure.

    The constraints are given as a list of strings, each string representing a
    constraint group. Each constraint group is a string with the constraints
    separated by the "|" character. Each constraint is a string with the name of
    the feature-value pair, preceded by a "+" if the feature-value pair must be
    present, or a "-" if it must be absent. If the constraint is not preceded by
    any of these characters, it is assumed to be a presence constraint.

    Parameters
    ----------
    constraints : Sequence
        The textual representation of the list of constraints to be parsed.

    Returns
    -------
    list
        The parsed constraints.
    """

    def _assert_valid_name(value_name: str) -> None:
        """
        Internal function for asserting that a value name is valid.

        A `ValueError` is raised if the name is not valid, with the function
        passing silently otherwise.

        Parameters
        ----------
        value_name : str
            The name of the value to be checked.

        Raises
        ------
        ValueError
            If the name is not valid.
        """

        if not re.match(RE_FVALUE, value_name):
            raise ValueError(f"Invalid value name `{value_name}` in constraint")

    # In case of an empty string, there is nothing to parse
    if not constraints:
        return []

    # Obtain all constraints and check for disjunctions
    ret = []
    for constr_str in parse_fvalues(constraints):
        # Collect each constraint group
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

        ret.append(constr_group)

    return ret


# TODO: write test with all delimiters
# TODO: should accept any iterable?
def parse_fvalues(fvalues: Iterable) -> frozenset:
    """
    Parse a sequence of fvalues as a frozenset.

    This function is mostly used for parsing strings provided by the user,
    splitting them accordingly, but accepts any sequence type. If a string is
    passed, it will use different delimiters and guarantees that all methods will
    allow the same delimiters. Delimiters can be white spaces, commas, semicolons,
    forward slashes, and the " and " substring.

    Parameters
    ----------
    fvalues : Iterable
        The sequence with the fvalues to be parsed.

    Returns
    -------
    frozenset
        A frozenset with the fvalues.
    """

    if isinstance(fvalues, str):
        # We internally convert everything to spaces
        for delimiter in [" and ", ",", ";", "/"]:
            fvalues = fvalues.replace(delimiter, " ")

        fvalues = re.sub(r"\s+", " ", fvalues.strip())
        fvalues = fvalues.split()

    return frozenset(fvalues)


def codepoint2glyph(codepoint: str) -> str:
    """
    Convert a Unicode codepoint, given as a string, to its glyph.

    The codepoint must be given in the format "U+XXXX", such as "U+0283" for "ʃ".

    Parameters
    ----------
    codepoint : str
        The codepoint to be converted, in the format "U+XXXX".

    Returns
    -------
    str
        The corresponding glyph.
    """

    codepoint = codepoint.lower()
    value = int(codepoint[2:], 16)

    return chr(value)


def replace_codepoints(text: str) -> str:
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
    str
        The text with codepoint annotations replaced.
    """

    # Internal function used for calling codepoint2glyph() on a match
    def _match_repr(match):
        return codepoint2glyph(match.group())

    return RE_CODEPOINT.sub(_match_repr, text)


def match_initial(string: str, candidates: List[str]) -> Tuple[str, Optional[str]]:
    """
    Returns the longest match at the initial position among a list of candidates.

    The function will check if any candidate among the list is found at the beginning
    of the string, making sure to match longer candidates first (so that it will
    match "abc" before "ab").

    Parameters
    ----------
    string : str
        The string to matched at the beginning.
    candidates : List[str]
        A list of string candidates for initial match. The list does not need to be
        sorted in any way.

    Returns
    -------
    Tuple[str, Optional[str]]
        A tuple, whose first element is the original string stripped of the initial
        match, if any (if no candidate matched the beginning of the string, it will be
        a copy of the original one). The second element of the tuple is the candidate
        that was matched at the beginning of the string, or `None` if no match could be
        found.
    """

    # Sort the candidates by inverse length -- this is a bit expensive computationally,
    # but it is better to perform it each time to make the function more general.
    # Note that we make sure to remove any empty string inadvertently passed among the
    # `candidates`.
    candidates = sorted([cand for cand in candidates if cand], reverse=True, key=len)
    for cand in candidates:
        if string.startswith(cand):
            return string[len(cand) :], cand

    return string, None
