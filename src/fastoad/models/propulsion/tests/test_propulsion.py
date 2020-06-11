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

from typing import Union, Sequence, Optional, Tuple

import numpy as np
from fastoad.constants import FlightPhase
from numpy.testing import assert_allclose

from ..propulsion import EngineSet
from ..propulsion import IPropulsion


class DummyEngine(IPropulsion):
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

    def compute_flight_points(
        self,
        mach: Union[float, Sequence],
        altitude: Union[float, Sequence],
        phase: Union[FlightPhase, Sequence],
        use_thrust_rate: Optional[Union[bool, Sequence]] = None,
        thrust_rate: Optional[Union[float, Sequence]] = None,
        thrust: Optional[Union[float, Sequence]] = None,
    ) -> Tuple[Union[float, Sequence], Union[float, Sequence], Union[float, Sequence]]:

        if use_thrust_rate or thrust is None:
            thrust = self.max_thrust * thrust_rate
        else:
            thrust_rate = thrust / self.max_thrust

        sfc = self.max_sfc * thrust_rate

        return sfc, thrust_rate, thrust


def test_EngineSet():
    """Tests behaviour of EngineSet"""
    engine = DummyEngine(1.2e5, 1.0e-5)

    # input = thrust rate
    thrust_rate = np.linspace(0.0, 1.0, 20)
    for engine_count in [1, 2, 3, 4]:
        engine_set = EngineSet(engine, engine_count)
        sfc, _, thrust = engine_set.compute_flight_points(0.0, 0.0, 1, thrust_rate=thrust_rate)
        assert_allclose(sfc, engine.max_sfc * thrust_rate)
        assert_allclose(thrust, engine.max_thrust * engine_count * thrust_rate)

    # input = thrust
    thrust = np.linspace(0.0, engine.max_thrust, 30)
    for engine_count in [1, 2, 3, 4]:
        engine_set = EngineSet(engine, engine_count)
        sfc, thrust_rate, _ = engine_set.compute_flight_points(0.0, 0.0, 1, thrust=thrust)
        assert_allclose(thrust_rate, thrust / engine_count / engine.max_thrust)
        assert_allclose(sfc, engine.max_sfc * thrust_rate)
