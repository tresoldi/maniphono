from typing import Optional, Union
import pathlib
import csv
import logging
import itertools

# Import 3rd party libraries
import joblib
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR

from .phonomodel import PhonoModel, model_mipa
from .sound import Sound


class DistanceRegressor:
    def __init__(
        self, matrix_file=None, regressor_file=None, regtype="svr", model=model_mipa
    ):
        self.regressor = None
        self.model = model
        self.regtype = regtype

        # TODO: test `reg_type`

        # Instantiate `._raw_matrix`; if a `regressor_file` is provided, load the
        # serialized model. Otherwise, read the matrix_file (which will likely be
        # used to train a model)
        self._raw_matrix: dict = {}
        if regressor_file:
            filename = pathlib.Path(regressor_file)
            if not filename.is_file():
                raise RuntimeError(f"Unable to read regressor from {filename}")
            self.regressor = joblib.load(filename.as_posix())
        else:
            # If `matrix_file` is None, the function will load the default one
            self._read_distance_matrix(matrix_file)

    def _read_distance_matrix(self, filepath: Optional[str] = None) -> dict:
        """
        Read a distance matrix, used to seed a regressor.

        @param filepath: Path to the TSV file containing the distance matrix used to seed the
            regressor. If not provided, will default to one derived from data presented in
            Mielke (2012) and included with the library.
        @return: A dictionary of dictionaries with the distances as floating-point
            values.
        """

        if not filepath:
            filepath = (
                pathlib.Path(__file__).parent.parent.parent
                / "distances"
                / "default.tsv"
            )
            filepath = filepath.as_posix()

        with open(filepath, encoding="utf-8") as tsvfile:
            for row in csv.DictReader(tsvfile, delimiter="\t"):
                # Graphemes are parsed to make sure they are normalized, valid, etc. The `distances`
                # dictionary is created without a comprehension, so we can skip over bad graphemes
                # TODO: have `Sound` return information on bad grapheme, so we can rework these
                #       ugly try/excepts; we can also show which graphemes are skipped
                try:
                    sound_a = Sound(row.pop("GRAPHEME"))
                    for gr, dist in row.items():
                        try:
                            sound_b = Sound(gr)
                            self._raw_matrix[str(sound_a), str(sound_b)] = float(dist)
                            # print(sound_a, sound_b, dist)
                        except:
                            pass
                except:
                    pass

    # TODO: write documentation once regressors have been extended
    def build_regressor(self):
        """
        Build or replace the quantitative distance regressor.

        Note that this method will silently replace any existing regressor.
        """

        # Read raw distance data and cache vectors, also allowing to
        # skip over unmapped graphemes. We sort `graphemes` to make inspection
        # easier
        # TODO: some graphemes are failing because of unknown diacritics
        vector = {}
        graphemes = set(itertools.chain.from_iterable(self._raw_matrix.keys()))
        for grapheme in sorted(graphemes):
            try:
                _, vector[grapheme] = self.model.fvalue_vector(grapheme)
            except KeyError:
                # logging.warning("Skipping over grapheme [%s]...", grapheme)
                pass

        # Collect (x,y) vectors
        x, y = [], []
        for (grapheme_a, grapheme_b), dist in self._raw_matrix.items():
            if grapheme_a in vector and grapheme_b in vector:
                x.append(vector[grapheme_a] + vector[grapheme_b])
                y.append(dist)

        # Train regressor; setting the random value for reproducibility
        np.random.seed(42)
        if self.regtype == "mlp":
            self.regressor = MLPRegressor(random_state=1, max_iter=500)
        elif self.regtype == "svr":  # default
            self.regressor = SVR()

        self.regressor.fit(x, y)

    # TODO: rename to `serialize` or something similar?
    def write_regressor(self, regressor_file: str):
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

        if not self.regressor:
            raise ValueError("No regressor to serialize.")

        # Build a pathlib object, create the directory (if necessary), and write
        regressor_file = pathlib.Path(regressor_file).absolute()
        regressor_file.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.regressor, regressor_file.as_posix())

    # TODO: decide if we should really build a regressor by default
    def distance(self, sound_a: Union[str, list], sound_b: Union[str, list]) -> float:
        """
        Return a quantitative distance based on a seed matrix.

        The distance is by definition 0.0 for equal sounds. If no regressor has
        previously been trained, one will be trained with default values and cached for
        future calls. Note that this method, as all methods related to quantitative
        distances, uses the `sklearn` library.

        @param sound_a: The first sound to be used for distance computation.
        @param sound_b: The second sound to be used for distance computation.
        @return: The distance between the two sounds.
        """

        sound_a, sound_b = Sound(sound_a), Sound(sound_b)

        # Build and cache a regressor with default parameters; `regtype` as None indicated
        # not to train a regressor
        if not self.regressor and self.regtype:
            self.build_regressor()

        # If we have no `self.regressor`, we try to match the `raw_matrix` only
        if not self.regressor:
            if sound_a == sound_b:
                return 0.0

            return self._raw_matrix[str(sound_a), str(sound_b)]

        # `.value_vector()` takes care of always returning values, whether `sound_a`
        # and `sound_b` are graphemes or lists
        _, vector_a = self.model.fvalue_vector(sound_a.fvalues)
        _, vector_b = self.model.fvalue_vector(sound_b.fvalues)

        # If the vectors are equal, by definition the distance is zero
        if vector_a == vector_b:
            return 0.0

        # Compute distance with the regressor
        return self.regressor.predict([vector_a + vector_b])[0]
