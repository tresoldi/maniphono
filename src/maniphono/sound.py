"""
Module for Sound abstraction and operations.
"""

# Import Python standard libraries
from typing import Optional, Union

# Import local modules
from .phonomodel import PhonoModel, model_mipa
from .utils import split_fvalues_str


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
    """

    def __init__(
        self,
        grapheme: Optional[str] = None,
        description: Optional[str] = None,
        partial: Optional[bool] = None,
        model: Optional[PhonoModel] = None,
    ) -> None:
        """
        Initialization method.

        @param grapheme: A string with a grapheme to be parsed or read directly from the
            model. Either a `grapheme` or a `description` can be provided for
            initialization.
        @param description: A string with a list of feature values separated by one of
            the accepted delimiters. Either a `grapheme` or a `description` can be
            provided for initialization.
        @param partial: A boolean indicating whether the sound should be considered a
            partially defined one. Partially defined sounds (in most cases, the
            equivalent of "sound classes") work differently in terms of comparison, and
            might be used differently by the user. The argument defaults to `None`,
            indicating that the user should decide how to treat sounds when there is not
            explicit information on them being partially defined or not.
        @param model: A phonological model in the `PhonoModel` class (default:
            `phonomodel.model_mipa`).
        """

        # Initialize the main property, the tuple of values, and information on
        # partial sounds. By default, `partial` will be `None`; if a sound initialized
        # with a `description` is supposed to be a partial one, this must explicitly
        # informed by the user
        # TODO: Use the "feature bundle" to be implemented
        self.fvalues = tuple()
        self.partial = partial

        # Store model (defaulting to MIPA)
        self.model = model or model_mipa

        # Either a description or a grapheme must be provided
        if all([grapheme, description]) or not any([grapheme, description]):
            raise ValueError("Either a `grapheme` or a `description` must be provided.")

        if grapheme:
            # Set the new `.fvalues` and, if it does not override a user-provided one,
            # the information on partially that mostly comes from a `class` attribute
            # in the sound list of the model
            self.fvalues, parser_partial = self.model.parse_grapheme(grapheme)
            if self.partial is None:
                self.partial = parser_partial
        else:
            self.set_fvalues(description)

    def set_fvalue(self, fvalue: str, check: bool = True) -> Optional[str]:
        """
        Set a single feature value to the sound.

        The method will remove all other feature values for the same feature before
        setting the new one. This method works as a convenient wrapper to the equivalent
        method in `PhonoModel`.

        @param fvalue: The feature value to be added to the sound.
        @param check: Whether to run constraints check after adding the new feature
            value (default: True).
        @return: The previous feature value for the feature, in case it was replaced, or
            None, in case no replacement happened. If the method is called to add a
            feature value which is already set, it will be returned as well
            (indicating that there was already a value for the corresponding feature).
        """

        self.fvalues, prev_fvalue = self.model.set_fvalue(self.fvalues, fvalue, check)

        return prev_fvalue

    def set_fvalues(self, fvalues: Union[str, list], check: bool = True) -> list:
        """
        Add multiple feature values to the sound.

        The method will remove all conflicting feature values before setting the new
        ones. The method acts as a wrapper to `.set_fvalue()`

        @param fvalues: A list of strings with the feature values to be added to the
            sound, a string with values separated by the standard delimiters.
        @param check: Whether to run constraint checks after adding the new feature
            values (default: True).
        @return: A list of strings with the feature values that were replaced, in no
            particular order.
        """

        # If `fvalues` is empty, just return
        if not fvalues:
            return []

        # If `fvalues` is a string, we assume it is space-separated list of
        # feature values, which can preprocess. Note that this allows to use a
        # string with a single descriptor without any special treatment.
        if isinstance(fvalues, str):
            fvalues = split_fvalues_str(fvalues)

        # Add all fvalues, collecting the replacements which are stripped of `None`s;
        # note that we don't run checks here, but only after all values have been added
        replaced = []
        for fvalue in fvalues:
            rep = self.set_fvalue(fvalue, check=False)
            if rep:
                replaced.append(rep)
            # Mark the sound as partial in all cases of removal
            # TODO: in some cases the sound might not be partial, like removing an aspiration, check this
            if fvalue[0] == "-":
                self.partial = True

        # Run a check if so requested (default)
        if check:
            offending = self.model.fail_constraints(self.fvalues)
            if offending:
                raise ValueError(f"At least one constraint unsatisfied by {offending}")

        return replaced

    def grapheme(self) -> str:
        """
        Return a graphemic representation of the current sound.

        @return: A string withthe graphemic representation of the sound.
        """

        return self.model.build_grapheme(self.fvalues)

    def feature_dict(self) -> dict:
        """
        Return a dictionary of features and feature values that are defined.

        @return: A dictionary of all feature values that are defined for the current
            sound, with features as keys and feature values as values.
        """

        return self.model.feature_dict(self.fvalues)

    def __repr__(self) -> str:
        """
        Return a representation with full name values.

        Following the convention from `PhonoModel`, the list of values is ordered by
        feature value rank first and, in case of feature values with equal ranks,
        alphabetically second.

        @return: A string with a representation of the current sound.
        """

        return " ".join(self.model.sort_fvalues(self.fvalues))

    def __str__(self) -> str:
        """
        Return a graphemic representation of the sound.

        By design, the `str()` command will return the same value of the
        `.grapheme()` method.

        @return: A string with a representation of the current sound.
        """

        return self.grapheme()

    # TODO: decide what to do with `.partial`
    def __add__(self, other):
        """
        Overload the `+` operator.
        """

        # The [:] syntax guarantees we make a copy of self.fvalues if it is a list
        snd = Sound(description=self.fvalues[:], partial=self.partial, model=self.model)
        snd.set_fvalues(other)

        return snd

    # TODO: decide what to do with `.partial`
    def __sub__(self, other):
        """
        Overload the `-` operator.
        """

        fvalues = [
            fvalue for fvalue in self.fvalues if fvalue not in split_fvalues_str(other)
        ]

        return Sound(
            description=" ".join(fvalues), partial=self.partial, model=self.model
        )

    # TODO: decide what to do with `.partial`, as this will interfere also with <= and >=
    def __hash__(self):
        """
        Return a hash of the current sound.
        """

        return hash(self.model.sort_fvalues(self.fvalues))

    # TODO: decide what to do with `.partial`, as this will interfere also with <= and >=
    def __eq__(self, other) -> bool:
        """
        Compare two sounds in terms of their fvalues.
        """

        return hash(self) == hash(other)

    def __lt__(self, other) -> bool:
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

    def __gt__(self, other) -> bool:
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

    def __le__(self, other) -> bool:
        return any([self == other, self < other])

    def __ge__(self, other) -> bool:
        return any([self == other, self > other])

    def __getattr__(self, feature: str) -> Optional[str]:
        """
        Get feature values from their features as object attributes.

        @param feature:
        @return: A string with the feature value for the requested `feature`, or `None`
            if no feature value associated with the requested `feature` has been
            set.
        """

        for fvalue in self.fvalues:
            if self.model.fvalues[fvalue]["feature"] == feature:
                return fvalue

        return None
