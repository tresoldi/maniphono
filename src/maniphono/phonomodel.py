"""
Module for phonological model abstraction and operations.
"""

import csv
import itertools
import pathlib
import re

# Import Python standard libraries
from collections import defaultdict, Counter
from typing import Optional, Union, Sequence, Tuple

# Import local modules
from .utils import (
    RE_FEATURE,
    RE_FVALUE,
    match_initial,
    normalize,
    parse_constraints,
    replace_codepoints,
    split_fvalues_str,
)


class PhonoModel:
    """
    Class for representing a phonological model.
    """

    def __init__(self, name: str, model_path: Optional[str] = None) -> None:
        """
        Initialize a phonological model.

        @param name: Name of the model.
        @param model_path: The path to the directory holding the model configuration
            files. If not provided, the library will default to the resources distributed
            along with its package.
        """

        # Setup model and defaults
        self.name = name  # model name
        self.features = defaultdict(set)  # set of features in the model
        self.fvalues = {}  # dictionary of structures with fvalues, as from CSV file

        # Dictionary with extra, internal material
        self._grapheme2fvalues = {}
        self._fvalues2grapheme = {}
        self._diacritics = {}
        self._classes = []

        # Build a path for reading the model (if it was not provided, we assume it
        # lives in the `model/` directory), and then load the features/values first
        # and the sounds later
        if not model_path:
            model_path = pathlib.Path(__file__).parent.parent.parent / "models" / name
        else:
            model_path = pathlib.Path(model_path).absolute()

        self._init_model(model_path)
        self._init_sounds(model_path)

    def _init_model(self, model_path: pathlib.Path) -> None:
        """
        Internal method for initializing a model.

        The method will read the feature/fvalues configurations stored in
        the `model.csv` file.

        @param model_path: Path to model directory.
        """

        # Parse file with feature definitions
        with open(model_path / "model.csv", encoding="utf-8") as csvfile:
            for row in csv.DictReader(csvfile):
                # Extract and clean strings as much as we can
                feature = row["FEATURE"].strip()
                fvalue = row["FVALUE"].strip()
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
                # the constraint string ("constraints" will be an empty list if
                # row["CONSTRAINTS"] is empty)
                prefix = replace_codepoints(row["PREFIX"])
                suffix = replace_codepoints(row["SUFFIX"])
                if prefix:
                    self._diacritics[prefix] = fvalue
                if suffix:
                    self._diacritics[suffix] = fvalue

                self.fvalues[fvalue] = {
                    "feature": feature,
                    "rank": rank,
                    "prefix": prefix,
                    "suffix": suffix,
                    "constraints": parse_constraints(row.get("CONSTRAINTS")),
                }

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

    def _init_sounds(self, model_path: pathlib.Path) -> None:
        """
        Internal method for initializing the sounds of a model.

        The method will read the sounds stored in the `sounds.csv` file.

        @param model_path: Path to model directory.
        """

        # Load the the descriptions as an internal dictionary; we also
        # normalize the grapheme by default; note that here we only sort for
        # comparison, alphabetically, with the actual rank sorting only performed
        # at the end if all checks pass
        with open(model_path / "sounds.csv", encoding="utf-8") as csvfile:
            _graphemes = {}
            for row in csv.DictReader(csvfile):
                grapheme = normalize(row["GRAPHEME"])
                _graphemes[grapheme] = split_fvalues_str(row["DESCRIPTION"])
                if row["CLASS"] == "True":
                    self._classes.append(grapheme)

        # Check for duplicate descriptions.
        dupl_desc = [
            desc for desc, count in Counter(_graphemes.values()).items() if count > 1
        ]
        for desc in dupl_desc:
            at_fault = "/".join(
                [
                    grapheme
                    for grapheme, description in _graphemes.items()
                    if description == desc
                ]
            )
            raise ValueError(f"`{desc}` is used for more than one sound ({at_fault})")

        # Check for bad fvalues names
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
                raise ValueError(f"/{grapheme}/ fails constraint check on {failed}")

            # Update the internal catalog
            self._grapheme2fvalues[grapheme] = fvalues
            self._fvalues2grapheme[fvalues] = grapheme

    def build_grapheme(self, fvalues: Sequence) -> str:
        """
        Return a grapheme representation for a collection of feature values.

        @param fvalues: A collection of feature values.
        @return: A grapheme representation of the provided collection of feature values.
        """

        # We first make sure the value_tuple is actually an expected, sorted tuple
        # TODO: can we drop this isinstance check?
        if isinstance(fvalues, str):
            fvalues = split_fvalues_str(fvalues)
        grapheme = self._fvalues2grapheme.get(fvalues, None)

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
            modifier = self.sort_fvalues(modifier)

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

    def set_fvalue(
        self, fvalues: Sequence, new_fvalue: str, check: bool = True
    ) -> Tuple[Sequence, Optional[str]]:
        """
        Set a single value in a collection of feature values.

        The method will remove all other feature values for the same feature before
        setting the provided one.

        @param fvalues:
        @param new_fvalue: The value to be added to the sound.
        @param check: Whether to run constraints check after adding the new value
            (default: True).
        @return: The previous feature value for the feature, in case it was replaced, or
            `None` in case no replacement happened. If the method is called to add a
            feature value which is already set, the same feature value will be returned
            (indicating that there was already a feature value for the corresponding
            feature).
        """

        # If the feature value is already set, not need to do the whole operation,
        # including clearing the cache, so just return to confirm
        if new_fvalue[0] not in "+-" and new_fvalue in fvalues:
            return fvalues, new_fvalue
        elif new_fvalue[0] == "+" and new_fvalue[1:] in fvalues:
            return fvalues, new_fvalue[1:]

        # We need a different treatment for setting positive values (i.e. "voiced")
        # and for removing them (i.e., "-voiced"). Note that it does *not* raise an
        # error if the value is not present (we use .discard(), not .remove())
        prev_fvalue = None
        if new_fvalue[0] == "-":
            if new_fvalue[1:] in fvalues:
                prev_fvalue = new_fvalue[1:]
                fvalues = [fvalue for fvalue in fvalues if fvalue != prev_fvalue]
        else:
            # Remove the implied `+`, if present
            if new_fvalue[0] == "+":
                new_fvalue = new_fvalue[1:]

            # Get the feature related to the value, cache its previous value (if any),
            # and remove it; we set `idx` to `None` in the beginning to avoid
            # false positives of non-initialization
            feature = self.fvalues[new_fvalue]["feature"]
            for _fvalue in fvalues:
                if _fvalue in self.features[feature]:
                    prev_fvalue = _fvalue
                    break

            # Remove the previous value (if there is one) and add the new value
            fvalues = [new_fvalue] + [fv for fv in fvalues if fv != prev_fvalue]

        # Run a check if so requested (default)
        if check and self.fail_constraints(fvalues):
            raise ValueError(f"FValue {new_fvalue} breaks a constraint")

        # Sort the new `fvalues`, which also makes sure we return a tuple
        # return self.sort_fvalues(fvalues), prev_fvalue
        return frozenset(fvalues), prev_fvalue

    def parse_grapheme(self, grapheme: str) -> Tuple[Sequence, bool]:
        """
        Parse a grapheme according to the library standard.

        The information on partiality, the second element of the returned tuple, is
        currently obtained from the `self._classes` internal structure. Note that,
        while the information is always returned, it is up to the calling function
        (usually the homonym `.parse_grapheme()` method of the `Sound` class) to
        decide whether and how to use this information.

        @param grapheme: A grapheme representation to be parsed.
        @return: The first element of the tuple is a Sequence with the feature values
            from the parsed grapheme. The second element is a boolean indicating whether
            the grapheme should be consider the representation of a partially defined
            sound (i.e., a sound class).
        """

        # Used model/cache graphemes if available; it is already a sorted tuple
        if grapheme in self._grapheme2fvalues:
            return self._grapheme2fvalues[grapheme], grapheme in self._classes

        # Capture list of modifiers, if any; no need to go full regex
        modifiers = []
        if "[" in grapheme and grapheme[-1] == "]":
            grapheme, _, modifier = grapheme.partition("[")
            modifiers = [mod.strip() for mod in split_fvalues_str(modifier[:-1])]

        # If the base is among the list of graphemes, we can just return the
        # grapheme values and apply the modifier. Otherwise, we take all characters
        # that are diacritics (remember we perform NFD normalization), remove them
        # while updating the modifier list, and again add the modifier at the end.
        # Note that diacritics are inserted to the beginning of the list, so that
        # the modifiers explicitly listed as value names are consumed at the end.
        # TODO: as the diacritics are now defined as single characters, we could just
        #       iterate over characters
        base_grapheme = ""
        while grapheme:
            grapheme, diacritic = match_initial(grapheme, self._diacritics)
            if not diacritic:
                base_grapheme += grapheme[0]
                grapheme = grapheme[1:]
            else:
                modifiers.insert(0, self._diacritics[diacritic])

        # Add base character and modifiers
        fvalues = self._grapheme2fvalues[base_grapheme]
        for mod in modifiers:
            # We only perform the check when adding the last modifier in the list
            check = mod == modifiers[-1]
            fvalues, _ = self.set_fvalue(fvalues, mod, check=check)

        # No need to sort, as it is already returned as a sorted tuple by .set_fvalue()
        return fvalues, base_grapheme in self._classes

    # TODO: `no_rank` is confusing as a name, look for an alternative
    def sort_fvalues(self, fvalues: Sequence, no_rank: bool = False) -> Tuple:
        """
        Sort a list of values according to the model.

        By default, the method sorts by rank first and, in case of multiple values with
        the same rank, alphabetically later. It is possible to perform a simple
        alphabetical sorting.

        @param fvalues: A list (or other iterable) of values or a string description of
            them. If a string is provided, the method will split them in the standard
            way.
        @param no_rank: Whether to perform a plain alphabetical sorting, not using the
            rank information. This is convenient in some cases and better than a simple
            Python `sorted()` operation as it takes care of splitting strings and
            accepting both strings and lists (default: `False`).
        @return: A tuple with the sorted values.
        """

        if isinstance(fvalues, str):
            fvalues = split_fvalues_str(fvalues)

        if no_rank:
            return tuple(sorted(fvalues))

        return tuple(sorted(fvalues, key=lambda v: (-self.fvalues[v]["rank"], v)))

    def feature_dict(self, fvalues: Sequence) -> dict:
        """
        Return a dictionary version of a feature value tuple.

        @param fvalues: The collection of feature values to be converted to a dictionary.
        @return: A dictionary with feature as keys and feature values as values. Only
            features for feature values that are found are included.
        """

        return {self.fvalues[fvalue]["feature"]: fvalue for fvalue in fvalues}

    def fail_constraints(self, fvalues: Sequence) -> list:
        """
        Checks if a list of feature values has any constraint failure.

        The method will check a list of feature values against the internal model,
        returning the list of feature values that fail the constraint check. The list
        will be empty if all feature values pass the checks; as empty lists are
        `False` by definition, a sound correctness can be checked with
        `if model.fail_constraints(fvalues)`. Note that, by definition, an empty list
        of feature values will be consider a valid one (as it will return an empty list
        of failing feature values).

        @param fvalues: A list, or another iterable, of the feature values to be checked,
            such as those stored in `self._grapheme2fvalues`.
        @return: A list of strings with the feature values that fail constraint check; it
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

    def fvalues2graphemes(self, fvalues_str: str, classes: bool = False) -> list:
        """
        Collect the set of graphemes in the model that satisfy a list of fvalues.

        Note that this will match the provided list against the sounds
        defined in the model only. To check against a custom list of sounds, it possible
        to use the overload operators, creating new sounds and checking whether they
        are equal or a superset (i.e., `>=`).

        @param fvalues_str: A list of feature values provided as constraints, such as
            `"+vowel +front -close"`.
        @param classes: Whether to include class graphemes in the output (default: False)
        @return: A list of all graphemes that satisfy the provided constraints.
        """

        # In this case we parse the fvalues as if they were constraints
        constraints = parse_constraints(fvalues_str)

        # Note that we could make the code more general by relying on
        # `.fail_constraints()`, but this would make the logic more complex and a bit
        # slower. It is better to perform a separately implemented check here,
        # unless we refactor the entire class.
        pass_test = []
        for fvalues, sound in self._fvalues2grapheme.items():
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
            pass_test = [sound for sound in pass_test if sound not in self._classes]

        return pass_test

    # TODO: have vector as a different method that uses this
    def minimal_matrix(self, sounds, vector: bool = False):
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
        # the model; otherwise, just take them as lists of values. The [0] indexing
        # is in place so we only extract the fvalues, discarding information on
        # sound partial definition
        sounds = [
            item if not isinstance(item, str) else self.parse_grapheme(item)[0]
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
                        matrix[frozenset(sound_fvalues)][feature] = fvalue
                        break

        # Return only fvalues, if a vector was requested, or a dict (instead of a
        # defaultdict) otherwise
        if vector:
            return list(matrix.values())

        return dict(matrix)

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    def class_features(self, sounds) -> dict:
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
        # the model; otherwise, just take them as lists of values. The [0] indexing
        # is in place so we only extract the fvalues, discarding information on
        # sound partial definition
        sounds = [
            item if not isinstance(item, str) else self.parse_grapheme(item)[0]
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

    def fvalue_vector(
        self, source: Union[str, list], categorical: bool = False
    ) -> Tuple[list, list]:
        """
        Build a vector representation of a sound from its fvalues.

        Vectors compiled with this method are mostly intended for statistical analyses,
        and can be either binary or categorical.

        @param source: Either a string with a grapheme or a feature value tuple for the
            sound to serve as basis for the vector.
        @param categorical: Whether to build a categorical vector instead of a binary one
            (default: `False`).
        @return: A tuple whose first element is a list with the feature names represented
            in the vector. The names will match the model features' names in the case of
            categorical vectors, or follow the pattern `feature_featurevalue` in the case
            of binary ones. The second element is a list with the actual vector. The
            elements will be the feature values strings when set and `None` when not set
            in the case of categorical vectors, or booleans indicating the presence or
            absence of the corresponding feature value in the case of binary vectors.
        """

        # Get the fvalues from the grapheme if `source` is a string
        if isinstance(source, str):
            # [0] to discard information on partial definition
            source_fvalues = self.parse_grapheme(source)[0]
        else:
            source_fvalues = source

        # Collect vector data in categorical or binary form
        if categorical:
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

    # TODO: consider the tuple in the return, which is not the most elegant solution
    def closest_grapheme(self, source, classes: bool = True):
        """
        Find the sound in the model that is the closest to a given value tuple.

        The method can be used to coarse sounds within a reference group.

        Parameters
        ----------
        source : tuple or str
            A feature value tuple, usually coming from the `.values` attributed of
            a sound,  or a string with a grapheme to be parsed.
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

        # Get the features if a grapheme was passed, or, in case of a feature tuple,
        # check if the corresponding grapheme happens to be already in our
        # internal list
        if isinstance(source, str):
            # [0] to discard information of partial definition
            fvalues = self.parse_grapheme(source)[0]
        else:
            fvalues = source

        # fvalues = self.sort_fvalues(fvalues)
        if fvalues in self._fvalues2grapheme:
            grapheme = self._fvalues2grapheme[fvalues]
            if not all([classes, grapheme in self._classes]):
                return self._fvalues2grapheme[fvalues], fvalues

        # Compute a similarity score based on inverse rank for all
        # graphemes, building a string with the representation if we hit a
        # `best_score`.
        best_score = 0.0
        best_fvalues = None
        grapheme = None
        for candidate_v, candidate_g in self._fvalues2grapheme.items():
            # Don't include classes if asked so
            if not classes and candidate_g in self._classes:
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

    def __str__(self) -> str:
        """
        Return a textual representation of the model.

        @return: A string with a textual description of the model.
        """

        _str = f"[`{self.name}` model ({len(self.features)} features, "
        _str += f"{len(self.fvalues)} fvalues, "
        _str += f"{len(self._grapheme2fvalues)} graphemes)]"

        return _str


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")