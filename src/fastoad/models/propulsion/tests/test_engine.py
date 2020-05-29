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
from fastoad.models.propulsion.fuel_engine.rubber_engine import RubberEngine
from numpy.testing import assert_allclose

from tests.testing_utilities import run_system
from ..engine import EngineTable
from ..engine import IEngine


class DummyEngine(IEngine):
    def compute_flight_points(
        self,
        mach: Union[float, Sequence],
        altitude: Union[float, Sequence],
        phase: Union[FlightPhase, Sequence],
        use_thrust_rate: Optional[Union[bool, Sequence]] = None,
        thrust_rate: Optional[Union[float, Sequence]] = None,
        thrust: Optional[Union[float, Sequence]] = None,
    ) -> Tuple[Union[float, Sequence], Union[float, Sequence], Union[float, Sequence]]:

        sfc = altitude + mach
        thrust = phase.astype(np.float) + thrust_rate

        return sfc, 0.0, thrust


def test_EngineTable_DummyEngine():
    class DummyTable(EngineTable):
        @staticmethod
        def get_engine(inputs) -> IEngine:
            return DummyEngine()

    table = DummyTable()
    problem = run_system(table, None)

    assert problem["private:propulsion:table:mach"].shape == (101,)
    assert problem["private:propulsion:table:altitude"].shape == (101,)
    assert problem["private:propulsion:table:thrust_rate"].shape == (21,)
    assert problem["private:propulsion:table:flight_phase"].shape == (4,)
    assert problem["private:propulsion:table:SFC"].shape == (101, 101, 21, 4)
    assert problem["private:propulsion:table:thrust"].shape == (101, 101, 21, 4)

    # now with custom table shape
    nb_mach_step = 20
    nb_altitude_step = 15
    nb_thrust_rate_step = 42
    flight_phases = [FlightPhase.CRUISE, FlightPhase.CLIMB]
    min_mach, max_mach = 0.2, 0.8
    min_altitude, max_altitude = 1000.0, 10000.0
    min_thrust_rate, max_thrust_rate = 0.3, 0.9

    table = DummyTable(
        mach_step_count=nb_mach_step,
        altitude_step_count=nb_altitude_step,
        thrust_rate_step_count=nb_thrust_rate_step,
        flight_phases=flight_phases,
        mach_min=min_mach,
        mach_max=max_mach,
        altitude_min=min_altitude,
        altitude_max=max_altitude,
        thrust_rate_min=min_thrust_rate,
        thrust_rate_max=max_thrust_rate,
    )
    problem = run_system(table, None)

    assert problem["private:propulsion:table:mach"].shape == (nb_mach_step + 1,)
    assert problem["private:propulsion:table:altitude"].shape == (nb_altitude_step + 1,)
    assert problem["private:propulsion:table:thrust_rate"].shape == (nb_thrust_rate_step + 1,)
    assert problem["private:propulsion:table:flight_phase"].shape == (2,)
    assert problem["private:propulsion:table:SFC"].shape == (
        nb_mach_step + 1,
        nb_altitude_step + 1,
        nb_thrust_rate_step + 1,
        2,
    )
    assert problem["private:propulsion:table:thrust"].shape == (
        nb_mach_step + 1,
        nb_altitude_step + 1,
        nb_thrust_rate_step + 1,
        2,
    )

    for i in range(nb_mach_step + 1):
        for j in range(nb_altitude_step + 1):
            for k in range(nb_thrust_rate_step + 1):
                for l in range(2):
                    assert (
                        problem["private:propulsion:table:SFC"][i, j, k, l]
                        == problem["private:propulsion:table:altitude"][j]
                        + problem["private:propulsion:table:mach"][i]
                    )
                    assert (
                        problem["private:propulsion:table:thrust"][i, j, k, l]
                        == problem["private:propulsion:table:flight_phase"][l]
                        + problem["private:propulsion:table:thrust_rate"][k]
                    )


def test_EngineTable_RubberEngine_interpolate():
    class RubberEngineTable(EngineTable):
        @staticmethod
        def get_engine(inputs) -> IEngine:
            return RubberEngine(5, 30, 1500, 1e5, 0.95, 10000)

    table = RubberEngineTable()
    problem = run_system(table, None)

    flight_points = [
        [0, 0, 0.8, FlightPhase.TAKEOFF],
        [0.3, 0, 0.5, FlightPhase.TAKEOFF],
        [0.3, 0, 0.5, FlightPhase.CLIMB],
        [0.8, 10000, 0.4, FlightPhase.IDLE],
        [0.8, 13000, 0.7, FlightPhase.CRUISE],
    ]

    assert_allclose(
        EngineTable.interpolate_SFC(problem, flight_points),
        [0.99210e-5, 1.3496e-5, 1.3496e-5, 1.8386e-5, 1.5957e-5],
        rtol=1e-3,
    )
    assert_allclose(
        EngineTable.interpolate_thrust(problem, flight_points),
        [95530 * 0.8, 38851, 35677, 9680, 11273],
        rtol=1e-3,
    )
