"""
Module for phonological model abstraction and operations.
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
    RE_FVALUE,
    startswithset,
)

# TODO: extend documentation after blog post
class PhonoModel:
    """
    Class for representing a phonological model.

    As per the extended documentation, phonological models are made of...

    Parameters
    ----------
    name : str
        Name of the model.
    model_path : str
        The path to the directory holding the model configuration files. If not
        provided, the library will default to the resources distributed along with
        its package.
    """

    def __init__(self, name, model_path=None):
        """
        Initialize a phonological model.
        """

        # Setup model and defaults
        self.name = name  # model name
        self.features = defaultdict(set)  # set of features in the model
        self.fvalues = {}  # dictionary of fvalue structures, as from CSV file

        # Dictionary with extra, internal material
        self._x = {
            "grapheme2fvalues": {},  # auxiliary dict for mapping
            "fvalues2grapheme": {},  # auxiliary dict for mapping
            "diacritics": {},  # auxiliary dict for parsing/representation
            "classes": [],  # auxiliary list to distinguish phonemes/classes
        }

        # Instantiate a property for the regressor used for computing
        # quantitative distances. These methods require the `sklearn`
        # library.
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

        The method will read the feature/fvalue configurations stored in
        the `model.csv` file.
        """

        # Parse file with feature definitions
        with open(model_path / "model.csv") as csvfile:
            for row in csv.DictReader(csvfile):
                # Extract and clean strings as much as we can
                feature = row["FEATURE"].strip()
                fvalue = row["VALUE"].strip()  # TODO: change files to FVALUE
                rank = int(row["RANK"].strip())

                # Run checks
                if not re.match(RE_FEATURE, feature):
                    raise ValueError(f"Invalid feature name `{feature}`")
                if not re.match(RE_FVALUE, fvalue):
                    raise ValueError(f"Invalid feature value name `{fvalue}`")
                if fvalue in self.fvalues:
                    raise ValueError(f"Duplicate feature value `{fvalue}`")
                if rank < 1:
                    raise ValueError(f"Rank must be a value >= 1.0 (passed `{rank}`)")

                # Store feature values for all features
                self.features[feature].add(fvalue)

                # Store values structs, which includes parsing the diacritics and
                # the constraint string
                prefix = replace_codepoints(row["PREFIX"])
                suffix = replace_codepoints(row["SUFFIX"])

                constraint_str = row.get("CONSTRAINTS")
                if constraint_str:
                    constr = parse_constraints(constraint_str)
                else:
                    constr = []

                self.fvalues[fvalue] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": prefix,
                    "suffix": suffix,
                    "constraints": constr,
                }

                # Store diacritics
                if prefix:
                    self._x["diacritics"][prefix] = fvalue
                if suffix:
                    self._x["diacritics"][suffix] = fvalue

        # Check if all constraints refer to existing fvalues; this cannot be done
        # before the entire model has been loaded
        all_constr = set()
        for fvalue in self.fvalues.values():
            for c_group in fvalue["constraints"]:
                all_constr |= {constr["fvalue"] for constr in c_group}

        missing_fvalues = [
            fvalue for fvalue in all_constr if fvalue not in self.fvalues
        ]
        if missing_fvalues:
            raise ValueError(f"Contraints have undefined fvalue(s): {missing_fvalues}")

    def _init_sounds(self, model_path):
        """
        Internal method for initializing the sounds of a model.

        The method will read the sounds stored in the `sounds.csv` file.
        """

        # Load the the descriptions as an internal dictionary; we also
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
                    f"At least one description {desc} is used for more than one sound ({at_fault})"
                )

        # Check for bad fvalue names
        bad_model_fvalues = [
            fvalue
            for fvalue in itertools.chain.from_iterable(_graphemes.values())
            if fvalue not in self.fvalues
        ]
        if bad_model_fvalues:
            raise ValueError(f"Undefined fvalues used: {bad_model_fvalues}")

        # We can now add the sounds, using fvalues as hasheable key, also checking if
        # constraints are met
        for grapheme, fvalues in _graphemes.items():
            # Check the grapheme constraints; we can adopt the walrus operator later
            failed = self.fail_constraints(fvalues)
            if failed:
                raise ValueError(
                    f"Grapheme `{grapheme}` fails constraint check on {failed}"
                )

            # Update the internal catalog
            fvalues = self.sort_fvalues(fvalues)
            self._x["grapheme2fvalues"][grapheme] = fvalues
            self._x["fvalues2grapheme"][fvalues] = grapheme

    def build_grapheme(self, fvalues):
        """
        Return a graphemic representation for a collection of feature values.

        Parameters
        ----------
        fvalues : list or tuple
            A collection of feature values.

        Return
        ------
        grapheme : str
            A graphemic representation of the provided collection of feature values.
        """

        # We first make sure the value_tuple is actually an expected, sorted tuple
        fvalues = self.sort_fvalues(fvalues)
        grapheme = self._x["fvalues2grapheme"].get(fvalues, None)

        # If no match, we look for the closest one
        if not grapheme:
            # Get the closest grapheme and its values from the model
            grapheme, best_fvalues = self.closest_grapheme(fvalues)

            # Extend grapheme, adding prefixes/suffixes for all missing feature
            # values; we first get the dictionary of features for both the current
            # sound and the candidate, make a list of features missing/different in
            # the candidate, extend with the features in candidate not found in the
            # current one, add feature values that can be expressed with diacritics,
            # and add the remaining feature values with full name.
            curr_features = self.feature_dict(fvalues)
            best_features = self.feature_dict(best_fvalues)

            # Collect the disagreements in a list of modifiers; note that it needs to
            # be sorted according to the rank to guarantee the order of values and
            # especially of diacritics is the "canonical" one.
            modifier = []
            for feat, val in curr_features.items():
                if feat not in best_features:
                    modifier.append(val)
                elif val != best_features[feat]:
                    modifier.append(val)
            # TODO: use default method
            modifier = sorted(modifier, key=lambda v: self.fvalues[v]["rank"])

            # Add all modifiers as diacritics whenever possible; those without a
            # diacritic are collected in an `expression` list and will be given
            # using their name (including those that need to be removed and not
            # replaced, thus preceded by a "-")
            expression = []
            for fvalue in modifier:
                prefix = self.fvalues[fvalue]["prefix"]
                suffix = self.fvalues[fvalue]["suffix"]
                if any([prefix, suffix]):
                    grapheme = f"{prefix}{grapheme}{suffix}"
                else:
                    expression.append(fvalue)

            # Add subtractions that have no diacritic
            for feat, val in best_features.items():
                if feat not in curr_features:
                    expression.append("-%s" % val)

            # Finally build string
            if expression:
                grapheme = f"{grapheme}[{','.join(sorted(expression))}]"

        return normalize(grapheme)

    def set_fvalue(self, fvalues, new_fvalue, check=True):
        """
        Set a single value in a collection of feature values.

        The method will remove all other feature values for the same feature before
        setting the provided one.

        Parameters
        ----------
        new_fvalue : str
            The value to be added to the sound.
        check : bool
            Whether to run constraints check after adding the new value (default: True).

        Returns
        -------
        prev_value : str or None
            The previous feature value for the feature, in case it was replaced, or
            `None` in case no replacement happened. If the method is called to add a
            feature value which is already set, the same feature value will be returned
            (indicating that there was already a feature value for the corresponding
            feature).
        """

        # TODO: move to tuple
        fvalues = set(fvalues)

        # If the feature value is already set, not need to do the whole operation,
        # including clearing the cache, so just return to confirm
        if new_fvalue in fvalues:
            return fvalues, new_fvalue

        # We need a different treatment for setting positive values (i.e. "voiced")
        # and for removing them (i.e., "-voiced"). Note that it does *not* raise an
        # error if the value is not present (we use .discard(), not .remove())
        prev_fvalue = None
        if new_fvalue[0] == "-":
            if new_fvalue[1:] in fvalues:
                # TODO make sure to return prev_fvalue only if it was there
                fvalues.discard(new_fvalue[1:])
                prev_fvalue = new_fvalue[1:]
        else:
            # Get the feature related to the value, cache its previous value (if any),
            # and remove it; we set `idx` to `None` in the beginning to avoid
            # false positives of non-initialization
            feature = self.fvalues[new_fvalue]["feature"]
            for _fvalue in fvalues:
                if _fvalue in self.features[feature]:
                    prev_fvalue = _fvalue
                    break

            # Remove the previous value (if there is one) and add the new value
            fvalues.discard(prev_fvalue)
            fvalues.add(new_fvalue)

        # Run a check if so requested (default)
        if check and self.fail_constraints(fvalues):
            raise ValueError(f"FValue {new_fvalue} ({feature}) breaks a constraint")

        return fvalues, prev_fvalue

    # TODO: replace set with sorted tuple
    def parse_grapheme(self, grapheme):
        """
        Parse a grapheme according to the library standard.

        Parameters
        ----------
        grapheme : str
            A graphemic representation to be parsed.

        Return
        ------
        fvalues : set
            A set with the feature values from the parsed grapheme.
        """

        # Used model/cache graphemes if available
        if grapheme in self._x["grapheme2fvalues"]:
            return set(self._x["grapheme2fvalues"][grapheme])

        # Capture list of modifiers, if any; no need to go full regex
        if "[" in grapheme and grapheme[-1] == "]":
            grapheme, _, modifier = grapheme.partition("[")
            modifiers = [mod.strip() for mod in _split_fvalues(modifier[:-1])]
        else:
            modifiers = []

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
                modifiers.insert(0, self._x["diacritics"][diacritic])

        # Add base character and modifiers
        fvalues = self._x["grapheme2fvalues"][base_grapheme]
        for mod in modifiers:
            # We only perform the check when adding the last modifier in the list
            check = mod == modifiers[-1]
            fvalues, _ = self.set_fvalue(fvalues, mod, check=check)

        # TODO: sort?
        return fvalues

    def sort_fvalues(self, fvalues):
        """
        Sort a list of values according to the model.

        In case of multiple values with the same rank, these are sorted alphabetically.

        Parameters
        ----------
        fvalues : list or str
            A list (or other iterable) of values or a string description of them. If
            a string is provided, the method will split them in the standard way.

        Return
        ------
        sorted : tuple
            A tuple with the sorted values.
        """

        if isinstance(fvalues, str):
            fvalues = _split_fvalues(fvalues)

        return tuple(sorted(fvalues, key=lambda v: (-self.fvalues[v]["rank"], v)))

    def feature_dict(self, fvalues):
        """
        Return a dictionary version of a feature value tuple.

        Parameters
        ----------
        fvalues : list or tuple
            The collection of feature values to be converted to a dictionary.

        Return
        ------
        fdict : dict
            A dictionary with feature as keys and feature values as values. Only
            features for feature values that are found are included.
        """

        return {self.fvalues[fvalue]["feature"]: fvalue for fvalue in fvalues}

    def fail_constraints(self, fvalues):
        """
        Checks if a list of feature values has any constraint failure.

        The method will check a list of feature values against the internal model,
        returning the list of feature values that fail the constraint check. The list
        will be empty if all feature values pass the checks; as empty lists are
        `False` by definition, a sound correctness can be checked with
        `if model.fail_constraints(fvalues)`. Note that, by definition, an empty list
        of feature values will be consider a valid one (as it will return an empty list
        of failing feature values).

        Parameters
        ----------
        fvalues : list
            A list, or another iterable, of the feature values to be checked, such as
            those stored in `self._grapheme2fvalues`.

        Returns
        -------
        offending : list
            A list of strings with the feature values that fail contraint check; it
            will be empty if all feature values pass the checks.
        """

        offending = []
        for fvalue in fvalues:
            for group in self.fvalues[fvalue]["constraints"]:
                offense = [
                    constr["fvalue"] in fvalues
                    if constr["type"] == "presence"
                    else constr["fvalue"] not in fvalues
                    for constr in group
                ]
                if not any(offense):
                    offending.append(fvalue)

        return offending

    # TODO: make sure it accepts lists as well strings
    def fvalues2graphemes(self, fvalues_str, classes=False):
        """
        Collect the set of graphemes in the model that satisfy a list of fvalues.

        Note that this will match the provided list against the sounds
        defined in the model only. To check against a custom list of sounds, it possible
        to use the overload operators, creating new sounds and checking whether they
        are equal or a superset (i.e., `>=`).

        Parameters
        ==========

        fvalues_str : str
            A list of feature values provided as constraints, such as
            `"+vowel +front -close"`.
        classes : bool
            Whether to include class graphemes in the output (default: False)

        Returns
        =======
        graphemes: list of str
            A list of all graphemes that satisfy the provided constraints.
        """

        # In this case we parse the fvalues as if they were constraints
        constraints = parse_constraints(fvalues_str)

        # Note that we could make the code more general by relying on
        # `.fail_constraints()`, but this would make the logic more complex and a bit
        # slower. It is better to perform a separately implemented check here,
        # unless we refactor the entire class.
        pass_test = []
        for fvalues, sound in self._x["fvalues2grapheme"].items():
            satisfy = itertools.chain.from_iterable(
                [
                    [
                        constr["fvalue"] in fvalues
                        if constr["type"] == "presence"
                        else constr["fvalue"] not in fvalues
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

        return pass_test

    # TODO: parse general graphemes, not only in model
    def minimal_matrix(self, sounds, vector=False):
        """
        Compute the minimal feature matrix for a set of sounds or graphemes.

        Parameters
        ----------
        sounds : list of str or fvalues
            The sounds to be considered in the minimal matrix, provided either as
            a list of graphemes or a list of fvalues.
        vector : bool
            Whether to return a vector of features, without variable names, instead
            of an actual matrix (default: `False`).

        Return
        ------
        mtx : dict or list
            Either a minimal matrix with features as keys as feature values as values,
            as default, or a list of feature values.
        """

        # If source is a collection of strings, assume they are graphemes from
        # the model; otherwise, just take them as lists of values
        # TODO: remove sort_fvalues() when moving from set to tuple
        sounds = [
            item
            if not isinstance(item, str)
            else self.sort_fvalues(self.parse_grapheme(item))
            for item in sounds
        ]

        # Build list of values for the sounds
        features = defaultdict(list)
        for fvalues in sounds:
            for fvalue in fvalues:
                features[self.fvalues[fvalue]["feature"]].append(fvalue)

        # Keep only features with a mismatch
        features = {
            feature: fvalues
            for feature, fvalues in features.items()
            if len(set(fvalues)) > 1
        }

        # Build matrix, iterating over graphemes and features
        matrix = defaultdict(dict)
        for feature, fvalues in features.items():
            for sound_fvalues in sounds:
                for fvalue in sound_fvalues:
                    if fvalue in fvalues:
                        matrix[sound_fvalues][feature] = fvalue
                        break

        # Return only fvalues, if a vector was requested, or a dict (instead of a
        # defaultdict) otherwise
        if vector:
            return list(matrix.values())

        return dict(matrix)

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    # TODO: parse general graphemes, not only in model
    def class_features(self, sounds):
        """
        Compute the class features for a set of graphemes or sounds.

        Parameters
        ----------
        sounds : list of str or fvalues
            The sounds to be considered when computing class features, provided either
            as a list of graphemes or a list of values.

        Return
        ------
        features : dict
            A dictionary with the common traits that make a class out of the
            provided sounds, with feature as keys and feature values as values.
        """

        # If source is a collection of strings, assume they are graphemes from
        # the model; otherwise, just take them as lists of values
        sounds = [
            item if not isinstance(item, str) else self._x["grapheme2fvalues"][item]
            for item in sounds
        ]

        # Build list of values for the sounds
        features = defaultdict(list)
        for fvalues in sounds:
            for fvalue in fvalues:
                features[self.fvalues[fvalue]["feature"]].append(fvalue)

        # Keep only features with a perfect match;
        # len(values) == len(sounds) checks there are no NAs;
        # len(set(values)) == 1 checks if there is a match
        features = {
            feature: fvalues[0]
            for feature, fvalues in features.items()
            if len(fvalues) == len(sounds) and len(set(fvalues)) == 1
        }

        return features

    # TODO: parse general graphemes, not only in model
    # TODO: rename binary/categorical
    def fvalue_vector(self, source, binary=True):
        """
        Build a vector representation of a sound from its fvalues.

        Vectors compiled with this method are mostly intended for stastical analyses,
        and can be either binary or categorical.

        Parameters
        ----------
        source : str or list
            Either a string with a grapheme or a feature value tuple for the sound
            to serve as basis for the vector.
        binary : bool
            Whether to build a binary vector (default) or a categorical one.

        Return
        ------
        features : list
            A list with the feature names represented in the vector. The names will
            match the model features' names in the case of categorical vectors,
            or follow the pattern `feature_featurevalue` in the case of binary ones.
        vector : list
            A list with the actual vector. The elements will be the feature values
            strings when set and `None` when not set in the case of categorical vectors,
            or booleans indicating the presence or absence of the corresponding
            feature value in the case of binary vectors.
        """

        # Get the fvalues from the grapheme if `source` is a string
        if isinstance(source, str):
            source_fvalues = self._x["grapheme2fvalues"][source]
        else:
            source_fvalues = source

        # Collect vector data in categorical or binary form
        if not binary:
            # First get all features that are set, and later add those that
            # are not set as `None` (it is up to the user to filter them out, if
            # not wanted)
            vector_data = [
                [(feature, fvalue) for fvalue in fvalues if fvalue in source_fvalues]
                for feature, fvalues in self.features.items()
            ]
            vector_data = list(itertools.chain.from_iterable(vector_data))
            vector_features = [entry[0] for entry in vector_data]

            # Add non-specified features
            for feature in self.features:
                if feature not in vector_features:
                    vector_data.append((feature, None))

        else:
            vector_data = [
                [
                    (f"{feature}_{fvalue}", fvalue in source_fvalues)
                    for fvalue in fvalues
                ]
                for feature, fvalues in self.features.items()
            ]

            vector_data = list(itertools.chain.from_iterable(vector_data))

        # Sort vector data and return a list of features and a vector
        vector_data = sorted(vector_data, key=lambda f: f[0])
        features, vector = zip(*vector_data)

        return features, vector

    # TODO: parse general graphemes, not only in model
    # TODO: allow used defined group of sounds, not only the model
    # TODO: rename to coarsing
    # TODO: optionally allow to use `distance`
    def closest_grapheme(self, fvalues, classes=True):
        """
        Find the sound in the model that is the closest to a given value tuple.

        The method can be used to coarse sounds within a reference group.

        Parameters
        ----------
        fvalues : tuple
            A feature value tuple, usually coming from the `.values` attributed of
            a sound.
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
        fvalues = self.sort_fvalues(fvalues)
        if fvalues in self._x["fvalues2grapheme"]:
            grapheme = self._x["fvalues2grapheme"][fvalues]
            if not all([classes, grapheme in self._x["classes"]]):
                return self._x["fvalues2grapheme"][fvalues], fvalues

        # Compute a similarity score based on inverse rank for all
        # graphemes, building a string with the representation if we hit a
        # `best_score`.
        best_score = 0.0
        best_fvalues = None
        grapheme = None
        for candidate_v, candidate_g in self._x["fvalues2grapheme"].items():
            # Don't include classes if asked so
            if not classes and candidate_g in self._x["classes"]:
                continue

            # Compute a score for the closest match; note that there is a penalty for
            # `extra` features, so that values such as "voiceless consonant" will tend
            # to match classes and not actual sounds
            common = [fvalue for fvalue in fvalues if fvalue in candidate_v]
            extra = [fvalue for fvalue in candidate_v if fvalue not in fvalues]
            score_common = sum([1 / self.fvalues[fvalue]["rank"] for fvalue in common])
            score_extra = sum([1 / self.fvalues[fvalue]["rank"] for fvalue in extra])
            score = score_common - score_extra
            if score > best_score:
                best_score = score
                best_fvalues = candidate_v
                grapheme = candidate_g

        return grapheme, best_fvalues

    # TODO: parse general graphemes, not only in model
    def distance(self, sound_a, sound_b):
        """
        Return a quantitative distance based on a seed matrix.

        The distance is by definition 0.0 for equal sounds.
        If no regressor has previously been trained, one will be trained with
        default values and cached for future calls.
        Note that this method, as all methods related to quantitative
        distances, uses the `sklearn` library.

        Parameters
        ==========

        sound_a : str
            The first sound to be used for distance computation.
        sound_b : str
            The second sound to be used for distance computation.

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
        _, vector_a = self.fvalue_vector(sound_a)
        _, vector_b = self.fvalue_vector(sound_b)

        # If the vectors are equal, by definition the distance is zero
        if tuple(vector_a) == tuple(vector_b):
            return 0.0

        # Compute distance with the regressor
        return self._regressor.predict([vector_a + vector_b])[0]

    # TODO: write documentation once regressors have been extended
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
        # TODO: check if all can be processed, with the new .fvalue_vector
        raw_matrix = read_distance_matrix(matrix_file)
        vector = {}
        for grapheme in raw_matrix:
            try:
                _, vector[grapheme] = self.fvalue_vector(grapheme)
            except KeyError:
                print("Skipping over unmapped [%s] grapheme..." % grapheme)

        # Collect (X,y) vectors
        # TODO: deal with the +1 -- just rebuild table
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

    def write_regressor(self, regressor_file):
        """
        Serialize the model's regressor to disk.

        This method uses `sklearn`/`joblib`, and is intended for caching
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

    def __str__(self):
        """
        Return a textual representation of the model.

        Return
        ------
        s : str
            A string with the textual representation of the model.
        """

        _str = f"[`{self.name}` model ({len(self.features)} features, "
        _str += f"{len(self.fvalues)} fvalues, "
        _str += f"{len(self._x['grapheme2fvalues'])} graphemes)]"

        return _str


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
