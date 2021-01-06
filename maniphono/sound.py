"""
Module for sound abstractions and operations.

This module holds the code for the sound model.
"""

# TODO: expand module documentation
# TODO: getattribute and set attribute can work on features
# TODO: investigate __slots__
# TODO: build implies -> e.g., all plosives will be consonants automatically
# TODO: set cache in the model (that is shared) and not in each segment

# Import Python standard libraries
import re
import unicodedata

# Import local modules
from .phonomodel import model_mipa
from .utils import _split_values, normalize


class Sound:
    """
    Class representing a bundle of phonetic features according to a model.

    Note that, by definition, a sound does not need to be a "complete sound", but
    can also be used to represent sound classes (such "consonant" or "front vowel").
    The class is intended to work with any generic model provided by the
    PhonoModel class.
    """

    def __init__(self, grapheme=None, description=None, model=None):
        # Initialize the main property, the set of values
        self.values = set()

        # Store model (defaulting to MIPA)
        self.model = model or model_mipa

        # Either a description or a grapheme must be provided
        if all([grapheme, description]) or not any([grapheme, description]):
            raise ValueError("Either a `grapheme` or a `description` must be provided.")

        # Set the values
        if not grapheme:
            self.add_values(description)
        elif grapheme in self.model.grapheme2values:
            self.add_values(self.model.grapheme2values[grapheme])
        else:
            self._parse_grapheme(grapheme)

    def _parse_grapheme(self, grapheme):
        """
        Internal function for parsing a grapheme.
        """

        # Capture list of modifiers, if any; no need to go full regex
        base, _, modifier = grapheme.partition("[")
        if modifier:
            modifier = [mod.strip() for mod in _split_values(modifier[:-1])]

        # If the base is among the list of graphemes, we can just return the
        # grapheme values and apply the modifier. Otherwise, we take all characters
        # that are diacritics (remember we perform NFD normalization), remove them
        # while updating the modifier list, and again add the modifier at the end.
        # Note that diacritics are inserted to the beginning of the list, so that
        # the modifiers explicitly listed as value names are consumed at the end.
        # TODO: this assumes diacritics are always one character, which could be good
        # TODO: needs to be updated if the cache system is added to the model
        if base not in self.model.grapheme2values:
            new_base = ""
            for char in base:
                if char in self.model.diacritics:
                    modifier.insert(0, self.model.diacritics[char])
                else:
                    new_base += char
            base = new_base

        # Add base character and modifiers
        self.add_values(self.model.grapheme2values[base])
        self.add_values(modifier)

    # TODO: rename to `set_value`?
    def add_value(self, value, check=True):
        """
        Add a single value to the sound.

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

        # If the value is already set, not need to do the whole operation, including
        # clearing the cache, so just return to confirm
        if value in self.values:
            return value

        # We need a different treatment for setting positive values (i.e. "voiced")
        # and for removing them (i.e., "-voiced"). Note that it does *not* raise an
        # error if the value is not present (we use .discard(), not .remove())
        prev_value = None
        if value[0] == "-":
            if value[1:] in self.values:
                self.values.discard(value[1:])
                prev_value = value[1:]
        else:
            # Get the feature related to the value, cache its previous value (if any),
            # and remove it; we set `idx` to `None` in the beginning to avoid
            # false positives of non-initialization
            feature = self.model.values[value]["feature"]
            for _value in self.values:
                if _value in self.model.features[feature]:
                    prev_value = _value
                    break

            # Remove the previous value (if there is one) and add the new value
            self.values.discard(prev_value)
            self.values.add(value)

        # Run a check if so requested (default)
        if check and self.model.fail_constraints(self.values):
            raise ValueError(f"Value {value} ({feature}) breaks a constraint")

        return prev_value

    def add_values(self, values, check=True):
        """
        Add multiple values to the sound.

        The method will remove all conflicting values before setting the new ones.
        Currently, this method acts as a wrapper to `.add_value()`

        Parameters
        ----------
        values : list or str
            A list of strings with the values to be added to the sound, a string
            with values separated by the delimiters specified in
            `_split_values()`.
        check : bool
            Whether to run constraints check after adding the new values (default: True).

        Returns
        -------
        replaced : list
            A list of strings with the values that were replaced, in no particular
            order.
        """

        # If `values` is a string, we assume it is space-separated list of
        # `values`, which can preprocess a bit. Note that this allows to use a
        # string with a single descriptor without any special treatment.
        if isinstance(values, str):
            values = _split_values(values)

        # Add all values, collecting the replacements which are stripped of Nones;
        # note that we don't run checks here, but only after all values have been added
        replaced = [self.add_value(value, check=False) for value in values]
        replaced = [value for value in replaced if value]

        # Run a check if so requested (default)
        if check:
            offending = self.model.fail_constraints(self.values)
            if offending:
                raise ValueError(f"At least one constraint unsatisfied by {offending}")

        return replaced

    # TODO: implement cache in the model
    # TODO: should be a property?
    def grapheme(self):
        """
        Return a graphemic representation of the current sound.
        """

        # We first build a feature tuple and check if there is a model match...
        value_tuple = tuple(sorted(self.values))
        grapheme = self.model.values2grapheme.get(value_tuple, None)

        # If no match, we look for the closest one
        if not grapheme:
            # Compute a similarity score based on inverse rank for all
            # graphemes, building a string with the representation if we hit a
            # `best_score`.
            # TODO: change to computation to penalize extra features, so that
            #       `C[+plosive]` has a better score than `t[-alveolar]`
            best_score = 0.0
            best_values = None
            grapheme = None
            for candidate_v, candidate_g in self.model.values2grapheme.items():
                common = [value for value in value_tuple if value in candidate_v]
                score = sum([1 / self.model.values[value]["rank"] for value in common])
                if score > best_score:
                    best_score = score
                    best_values = candidate_v
                    grapheme = candidate_g

            # Extend grapheme, adding prefixes/suffixes for all missing values; we first
            # get the dictionary of features for both the current sound and the
            # candidate, make a list of features missing/different in the candidate,
            # extend with the features in candidate not found in the current one, add
            # values that can be expressed with diacritics, and add the remaining
            # values with full name.
            curr_features = self.feature_dict()
            best_features = Sound(description=best_values).feature_dict()

            # Collect the disagreements in a list of modifiers; note that it needs to
            # be sorted according to the rank to guarantee the order of values and
            # especially of diacritics is the "canonical" one.
            modifier = []
            for feat, val in curr_features.items():
                if feat not in best_features:
                    modifier.append(val)
                elif val != best_features[feat]:
                    modifier.append(val)
            modifier = sorted(modifier, key=lambda v: self.model.values[v]["rank"])

            # Add all modifiers as diacritics whenever possible; those without a
            # diacritic are collected in an `expression` list and will be given
            # using their name (including those that need to be removed and not
            # replaced, thus preceded by a "-")
            expression = []
            for value in modifier:
                prefix = self.model.values[value]["prefix"]
                suffix = self.model.values[value]["suffix"]
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

    # TODO: should be a property?
    def feature_dict(self):
        """
        Return the defined features as a dictionary.
        """

        return {self.model.values[value]["feature"]: value for value in self.values}

    # TODO: as rank is ascending, the alphabet is inverted in the sorting
    def __repr__(self):
        """
        Return a representation with full name values.

        The list of values is ordered by rank first and alphabetically in case of
        values with equal ranks.
        """

        desc = " ".join(
            sorted(
                self.values,
                reverse=True,
                key=lambda v: (self.model.values[v]["rank"], v),
            )
        )

        return desc

    def __str__(self):
        """
        Return a graphemic normalized representation of the sound.
        """

        return self.grapheme()

    def __add__(self, other):
        """
        Overload the `+` operator.
        """

        snd = Sound(description=self.values, model=self.model)
        snd.add_values(other)

        return snd

    def __sub__(self, other):
        """
        Overload the `-` operator.
        """

        values = [value for value in self.values if value not in _split_values(other)]

        return Sound(description=" ".join(values), model=self.model)

    def __hash__(self):
        """
        Return a hash of the current sound.
        """

        return hash(tuple(self.values))

    def __eq__(self, other):
        """
        Compare two sounds in terms of their values.
        """

        return hash(self) == hash(other)

    def __lt__(self, other):
        """
        Checks if the values of the current sound are a subset of the other.
        """

        other_dict = other.feature_dict()
        for feature, value in self.feature_dict():
            if feature not in other_dict:
                return False
            elif other_dict[feature] != value:
                return False

        return True

    def __gt__(self, other):
        """
        Checks if the values of the current sound are a superset of the other.
        """

        this_dict = self.feature_dict()
        for feature, value in other.feature_dict():
            if feature not in this_dict:
                return False
            elif this_dict[feature] != value:
                return False

        return True
