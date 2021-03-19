#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from ..flight_point import FlightPoint


def test_add_remove_field():

    # Without add_field(), an unknown field will raise errors
    fp1 = FlightPoint(time=100.0, mass=70000.0)
    with pytest.raises(AttributeError):
        fp1.foo
    with pytest.raises(TypeError):
        fp2 = FlightPoint(time=100.0, mass=70000.0, foo=42)

    # After add_field(), no problem
    FlightPoint.add_field("foo", annotation_type=int, default_value=5)
    fp1 = FlightPoint(time=100.0, mass=70000.0)
    fp1.foo
    fp2 = FlightPoint(time=100.0, mass=70000.0, foo=42)

    # After remove_field(), back to initial state, an unknown field will raise errors
    FlightPoint.remove_field("foo")
    fp1 = FlightPoint(time=100.0, mass=70000.0)
    with pytest.raises(AttributeError):
        fp1.foo
    with pytest.raises(TypeError):
        fp2 = FlightPoint(time=100.0, mass=70000.0, foo=42)


def test_create():
    df = pd.DataFrame(dict(time=[0.0, 1.0, 2.0], mach=[0.0, 0.02, 0.05]))

    flight_point = FlightPoint.create(df.iloc[1])
    assert flight_point.time == 1.0
    assert flight_point.mach == 0.02


def test_create_list():
    df = pd.DataFrame(dict(time=[0.0, 1.0, 2.0], mach=[0.0, 0.02, 0.05]))

    flight_points = FlightPoint.create_list(df)
    assert flight_points[0].time == 0.0
    assert flight_points[0].mach == 0.0
    assert flight_points[1].time == 1.0
    assert flight_points[1].mach == 0.02
    assert flight_points[2].time == 2.0
    assert flight_points[2].mach == 0.05


def test_scalarize():
    fp = FlightPoint(time=[100.0], mass=np.array([70000.0]), altitude=(1000.0,), mach=[0.7, 0.8])

    assert isinstance(fp.time, list)
    assert isinstance(fp.mass, np.ndarray)
    assert isinstance(fp.altitude, tuple)
    assert isinstance(fp.mach, list)

    fp.scalarize()
    assert isinstance(fp.time, float)
    assert isinstance(fp.mass, float)
    assert isinstance(fp.altitude, float)
    assert isinstance(fp.mach, list)

    assert fp.time == 100.0
    assert fp.mass == 70000.0
    assert fp.altitude == 1000.0
    assert_allclose(fp.mach, [0.7, 0.8])
