import csv
from pprint import pprint
from collections import defaultdict

# TODO: solution for name order, with a weight

# TODO: rename implies to constrains (should have OR?)

# TODO: allow to initialize a bundle from a grapheme in the model (including modifiers)
class Bundle:
    """
    Class representing a bundle of phonetic features according to a model.

    Note that, by definition, a bundle does not need to be a complete sound, but
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
                self.set_description(model.graph2feats[grapheme])

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
            feature = self.model.value2feature[descriptor]
            self.values = [
                value
                for value in self.values
                if value not in self.model.features[feature]
            ]
            self.values.append(descriptor)

    def grapheme(self):
        # get the grapheme from the model

        # We first build a feature tuple and check if there is a perfect match in
        # the model. If not, we look for the closest match...
        # TODO: add a cache in the model
        feat_tuple = tuple(sorted(self.values))
        grapheme = self.model.feats2graph.get(feat_tuple, None)
        if not grapheme:
            # Compute a similarity score based on inverse value weight for all
            # graphemes, building a string with the representation if we hit a
            # `best_score`
            best_score = 0.0
            best_features = None
            best_grapheme = None
            for candidate_f, candidate_g in self.model.feats2graph.items():
                common = [value for value in feat_tuple if value in candidate_f]
                score = sum([1 / self.model.weights[value] for value in common])
                if score > best_score:
                    best_score = score
                    best_features = candidate_f
                    best_grapheme = candidate_g

            # Build grapheme
            # TODO: deal with diacritics
            not_common = [value for value in feat_tuple if value not in best_features]
            grapheme = f"{best_grapheme}[{','.join(not_common)}]"

        return grapheme

    def __repr__(self):
        # TODO: build in order, something which probably should be cached
        return " ".join(sorted(self.values))


class PhonoModel:
    def __init__(self, feature_file, inventory_file):
        # TODO: read model name from file name
        self.name = "bipa"

        # Parse file with feature definitions
        self.features = defaultdict(list)
        self.weights = {}
        self.implies = defaultdict(list)
        self.value2feature = {}
        with open(feature_file) as csvfile:
            for row in csv.DictReader(csvfile):
                # Make sure the value is not repeated
                if row["VALUE"] in self.value2feature:
                    raise ValueError(f"Duplicate value {row['VALUE']}")
                else:
                    # Store features (also as reverse map) as weights
                    self.features[row["FEATURE"]].append(row["VALUE"])
                    self.value2feature[row["VALUE"]] = row["FEATURE"]
                    self.weights[row["VALUE"]] = int(row["WEIGHT"])

                    # Store implies (unless it is an empty string, as read from file)
                    if row["IMPLIES"]:
                        self.implies[row["VALUE"]].append(row["IMPLIES"])

        # Read inventory
        # TODO: add checks
        self.graph2feats = {}
        self.feats2graph = {}
        with open(inventory_file) as csvfile:
            for row in csv.DictReader(csvfile):
                feat_tuple = tuple(sorted(row["DESCRIPTION"].split()))
                self.graph2feats[row["GRAPHEME"]] = feat_tuple
                self.feats2graph[feat_tuple] = row["GRAPHEME"]
