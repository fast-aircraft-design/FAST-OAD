"""
Module for dict-related operations
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, TypeVar

_KT = TypeVar("_KT", bound=Any)
_VT = TypeVar("_VT", bound=Any)


class AbstractNormalizedDict(ABC, dict):
    """
    Dictionary where keys are normalized using :meth:`normalize`.

    Example::

        >>> class DictWithLowerCaseKeys(AbstractNormalizedDict):
        >>>     @staticmethod
        >>>     def normalize(key):
        >>>         return key.lower()
    """

    @abstractmethod
    def normalize(self, key):
        """Redefine this function when subclassing to define your key normalization."""
        return key

    def __init__(self, seq=None, **kwargs):
        kwargs = {self.normalize(key): value for key, value in kwargs.items()}
        if seq:
            if isinstance(seq, Mapping):
                seq = {self.normalize(key): value for key, value in seq.items()}
            elif isinstance(seq, Iterable):
                seq = [(self.normalize(key), value) for key, value in seq]
            super().__init__(seq, **kwargs)
        else:
            super().__init__(**kwargs)

    def __getitem__(self, __key: str) -> _VT:
        return super().__getitem__(self.normalize(__key))

    def __setitem__(self, __key: str, __value: _VT) -> None:
        super().__setitem__(self.normalize(__key), __value)

    def __delitem__(self, __key: _KT) -> None:
        super().__delitem__(self.normalize(__key))

    def __contains__(self, __o: object) -> bool:
        return super().__contains__(self.normalize(__o))
