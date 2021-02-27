"""
Utility functions for `maniphono`.
"""

import csv
import re
import unicodedata
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# Pattern for unicode codepoint replacement
RE_CODEPOINT = re.compile(r"[Uu]\+[0-9A-Fa-f]{4}")

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_FVALUE = re.compile(r"^[a-z][-_a-z]*$")


def normalize(grapheme: str) -> str:
    """
    Normalize the string representation of a grapheme.

    Currently, normalization involves NFD Unicode normalization and stripping any leading
    and trailing white spaces. As these opeations might change in the future, it is
    suggested to always use this function instead of reimplementing it in code
    each time.

    @param grapheme: The grapheme to be normalized.
    @return: The normalized version of the grapheme.
    """

    return unicodedata.normalize("NFD", grapheme).strip()


# TODO: comment on the syntax that is accepted
# TODO: annotate the type of return, which might involve changing it
# TODO: check for duplicates and inconsistencies after the parsing
def parse_constraints(constraints_str: str) -> list:
    """
    Parses a string of constraints into a constraint structure.

    @param constraints_str: The textual representation of the list of constraints to be
        parsed.
    @return: The parsed constraints.
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
    for constr_str in parse_fvalues(constraints_str):
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

        constraints.append(constr_group)

    return constraints


# TODO: write test with all delimiters
# TODO: should accept any iterable?
def parse_fvalues(fvalues: Sequence) -> frozenset:
    """
    Parse a sequence of fvalues as a frozenset.

    This function is mostly used for parsing string provided by the user,
    splitting them accordingly, but accepts any sequence type. If a string is
    passed, it will use different delimiters and guarantees that all methods will
    allow the same delimiters. Delimiters can be white spaces, commas, semicolons,
    forward slashes, and the " and " substring.

    @param fvalues: The sequence with the fvalues to be parsed.
    @return: A frozenset with the fvalues.
    """

    # We internally convert everything to spaces
    if isinstance(fvalues, str):
        for delimiter in [" and ", ",", ";", "/"]:
            fvalues = fvalues.replace(delimiter, " ")

        fvalues = re.sub(r"\s+", " ", fvalues.strip())
        fvalues = fvalues.split()

    return frozenset(fvalues)


def codepoint2glyph(codepoint: str) -> str:
    """
    Convert a Unicode codepoint, given as a string, to its glyph.

    @param codepoint: A string with the codepoint in the format "U+XXXX", such as
        "U+0283".
    @return: The correponding glyph (such as "ʃ").
    """

    codepoint = codepoint.lower()
    if codepoint.startswith("u+"):
        value = int(codepoint[2:], 16)
    else:
        value = int(codepoint, 16)

    return chr(value)


def replace_codepoints(text: str) -> str:
    """
    Replaces Unicode codepoints in a string with the corresponding glyphs.

    Multiple codepoints can be specified in the same string. Characters
    which are not part of codepoint annotation are kept.

    @param text: The text with codepoint annotations to be replaced.
    @return: The text with codepoint annotations replaced.
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

    @param string: The string to matched at the beginning.
    @param candidates: A list of string candidates for initial match. The list does not
        need to be sorted in any way.
    @return: A tuple, whose first element is the original string stripped of the initial
        match, if any (if no candidate matched the beginning of the string, it will be
        a copy of the original one). The second element of the tuple is the candidate
        that was matched at the beginning of the string, or `None` if no match could be
        found.
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
