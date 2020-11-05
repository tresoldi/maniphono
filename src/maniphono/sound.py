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

    def __init__(self, model, description=None, grapheme=None):
        # Store model, initialize, and add descriptors
        self.model = model
        self.values = []

        # Either a description or a grapheme must be provided
        if all([description, grapheme]) or not any([description, grapheme]):
            raise ValueError("Either a `description` or a `grapheme` must be provided.")
        else:
            if description:
                self.set_description(description)
            else:
                self.set_description(model.grapheme2values[grapheme])

    # TODO: check the implies, at the end
    # TODO: cache grapheme at the end
    def set_description(self, descriptors):
        # If descriptors is a string, we assume it is space-separated list of
        # descriptors. Note that this allows to use a string with a single descriptor
        # without any special treatment.
        if isinstance(descriptors, str):
            descriptors = descriptors.split()

        # Add each descriptor
        for descriptor in descriptors:
            # Get the feature for the value, remove all conflicting values,
            # and add the current one
            self.add_value(descriptor)

    # TODO: add multiple values?
    # TODO: run constraint check
    def add_value(self, value):
        # Get the feature related to the value, remove all values for that feature,
        # and add the new feature
        feature = self.model.values[value]["feature"]
        self.values = [
            _value
            for _value in self.values
            if _value not in self.model.features[feature]
        ]
        self.values.append(value)

    def grapheme(self):
        # get the grapheme from the model

        # We first build a feature tuple and check if there is a perfect match in
        # the model. If not, we look for the closest match...
        # TODO: add a cache in the model
        feat_tuple = tuple(sorted(self.values))
        grapheme = self.model.values2grapheme.get(feat_tuple, None)
        if not grapheme:
            # Compute a similarity score based on inverse value weight for all
            # graphemes, building a string with the representation if we hit a
            # `best_score`
            best_score = 0.0
            best_features = None
            for candidate_f, candidate_g in self.model.feats2graph.items():
                common = [value for value in feat_tuple if value in candidate_f]
                score = sum([1 / self.model.weights[value] for value in common])
                if score > best_score:
                    best_score = score
                    best_features = candidate_f
                    grapheme = candidate_g

            # Build grapheme
            not_common = [value for value in feat_tuple if value not in best_features]
            leftover = []
            for value in not_common:
                # If there is no prefix or no suffix
                prefix = self.model.modifiers[value]["prefix"]
                suffix = self.model.modifiers[value]["suffix"]
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
