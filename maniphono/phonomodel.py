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
from sklearn.svm import SVR
import joblib
import numpy as np

# Import local modules
from .utils import (
    replace_codepoints,
    read_distance_matrix,
    parse_constraints,
    normalize,
    _split_fvalues,
    RE_FEATURE,
    RE_VALUE,
    startswithset,
)


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

        # dictionary with extra, internal material
        self._x = {
            "grapheme2values": {},  # auxiliary dict for mapping
            "values2grapheme": {},  # auxiliary dict for mapping
            "diacritics": {},  # auxiliary dict for parsing/representation
            "classes": [],  # auxiliary list to distinguish phonemes/classes
        }

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
                    raise ValueError(f"Rank must be a value >= 1.0 (passed `{rank}`)")

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
                    self._x["diacritics"][prefix] = value
                if suffix:
                    self._x["diacritics"][suffix] = value

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

        # Load the the descriptions as an internal dictionary; we normalize also
        # normalize the grapheme by default
        with open(model_path / "sounds.csv") as csvfile:
            _graphemes = {}
            for row in csv.DictReader(csvfile):
                grapheme = normalize(row["GRAPHEME"])
                desc = self.sort_fvalues(row["DESCRIPTION"])
                _graphemes[grapheme] = desc

                if row["CLASS"] == "True":
                    self._x["classes"].append(grapheme)

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
            self._x["grapheme2values"][grapheme] = values
            self._x["values2grapheme"][values] = grapheme

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
            those stored in `self._grapheme2values`.

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

    def values2graphemes(self, values_str, classes=False):
        """
        Collect the set of graphemes in the model that satisfy a list of values.

        Note that this will always match the provided list against the sounds
        defined in the model. To check against a custom list of sounds, it possible
        to use the overload operators, creating new sounds and checking whether they
        are equal or a superset (i.e., `>=`).

        Parameters
        ==========

        values_str : str
            A list of values provided as constraints, such as `"+vowel +front -close"`.
        classes : bool
            Whether to include class graphemes in the output (default: False)

        Returns
        =======

        graphemes: list of str
            A list of all graphemes that satisfy the provided constraints.
        """

        # In this case we parse the values as if they were constraints
        constraints = parse_constraints(values_str)

        # Note that we could make the code more general by relying on
        # `.fail_constraints()`, but it would make the code more complex and a bit
        # slower. It is better to perform a separately implemented check here,
        # unless we refactor the class.
        pass_test = []
        for sound_values, sound in self._x["values2grapheme"].items():
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

        # Remove sounds that are classes
        if not classes:
            pass_test = [
                sound for sound in pass_test if sound not in self._x["classes"]
            ]

        # No need to sort, as the internal list is already sorted
        return pass_test

    def minimal_matrix(self, source, vector=False):
        """
        Compute the minimal feature matrix for a set of sounds or graphemes.
        """

        # If source is a collection of strings, assume they are graphemes from
        # the model; otherwise, just take them as lists of values
        source = [
            item if not isinstance(item, str) else self._x["grapheme2values"][item]
            for item in source
        ]

        # Build list of values for the sounds
        features = defaultdict(list)
        for sound_values in source:
            for value in sound_values:
                features[self.values[value]["feature"]].append(value)

        # Keep only features with a mismatch
        features = {
            feature: values
            for feature, values in features.items()
            if len(set(values)) > 1
        }

        # Build matrix, iterating over graphemes and features
        matrix = defaultdict(dict)
        for feature, f_values in features.items():
            for sound_values in source:
                for value in sound_values:
                    if value in f_values:
                        matrix[sound_values][feature] = value
                        break

        # Return only values, if a vector was requested, or a dict (instead of a
        # defaultdict) otherwise
        if vector:
            return matrix.values()

        return dict(matrix)

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    def class_features(self, source):
        """
        Compute the class features for a set of graphemes or sounds.
        """

        # If source is a collection of strings, assume they are graphemes from
        # the model; otherwise, just take them as lists of values
        source = [
            item if not isinstance(item, str) else self._x["grapheme2values"][item]
            for item in source
        ]

        # Build list of values for the sounds
        features = defaultdict(list)
        for sound_values in source:
            for value in sound_values:
                features[self.values[value]["feature"]].append(value)

        # Keep only features with a perfect match;
        # len(values) == len(sounds) checks there are no NAs;
        # len(set(values)) == 1 checks if there is a match
        features = {
            feature: values[0]
            for feature, values in features.items()
            if len(values) == len(source) and len(set(values)) == 1
        }

        return features

    def value_vector(self, source, binary=True):
        """
        Return a vector representation of the values of a sound.
        """

        # Get the values from the grapheme if `source` is a string
        if isinstance(source, str):
            source_values = self._x["grapheme2values"][source]
        else:
            source_values = source

        # Collect vector data in categorical or binary form

        if not binary:
            # First get all features that are set, and later add those that
            # are not set as `None` (it is up to the user to filter, if
            # not wanted)
            vector_data = [
                [(feature, value) for value in values if value in source_values]
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
                [(f"{feature}_{value}", value in source_values) for value in values]
                for feature, values in self.features.items()
            ]

            vector_data = list(itertools.chain.from_iterable(vector_data))

        # Sort vector data and return a list of features and a vector
        vector_data = sorted(vector_data, key=lambda f: f[0])
        features, vector = zip(*vector_data)

        return features, vector

    def write_regressor(self, regressor_file):
        """
        Serialize the model regressor to disk.

        The method uses `sklearn`/`joblib` method, which is intended for caching
        across different runs in the same system. Using a model serialized in one
        machine/environment in a different configuration might raise an error, fail,
        or return different results.

        The method will raise `ValueErrors` if no regressor has been built in the
        current model, or if it is unable to serialize the regressor to disk.

        Parameters
        ----------

        regressor_file : str
            Path to the file where the regressor will be serialized.
        """

        if not self._regressor:
            raise ValueError("No regressor to serialize.")

        # Build a pathlib object, create the directory (if necessary), and write
        regressor_file = Path(regressor_file).absolute()
        regressor_file.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._regressor, regressor_file.as_posix())

    def build_regressor(self, regtype="svr", filename=None, matrix_file=None):
        """
        Build or replace the quantitative distance regressor.

        Note that this method will silently replace any existing regressor.
        """

        # Load serialized model, if provided and existing
        if filename:
            filename = Path(filename)
            if filename.is_file():
                self._regressor = joblib.load(filename.as_posix())
                return

            raise ValueError(f"Unable to read regressor from {filename}")

        # Read raw distance data and cache vectors, also allowing to
        # skip over unmapped graphemes
        raw_matrix = read_distance_matrix(matrix_file)
        vector = {}
        for grapheme in raw_matrix:
            try:
                _, vector[grapheme] = self.value_vector(grapheme)
            except KeyError:
                print("Skipping over unmapped [%s] grapheme..." % grapheme)

        # Collect (X,y) vectors
        X, y = [], []  # pylint: disable=invalid-name
        for grapheme_a in raw_matrix:
            if grapheme_a in vector:
                for grapheme_b, dist in raw_matrix[grapheme_a].items():
                    if grapheme_b in vector:
                        X.append(vector[grapheme_a] + vector[grapheme_b])
                        if dist == 0.0:
                            y.append(dist)
                        else:
                            y.append(dist + 1.0)

        # Train regressor; setting the random value for reproducibility
        np.random.seed(42)
        if regtype == "mlp":
            self._regressor = MLPRegressor(random_state=1, max_iter=500)
        elif regtype == "svr":  # default
            self._regressor = SVR()

        self._regressor.fit(X, y)

    def distance(self, sound_a, sound_b):
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
            self.build_regressor()

        # `.value_vector()` takes care of always returning values, whether `sound_a`
        # and `sound_b` are graphemes or lists
        _, vector_a = self.value_vector(sound_a)
        _, vector_b = self.value_vector(sound_b)

        # If the vectors are equal, by definition the distance is zero
        if tuple(vector_a) == tuple(vector_b):
            return 0.0

        # Compute distance with the regressor
        return self._regressor.predict([vector_a + vector_b])[0]

    def __str__(self):
        _str = f"[`{self.name}` model ({len(self.features)} features, "
        _str += (
            f"{len(self.values)} values, {len(self._x['grapheme2values'])} graphemes)]"
        )

        return _str

    def closest_grapheme(self, value_tuple, classes=True):
        """
        Find the sound in the model that is the closest to a given value tuple.

        Parameters
        ----------
        value_tuple : tuple
            A value tuple, usually coming from the `.values` attributed of a sound.
        classes : bool
            Whether to allow a grapheme marked as a class to be returned; note that,
            if a grapheme class is passed but `classes` is set to `False`, a different
            grapheme will be returned (default: True).

        Return
        ------
        grapheme : str
            The grapheme for the closest match.
        values : tuple
            A tuple with the values for the closest match.
        """

        # Check if the grapheme happens to be already in our list, also making sure
        # the tuple is sorted
        value_tuple = self.sort_fvalues(value_tuple)
        if value_tuple in self._x["values2grapheme"]:
            grapheme = self._x["values2grapheme"][value_tuple]
            if not all([classes, grapheme in self._x["classes"]]):
                return self._x["values2grapheme"][value_tuple], value_tuple

        # Compute a similarity score based on inverse rank for all
        # graphemes, building a string with the representation if we hit a
        # `best_score`.
        best_score = 0.0
        best_values = None
        grapheme = None
        for candidate_v, candidate_g in self._x["values2grapheme"].items():
            # Don't include classes if asked so
            if not classes and candidate_g in self._x["classes"]:
                continue

            # Compute a score for the closest match; note that there is a penalty for
            # `extra` features, so that values such as "voiceless consonant" will tend
            # to match classes and not actual sounds
            common = [value for value in value_tuple if value in candidate_v]
            extra = [value for value in candidate_v if value not in value_tuple]
            score_common = sum([1 / self.values[value]["rank"] for value in common])
            score_extra = sum([1 / self.values[value]["rank"] for value in extra])
            score = score_common - score_extra
            if score > best_score:
                best_score = score
                best_values = candidate_v
                grapheme = candidate_g

        return grapheme, best_values

    def sort_fvalues(self, values):
        """
        Sort a list of values according to their ranks.

        In case of multiple values with the same rank, these are sorted alphabetically.

        Parameters
        ----------
        values : list or str
            A list (or other iterable) of values or a string description of them. If
            a string is provided, the method will split them in the standard way.

        Return
        ------
        sorted : tuple
            A tuple with the sorted values.
        """

        if isinstance(values, str):
            values = _split_fvalues(values)

        return tuple(sorted(values, key=lambda v: (-self.values[v]["rank"], v)))

    def feature_dict(self, values):
        """
        Return the defined features as a dictionary.
        """

        return {self.values[value]["feature"]: value for value in values}

    def build_grapheme(self, value_tuple):
        """
        Return a graphemic representation of the current sound.
        """

        # We first make sure the value_tuple is actually an expected, sorted tuple
        value_tuple = self.sort_fvalues(value_tuple)
        grapheme = self._x["values2grapheme"].get(value_tuple, None)

        # If no match, we look for the closest one
        if not grapheme:
            # Get the closest grapheme and its values from the model
            grapheme, best_values = self.closest_grapheme(value_tuple)

            # Extend grapheme, adding prefixes/suffixes for all missing values; we first
            # get the dictionary of features for both the current sound and the
            # candidate, make a list of features missing/different in the candidate,
            # extend with the features in candidate not found in the current one, add
            # values that can be expressed with diacritics, and add the remaining
            # values with full name.
            curr_features = self.feature_dict(value_tuple)
            best_features = self.feature_dict(best_values)

            # Collect the disagreements in a list of modifiers; note that it needs to
            # be sorted according to the rank to guarantee the order of values and
            # especially of diacritics is the "canonical" one.
            modifier = []
            for feat, val in curr_features.items():
                if feat not in best_features:
                    modifier.append(val)
                elif val != best_features[feat]:
                    modifier.append(val)
            modifier = sorted(modifier, key=lambda v: self.values[v]["rank"])

            # Add all modifiers as diacritics whenever possible; those without a
            # diacritic are collected in an `expression` list and will be given
            # using their name (including those that need to be removed and not
            # replaced, thus preceded by a "-")
            expression = []
            for value in modifier:
                prefix = self.values[value]["prefix"]
                suffix = self.values[value]["suffix"]
                if any([prefix, suffix]):
                    grapheme = f"{prefix}{grapheme}{suffix}"
                else:
                    expression.append(value)

            # Add subtractions that have no diacritic
            for feat, val in best_features.items():
                if feat not in curr_features:
                    expression.append("-%s" % val)

            # Finally build string
            if expression:
                grapheme = f"{grapheme}[{','.join(sorted(expression))}]"

        return normalize(grapheme)

    def set_fvalue(self, value_set, new_value, check=True):
        """
        Set a single value to the sound.

        The method will remove all other values for the same feature before setting the
        new value.

        Parameters
        ----------
        value : str
            The value to be added to the sound.
        check : bool
            Whether to run constraints check after adding the new value (default: True).

        Returns
        -------
        prev_value : str or None
            The previous value for the feature, in case it was replaced, or None whether
            no replacement happened. If the method is called to add a value which is
            already set, the value will be returned (indicating that there was already
            a value for the corresponding feature).
        """

        value_set = set(value_set)

        # If the value is already set, not need to do the whole operation, including
        # clearing the cache, so just return to confirm
        if new_value in value_set:
            return value_set, new_value

        # We need a different treatment for setting positive values (i.e. "voiced")
        # and for removing them (i.e., "-voiced"). Note that it does *not* raise an
        # error if the value is not present (we use .discard(), not .remove())
        prev_value = None
        if new_value[0] == "-":
            if new_value[1:] in value_set:
                value_tuple.discard(new_value[1:])
                prev_value = new_value[1:]
        else:
            # Get the feature related to the value, cache its previous value (if any),
            # and remove it; we set `idx` to `None` in the beginning to avoid
            # false positives of non-initialization
            feature = self.values[new_value]["feature"]
            for _value in value_set:
                if _value in self.features[feature]:
                    prev_value = _value
                    break

            # Remove the previous value (if there is one) and add the new value
            value_set.discard(prev_value)
            value_set.add(new_value)

        # Run a check if so requested (default)
        if check and self.fail_constraints(value_set):
            raise ValueError(f"Value {new_value} ({feature}) breaks a constraint")

        return value_set, prev_value

    # TODO: replace set with sorted tuple
    def parse_grapheme(self, grapheme):
        """
        Internal function for parsing a grapheme.
        """

        # Used model/cache graphemes if available
        if grapheme in self._x["grapheme2values"]:
            return set(self._x["grapheme2values"][grapheme])

        # Capture list of modifiers, if any; no need to go full regex
        modifier = []
        if "[" in grapheme and grapheme[-1] == "]":
            grapheme, _, modifier = grapheme.partition("[")
            modifier = [mod.strip() for mod in _split_fvalues(modifier[:-1])]

        # If the base is among the list of graphemes, we can just return the
        # grapheme values and apply the modifier. Otherwise, we take all characters
        # that are diacritics (remember we perform NFD normalization), remove them
        # while updating the modifier list, and again add the modifier at the end.
        # Note that diacritics are inserted to the beginning of the list, so that
        # the modifiers explicitly listed as value names are consumed at the end.
        base_grapheme = ""
        while grapheme:
            grapheme, diacritic = startswithset(grapheme, self._x["diacritics"])
            if not diacritic:
                base_grapheme += grapheme[0]
                grapheme = grapheme[1:]
            else:
                modifier.insert(0, self._x["diacritics"][diacritic])

        # Add base character and modifiers
        values = self._x["grapheme2values"][base_grapheme]
        for mod in modifier:
            values, _ = self.set_value(values, mod, check=False)

        # TODO: add a value already in it just to trigger the check

        # TODO: sort?
        return values


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
