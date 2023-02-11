"""
Module for Sound abstraction and operations.
"""

# Import Python standard libraries
from typing import Optional, Sequence, Union

# Import local modules
from .phonomodel import PhonoModel, model_mipa
from .common import parse_fvalues


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

    # TODO: condense `grapheme` and `description` into a single argument
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
            equivalent of "sound _snd_classes") work differently in terms of comparison, and
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
        self.fvalues: frozenset = frozenset()
        self.partial: bool = partial

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

        The method will remove any feature value for the same feature before
        setting the new one. This method works as a convenient wrapper to the equivalent
        method in `PhonoModel`.

        Parameters
        ----------
        fvalue : str
            The feature value to be added to the sound.
        check : bool, optional
            Whether to run constraints check after adding the new feature value
            (default: True).

        Returns
        -------
        Optional[str]
            The previous feature value for the feature, in case it was replaced, or
            None, in case no replacement happened. If the method is called to add a
            feature value which is already set, it will be returned as well
            (indicating that there was already a value for the corresponding feature).
        """

        self.fvalues, prev_fvalue = self.model.set_fvalue(self.fvalues, fvalue, check)

        return prev_fvalue

    def set_fvalues(self, fvalues: Sequence, check: bool = True) -> list:
        """
        Set multiple feature values to the sound.

        The method will remove all conflicting feature values before setting the new
        ones. The method acts as a wrapper to `.set_fvalue()`

        Parameters
        ----------
        fvalues : Sequence
            A list of strings with the feature values to be added to the sound, a
            string with values separated by the standard delimiters.
        check : bool, optional

        Returns
        -------
        list
            An alphabetically sorted list of strings with the feature values that
            were replaced.

        Raises
        ------
        ValueError
            If at least one constraint is unsatisfied by the new feature values.
        """

        # If `fvalues` is empty, just return
        if not fvalues:
            return []

        # Parse `fvalues` as a frozen set
        fvalues = parse_fvalues(fvalues)

        # Add all fvalues, collecting the replacements which are stripped of `None`s;
        # note that we don't run checks at this point, but only after all values have been set
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

        return sorted(replaced)

    def grapheme(self) -> str:
        """
        Return a graphemic representation of the current sound.

        Returns
        -------
        str
            A string with the graphemic representation of the sound.
        """

        return self.model.build_grapheme(self.fvalues)

    def feature_dict(self) -> dict:
        """
        Return a dictionary of features and feature values that are defined.

        Returns
        -------
        dict
            A dictionary of all feature values that are defined for the current
            sound, with features as keys and feature values as values.
        """

        return self.model.feature_dict(self.fvalues)

    def __repr__(self) -> str:
        """
        Return a representation with full name values.

        Following the convention from `PhonoModel`, the list of values is ordered by
        feature value rank first and, in case of feature values with equal ranks,
        alphabetically second.

        Returns
        -------
        str
            A string with a representation of the current sound.
        """

        ret = " ".join(self.model.sort_fvalues(self.fvalues))
        if self.partial:
            ret += " [partial]"

        return ret

    def __str__(self) -> str:
        """
        Return a graphemic representation of the sound.

        By design, the `str()` command will return the same value of the
        `.grapheme()` method.

        Returns
        -------
        str
            A string with a representation of the current sound.
        """

        return self.grapheme()

    # TODO: decide what to do with `.partial`
    def __add__(self, other: str):
        """
        Overload the `+` operator.
        """

        snd = Sound(description=self.fvalues, partial=self.partial, model=self.model)
        snd.set_fvalues(other)

        return snd

    # TODO: decide what to do with `.partial`; right now we are keeping the information it in all cases,
    #       as an aspirated /p/ with aspiration is not a partial sound -- should probably check
    #       the list of sounds in the model. This is complex because setting a value might involve
    #       removing a previous one.
    def __sub__(self, other: str):
        """
        Overload the `-` operator.
        """

        fvalues = [
            fvalue for fvalue in self.fvalues if fvalue not in parse_fvalues(other)
        ]

        return Sound(description=fvalues, partial=self.partial, model=self.model)

    def __hash__(self) -> int:
        """
        Return a hash of the current sound.

        The hash is based on the model, the feature values, and the information on
        whether the sound is partial or not. The hash is used to compare sounds in
        terms of their values and internal information.

        Returns
        -------
        int
            A hash of the current sound.
        """

        # We cannot combine the hash of `self.partial` with a ^ operator as normally done,
        # as it is a boolean and, when false, will held zero. We must resort to the more
        # expansive operation of creating a list that includes the information from
        # `self.partial` and of `self.values`. We do combine the information from the
        # model, however.

        return hash(tuple([self.partial] + list(self.fvalues))) ^ hash(self.model)

    # TODO: decide what to do with `.partial`, as this will interfere also with <= and >=
    def __eq__(self, other) -> bool:
        """
        Compare two sounds in terms of their values and internal information.

        The comparison is based on the model, the feature values, and the information
        on whether the sound is partial or not. The comparison is used to compare
        sounds in terms of their values and internal information.

        Returns
        -------
        bool
            True if the two sounds are equal, False otherwise.
        """

        # If the models are different, the sounds are different
        if hash(self.model) != hash(other.model):
            return False

        # We are not considering `self.partial` if it is None
        # TODO: remove this check once self.partial is properly set from sounds
        if self.partial is None or other.partial is None:
            return self.fvalues == other.fvalues

        return all([self.fvalues == other.fvalues, self.partial == other.partial])

    def __lt__(self, other) -> bool:
        """
        Checks if the fvalues of the current sound are a subset of the other.

        Returns
        -------
        bool
            True if the fvalues of the current sound are a subset of the other,
        """

        # If the models are different, the sounds are different
        if hash(self.model) != hash(other.model):
            return False

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

        Returns
        -------
        bool
            True if the fvalues of the current sound are a superset of the other,
        """

        # If the models are different, the sounds are different
        if hash(self.model) != hash(other.model):
            return False

        this_dict = self.feature_dict()
        for feature, fvalue in other.feature_dict().items():
            if feature not in this_dict:
                return False
            if this_dict[feature] != fvalue:
                return False

        return True

    # TODO: __le__ and __ge__ are using __eq__ which considers self.partial
    def __le__(self, other) -> bool:
        return any([self == other, self < other])

    def __ge__(self, other) -> bool:
        return any([self == other, self > other])

    def __getattr__(self, feature: str) -> Optional[str]:
        """
        Get feature values from their features as object attributes.

        This method allows to get the feature value associated with a feature
        by using the feature as an attribute of the sound object. For example,
        if the sound has a feature value for the feature `place`, the feature
        value can be retrieved by using the following syntax:

        >>> sound.place
        'bilabial'

        Parameters
        ----------
        feature: str
            The name of the feature for which the feature value is requested.

        Returns
        -------
        str
            The feature value associated with the requested feature, or `None`
            if no feature value associated with the requested feature has been
            set.
        """

        for fvalue in self.fvalues:
            if self.model.fvalues[fvalue]["feature"] == feature:
                return fvalue

        return None
