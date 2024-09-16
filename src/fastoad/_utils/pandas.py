#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Callable, Optional

import pandas as pd
from packaging.version import Version

if Version(pd.__version__) >= Version("2.1"):
    map_method = pd.DataFrame.map
else:
    map_method = pd.DataFrame.applymap


# TODO: remove me when pandas <2.1 is no longer used.
def apply_map(
    df: pd.DataFrame, func: Callable, na_action: Optional[str] = None, **kwargs
) -> pd.DataFrame:
    """
    Convenience function for using DataFrame.applymap or DataFrame.map
    according to pandas version.
    """
    return map_method(df, func, na_action, **kwargs)