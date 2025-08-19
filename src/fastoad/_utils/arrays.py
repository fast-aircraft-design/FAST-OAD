"""
Module for array-related operations
"""

from typing import Any

import numpy as np


def scalarize(value: Any):
    """
    :param value:
    :return: the scalar value inside input array if it is a one-element array/sequence.
             Returns `value` itself otherwise
    """
    try:
        return np.asarray(value).item()
    except ValueError:
        return value
