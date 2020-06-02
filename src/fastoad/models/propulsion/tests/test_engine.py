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

    expected_shape = (
        EngineTable.MACH_STEP_COUNT + 1,
        EngineTable.ALTITUDE_STEP_COUNT + 1,
        EngineTable.THRUST_RATE_STEP_COUNT + 1,
        len(EngineTable.FLIGHT_PHASES),
    )
    assert problem["private:propulsion:table:mach"].shape == (expected_shape[0],)
    assert problem["private:propulsion:table:altitude"].shape == (expected_shape[1],)
    assert problem["private:propulsion:table:thrust_rate"].shape == (expected_shape[2],)
    assert problem["private:propulsion:table:flight_phase"].shape == (expected_shape[3],)
    assert problem["private:propulsion:table:SFC"].shape == expected_shape
    assert problem["private:propulsion:table:thrust"].shape == expected_shape

    # Simple iterative check. Some elements are skipped for speeding up the test.
    for i in range(0, expected_shape[0], 5):
        for j in range(0, expected_shape[1], 5):
            for k in range(0, expected_shape[2], 2):
                for l in range(expected_shape[3]):
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


def test_EngineTable_RubberEngine_interpolate_from_thrust_rate():

    engine = RubberEngine(5, 30, 1500, 1e5, 0.95, 10000)

    class RubberEngineTable(EngineTable):
        @staticmethod
        def get_engine(inputs) -> IEngine:
            return engine

    table = RubberEngineTable()
    problem = run_system(table, None)

    machs = np.array([0, 0.3, 0.3, 0.8, 0.8])
    altitudes = [0, 0, 0, 10000, 13000]
    thrust_rates = [0.8, 0.5, 0.5, 0.4, 0.7]
    phases = [
        FlightPhase.TAKEOFF,
        FlightPhase.TAKEOFF,
        FlightPhase.CLIMB,
        FlightPhase.IDLE,
        FlightPhase.CRUISE,
    ]

    # Let's compare the interpolation to a direct call to the RubberEngine instance
    ref_sfc, _, ref_thrust = engine.compute_flight_points(
        machs, altitudes, phases, thrust_rate=thrust_rates
    )

    sfc, thrust = EngineTable.interpolate_from_thrust_rate(
        problem, machs, altitudes, thrust_rates, phases
    )

    assert_allclose(
        sfc, ref_sfc, rtol=1e-3,
    )
    assert_allclose(
        thrust, ref_thrust, rtol=1e-3,
    )


def test_EngineTable_RubberEngine_interpolate_from_thrust():

    engine = RubberEngine(5, 30, 1500, 1e5, 0.95, 10000)

    class RubberEngineTable(EngineTable):
        @staticmethod
        def get_engine(inputs) -> IEngine:
            return engine

    table = RubberEngineTable()
    problem = run_system(table, None)

    machs = np.array([0, 0.3, 0.3, 0.8, 0.8])
    altitudes = [0, 0, 0, 10000, 13000]
    thrusts = [9553 * 0.8, 38851, 35677, 9680, 11273]
    phases = [
        FlightPhase.TAKEOFF,
        FlightPhase.TAKEOFF,
        FlightPhase.CLIMB,
        FlightPhase.IDLE,
        FlightPhase.CRUISE,
    ]

    # Let's compare the interpolation to a direct call to the RubberEngine instance
    ref_sfc, ref_thrust_rate, _ = engine.compute_flight_points(
        machs, altitudes, phases, thrust=thrusts
    )

    sfc, thrust_rate = EngineTable.interpolate_from_thrust(
        problem, machs, altitudes, thrusts, phases
    )

    assert_allclose(
        sfc, ref_sfc, rtol=1e-3,
    )
    assert_allclose(
        thrust_rate, ref_thrust_rate, rtol=1e-3,
    )
