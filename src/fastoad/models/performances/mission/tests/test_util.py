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
