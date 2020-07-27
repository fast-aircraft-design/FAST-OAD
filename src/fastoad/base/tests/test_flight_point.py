#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from fastoad.exceptions import FastUnexpectedKeywordArgument
from ..flight_point import FlightPoint


def test_FlightPoint():

    # Init with kwargs, with one attribute initialized #############################################
    fp1 = FlightPoint(mass=50000.0)
    assert fp1.mass == 50000.0
    assert fp1.mass == fp1["mass"]
    fp1.mass = 70000.0
    assert fp1["mass"] == 70000.0

    # Non initialized but known attributes are initialized to None
    for label in FlightPoint.get_attribute_keys():
        if label != "mass":
            assert getattr(fp1, label) is None

    # Init with dictionary, with all attributes initialized ########################################
    test_values = {
        key: value
        for key, value in zip(
            FlightPoint.get_attribute_keys(), range(len(FlightPoint.get_attribute_keys()))
        )
    }
    fp2 = FlightPoint(test_values)
    for label in FlightPoint.get_attribute_keys():
        assert getattr(fp2, label) == test_values[label]
        assert getattr(fp2, label) == fp2[label]
        new_value = test_values[label] * 100
        setattr(fp2, label, new_value)
        assert fp2[label] == new_value

    # Init with unknown attribute ##################################################################
    with pytest.raises(FastUnexpectedKeywordArgument):
        _ = FlightPoint(unknown=0)

    # Unknown dictionary keys are allowed, though
    _ = FlightPoint({"unknown": 0})

    # FlightPoint to/from pandas DataFrame #########################################################
    assert fp1 == FlightPoint(pd.DataFrame([fp1]).iloc[0])

    df = pd.DataFrame([fp1, fp2])
    for label in FlightPoint.get_attribute_keys():
        assert_allclose(df[label], [fp1.get(label, np.nan), fp2.get(label, np.nan)])

    fp2bis = FlightPoint(df.iloc[-1])
    assert fp2 == fp2bis

    fp1bis = FlightPoint(df.iloc[0])
    assert fp1 == fp1bis
