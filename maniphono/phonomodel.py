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

# Import local modules
from .utils import replace_codepoints

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_VALUE = re.compile(r"^[a-z][-_a-z]*$")

# TODO: dont use `presence` and `absence` strings
def parse_constraints(constraints_str):
    # Prepare constraint string for manipulation
    for delimiter in [",", ";", "/"]:
        constraints_str = constraints_str.replace(delimiter, " ")
    constraints_str = re.sub(r"\s+", " ", constraints_str.strip())

    # Obtain all constraints and check for disjunctions
    constraints = []
    for constr_str in constraints_str.split():
        constr_group = []
        for constr in constr_str.split("|"):
            if constr[0] == "-" or constr[0] == "!":
                if not re.match(RE_VALUE, constr[1:]):
                    raise ValueError(f"Invalid value name `{constr[1:]}` in constraint")

                constr_group.append({"type": "absence", "value": constr[1:]})

            elif constr[0] == "+":
                if not re.match(RE_VALUE, constr[1:]):
                    raise ValueError(f"Invalid value name `{constr[1:]}` in constraint")

                constr_group.append({"type": "presence", "value": constr[1:]})

            else:
                if not re.match(RE_VALUE, constr):
                    raise ValueError(f"Invalid value name `{constr}` in constraint")

                constr_group.append({"type": "presence", "value": constr})

        # Collect constraint group
        constraints.append(constr_group)

    # Check for duplicates/inconsistent
    # TODO: we can have a simple check for duplicates when groups have only
    # one entry, but it would be difficult to check when allowing disjunction

    return constraints


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
            model_path = Path(__file__).parent.parent / "models" / name
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

                constraint_str = row.get("CONSTRAINTS")
                if constraint_str:
                    constr = parse_constraints(constraint_str)
                else:
                    constr = []

                self.values[value] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": replace_codepoints(row["PREFIX"]),
                    "suffix": replace_codepoints(row["SUFFIX"]),
                    "constraints": constr,
                }

        # Check if all constraints refer to existing values; this cannot be done
        # before the entire model is loaded
        all_constr = set()
        for value in self.values.values():
            for c_group in value["constraints"]:
                values = [entry["value"] for entry in c_group]
                all_constr |= set(values)

        missing_values = [value for value in all_constr if value not in self.values]
        if missing_values:
            raise ValueError(f"Contraints have undefined value(s): {missing_values}")

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
            # Get a vector for each group
            for group in self.values[value]["constraints"]:
                z = [
                    constr["value"] in sound_values
                    if constr["type"] == "presence"
                    else constr["value"] not in sound_values
                    for constr in group
                ]
                if not any(z):
                    offending.append(value)

        return offending

    # TODO: add check for inconsistent values
    # TODO: allow custom list of graphemes (default to sounds here)
    # TODO: generalize constraint checking with `fail_constraints` above
    def values2sounds(self, values_str):
        """
        Collect the set of sounds that satisfy a list of values.

        This method is intended to replace `distfeat`'s
        `.features2graphemes()` function.
        """

        # Parse values as constraints
        constraints = parse_constraints(values_str)

        pass_test = []
        for sound_values, sound in self.values2grapheme.items():
            satisfy = itertools.chain.from_iterable(
                [
                    [
                        constr["value"] in sound_values
                        if constr["type"] == "presence"
                        else constr["value"] not in sound_values
                        for constr in constr_group
                    ]
                    for constr_group in constraints
                ]
            )

            if all(satisfy):
                pass_test.append(sound)

        # While the internal list is already sorted, we sort
        # again here so as to allow user-defined groups of sounds
        # in the future
        return sorted(pass_test)

    # TODO: add `vector` option as in distfeat
    # TODO: deal with sounds/values
    # TODO: allow use to pass their collection of sounds
    # TODO: deal with `drop_na` as in distfeat
    # TODO: have in documentation that you can get the values with
    #       a .values() on the return (or just return as vector as well)
    # TODO: add a tabulate matrix
    def minimal_matrix(self, sounds):
        """
        Compute the minimal feature matrix for a set of sounds.

        Not implemented yet.
        """

        # Build list of values for the sounds
        features = defaultdict(list)
        for grapheme in sounds:
            for value in self.grapheme2values[grapheme]:
                features[self.values[value]["feature"]].append(value)

        # Keep only features with a mismatch
        features = {
            feature: values
            for feature, values in features.items()
            if len(set(values)) > 1
        }

        # Build matrix
        # TODO: rewrite loop
        matrix = defaultdict(dict)
        for grapheme in sounds:
            for feature, f_values in features.items():
                # Get the value for the current feature
                matrix[grapheme][feature] = [
                    value
                    for value in self.grapheme2values[grapheme]
                    if value in f_values
                ][0]

        return matrix

    # TODO: implement class_features from `distfeat`, including documentation
    def class_features(self):
        """
        Compute the class features for a set of sounds.

        Not implemented yet.
        """
        raise ValueError("Not implemented yet")


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
