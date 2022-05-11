#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet
from .conftest import DummyEngine
from ..hold import HoldSegment


def test_hold(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 2.0e-5), 2)

    segment = HoldSegment(
        target=FlightPoint(time=3000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=500.0, equivalent_airspeed=250.0, mass=60000.0)
        )

        last_point = flight_points.iloc[-1]
        assert_allclose(last_point.time, 3000.0)
        assert_allclose(last_point.altitude, 500.0)
        assert_allclose(last_point.equivalent_airspeed, 250.0, atol=0.1)
        assert_allclose(last_point.mass, 57776.0, rtol=1e-4)
        if segment.isa_offset == 0.0:
            assert_allclose(last_point.true_airspeed, 256.1, atol=0.1)
            assert_allclose(last_point.ground_distance, 768323.0, rtol=1.0e-3)
        if segment.isa_offset == 15.0:
            assert_allclose(last_point.true_airspeed, 262.8, atol=0.1)
            assert_allclose(last_point.ground_distance, 788289.0, rtol=1.0e-3)
        assert last_point.engine_setting == EngineSetting.CRUISE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()

    # Test with non-zero dISA
    segment.isa_offset = 15.0
    run()
