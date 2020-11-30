#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

import pytest
from scipy.constants import foot

from fastoad.models.performances.mission.util import get_closest_flight_level


def test_get_closest_flight_level():
    # Getting the flight level immediately above
    assert get_closest_flight_level(4400.0 * foot) == pytest.approx(5000.0 * foot)

    # Getting the flight level immediately below
    assert get_closest_flight_level(4400.0 * foot, up_direction=False) == pytest.approx(
        4000.0 * foot
    )

    # Getting the next even flight level
    assert get_closest_flight_level(4400.0 * foot, level_step=20) == pytest.approx(6000.0 * foot)

    # Getting the next odd flight level
    assert get_closest_flight_level(3100.0 * foot, base_level=10, level_step=20) == pytest.approx(
        5000.0 * foot
    )

    # Returns the same altitude if already a flight level
    assert get_closest_flight_level(6000.0 * foot) == pytest.approx(6000.0 * foot)
    assert get_closest_flight_level(6000.0 * foot, up_direction=False) == pytest.approx(
        6000.0 * foot
    )
