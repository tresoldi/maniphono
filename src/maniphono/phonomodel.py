"""
Module for phonological model abstraction and operations.
"""

# Import Python standard libraries
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Iterable, Union
import csv
import itertools
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
    euclidean,
)


# TODO: how to deal with resonant=-stop?
# TODO: review "partial" and "complete" graphemes


class PhonoModel:
    def __init__(
        self, name: str, model_path: Optional[Union[str, Path]] = None
    ) -> None:
        # Setup model, instantiating variables and defaults
        self.name = name  # model name
        self.features = defaultdict(set)  # set of features in the model
        self.fvalues = {}  # dictionary of structures with fvalues, as from CSV file

        # Auxiliary variables for the various operations, not intended for direct access
        self._grapheme2fvalues = {}
        self._fvalues2grapheme = {}
        self._diacritics = {}
        self._snd_classes = []
        self._info = {}  # additional, non-mandatory information on sounds

        # Build a Path object for loading the model (if it was not provided, we assume it
        # lives in the `models/` directory), and then load the features/values first
        # and the sounds later
        if not model_path:
            model_path = Path(__file__).parent / "models" / name
        else:
            model_path = Path(model_path).absolute()

        # Invoke the model loader in each subclass
        self._init_model(model_path)

    def _init_model(self, model_path: Path) -> None:
        raise NotImplementedError

    def build_grapheme(self, fvalues: Sequence) -> str:
        raise NotImplementedError

    def parse_grapheme(self, grapheme: str) -> Tuple[Sequence, bool]:
        raise NotImplementedError

    def closest_grapheme(
        self, source: Sequence, classes: bool = True
    ) -> Tuple[str, frozenset]:
        raise NotImplementedError

    def get_info(self, source, field):
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class MachineModel(PhonoModel):
    """
    Class for representing a phonological model with quantitative feature description.
    """

    def __init__(
        self, name: str, model_path: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Initialize a machine phonological model.

        Parameters
        ----------
        name : str
            Name of the model.
        model_path : str, optional
            The path to the directory holding the model configuration files. If not
            provided, the library will default to the resources distributed along
            with the `maniphono` package.

        Raises
        ------
        ValueError
            If the model name is invalid, if the model path is invalid, if the model
            contains invalid feature names, if the model contains invalid feature
            values, if the model contains duplicate feature values, if the model
            contains invalid ranks, if the model contains constraints that refer to
            undefined feature values, or if the model contains invalid graphemes.
        """

        # Initialize variables specific to machine models
        self._grapheme2vector = {}

        # Call superclass constructor
        super().__init__(name, model_path)

    def _init_model(self, model_path: Path) -> None:
        """
        Internal method for initializing a model.

        The method will read the feature/fvalues configurations stored in
        the `model.csv` file.

        Parameters
        ----------
        model_path : Path
            Path to model directory.

        Raises
        ------
        ValueError
            If the model contains invalid feature names, if the model contains
            invalid feature values, if the model contains duplicate feature values,
            if the model contains invalid ranks, or if the model contains constraints
            that refer to undefined feature values.
        """

        # Read the contents of the the model `graphemes.tsv` file, where the first
        # column is the grapheme and the remaining columns are the elements in
        # the feature vector
        with open(model_path / "graphemes.tsv", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            for row in reader:
                # Extract and clean strings as much as we can
                grapheme = row[0].strip()
                vector = [fvalue.strip() for fvalue in row[1:]]

                # Run checks
                if not grapheme:
                    raise ValueError(
                        f"Invalid grapheme in model `{self.name}`: {grapheme}"
                    )
                try:
                    vector = [float(fvalue) for fvalue in vector]
                except:
                    raise ValueError(
                        f"Invalid feature value in model `{self.name}`: {vector}"
                    )

                # Store grapheme and vector
                self._grapheme2vector[grapheme] = vector

    def parse_grapheme(self, grapheme: str) -> Tuple[Sequence, bool]:
        """
        Parse a grapheme into a feature vector.

        Parameters
        ----------
        grapheme : str
            Grapheme to parse.

        Returns
        -------
        Tuple[Sequence, bool]
            A tuple containing the feature vector and a boolean indicating
            whether the grapheme is partial or not.
        """

        # For the time being, we assume that the grapheme is not partial
        # and that it is a valid grapheme, so that we just query the
        # self._grapheme2vector dictionary and return the result
        return self._grapheme2vector[grapheme], False

    def closest_grapheme(
        self, source: Sequence[float], classes: bool = True
    ) -> Tuple[str, frozenset]:
        """
        Find the closest grapheme to a given feature vector.

        Parameters
        ----------
        source : Sequence
            Feature vector to match.
        classes : bool, optional
            Whether to return the sound class of the closest grapheme. Defaults
            to `True`.

        Returns
        -------
        Tuple[str, frozenset]
            A tuple containing the closest grapheme and the sound class of the
            grapheme, if `classes` is `True`. If `classes` is `False`, the
            second element of the tuple will be an empty set.
        """

        # Find the closest grapheme and return it; the closest grapheme is
        # the one with the smallest Euclidean distance to the source vector
        closest = min(
            self._grapheme2vector.items(),
            key=lambda x: euclidean(source, x[1]),
        )

        return closest[0], frozenset()


class HumanModel(PhonoModel):
    """
    Class for representing a phonological model with qualitative feature description.
    """

    def __init__(
        self, name: str, model_path: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Initialize a human phonological model.

        Parameters
        ----------
        name : str
            Name of the model.
        model_path : str, optional
            The path to the directory holding the model configuration files. If not
            provided, the library will default to the resources distributed along
            with the `maniphono` package.

        Raises
        ------
        ValueError
            If the model name is invalid, if the model path is invalid, if the model
            contains invalid feature names, if the model contains invalid feature
            values, if the model contains duplicate feature values, if the model
            contains invalid ranks, if the model contains constraints that refer to
            undefined feature values, or if the model contains invalid graphemes.
        """

        # Call superclass constructor
        super().__init__(name, model_path)

        # self._init_model(model_path)
        # self._init_sounds(model_path)

    def _init_model(self, model_path: Path) -> None:
        """
        Internal method for initializing a model.

        The method will read the feature/fvalues configurations stored in
        the `model.csv` file.

        Parameters
        ----------
        model_path : Path
            Path to model directory.

        Raises
        ------
        ValueError
            If the model contains invalid feature names, if the model contains
            invalid feature values, if the model contains duplicate feature values,
            if the model contains invalid ranks, or if the model contains constraints
            that refer to undefined feature values.
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

                # Store values structs, which includes parsing the _diacritics and
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

        # Initialize the sounds
        self._init_sounds(model_path)

    def _init_sounds(self, model_path: Path) -> None:
        """
        Internal method for initializing the sounds of a model.

        The method will read the sounds stored in the `sounds.csv` file.

        Parameters
        ----------
        model_path : Path
            Path to model directory.

        Raises
        ------
        ValueError
            If the model contains invalid graphemes.
        """

        # Load the the descriptions as an internal dictionary; we also
        # normalize the grapheme by default; note that here we only sort for
        # comparison, alphabetically, with the actual rank sorting only performed
        # at the end if all checks pass
        _graphemes = {}
        with open(model_path / "sounds.csv", encoding="utf-8") as csvfile:
            for row in csv.DictReader(csvfile):
                # Collect the main information first: graphemes, descriptors,
                # and partial. If the "PARTIAL" column is not provided, `._snd_classes`
                # is left untouched, implying that no sound is partial
                grapheme = normalize(row.pop("GRAPHEME"))
                _graphemes[grapheme] = parse_fvalues(row.pop("DESCRIPTION"))
                partial = row.pop("PARTIAL", None)
                if partial == "True":
                    self._snd_classes.append(grapheme)

                # Collect additional information
                self._info[grapheme] = row

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
            self._grapheme2fvalues[grapheme] = fvalues
            self._fvalues2grapheme[fvalues] = grapheme

    # TODO: For partial sounds, we should allow (if desired) to build proper
    #       IPA representation instead of a shortcut for partial sounds
    #       (e.g., 'S̥' instead of 'SVL')
    # TODO: type annotation for sequence
    def build_grapheme(self, fvalues: Iterable) -> str:
        """
        Return a grapheme representation for a collection of feature values.

        The method will try to find a perfect match for the provided feature values,
        and if no match is found, it will try to find the closest match.

        Parameters
        ----------
        fvalues : Iterable
            A collection of feature values.

        Returns
        -------
        str
            A grapheme representation of the provided collection of feature values.

        Raises
        ------
        ValueError
            If the provided feature values are not valid.
        """

        # We first make sure `fvalues` is a sequence of fvalues parsed as
        # a frozenset, and try to obtain a perfect grapheme match
        fvalues = parse_fvalues(fvalues)
        grapheme = self._fvalues2grapheme.get(fvalues, None)

        # If there is no grapheme match, we look for the closest one
        if not grapheme:
            # Get the closest grapheme and its values from the model
            grapheme, best_fvalues = self.closest_grapheme(fvalues)

            # Extend the grapheme, adding prefixes/suffixes for all missing feature
            # values; we first get the dictionary of features for both the current
            # sound and the candidate, make a list of features missing/different in
            # the candidate, extend with the features in candidate not found in the
            # current one, add feature values that can be expressed with _diacritics,
            # and add the remaining feature values with full name.
            curr_features = self.feature_dict(fvalues)
            best_features = self.feature_dict(best_fvalues)

            # Collect the disagreements in a list of modifiers; note that it needs to
            # be sorted according to the rank to guarantee the order of values and
            # especially of _diacritics is the "canonical" one.
            modifier = []
            for feat, val in curr_features.items():
                if feat not in best_features:
                    modifier.append(val)
                elif val != best_features[feat]:
                    modifier.append(val)
            modifier = self.sort_fvalues(modifier)

            # Add all modifiers as _diacritics whenever possible; those without a
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
        currently obtained from the `self._snd_classes` internal structure. Note that,
        while the information is always returned, it is up to the calling function
        (usually the homonym `.parse_grapheme()` method of the `Sound` class) to
        decide whether and how to use this information.

        Parameters
        ----------
        grapheme : str
            A grapheme representation to be parsed.

        Returns
        -------
        tuple
            The first element of the tuple is a Sequence with the feature values
            from the parsed grapheme. The second element is a boolean indicating whether
            the grapheme should be consider the representation of a partially defined
            sound (i.e., a "sound class" as understood in maniphono).

        Raises
        ------
        ValueError
            If the provided grapheme is not valid.
        """

        # Used model/cache graphemes if available; it is already a sorted tuple
        if grapheme in self._grapheme2fvalues:
            return self._grapheme2fvalues[grapheme], grapheme in self._snd_classes

        # Capture list of modifiers, if any; no need to go full regex; note
        # that, while `parse_fvalues` returns a frozenset, we cast it to
        # a list here so that we can keep track of modifier order
        modifiers = []
        if "[" in grapheme and grapheme[-1] == "]":
            grapheme, _, modifier = grapheme.partition("[")
            modifiers += list(parse_fvalues(modifier[:-1]))  # drop final "]"

        # If the base is among the list of graphemes, we can just return the
        # grapheme values and apply the modifier. Otherwise, we take all characters
        # that are _diacritics (remember we perform NFD normalization), remove them
        # while updating the modifier list, and again add the modifier at the end.
        # Note that _diacritics are inserted to the beginning of the list, so that
        # the modifiers explicitly listed as value names are consumed at the end.
        base_grapheme = ""
        while grapheme:
            grapheme, diacritic = match_initial(grapheme, self._diacritics)
            if not diacritic:
                base_grapheme += grapheme[0]
                grapheme = grapheme[1:]
            else:
                modifiers.insert(0, self._diacritics[diacritic])

        # Add base character and modifiers; note that we can only check the validity of the
        # sound after setting all the fvalues
        fvalues = self._grapheme2fvalues[base_grapheme]
        for mod in modifiers:
            # We only perform the check when adding the last modifier in the list
            fvalues, _ = self.set_fvalue(fvalues, mod, check=False)

        offending = self.fail_constraints(fvalues)
        if offending:
            raise ValueError(f"Parsed graphemes fails contrainsts ({offending})")

        # Return the grapheme and whether it is a partial sound
        return fvalues, base_grapheme in self._snd_classes

    def set_fvalue(
        self, fvalues: Sequence, new_fvalue: str, check: bool = True
    ) -> Tuple[Iterable, Optional[str]]:
        """
        Set a single value in a collection of feature values.

        The method will remove all other feature values for the same feature before
        setting the provided one.

        Parameters
        ----------
        fvalues : Sequence
            A collection of fvalues which will be modified.
        new_fvalue : str
            The value to be added to the sound.
        check : bool, optional
            Whether to run constraints check after adding the new value
            (default: True).

        Returns
        -------
        tuple
            The first element of the tuple is the modified collection of feature values.
            The second element is the previous feature value for the feature, in case it
            was replaced, or `None` in case no replacement happened. If the method is
            called to add a feature value which is already set, the same feature value
            will be returned (indicating that there was already a feature value for the
            corresponding feature).

        Raises
        ------
        ValueError
            If the provided feature value is not valid.
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

        Parameters
        ----------
        fvalues : Sequence
            A list (or other iterable) of values or a string description of them. If a
            string is provided, the method will split them in the standard way.
        use_rank : bool, optional
            Whether to perform the default sorting or a simpler one using only
            alphabet sorting (and thus skipping over rank information). Even in the
            latter case, the method is convenient and recommended in place of a normal
            Python `sorted()` operation as it takes care of splitting strings and
            accepting different sequence types (default: `True`).

        Returns
        -------
        list
            A list with the sorted values.
        """

        # Make sure we have a frozenset
        fvalues = parse_fvalues(fvalues)

        # Sort according to the requested method
        if not use_rank:
            ret = sorted(fvalues)
        else:
            ret = sorted(fvalues, key=lambda v: (-self.fvalues[v]["rank"], v))

        return ret

    def feature_dict(self, fvalues: Iterable) -> dict:
        """
        Return a dictionary version of a feature value tuple.

        Parameters
        ----------
        fvalues : Iterable
            A collection of feature values.

        Returns
        -------
        dict
            A dictionary with feature as keys and feature values as values. Only
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

        Parameters
        ----------
        fvalues : Sequence
            A collection of feature values.

        Returns
        -------
        list
            A list of strings with the feature values that fail constraint check; it
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

        Parameters
        ----------
        fvalues : Sequence
            A collection of feature values.
        include_classes : bool, optional
            Whether to include class graphemes in the output (default: `False`).

        Returns
        -------
        list
            A list of strings with the graphemes that satisfy the provided
            constraints.
        """

        # In this case we parse the fvalues as if they were constraints
        constraints = parse_constraints(fvalues)

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

        # Remove sounds that are _snd_classes
        if not include_classes:
            pass_test = [sound for sound in pass_test if sound not in self._snd_classes]

        return pass_test

    def _parse_sound_group(self, sounds: Sequence) -> List[frozenset]:
        """
        Internal method allowing to accept groups of sounds specified in different ways.

        The method allows us to accept sounds defined as graphemes, fvalues frozen sets, of fvalues
        provided as strings, including mixing them.

        Parameters
        ----------
        sounds : Sequence
            A collection of sounds, provided either as graphemes, fvalues frozen sets, or fvalues
            provided as strings.

        Returns
        -------
        list
            A list of frozensets with the parsed sounds.
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
                    parsed = self.parse_grapheme(sound)[0]  # drops `partial` _info

                ret.append(parsed)
            else:
                ret.append(frozenset(sound))

        return ret

    def minimal_matrix(self, sounds) -> dict:
        """
        Compute the minimal feature matrix for a set of sounds or graphemes.

        The method will compute the minimal feature matrix for a set of sounds or
        graphemes, returning a dictionary with features as keys and feature values
        as values. The method will raise an error if the provided sounds are not
        consistent with the model.

        Parameters
        ----------
        sounds : Sequence
            A collection of sounds, provided either as graphemes or fvalues.

        Returns
        -------
        dict
            A dictionary with features as keys and feature values as values.

        Raises
        ------
        ValueError
            If the provided sounds are not consistent with the model.
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

        The values returned by this method are derived from the `.minimal_matrix()` method.

        Parameters
        ----------
        sounds : Sequence
            A collection of sounds, provided either as graphemes or fvalues.

        Returns
        -------
        list
            A list with feature values.

        Raises
        ------
        ValueError
            If the provided sounds are not consistent with the model.
        """

        return list(self.minimal_matrix(sounds).values())

    # While this method is to a good extend similar to `.minimal_matrix`, it is not
    # reusing its codebase as it would add an unnecessary level of abstraction.
    def class_features(self, sounds) -> dict:
        """
        Compute the class features for a set of graphemes or sounds.

        Parameters
        ----------
        sounds : Sequence
            A collection of sounds, provided either as graphemes or fvalues.

        Returns
        -------
        dict
            A dictionary with features as keys and feature values as values.

        Raises
        ------
        ValueError
            If the provided sounds are not consistent with the model.
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

        Parameters
        ----------
        source : Sequence
            Either a string with a grapheme or a feature value group for the
            sound to serve as basis for the vector.
        categorical : bool, optional
            Whether to build a categorical vector instead of a binary one
            (default: `False`).

        Returns
        -------
        tuple
            A tuple whose first element is a list with the feature names represented
            in the vector. The names will match the model features' names in the case of
            categorical vectors, or follow the pattern `feature_featurevalue` in the case
            of binary ones. The second element is a list with the actual vector. The
            elements will be the feature values strings when set and `None` when not set
            in the case of categorical vectors, or booleans indicating the presence or
            absence of the corresponding feature value in the case of binary vectors.
        """

        if isinstance(source, str):
            source_fvalues = self._parse_sound_group(source)[0]
        else:
            source_fvalues = self._parse_sound_group([source])[0]

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
    # TODO: allow a `k` parameter to return the `k` closest sounds
    def closest_grapheme(
        self, source: Iterable, classes: bool = True
    ) -> Tuple[str, frozenset]:
        """
        Find the sound in the model that is the closest to a given group of fvalues.

        The method can be used to coarse sounds within a reference group.

        Parameters
        ----------
        source : Iterable
            A feature value group, usually coming from the `.values` attributed of
            a sound, or a string with a grapheme to be parsed.
        classes : bool, optional
            Whether to allow a grapheme marked as a class to be returned (default: `True`).

        Returns
        -------
        tuple
            A tuple with the the grapheme representation as the first element and the
            frozenset of fvalues for the closes match as the second.

        Raises
        ------
        ValueError
            If the provided sounds are not consistent with the model.
        """

        fvalues = self._parse_sound_group([source])[0]

        if fvalues in self._fvalues2grapheme:
            grapheme = self._fvalues2grapheme[fvalues]
            if not all([classes, grapheme in self._snd_classes]):
                return self._fvalues2grapheme[fvalues], fvalues

        # Compute a similarity score based on inverse rank for all
        # graphemes, building a string with the representation if we hit a
        # `best_score`.
        best_score = 0.0
        best_fvalues = None
        grapheme = None
        for candidate_v, candidate_g in self._fvalues2grapheme.items():
            # Don't include _snd_classes if asked so
            if not classes and candidate_g in self._snd_classes:
                continue

            # Compute a score for the closest match; note that there is a penalty for
            # `extra` features, so that values such as "voiceless consonant" will tend
            # to match _snd_classes and not actual sounds
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

    # TODO: use a method different from `.closest_grapheme` -- perhaps a weight Jaccard on the fvalues?
    # TODO: review if really necessary
    def get_info(self, source, field):
        """
        Return additional information on a sound.

        The method is used to obtain non-mandatory information in a model, such as prosody value and
        sound class. If the `field` is not available, a `None` is returned. If the sound is not found
        in the model but is a valid one, the `field` for the closest sound will be returned.

        Note that field names are case-insensitive.

        Parameters
        ----------
        source : str or Sequence
            A sound to be parsed, either as a string with a grapheme or as a sequence of feature values.
        field : str
            The name of the field to be returned.

        Returns
        -------
        str or None
            The value of the field for the sound, or `None` if the field is not available.

        Raises
        ------
        ValueError
            If the provided sounds are not consistent with the model.
        """

        fvalues = self._parse_sound_group([source])[0]
        grapheme = self.build_grapheme(fvalues)

        return self._info[grapheme].get(field.upper(), None)

    def __str__(self) -> str:
        """
        Return a textual representation of the model.

        Returns
        -------
        str
            A string with a textual description of the model.
        """

        _str = f"[`{self.name}` model ({len(self.features)} features, "
        _str += f"{len(self.fvalues)} fvalues, "
        _str += f"{len(self._grapheme2fvalues)} graphemes)]"

        return _str


# Load default models
model_mipa = HumanModel("mipa")
model_tresoldi = HumanModel("tresoldi")
model_encoder = MachineModel("encoder")
