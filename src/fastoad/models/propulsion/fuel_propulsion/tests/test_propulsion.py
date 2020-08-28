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

from typing import Union

import numpy as np
import pandas as pd
from numpy.testing import assert_allclose

from fastoad.base.flight_point import FlightPoint
from ..base import AbstractFuelPropulsion, FuelEngineSet


class DummyEngine(AbstractFuelPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC is proportional to thrust rate.

        :param max_thrust: thrust when thrust rate = 1.0
        :param max_sfc: SFC when thrust rate = 1.0
        """
        self.max_thrust = max_thrust
        self.max_sfc = max_sfc

    def compute_flight_points(self, flight_points: Union[FlightPoint, pd.DataFrame]):
        if flight_points.thrust_is_regulated or flight_points.thrust is None:
            flight_points.thrust = self.max_thrust * flight_points.thrust_rate
        else:
            flight_points.thrust_rate = flight_points.thrust / self.max_thrust

        flight_points.sfc = self.max_sfc * flight_points.thrust_rate


def test_EngineSet():
    """Tests behaviour of FuelEngineSet"""
    engine = DummyEngine(1.2e5, 1.0e-5)

    # input = thrust rate
    thrust_rate = np.linspace(0.0, 1.0, 20)
    for engine_count in [1, 2, 3, 4]:
        engine_set = FuelEngineSet(engine, engine_count)
        flight_point = FlightPoint(
            mach=0.0, altitude=0.0, engine_setting=1, thrust_rate=thrust_rate
        )
        engine_set.compute_flight_points(flight_point)
        assert_allclose(flight_point.sfc, engine.max_sfc * thrust_rate)
        assert_allclose(flight_point.thrust, engine.max_thrust * engine_count * thrust_rate)

    # input = thrust
    thrust = np.linspace(0.0, engine.max_thrust, 30)
    for engine_count in [1, 2, 3, 4]:
        engine_set = FuelEngineSet(engine, engine_count)
        flight_point = FlightPoint(mach=0.0, altitude=0.0, engine_setting=1, thrust=thrust)
        engine_set.compute_flight_points(flight_point)
        assert_allclose(flight_point.thrust_rate, thrust / engine_count / engine.max_thrust)
        assert_allclose(flight_point.sfc, engine.max_sfc * flight_point.thrust_rate)
