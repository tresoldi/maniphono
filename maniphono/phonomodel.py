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

import appdirs

from sklearn.neural_network import MLPRegressor
import joblib
import numpy as np

# Import local modules
from .utils import replace_codepoints, read_distance_matrix

# Define regular expression for accepting names
RE_FEATURE = re.compile(r"^[a-z][-_a-z]*$")
RE_VALUE = re.compile(r"^[a-z][-_a-z]*$")

# TODO: dont use `presence` and `absence` strings
# TODO: add documentation
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

        # Instantiate a property for the regressor used for computing
        # quantitative distances. All such methods require the `sklearn`
        # library, which is *not* listed as a dependency; as such, by
        # design we are not allowing to create it when initializing the
        # object, and the user must be explicit about it.
        self._regressor = None

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
        """
        Internal method for initializing a model.
        """

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

                # Store features
                self.features[feature].add(value)

                # Store values, which includes parsing the constraint string
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
        # before the entire model has been loaded
        all_constr = set()
        for value in self.values.values():
            for c_group in value["constraints"]:
                values = [entry["value"] for entry in c_group]
                all_constr |= set(values)

        missing_values = [value for value in all_constr if value not in self.values]
        if missing_values:
            raise ValueError(f"Contraints have undefined value(s): {missing_values}")

    def _init_sounds(self, model_path):
        """
        Internal method for initializing the sounds of a model.
        """

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
            raise ValueError(f"Undefined values used: {bad_model_values}")

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

    # TODO: note that, while this is to a large extent the inverse
    #       of minimal_matrix, to use the same codebase for both
    #       will add an unnecessary level of abstraction; better to
    #       just write on its own
    # TODO: decide on NAs
    def class_features(self, sounds):
        """
        Compute the class features for a set of sounds.
        """

        # Build list of values for the sounds
        features = defaultdict(list)
        for grapheme in sounds:
            for value in self.grapheme2values[grapheme]:
                features[self.values[value]["feature"]].append(value)

        # Keep only features with a perfect match;
        # len(values) == len(sounds) checks there are no NAs;
        # len(set(values)) == 1 checks if there is a match
        features = {
            feature: values[0]
            for feature, values in features.items()
            if len(values) == len(sounds) and len(set(values)) == 1
        }

        return features

    # TODO: allow more sounds, etc
    # TODO: allow categorical and boolean
    def value_vector(self, sound, binary=True):
        """
        Return a vector representation of the values of a sound.
        """

        sound_values = self.grapheme2values[sound]

        # Binary vector
        if not binary:
            # First get all features that are set, and later add those that
            # are not set as `None` (it is up to the user to filter, if
            # not wanted)
            vector_data = [
                [(feature, value) for value in values if value in sound_values]
                for feature, values in self.features.items()
            ]
            vector_data = list(itertools.chain.from_iterable(vector_data))
            vector_features = [entry[0] for entry in vector_data]

            for feature in self.features:
                if feature not in vector_features:
                    vector_data.append((feature, None))

        else:
            # TODO: better name without underscore?
            vector_data = [
                [(f"{feature}_{value}", value in sound_values) for value in values]
                for feature, values in self.features.items()
            ]

            vector_data = list(itertools.chain.from_iterable(vector_data))

        vector_data = sorted(vector_data, key=lambda f: f[0])

        feature_names = [entry[0] for entry in vector_data]
        vector = [entry[1] for entry in vector_data]

        return feature_names, vector

    # TODO: cache properties to know if the cached regressor can
    #       be used -- maybe hash the matrix
    # TODO: have a parameter to delete/overwrite regressor
    def _build_regressor(self):
        """
        Build or replace the quantitative distance regressor.
        """

        # Set path for cache regressor: get path with `appdirs`, create path
        # if necessary, and write it
        cache_path = appdirs.user_data_dir("maniphono", "tresoldi")
        cache_path = Path(cache_path)
        cache_file = cache_path / "regressor.joblib"

        # if cache file exists, load it
        if cache_file.is_file():
            self._regressor = joblib.load(cache_file.as_posix())
            return

        # TODO: get `matrix_path` when initializing
        matrix_path = None

        # Read raw distance data and cache vectors, also allowing to
        # skip over unmapped graphemes
        raw_matrix = read_distance_matrix(matrix_path)
        mapper = {"-": -1.0, "0": 0.0, "+": +1.0}
        vector = {}
        for grapheme in raw_matrix:
            try:
                _, vector[grapheme] = self.value_vector(grapheme)
            except KeyError:
                print("Skipping over unmapped [%s] grapheme..." % grapheme)

        # Collect (X,y) vectors
        X, y = [], []
        for grapheme_a in raw_matrix:
            # Skip over unmapped graphemes
            if grapheme_a not in vector:
                continue

            for grapheme_b, dist in raw_matrix[grapheme_a].items():
                # Skip over unmapped graphemes
                if grapheme_b not in vector:
                    continue

                X.append(vector[grapheme_a] + vector[grapheme_b])
                if dist == 0.0:
                    y.append(dist)
                else:
                    y.append(dist + 1.0)

        # Train regressor; setting the random value for reproducibility
        # TODO: config regressor parameters, including seed
        np.random.seed(42)
        # TODO: use logger
        print("Training MLPRegressor...")
        self._regressor = MLPRegressor(random_state=1, max_iter=500)
        self._regressor.fit(X, y)

        # TODO: wrap to catch exceptions
        cache_path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._regressor, cache_file.as_posix())

    # TODO: allow to run on categorical vectors?
    def distance(self, grapheme_a, grapheme_b):
        """
        Return a quantitative distance based on a seed matrix.

        The distance is by definition 0.0 for equal graphemes.
        If no regressor has previously been trained, one will be trained with
        default values and cached for future calls.
        Note that this method, as all methods related to quantitative
        distances, requires the `sklearn` library, which is not listed as
        a dependency of the package.

        Parameters
        ==========

        grapheme_a : str
            The first grapheme to be used for distance computation.
        grapheme_b : str
            The second grapheme to be used for distance computation.

        Returns
        =======

        dist : float
            The distance between the two sounds.
        """

        # Build and cache a regressor with default parameters
        if not self._regressor:
            self._build_regressor()

        # Get vectors, dropping feature names that are not needed
        mapper = {"-": -1.0, "0": 0.0, "+": +1.0}
        _, vector_a = self.value_vector(grapheme_a)
        _, vector_b = self.value_vector(grapheme_b)

        # If the vectors are equal, by definition the distance is zero
        if tuple(vector_a) == tuple(vector_b):
            return 0.0

        # Compute distance with the regressor
        return self._regressor.predict([vector_a + vector_b])[0]


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
