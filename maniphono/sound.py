"""
Module for Sound abstraction and operations.
"""

# Import local modules
from .phonomodel import model_mipa
from .utils import _split_fvalues


class Sound:
    """
    Class for representing a sound as a bundle of feature values.

    By design, a "sound" does not need to be a "complete sound", as it can
    hold any number of feature values, including none. All sounds work with
    phonological models provided by the an instance of the `PhonoModel`
    class. If a `model` is not provided, the library will default to
    a shared MIPA model.

    A sound can be initialized with either a `grapheme` (the default) or a
    `description`.

    Parameters
    ----------
    grapheme : str
        A string with a grapheme to be parsed or read directly from the model.
        Either a `grapheme` or a `description` can be provided for initialization.
    description : str
        A string with a list of feature values separated by one of the accepted
        delimiters.
        Either a `grapheme` or a `description` can be provided for initialization.
    model : PhonoModel
        A phonological model in the `PhonoModel` class (default:
        `phonomodel.model_mipa`).
    """

    def __init__(self, grapheme=None, description=None, model=None):
        """
        Initialization method.
        """

        # Initialize the main property, the tuple of values
        self.fvalues = tuple()

        # Store model (defaulting to MIPA)
        self.model = model or model_mipa

        # Either a description or a grapheme must be provided
        # # pylint: disable=no-else-raise
        if all([grapheme, description]) or not any([grapheme, description]):
            raise ValueError("Either a `grapheme` or a `description` must be provided.")
        elif grapheme:
            self.fvalues = self.model.parse_grapheme(grapheme)
        else:
            self.add_fvalues(description)

    def set_fvalue(self, fvalue, check=True):
        """
        Set a single feature value to the sound.

        The method will remove all other feature values for the same feature
        before setting the new one.

        This method works as a convenient wrapper to the equivalent method in
        `PhonoModel`.

        Parameters
        ----------
        fvalue : str
            The feature value to be added to the sound.
        check : bool
            Whether to run constraints check after adding the new feature
            value (default: True).

        Returns
        -------
        prev_value : str or None
            The previous feature value for the feature, in case it was replaced, or
            None, in case no replacement happened. If the method is called to add a
            feature value which is already set, it will be returned as well
            (indicating that there was already a value for the corresponding feature).
        """

        self.fvalues, prev_fvalue = self.model.set_fvalue(self.fvalues, fvalue, check)

        return prev_fvalue

    def add_fvalues(self, fvalues, check=True):
        """
        Add multiple feature values to the sound.

        The method will remove all conflicting feature values before setting the new
        ones. The method acts as a wrapper to `.add_value()`

        Parameters
        ----------
        fvalues : list or str
            A list of strings with the feature values to be added to the sound, a string
            with values separated by the delimiters specified in `_split_values()`.
        check : bool
            Whether to run constraint checks after adding the new feature values
            (default: True).

        Returns
        -------
        replaced : list
            A list of strings with the feature values that were replaced, in no
            particular order.
        """

        # If `fvalues` is a string, we assume it is space-separated list of
        # feature values, which can preprocess. Note that this allows to use a
        # string with a single descriptor without any special treatment.
        if isinstance(fvalues, str):
            fvalues = _split_fvalues(fvalues)

        # Add all fvalues, collecting the replacements which are stripped of `None`s;
        # note that we don't run checks here, but only after all values have been added
        replaced = [self.set_fvalue(fvalue, check=False) for fvalue in fvalues]
        replaced = [fvalue for fvalue in replaced if fvalue]

        # Run a check if so requested (default)
        if check:
            offending = self.model.fail_constraints(self.fvalues)
            if offending:
                raise ValueError(f"At least one constraint unsatisfied by {offending}")

        return replaced

    def grapheme(self):
        """
        Return a graphemic representation of the current sound.

        Return
        ------
        grapheme : str
            A string withthe graphemic representation of the sound.
        """

        return self.model.build_grapheme(self.fvalues)

    def feature_dict(self):
        """
        Return a dictionary of features and feature values that are defined.

        Return
        ------
        fdict : dict
            A dictionary of all feature values that are defined for the current sound,
            with features as keys and feature values as values.
        """

        return self.model.feature_dict(self.fvalues)

    def __repr__(self):
        """
        Return a representation with full name values.

        Following the convention from `PhonoModel`, the list of values is ordered by
        feature value rank first and, in case of feature values with equal ranks,
        alphabetically second.

        Return
        ------
        r : str
            A string with a representation of the current sound.
        """

        return " ".join(self.model.sort_fvalues(self.fvalues))

    def __str__(self):
        """
        Return a graphemic representation of the sound.

        By design, the `str()` command will return the same value of the
        `.grapheme()` method.

        Return
        ------
        s : str
            A string with the graphemic representation of the sound.
        """

        return self.grapheme()

    def __add__(self, other):
        """
        Overload the `+` operator.
        """

        snd = Sound(description=self.fvalues, model=self.model)
        snd.add_fvalues(other)

        return snd

    def __sub__(self, other):
        """
        Overload the `-` operator.
        """

        fvalues = [
            fvalue for fvalue in self.fvalues if fvalue not in _split_fvalues(other)
        ]

        return Sound(description=" ".join(fvalues), model=self.model)

    def __hash__(self):
        """
        Return a hash of the current sound.
        """

        return hash(self.model.sort_fvalues(self.fvalues))

    def __eq__(self, other):
        """
        Compare two sounds in terms of their fvalues.
        """

        return hash(self) == hash(other)

    def __lt__(self, other):
        """
        Checks if the fvalues of the current sound are a subset of the other.
        """

        other_dict = other.feature_dict()
        for feature, fvalue in self.feature_dict().items():
            if feature not in other_dict:
                return False
            if other_dict[feature] != fvalue:
                return False

        return True

    def __gt__(self, other):
        """
        Checks if the fvalues of the current sound are a superset of the other.
        """

        this_dict = self.feature_dict()
        for feature, fvalue in other.feature_dict().items():
            if feature not in this_dict:
                return False
            if this_dict[feature] != fvalue:
                return False

        return True

    def __le__(self, other):
        return any([self == other, self < other])

    def __ge__(self, other):
        return any([self == other, self > other])

    def __getattr__(self, feature):
        """
        Get feature values from their features as object attributes.

        Return
        ------
        fvalue : string
            A string with the feature value for the requested `feature`, or `None`
            if no feature value associated with the requested `feature` has been
            set.
        """

        for fvalue in self.fvalues:
            if self.model.fvalues[fvalue]["feature"] == feature:
                return fvalue

        return None
