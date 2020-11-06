# TODO: unicode escaper -- as utils?
# TODO: allow initialization from description to be a list and not only a stirng,
#       making __add__ and __sub__ easier for example
# TODO: allow " and " as separator for adding and removing features
# TODO: add __hash__ and comparison
# TODO: getattribute and set attribute can work on features
# TODO: investigate __slots__
# TODO: overload operators
# TODO: build implies -> e.g., all plosives will be consonants automatically
# TODO: use unidecode? other normalizations?
# TODO: cache grapheme at the end of add_value/add_values

import unicodedata


class Sound:
    """
    Class representing a bundle of phonetic features according to a model.

    Note that, by definition, a sound does not need to be a "complete sound", but
    can also be used to represent sound classes (such "consonant" or "front vowel").
    The class is intended to work with any generic model provided by the
    PhonoModel class.
    """

    def __init__(self, model, grapheme=None, description=None):
        # Store model, initialize, and add descriptors
        self.model = model
        self.values = []

        # Initialize/empty the cache
        self._empty_cache()

        # Either a description or a grapheme must be provided
        if all([grapheme, description]) or not any([grapheme, description]):
            raise ValueError("Either a `grapheme` or a `description` must be provided.")
        else:
            if grapheme:
                self.add_values(model.grapheme2values[grapheme])
            else:
                self.add_values(description)

    def _empty_cache(self):
        """
        Internal function for creating/clearning the cache.
        """

        self._cache = {"grapheme": None, "description": None}

    def add_value(self, value, check=True):
        """
        Add a value to the sound.

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
        # clearning the cache, so just return to confirm
        if value in self.values:
            return value

        # Clear the cache
        self._empty_cache()

        # Get the feature related to the value, cache its previous value (if any),
        # and remove it
        feature = self.model.values[value]["feature"]
        prev_value = None
        for idx, _value in enumerate(self.values):
            if _value in self.model.features[feature]:
                prev_value = value
                break
        if prev_value:
            self.values.pop(idx)

        # Add the new feature
        self.values.append(value)

        # Run a check if so requested (default)
        if check and self.model.fail_constraints(self.values):
            raise ValueError(f"Value {value} ({feature}) breaks a constraint")

        return prev_value

    # TODO: Instead of wrapping, we can do everything here, also smarter (setting constr)
    def add_values(self, values, check=True):
        """
        Add multiple values to the sound.

        The method will remove all conflicting values before setting the new ones.
        Currently, this method acts as a wrapper to `.add_value()`

        Parameters
        ----------
        values : list or str
            A list of strings with the values to be added to the sound, a string
            with values separated by spaces, commas, or semicolons.
        check : bool
            Whether to run constraints check after adding the new values (default: True).

        Returns
        -------
        replaced : list
            A list of strings with the values that were replaced, in no particular
            order.
        """

        # Note that we don't need to empty the cache, as it will be done repeatedly
        # by `.add_value()` in this implementation (a small price to pay)

        # If `values` is a string, we assume it is space-separated list of
        # `values`, which can preprocess a bit. Note that this allows to use a
        # string with a single descriptor without any special treatment.
        # TODO: preprocessing
        if isinstance(values, str):
            values = values.replace(",", " ")
            values = values.replace(";", " ")
            values = values.split()

        # Add all values, collecting the replacements which are stripped of Nones
        replaced = [self.add_value(value, check=False) for value in values]
        replaced = [value for value in replaced if value]

        # Run a check if so requested (default)
        if check:
            offending = self.model.fail_constraints(self.values)
            if offending:
                raise ValueError(f"At least one constraint unsatisfied by {offending}")

        return replaced

    def grapheme(self):
        # get the grapheme from the cache, if it exists
        if self._cache["grapheme"]:
            return self._cache["grapheme"]

        # We first build a feature tuple and check if there is a model match...
        feat_tuple = tuple(sorted(self.values))
        grapheme = self.model.values2grapheme.get(feat_tuple, None)

        # If no match, we look for the closest one
        if not grapheme:
            # Compute a similarity score based on inverse rank for all
            # graphemes, building a string with the representation if we hit a
            # `best_score`
            best_score = 0.0
            best_features = None
            for candidate_f, candidate_g in self.model.values2grapheme.items():
                common = [value for value in feat_tuple if value in candidate_f]
                score = sum([1 / self.model.values[value]["rank"] for value in common])
                if score > best_score:
                    best_score = score
                    best_features = candidate_f
                    grapheme = candidate_g

            # Build grapheme, adding prefixes/suffixes for all missing values;
            # we also build a `leftover` list of values that could not be expressed
            # with affixes and which will be added later
            not_common = [value for value in feat_tuple if value not in best_features]
            leftover = []
            for value in not_common:
                # If there is no prefix or no suffix
                prefix = self.model.values[value]["prefix"]
                suffix = self.model.values[value]["suffix"]
                if not any([prefix, suffix]):
                    leftover.append(value)
                else:
                    grapheme = f"{prefix}{grapheme}{suffix}"

            if leftover:
                grapheme = f"{grapheme}[{','.join(sorted(leftover))}]"

        # Unicode and other normalizations
        grapheme = unicodedata.normalize("NFC", grapheme)

        # Store in the cache and return
        self._cache["grapheme"] = grapheme

        return grapheme

    def __repr__(self):
        # Return the cache description, if it exists
        if self._cache["description"]:
            return self._cache["description"]

        # Build the description following the rank
        # TODO: what about same weight values, like palatalization and velarization? alphabetical?
        desc = " ".join(
            sorted(
                self.values, reverse=True, key=lambda v: self.model.values[v]["rank"]
            )
        )

        # Store the description in the cache and return
        self._cache["description"] = desc

        return desc

    def __str__(self):
        return self.grapheme()

    def __add__(self, other):
        _snd = Sound(self.model, description=" ".join(self.values))
        _snd.add_values(other)
        return _snd

    def __sub__(self, other):
        other = other.replace(",", " ")
        other = other.replace(";", " ")
        values = [value for value in self.values if value not in other.split()]
        return Sound(self.model, description=" ".join(values))
