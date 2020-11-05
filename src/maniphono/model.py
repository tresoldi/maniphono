# TODO: check if constrainst refer to valid values (can only be done after loading everything)
# TODO: preprocessing with double space removal and strip, at least for description

import itertools
from collections import defaultdict, Counter
from pathlib import Path
import csv
import re

# Define regular expression for accepting names
# TODO: cannot start with "-"
RE_FEATURE = re.compile(r"[-a-z]+")
RE_VALUE = re.compile(r"[-a-z]+")

# TODO: future version, disjoint constrains?
# TODO: cascading of constrains? explain it
def parse_constrains(constrains_str):
    """
    Parse a list of value constrains.

    A list of value constrains is given as a forward slash ("/") or semicolon (";")
    delimited list of values that can be constrained for either presence or
    absence. A "presence" constrain indicates a root value that must be set for
    a child value to be allowed, such as "consonant" as a presence constrain for
    "fricative" in most models. An "absence" constrain indicates a root value that
    must not be set for a child value to be allowed, such as "vowel" as an absence
    constrain for "stop" in most models.

    Absence constrains are indicated by a preceding minus sign ("-") or exclamation
    mark ("!"), such as "-consonant" or "!consonant". Presence constrains are
    indicated by a preceding plus sign ("+") or no mark, such as "+consonant"
    or just "consonant".

    The function takes care of checking for duplicates (two or more instances of
    the same value in the same constrain) and inconsistencies (the same value
    listed as both a presence and an absance constrain), as well as for valid
    value identifiers. Note that it does not check if a value identifier is
    actually found in the model (a task carried by the PhonoModel object), nor
    deeper levels of constrains.

    Parameters
    ----------
    constrains_str : str
        A string with a list of constrains, separated by forward slashes or semicolons.

    Returns
    -------
    contrains : dict
        A dictionary of sets with `presence` and `absence` value identifiers.
    """

    # Return default if empty or non-existent string
    if not constrains_str:
        return {"presence": set(), "absence": set()}

    # Preprocess, also setting a single delimiter
    constrains_str = constrains_str.replace(" ", "")
    constrians_str = constrains_str.replace(";", "/")

    # Split the various constrains in presence and absence
    presence, absence = [], []
    for constr in constrains_str.split("/"):
        if constr[0] == "-" or constr[0] == "!":
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr[1:]}` in constrain")

            absence.append(constr[1:])
        elif constr[0] == "+":
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr[1:]}` in constrain")

            presence.append(constr[1:])
        else:
            if not re.match(RE_VALUE, constr[1:]):
                raise ValueError(f"Invalid value name `{constr}` in constrain")

            presence.append(constr)

    # Check for duplicates
    if len(presence) != len(set(presence)):
        raise ValueError("Duplicate value name in `presence` constrains")
    if len(absence) != len(set(absence)):
        raise ValueError("Duplicate value name in `absence` constrains")

    # Check for inconsistencies
    inconsistent = [value for value in presence if value in absence]
    if inconsistent:
        value_str = "/".join([sorted(inconsistent)])
        raise ValueError("Inconsistent constrains ({value_str})")

    return {"presence": set(presence), "absence": set(absence)}


class PhonoModel:
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
                # TODO: maybe just rename `value2features` to `values`? could have rank/const/mod here
                self.features[feature].add(value)
                self.values[value] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": row["PREFIX"],
                    "suffix": row["SUFFIX"],
                    "constrains": parse_constrains(row.get("CONSTRAINS")),
                }

        # Parse file with inventory, filling `.grapheme2values` and `.values2grapheme`
        # from uniform `value_keys` (tuples of the sorted values). We first load
        # all the data to perform checks.
        # TODO: add imply checks, as a method of the Model
        with open(model_path / "sounds.csv") as csvfile:
            _graphemes = {
                row["GRAPHEME"].strip(): tuple(sorted(row["DESCRIPTION"].split()))
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
        _values = [
            value
            for value in itertools.chain.from_iterable(_graphemes.values())
            if value not in self.values
        ]
        import pprint
        pprint.pprint(self.values)
        print(_values)

        # we build a feature tuple, alphabetically sorted,
        # as a hasheable key
        # TODO: add checks: feature/value, implies, duplicates
        # TODO: normalize description string and grapheme
        # TODO: are descriptions unique as well?
        with open(model_path / "sounds.csv") as csvfile:
            for row in csv.DictReader(csvfile):
                value_key = tuple(sorted(row["DESCRIPTION"].split()))
                self.grapheme2values[row["GRAPHEME"]] = value_key
                self.values2grapheme[value_key] = row["GRAPHEME"]


# Load default models
IPA = PhonoModel("ipa")
Tresoldi = PhonoModel("tresoldi")
