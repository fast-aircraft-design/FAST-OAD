#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from numpy.testing import assert_allclose

from fastoad.model_base import FlightPoint

from ..mass_input import MassTargetSegment


def test_dummy_target_mass():
    dummy_target_mass = MassTargetSegment(target=FlightPoint(mass=70.0e5))

    flight_points = dummy_target_mass.compute_from(
        FlightPoint(altitude=10.0, time=1000.0, mach=0.3, mass=100.0e5)
    )
    assert len(flight_points) == 1
    point = flight_points.iloc[-1]
    assert_allclose(point.altitude, 10.0, atol=1.0)
    assert_allclose(point.time, 1000.0, rtol=1e-2)
    assert_allclose(point.mach, 0.3, atol=0.001)
    assert_allclose(point.mass, 70.0e5, rtol=1e-4)
