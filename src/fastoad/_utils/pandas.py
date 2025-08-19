"""
Module for pandas-related operations
"""

from typing import Callable, Optional

import pandas as pd
from packaging.version import Version

# DataFrame.applymap() is deprecated since pandas 2.1.0, in favor of DataFrame.map()
# We get the correct one here once and for all.
if Version(pd.__version__) >= Version("2.1"):
    MAP_METHOD = pd.DataFrame.map
else:
    MAP_METHOD = pd.DataFrame.applymap


# TODO: remove me when pandas <2.1 is no longer used.
def apply_map(
    dataframe: pd.DataFrame, func: Callable, na_action: Optional[str] = None, **kwargs
) -> pd.DataFrame:
    """
    Convenience function for using DataFrame.applymap or DataFrame.map
    according to pandas version.
    """
    return MAP_METHOD(dataframe, func, na_action, **kwargs)
