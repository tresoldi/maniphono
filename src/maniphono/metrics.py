from typing import Optional, Union
from pathlib import Path
import csv

# Import 3rd party libraries
import joblib
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR

from .phonomodel import PhonoModel, model_mipa


class DistanceRegressor:
    def __init__(self, model=model_mipa):
        self.regressor = None
        self.model = model

    # TODO: write documentation once regressors have been extended
    def build_regressor(self, regtype="svr", filename=None, matrix_file=None):
        """
        Build or replace the quantitative distance regressor.

        Note that this method will silently replace any existing regressor.
        """

        # Load serialized model, if provided and existing
        if filename:
            filename = pathlib.Path(filename)
            if filename.is_file():
                self.regressor = joblib.load(filename.as_posix())
                return
            raise RuntimeError(f"Unable to read regressor from {filename}")

        # Read raw distance data and cache vectors, also allowing to
        # skip over unmapped graphemes
        # TODO: some graphemes are failing because of unknown diacritics
        raw_matrix = self._read_distance_matrix(matrix_file)
        vector = {}
        for grapheme in raw_matrix:
            try:
                _, vector[grapheme] = self.model.fvalue_vector(grapheme)
            except KeyError:
                print("Skipping over grapheme [%s]..." % grapheme)

        # Collect (x,y) vectors
        x, y = [], []
        for grapheme_a in raw_matrix:
            if grapheme_a in vector:
                for grapheme_b, dist in raw_matrix[grapheme_a].items():
                    if grapheme_b in vector:
                        x.append(vector[grapheme_a] + vector[grapheme_b])
                        y.append(dist)

        # Train regressor; setting the random value for reproducibility
        np.random.seed(42)
        if regtype == "mlp":
            self.regressor = MLPRegressor(random_state=1, max_iter=500)
        elif regtype == "svr":  # default
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

        # Build and cache a regressor with default parameters
        if not self.regressor:
            self.build_regressor()

        # `.value_vector()` takes care of always returning values, whether `sound_a`
        # and `sound_b` are graphemes or lists
        _, vector_a = self.model.fvalue_vector(sound_a)
        _, vector_b = self.model.fvalue_vector(sound_b)

        # If the vectors are equal, by definition the distance is zero
        if tuple(vector_a) == tuple(vector_b):
            return 0.0

        # Compute distance with the regressor
        return self.regressor.predict([vector_a + vector_b])[0]

    # TODO: extend return annotation
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
            filepath = Path(__file__).parent.parent.parent / "distances" / "default.tsv"
            filepath = filepath.as_posix()

        matrix = {}
        with open(filepath, encoding="utf-8") as tsvfile:
            for row in csv.DictReader(tsvfile, delimiter="\t"):
                grapheme = row.pop("GRAPHEME")
                matrix[grapheme] = {gr: float(dist) for gr, dist in row.items()}

        return matrix
