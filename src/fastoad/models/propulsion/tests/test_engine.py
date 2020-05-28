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
from fastoad.models.propulsion.engine import EngineTable

from tests.testing_utilities import run_system
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
