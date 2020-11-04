# TODO: should WEIGHT be reversed to be more obvious? renameto RANK?
# TODO: rename implies to constrains (should have OR?)
# TODO: multiple implies, such as aspiration -> voiceless consonant; also positive negative?
# TODO: `model_path` is not strictly necessary, we can infer it if a default one
# TODO: already load and provide IPA/TRESOLDI models here

import csv
from collections import defaultdict
from pathlib import Path


class PhonoModel:
    def __init__(self, name, model_path=None):
        # Setup model and defaults
        self.name = name
        self.features = defaultdict(list)
        self.weights = {}
        self.implies = defaultdict(list)
        self.value2feature = {}
        self.modifiers = {}
        self.graph2feats = {}
        self.feats2graph = {}

        # Build a path for reading the model; if it was not provided, assume it lives in
        # the `model/` directory
        if not model_path:
            model_path = Path(__file__).parent.parent.parent / "models" / name
        else:
            model_path = Path(model_path).absolute()

        # Parse file with feature definitions
        # TODO: enforce feature/value name restrictions
        # TODO: strip strings?
        with open(model_path / "model.csv") as csvfile:
            for row in csv.DictReader(csvfile):
                # Make sure the value is not repeated
                if row["VALUE"] in self.value2feature:
                    raise ValueError(f"Duplicate value {row['VALUE']}")
                else:
                    # Store features (also as reverse map) as weights
                    self.features[row["FEATURE"]].append(row["VALUE"])
                    self.value2feature[row["VALUE"]] = row["FEATURE"]
                    self.weights[row["VALUE"]] = int(row["WEIGHT"])

                    # Store implies, if they exist
                    # TODO: parse here
                    if row["IMPLIES"]:
                        self.implies[row["VALUE"]].append(row["IMPLIES"])

                    # Store modifiers (i.e., diacritics)
                    self.modifiers[row["VALUE"]] = {
                        "prefix": row["PREFIX"],
                        "suffix": row["SUFFIX"],
                    }

        # Parse file with inventory; we build a feature tuple, alphabetically sorted,
        # as a hasheable key
        # TODO: add checks: feature/value, implies, duplicates
        # TODO: normalize description string and grapheme
        with open(model_path / "sounds.csv") as csvfile:
            for row in csv.DictReader(csvfile):
                feat_key = tuple(sorted(row["DESCRIPTION"].split()))
                self.graph2feats[row["GRAPHEME"]] = feat_key
                self.feats2graph[feat_key] = row["GRAPHEME"]


# Load default models
IPA = PhonoModel("ipa")
Tresoldi = PhonoModel("tresoldi")
