"""
Module for phonological model abstraction and operations.
"""

# Import Python standard libraries
from collections import defaultdict, Counter
from typing import List, Optional, Sequence, Tuple, Union
import csv
import itertools
import pathlib
import re

# Import local modules
from .common import (
    RE_FEATURE,
    RE_FVALUE,
    match_initial,
    normalize,
    parse_constraints,
    replace_codepoints,
    parse_fvalues,
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
            files. If not provided, the library will default to the resources
            distributed along with the maniphono package.
        """

        # Setup model, instantianting variables and defaults
        self.name = name  # model name
        self.features = defaultdict(set)  # set of features in the model
        self.fvalues = {}  # dictionary of structures with fvalues, as from CSV file
        self.grapheme2fvalues = {}
        self.fvalues2grapheme = {}
        self.diacritics = {}
        self.snd_classes = []

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
                    raise ValueError(f"Rank must be a value >= 1 (passed `{rank}`)")

                # Store feature values for all features
                self.features[feature].add(fvalue)

                # Store values structs, which includes parsing the diacritics and
                # the constraint string ("constraints" will be an empty list if
                # row["CONSTRAINTS"] is empty)
                prefix = replace_codepoints(row["PREFIX"])
                suffix = replace_codepoints(row["SUFFIX"])
                if prefix:
                    self.diacritics[prefix] = fvalue
                if suffix:
                    self.diacritics[suffix] = fvalue

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
        _graphemes = {}
        with open(model_path / "sounds.csv", encoding="utf-8") as csvfile:
            for row in csv.DictReader(csvfile):
                grapheme = normalize(row["GRAPHEME"])
                _graphemes[grapheme] = parse_fvalues(row["DESCRIPTION"])
                if row["CLASS"] == "True":
                    self.snd_classes.append(grapheme)

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

            # Update the internal catalogs
            self.grapheme2fvalues[grapheme] = fvalues
            self.fvalues2grapheme[fvalues] = grapheme

    def build_grapheme(self, fvalues: Sequence) -> str:
        """
        Return a grapheme representation for a collection of feature values.

        @param fvalues: A collection of feature values.
        @return: A grapheme representation of the provided collection of feature values.
        """

        # We first make sure `fvalues` is a sequence of fvalues parsed as
        # a frozenset, and try to obtain a perfect grapheme match
        fvalues = parse_fvalues(fvalues)
        grapheme = self.fvalues2grapheme.get(fvalues, None)

        # If there is no grapheme match, we look for the closest one
        if not grapheme:
            # Get the closest grapheme and its values from the model
            grapheme, best_fvalues = self.closest_grapheme(fvalues)

            # Extend the grapheme, adding prefixes/suffixes for all missing feature
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

    def parse_grapheme(self, grapheme: str) -> Tuple[Sequence, bool]:
        """
        Parse a grapheme according to the library standard.

        The information on partiality, the second element of the returned tuple, is
        currently obtained from the `self.snd_classes` internal structure. Note that,
        while the information is always returned, it is up to the calling function
        (usually the homonym `.parse_grapheme()` method of the `Sound` class) to
        decide whether and how to use this information.

        @param grapheme: A grapheme representation to be parsed.
        @return: The first element of the tuple is a Sequence with the feature values
            from the parsed grapheme. The second element is a boolean indicating whether
            the grapheme should be consider the representation of a partially defined
            sound (i.e., a sound class as understood in maniphono).
        """

        # Used model/cache graphemes if available; it is already a sorted tuple
        if grapheme in self.grapheme2fvalues:
            return self.grapheme2fvalues[grapheme], grapheme in self.snd_classes

        # Capture list of modifiers, if any; no need to go full regex
        modifiers = []
        if "[" in grapheme and grapheme[-1] == "]":
            grapheme, _, modifier = grapheme.partition("[")
            modifiers = parse_fvalues(modifier[:-1])  # drop final "]"

        # If the base is among the list of graphemes, we can just return the
        # grapheme values and apply the modifier. Otherwise, we take all characters
        # that are diacritics (remember we perform NFD normalization), remove them
        # while updating the modifier list, and again add the modifier at the end.
        # Note that diacritics are inserted to the beginning of the list, so that
        # the modifiers explicitly listed as value names are consumed at the end.
        base_grapheme = ""
        while grapheme:
            grapheme, diacritic = match_initial(grapheme, self.diacritics)
            if not diacritic:
                base_grapheme += grapheme[0]
                grapheme = grapheme[1:]
            else:
                modifiers.insert(0, self.diacritics[diacritic])

        # Add base character and modifiers; note that we can only check the validity of the
        # sound after setting all the fvalues
        fvalues = self.grapheme2fvalues[base_grapheme]
        for mod in modifiers:
            # We only perform the check when adding the last modifier in the list
            fvalues, _ = self.set_fvalue(fvalues, mod, check=False)

        offending = self.fail_constraints(fvalues)
        if offending:
            raise ValueError(f"Parsed graphemes fails contrainsts ({offending})")

        # Return the grapheme and whether it is a partial sound
        # TODO: recheck the partial information -- if the base_grapheme has modifications is it partial?
        return fvalues, base_grapheme in self.snd_classes

    def set_fvalue(
        self, fvalues: Sequence, new_fvalue: str, check: bool = True
    ) -> Tuple[Sequence, Optional[str]]:
        """
        Set a single value in a collection of feature values.

        The method will remove all other feature values for the same feature before
        setting the provided one.

        @param fvalues: a collection of fvalues which will be modified.
        @param new_fvalue: The value to be added to the sound.
        @param check: Whether to run constraints check after adding the new value
            (default: True).
        @return: The previous feature value for the feature, in case it was replaced, or
            `None` in case no replacement happened. If the method is called to add a
            feature value which is already set, the same feature value will be returned
            (indicating that there was already a feature value for the corresponding
            feature).
        """

        # If the feature value is already set, there is no need to do the
        # whole operation, so just return to confirm
        if new_fvalue[0] not in "+-" and new_fvalue in fvalues:
            return fvalues, new_fvalue
        elif new_fvalue[0] == "+" and new_fvalue[1:] in fvalues:
            return fvalues, new_fvalue[1:]

        # We need a different treatment for setting positive values (e.g. "voiced")
        # and for removing them (e.g., "-voiced"). Note that it does *not* raise an
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
            # and remove it
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

        # Sort the new `fvalues`, which also makes sure we return a frozenset,
        # and the replace fvalue, if any
        return frozenset(fvalues), prev_fvalue

    def sort_fvalues(self, fvalues: Sequence, use_rank: bool = True) -> list:
        """
        Sort a list of values according to the model.

        By default, the method sorts by rank first and, in case of multiple values with
        the same rank, alphabetically later. It is possible to perform a simple
        alphabetical sorting.

        @param fvalues: A list (or other iterable) of values or a string description of
            them. If a string is provided, the method will split them in the standard
            way.
        @param use_rank: Whether to perform the default sorting or a simpler one
            using only alphabet sorting (and thus skipping over rank information).
            Even in the latter case, the method is convenient and recommended in place
            of a normal Python `sorted()` operation as it takes care of splitting
            strings and accepting different sequence types (default: `True`).
        @return: A tuple with the sorted values.
        """

        # Make sure we have a frozenset
        fvalues = parse_fvalues(fvalues)

        # Sort according to the requested method
        if not use_rank:
            ret = sorted(fvalues)
        else:
            ret = sorted(fvalues, key=lambda v: (-self.fvalues[v]["rank"], v))

        return ret

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
        Checks if a group of feature values has any constraint failure.

        The method will check a group of feature values against the internal model,
        returning the list of feature values that fail the constraint check. The list
        will be empty if all feature values pass the checks; as empty lists are
        `False` by definition, a correctness can be checked with
        `if model.fail_constraints(fvalues)`. Note that, by the same definition
        and design, an empty list of feature values will be consider a valid one (as
        it will return an empty list of failing feature values), allowing sounds
        of which nothing is known about (empty set).

        @param fvalues: A list, or another iterable, of the feature values to be checked,
            such as those stored in `self.grapheme2fvalues`.
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

    # TODO: could have a supporting function, outside the class, to apply to a custom group
    #       of sounds, which would be better for coarsing
    def fvalues2graphemes(
        self, fvalues: Sequence, include_classes: bool = False
    ) -> list:
        """
        Collect the set of graphemes in the model that satisfy a group of fvalues.

        Note that this will match the provided list only against the sounds
        defined in the model. To check against a custom list of sounds, it possible
        to use the overload operators, creating new sounds and checking whether they
        are equal or a superset (i.e., `>=`).

        @param fvalues: A group of fvalues/constraints with a list of feature values provided as constraints,
            such as `"+vowel +front -close"` or `["vowel", "+front", "-close"]`.
        @param include_classes: Whether to include class graphemes in the output (default: False)
        @return: A list of all graphemes that satisfy the provided constraints.
        """

        # In this case we parse the fvalues as if they were constraints
        constraints = parse_constraints(fvalues)

        # Note that we could make the code more general by relying on
        # `.fail_constraints()`, but this would make the logic more complex and a bit
        # slower. It is better to perform a separately implemented check here,
        # unless we refactor the entire class.
        pass_test = []
        for fvalues, sound in self.fvalues2grapheme.items():
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

        # Remove sounds that are snd_classes
        if not include_classes:
            pass_test = [sound for sound in pass_test if sound not in self.snd_classes]

        return pass_test

    def _parse_sound_group(self, sounds: Sequence) -> List[frozenset]:
        """
        Internal method allowing to accept groups of sounds specified in different ways.

        The method allows us to accept sounds defined as graphemes, fvalues frozen sets, of fvalues
        provided as strings, including mixing them.

        @param sounds:
        @return:
        """

        ret = []
        for sound in sounds:
            if isinstance(sound, str):
                # If we obtain a single string, it can be either a grapheme or a textual representation
                # of fvalues. To distinguish, we try to parse it as fvalues and check the consistency
                # of the results.
                # TODO: should delegate the checking of valid names to another method
                parsed = parse_fvalues(sound)
                if not all([fvalue in self.fvalues for fvalue in parsed]):
                    parsed = self.parse_grapheme(sound)[0]  # drop `partial` info

                ret.append(parsed)
            else:
                ret.append(frozenset(sound))

        return ret

    def minimal_matrix(self, sounds) -> dict:
        """
        Compute the minimal feature matrix for a set of sounds or graphemes.

        @param sounds: The sounds to be considered in the minimal matrix, provided either as
            a list of graphemes or a list of fvalues.
        @return: A minimal matrix with features as keys as feature values as values.
        """

        sounds = self._parse_sound_group(sounds)

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

        return dict(matrix)

    def minimal_vector(self, sounds) -> list:
        """
        Compute the minimal feature vector for a set of sounds or graphemes.

        The values returned by this method are derived from the `.minimal_matrix()` method..

        @param sounds: The sounds to be considered in the minimal matrix, provided either as
            a list of graphemes or a list of fvalues.
        @return: A minimal vector with feature values.
        """

        return list(self.minimal_matrix(sounds).values())

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    def class_features(self, sounds) -> dict:
        """
        Compute the class features for a set of graphemes or sounds.

        @param sounds: The sounds to be considered when computing class features, provided either
            as a list of graphemes or a group of fvalues.
        @return: A dictionary with the common traits that make a class out of the
            provided sounds, with feature as keys and feature values as values.
        """

        sounds = self._parse_sound_group(sounds)

        # Build list of values for the sounds
        features = defaultdict(list)
        for fvalues in sounds:
            for fvalue in fvalues:
                features[self.fvalues[fvalue]["feature"]].append(fvalue)

        # Keep only features with a perfect match;
        # len(values) == len(sounds) checks that there are no NAs;
        # len(set(values)) == 1 checks if there is a match
        features = {
            feature: fvalues[0]
            for feature, fvalues in features.items()
            if len(fvalues) == len(sounds) and len(set(fvalues)) == 1
        }

        return features

    def fvalue_vector(
        self, source: Sequence, categorical: bool = False
    ) -> Tuple[list, list]:
        """
        Build a vector representation of a sound from its fvalues.

        Vectors compiled with this method are mostly intended for statistical analyses,
        and can be either binary or categorical.

        @param source: Either a string with a grapheme or a feature value group for the
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

        source_fvalues = self._parse_sound_group(source)[0]

        # Collect vector data in either categorical or binary form
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
    def closest_grapheme(
        self, source: Sequence, classes: bool = True
    ) -> Tuple[str, frozenset]:
        """
        Find the sound in the model that is the closest to a given group of fvalues.

        The method can be used to coarse sounds within a reference group.

        @param source: A feature value group, usually coming from the `.values` attributed of
            a sound, or a string with a grapheme to be parsed.
        @param classes:  Whether to allow a grapheme marked as a class to be returned; note that,
            if a grapheme class is passed but `snd_classes` is set to `False`, a different
            grapheme will be returned (default: True).
        @return: A tuple with the the grapheme representation as the first element and the
            frozenset of fvalues for the closes match as the second.
        """

        fvalues = self._parse_sound_group([source])[0]

        # fvalues = self.sort_fvalues(fvalues)
        if fvalues in self.fvalues2grapheme:
            grapheme = self.fvalues2grapheme[fvalues]
            if not all([classes, grapheme in self.snd_classes]):
                return self.fvalues2grapheme[fvalues], fvalues

        # Compute a similarity score based on inverse rank for all
        # graphemes, building a string with the representation if we hit a
        # `best_score`.
        best_score = 0.0
        best_fvalues = None
        grapheme = None
        for candidate_v, candidate_g in self.fvalues2grapheme.items():
            # Don't include snd_classes if asked so
            if not classes and candidate_g in self.snd_classes:
                continue

            # Compute a score for the closest match; note that there is a penalty for
            # `extra` features, so that values such as "voiceless consonant" will tend
            # to match snd_classes and not actual sounds
            common = [fvalue for fvalue in fvalues if fvalue in candidate_v]
            extra = [fvalue for fvalue in candidate_v if fvalue not in fvalues]
            score_common: float = sum(
                [1.0 / self.fvalues[fvalue]["rank"] for fvalue in common]
            )
            score_extra: float = sum(
                [1.0 / self.fvalues[fvalue]["rank"] for fvalue in extra]
            )
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
        _str += f"{len(self.grapheme2fvalues)} graphemes)]"

        return _str


# Load default models
model_mipa = PhonoModel("mipa")
model_tresoldi = PhonoModel("tresoldi")
