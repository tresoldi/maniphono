"""
Module for phonological model abstractions and operations.

This module holds the code for phonological models, the bottom-most layer of our
abstractions. A model is defined from tabular data as...
"""
# TODO: expand module doc, preparing for paper

# Import Python standard libraries
from collections import defaultdict, Counter
from pathlib import Path
import csv
import itertools
import re

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"[a-z][-a-z]*")
RE_VALUE = re.compile(r"[a-z][-a-z]*")


def parse_constraints(constraints_str):
    """
    Parse a list of value constraints.

    A list of value constraints is given as a forward slash ("/") or semicolon (";")
    delimited list of values that can be constrained for either presence or
    absence. A "presence" constraint indicates a root value that must be set for
    a child value to be allowed, such as "consonant" as a presence constraint for
    "fricative" in most models. An "absence" constraint indicates a root value that
    must not be set for a child value to be allowed, such as "vowel" as an absence
    constraint for "stop" in most models.

    Absence constraints are indicated by a preceding minus sign ("-") or exclamation
    mark ("!"), such as "-consonant" or "!consonant". Presence constraints are
    indicated by a preceding plus sign ("+") or no mark, such as "+consonant"
    or just "consonant".

    The function takes care of checking for duplicates (two or more instances of
    the same value in the same constraint) and inconsistencies (the same value
    listed as both a presence and an absance constraint), as well as for valid
    value identifiers. Note that it does not check if a value identifier is
    actually found in the model (a task carried by the PhonoModel object), nor
    deeper levels of constraints.

    Parameters
    ----------
    constraints_str : str
        A string with a list of constraints, separated by forward slashes or semicolons.

    Returns
    -------
    contrains : dict
        A dictionary of sets with `presence` and `absence` value identifiers.
    """

    # Return default if empty or non-existent string
    if not constraints_str:
        return {"presence": set(), "absence": set()}

    # Preprocess, also setting a single delimiter
    constraints_str = constraints_str.replace(" ", "")
    constraints_str = constraints_str.replace(";", "/")

    # Split the various constraints in presence and absence
    presence, absence = [], []
    for constr in constraints_str.split("/"):
        if constr[0] == "-" or constr[0] == "!":
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr[1:]}` in constraint")

            absence.append(constr[1:])
        elif constr[0] == "+":
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr[1:]}` in constraint")

            presence.append(constr[1:])
        else:
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr}` in constraint")

            presence.append(constr)

    # Check for duplicates
    if len(presence) != len(set(presence)):
        raise ValueError("Duplicate value name in `presence` constraints")
    if len(absence) != len(set(absence)):
        raise ValueError("Duplicate value name in `absence` constraints")

    # Check for inconsistencies
    inconsistent = [value for value in presence if value in absence]
    if inconsistent:
        raise ValueError("Inconsistent constraints ({sorted(inconsistent)})")

    return {"presence": set(presence), "absence": set(absence)}


class PhonoModel:
    """
    Phonological model.
    """

    # TODO: expand class documentation

    def __init__(self, name, model_path=None):
        # Setup model and defaults
        self.name = name
        self.features = defaultdict(set)
        self.values = {}
        self.grapheme2values = {}
        self.values2grapheme = {}

        # Build a path for reading the model; if it was not provided, assume it lives in
        # the `model/` directory
        if not model_path:
            model_path = Path(__file__).parent.parent.parent / "models" / name
        else:
            model_path = Path(model_path).absolute()

        # Init model first, and inventory later
        self._init_model(model_path)
        self._init_sounds(model_path)

    def _init_model(self, model_path):
        # Parse file with feature definitions
        with open(model_path / "model.csv") as csvfile:
            for row in csv.DictReader(csvfile):
                # Extract and clean strings as much as we can
                feature = row["FEATURE"].strip()
                value = row["VALUE"].strip()
                rank = int(row["RANK"].strip())

                # Run checks
                if not re.match(RE_FEATURE, feature):
                    raise ValueError(f"Invalid feature name `{feature}`")
                if not re.match(RE_VALUE, value):
                    raise ValueError(f"Invalid value name `{value}`")
                if value in self.values:
                    raise ValueError(f"Duplicate value `{value}`")
                if rank < 1:
                    raise ValueError(
                        f"Rank must be an integer >= 1.0 (passed `{rank}`)"
                    )

                # Store features (also as reverse map) and ranks
                self.features[feature].add(value)
                self.values[value] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": row["PREFIX"],
                    "suffix": row["SUFFIX"],
                    "constraints": parse_constraints(row.get("CONSTRAINTS")),
                }

        # Check if all constraints refer to existing values; this cannot be done
        # before the entire model is loaded
        all_constr = set(
            itertools.chain.from_iterable(
                [
                    list(value["constraints"]["presence"])
                    + list(value["constraints"]["absence"])
                    for value in self.values.values()
                ]
            )
        )
        missing_values = [value for value in all_constr if value not in self.values]
        if missing_values:
            raise ValueError("Contraints have undefined value(s): {missing_values}")

    def _init_sounds(self, model_path):
        # Parse file with inventory, filling `.grapheme2values` and `.values2grapheme`
        # from uniform `value_keys` (tuples of the sorted values). We first load
        # all the data to perform checks.
        def _desc2valkey(description):
            description = re.sub(r"\s+", " ", description.strip())
            return tuple(sorted(description.split()))

        with open(model_path / "sounds.csv") as csvfile:
            _graphemes = {
                row["GRAPHEME"].strip(): _desc2valkey(row["DESCRIPTION"])
                for row in csv.DictReader(csvfile)
            }

        # Check for duplicate descriptions; in any are found, we collect back the
        # graphemes that share them
        for desc, count in Counter(_graphemes.values()).items():
            if count > 1:
                at_fault = "/".join(
                    [
                        grapheme
                        for grapheme, description in _graphemes.items()
                        if description == desc
                    ]
                )
                raise ValueError(
                    f"At least one description {desc} is used for more than one value ({at_fault})"
                )

        # Check for bad value names
        bad_model_values = [
            value
            for value in itertools.chain.from_iterable(_graphemes.values())
            if value not in self.values
        ]
        if bad_model_values:
            raise ValueError(f"Undefined values used {bad_model_values}")

        # We can now add the sounds, using values as hasheable key, also checking if
        # contranints are met
        for grapheme, values in _graphemes.items():
            # Check the grapheme constraints; we can adopt the walrus operator in
            # the future
            failed = self.fail_constraints(values)
            if failed:
                raise ValueError(
                    f"Grapheme `{grapheme}` (model {self.name}) fails constraint check on {failed}"
                )

            # Update the internal catalog
            self.grapheme2values[grapheme] = values
            self.values2grapheme[values] = grapheme

    def fail_constraints(self, sound_values):
        """
        Checks if a list of values has any constraint failure.

        The method will check a list of values against the internal model, returning
        the list of values that fail the constraint check. The list will be empty
        if all values pass the checks; as empty lists are `False` by definition in
        Python, a grapheme correctness can be checked with
        `if model.fail_constraints(values)`. Note that, but definition, an empty list
        of values will be consider valid (returning an empty list of failing values).

        Parameters
        ----------
        sound_values : list
            A list, or another iterable, of the string values to be checked, such as
            those stored in `self.grapheme2values`.

        Returns
        -------
        offending : list
            A list of strings with the values that fail contraint check; will be
            empty if all values pass the checks.
        """

        offending = []
        for value in sound_values:
            unmet_presence = [
                value
                for value in self.values[value]["constraints"]["presence"]
                if value not in sound_values
            ]
            unmet_absence = [
                value
                for value in self.values[value]["constraints"]["absence"]
                if value in sound_values
            ]

            if any([unmet_presence, unmet_absence]):
                offending.append(value)

        return offending

    # TODO: implement minimal_matrix from `distfeat`, including documentation
    def minimal_matrix(self):
        """
        Compute the minimal feature matrix for a set of sounds.

        Not implemented yet.
        """
        raise ValueError("Not implemented yet")

    # TODO: implement class_features from `distfeat`, including documentation
    def class_features(self):
        """
        Compute the class features for a set of sounds.

        Not implemented yet.
        """
        raise ValueError("Not implemented yet")


# Load default models
IPA = PhonoModel("ipa")
Tresoldi = PhonoModel("tresoldi")
