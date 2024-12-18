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

from ..start import Start


def test_start():
    start_point = FlightPoint(time=500.0, mass=500, altitude=10)
    segment = Start(target=start_point)

    def run1():
        flight_points = segment.compute_from(FlightPoint())
        assert len(flight_points) == 1
        assert flight_points.time[0] == 500.0
        assert flight_points.mass[0] == 500.0
        assert flight_points.altitude[0] == 10.0
        assert flight_points.true_airspeed[0] == 0.0
        assert flight_points.mach[0] == 0.0

    run1()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run1()

    start_point = FlightPoint(altitude=0, true_airspeed=100.0, mass=0.0)
    segment = Start(target=start_point)

    def run2():
        flight_points = segment.compute_from(FlightPoint(mass=1e9))
        assert len(flight_points) == 1
        assert flight_points.time[0] == 0.0
        assert flight_points.mass[0] == 0.0
        assert flight_points.altitude[0] == 0.0
        assert flight_points.true_airspeed[0] == 100.0
        assert_allclose(flight_points.mach, 0.29386, rtol=1e-4)

    run2()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run2()
