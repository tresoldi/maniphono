"""
Module for phonological model abstractions and operations.
"""

# Import Python standard libraries
from collections import defaultdict, Counter
from pathlib import Path
import csv
import itertools
import re

# Import 3rd party libraries
from sklearn.neural_network import MLPRegressor
import appdirs
import joblib
import numpy as np

# Import local modules
from .utils import (
    replace_codepoints,
    read_distance_matrix,
    _split_values,
    parse_constraints,
    normalize,
    RE_FEATURE,
    RE_VALUE,
)


# TODO: expand class documentation
class PhonoModel:
    """
    Phonological model.
    """

    def __init__(self, name, model_path=None):
        """
        Initialize a phonological model.
        """

        # Setup model and defaults
        self.name = name  # model name
        self.features = defaultdict(set)  # set of features in the model
        self.values = {}  # dictionary of value structures
        self.grapheme2values = {}  # auxiliary dict for mapping
        self.values2grapheme = {}  # auxiliary dict for mapping
        self.diacritics = {}  # auxiliary dict for parsing/representation

        # Instantiate a property for the regressor used for computing
        # quantitative distances. These methods require the `sklearn`
        # library, which is a dependency but which, due to issues with serialization
        # and computation time, is *not* used by default; as such, by
        # design we are not allowing to create it when initializing the
        # object, and the user must be explicit about it.
        self._regressor = None

        # Build a path for reading the model (if it was not provided, we assume it
        # lives in the `model/` directory), and then load the features/values first
        # and the sounds later
        if not model_path:
            model_path = Path(__file__).parent.parent / "models" / name
        else:
            model_path = Path(model_path).absolute()

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

                # Store values for all features
                self.features[feature].add(value)

                # Store values structs, which includes parsing the diacritics and
                # the constraint string
                prefix = replace_codepoints(row["PREFIX"])
                suffix = replace_codepoints(row["SUFFIX"])

                constraint_str = row.get("CONSTRAINTS")
                if constraint_str:
                    constr = parse_constraints(constraint_str)
                else:
                    constr = []

                self.values[value] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": prefix,
                    "suffix": suffix,
                    "constraints": constr,
                }

                # Store diacritics
                if prefix:
                    self.diacritics[prefix] = value
                if suffix:
                    self.diacritics[suffix] = value

        # Check if all constraints refer to existing values; this cannot be done
        # before the entire model has been loaded
        all_constr = set()
        for value in self.values.values():
            for c_group in value["constraints"]:
                all_constr |= {constr["value"] for constr in c_group}

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
        # TODO: wrap _split_values?
        def _desc2valkey(description):
            """
            Internal function returning a description as a sorted tuple.
            """
            description = re.sub(r"\s+", " ", description.strip())
            return tuple(sorted(description.split()))

        # Load the the descriptions as an internal dictionary; we normalize also
        # normalize the grapheme by default
        with open(model_path / "sounds.csv") as csvfile:
            _graphemes = {
                normalize(row["GRAPHEME"]): _desc2valkey(row["DESCRIPTION"])
                for row in csv.DictReader(csvfile)
            }

        # Check for duplicate descriptions
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
        # constraints are met
        for grapheme, values in _graphemes.items():
            # Check the grapheme constraints; we can adopt the walrus operator later
            failed = self.fail_constraints(values)
            if failed:
                raise ValueError(
                    f"Grapheme `{grapheme}` fails constraint check on {failed}"
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
                offense = [
                    constr["value"] in sound_values
                    if constr["type"] == "presence"
                    else constr["value"] not in sound_values
                    for constr in group
                ]
                if not any(offense):
                    offending.append(value)

        return offending

    # TODO: add check for inconsistent values
    # TODO: generalize constraint checking with `fail_constraints` above
    # TODO: should take user-defined sets of sounds/graphemes (instead of model only)
    def values2graphemes(self, values_str):
        """
        Collect the set of graphemes in the model that satisfy a list of values.

        Parameters
        ==========

        values_str : str
            A list of values provided as constraints, such as `"+vowel +front -close"`.

        Returns
        =======

        graphemes: list of str
            A list of all graphemes that satisfy the provided constraints.
        """

        # Parse the values as if they were constraints
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

        # No need to sort, as the internal list is already sorted
        return pass_test

    # TODO: add `vector` option as in distfeat
    # TODO: deal with sounds/values
    # TODO: deal with `drop_na` as in distfeat
    # TODO: have in documentation that you can get the values with
    #       a .values() on the return (or just return as vector as well)
    # TODO: should take user-defined sets of sounds/graphemes (instead of model only)
    def minimal_matrix(self, graphemes):
        """
        Compute the minimal feature matrix for a set of sounds.
        """

        # Build list of values for the sounds
        features = defaultdict(list)
        for grapheme in graphemes:
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
        for grapheme in graphemes:
            for feature, f_values in features.items():
                # Get the value for the current feature
                matrix[grapheme][feature] = [
                    value
                    for value in self.grapheme2values[grapheme]
                    if value in f_values
                ][0]

        # return as a normal dictionary
        return dict(matrix)

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    # TODO: decide on NAs
    # TODO: should take user-defined sets of sounds/graphemes (instead of model only)
    def class_features(self, graphemes):
        """
        Compute the class features for a set of graphemes.
        """

        # Build list of values for the sounds
        features = defaultdict(list)
        for grapheme in graphemes:
            for value in self.grapheme2values[grapheme]:
                features[self.values[value]["feature"]].append(value)

        # Keep only features with a perfect match;
        # len(values) == len(sounds) checks there are no NAs;
        # len(set(values)) == 1 checks if there is a match
        features = {
            feature: values[0]
            for feature, values in features.items()
            if len(values) == len(graphemes) and len(set(values)) == 1
        }

        return features

    # TODO: should take user-defined sets of sounds/graphemes (instead of model only)
    def value_vector(self, grapheme, binary=True):
        """
        Return a vector representation of the values of a sound.
        """

        # Collect vector data in categorical or binary form
        grapheme_values = self.grapheme2values[grapheme]
        if not binary:
            # First get all features that are set, and later add those that
            # are not set as `None` (it is up to the user to filter, if
            # not wanted)
            vector_data = [
                [(feature, value) for value in values if value in grapheme_values]
                for feature, values in self.features.items()
            ]
            vector_data = list(itertools.chain.from_iterable(vector_data))
            vector_features = [entry[0] for entry in vector_data]

            # Add non-specified features
            for feature in self.features:
                if feature not in vector_features:
                    vector_data.append((feature, None))

        else:
            vector_data = [
                [(f"{feature}_{value}", value in grapheme_values) for value in values]
                for feature, values in self.features.items()
            ]

            vector_data = list(itertools.chain.from_iterable(vector_data))

        # Sort vector data and return a list of features and a vector
        vector_data = sorted(vector_data, key=lambda f: f[0])
        features, vector = zip(*vector_data)

        return features, vector

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
    # TODO: should take user-defined sets of sounds/graphemes (instead of model only)
    def distance(self, grapheme_a, grapheme_b):
        """
        Return a quantitative distance based on a seed matrix.

        The distance is by definition 0.0 for equal graphemes.
        If no regressor has previously been trained, one will be trained with
        default values and cached for future calls.
        Note that this method, as all methods related to quantitative
        distances, uses the `sklearn` library.

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
        _, vector_a = self.value_vector(grapheme_a)
        _, vector_b = self.value_vector(grapheme_b)

        # If the vectors are equal, by definition the distance is zero
        if tuple(vector_a) == tuple(vector_b):
            return 0.0

        # Compute distance with the regressor
        return self._regressor.predict([vector_a + vector_b])[0]

    def __str__(self):
        _str = f"[`{self.name}` model ({len(self.features)} features, "
        _str += f"{len(self.values)} values, {len(self.grapheme2values)} graphemes)]"

        return _str


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
