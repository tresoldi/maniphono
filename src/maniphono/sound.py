# TODO: default to grapheme, description secondary

# TODO: overload operators
# TODO: allow to initialize a sound from a grapheme in the model (including modifiers)
# TODO: build implies -> e.g., all plosives will be consonants automatically
# TODO: use unidecode? other normalizations?
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

        # Either a description or a grapheme must be provided
        if all([grapheme, description]) or not any([grapheme, description]):
            raise ValueError("Either a `grapheme` or a `description` must be provided.")
        else:
            if grapheme:
                self.set_description(model.grapheme2values[grapheme])
            else:
                self.set_description(description)

    # TODO: check the implies, at the end
    # TODO: cache grapheme at the end
    def set_description(self, descriptors):
        # If descriptors is a string, we assume it is space-separated list of
        # descriptors. Note that this allows to use a string with a single descriptor
        # without any special treatment.
        if isinstance(descriptors, str):
            descriptors = descriptors.split()

        # Add descriptors; note that this will run constraint checking
        self.add_values(descriptors)

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

        # If the value is already set, not need to do the whole operation, just return
        # to confirm
        if value in self.values:
            return value

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
        values : list
            A list of strings with the values to be added to the sound.
        check : bool
            Whether to run constraints check after adding the new values (default: True).

        Returns
        -------
        replaced : list
            A list of strings with the values that were replaced, in no particular
            order.
        """

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
        # get the grapheme from the model

        # We first build a feature tuple and check if there is a perfect match in
        # the model. If not, we look for the closest match...
        feat_tuple = tuple(sorted(self.values))
        grapheme = self.model.values2grapheme.get(feat_tuple, None)
        if not grapheme:
            # Compute a similarity score based on inverse rank for all
            # graphemes, building a string with the representation if we hit a
            # `best_score`
            best_score = 0.0
            best_features = None
            for candidate_f, candidate_g in self.model.feats2graph.items():
                common = [value for value in feat_tuple if value in candidate_f]
                score = sum([1 / self.model[value]['rank'] for value in common])
                if score > best_score:
                    best_score = score
                    best_features = candidate_f
                    grapheme = candidate_g

            # Build grapheme
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
                grapheme = f"{grapheme}[{','.join(leftover)}]"

        return grapheme

    def __repr__(self):
        # TODO: build in order, something which probably should be cached
        # TODO: what about same weight values, like palatalization and velarization? alphabetical?
        return " ".join(
            sorted(
                self.values, reverse=True, key=lambda v: self.model.values[v]["rank"]
            )
        )

    def __str__(self):
        return self.grapheme()
