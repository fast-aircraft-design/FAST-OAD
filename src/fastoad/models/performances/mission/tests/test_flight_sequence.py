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

import pytest
from numpy.testing import assert_allclose

from fastoad.model_base import FlightPoint

from ..base import FlightSequence
from ..segments.registered.mass_input import MassTargetSegment
from ..segments.registered.taxi import TaxiSegment


def get_taxi_definition(propulsion, target_mass=None):
    return TaxiSegment(
        "taxi_out",
        target=FlightPoint(time=100.0, mass=target_mass),
        thrust_rate=0.3,
        propulsion=propulsion,
    )


@pytest.fixture(scope="module")
def taxi_consumption(propulsion):
    masses = (
        get_taxi_definition(propulsion).compute_from(FlightPoint(altitude=0.0, mass=100000.0)).mass
    )
    return masses.iloc[0] - masses.iloc[-1]


def get_sequence_without_target_mass(propulsion):
    return FlightSequence() + [get_taxi_definition(propulsion), get_taxi_definition(propulsion)]


def get_sequence_with_target_mass(propulsion):
    return FlightSequence() + [
        get_taxi_definition(propulsion),
        get_taxi_definition(propulsion),
        MassTargetSegment(target=FlightPoint(mass=70000.0)),
    ]


def get_nested_flight_sequence_without_target_mass(propulsion):
    return FlightSequence() + [
        get_taxi_definition(propulsion),
        FlightSequence() + get_sequence_without_target_mass(propulsion),
        FlightSequence() + get_sequence_without_target_mass(propulsion),
    ]


def get_nested_flight_sequence_with_target_mass(propulsion):
    return FlightSequence() + [
        get_taxi_definition(propulsion),
        FlightSequence() + get_sequence_with_target_mass(propulsion),
        FlightSequence() + get_sequence_without_target_mass(propulsion),
    ]


def test_flight_sequence_without_target_mass(propulsion, taxi_consumption):
    sequence = get_sequence_without_target_mass(propulsion)
    flight_points = sequence.compute_from(FlightPoint(altitude=0.0, mass=50000.0))

    assert_allclose(flight_points.mass.iloc[0] - flight_points.mass.iloc[-1], taxi_consumption * 2)
    assert_allclose(flight_points.mass.iloc[-1], 50000.0 - taxi_consumption * 2)
    assert_allclose(sequence.consumed_mass_before_input_weight, 0.0)


def test_flight_sequence_with_target_mass(propulsion, taxi_consumption):
    sequence = FlightSequence()
    sequence.extend(get_sequence_with_target_mass(propulsion))
    flight_points = sequence.compute_from(FlightPoint(altitude=0.0, mass=50000.0))

    assert_allclose(flight_points.mass.iloc[0] - flight_points.mass.iloc[-1], taxi_consumption * 2)
    assert_allclose(flight_points.mass.iloc[-1], 70000.0)
    assert_allclose(sequence.consumed_mass_before_input_weight, taxi_consumption * 2)


def test_nested_flight_sequence_without_target_mass(propulsion, taxi_consumption):
    sequence = get_nested_flight_sequence_without_target_mass(propulsion)
    flight_points = sequence.compute_from(FlightPoint(altitude=0.0, mass=50000.0))

    assert_allclose(flight_points.mass.iloc[0] - flight_points.mass.iloc[-1], taxi_consumption * 5)
    assert_allclose(flight_points.mass.iloc[-1], 50000.0 - taxi_consumption * 5)
    assert_allclose(sequence.consumed_mass_before_input_weight, 0.0)


def test_nested_flight_sequence_with_target_mass(propulsion, taxi_consumption):
    sequence = FlightSequence()
    sequence.extend(get_nested_flight_sequence_with_target_mass(propulsion))
    flight_points = sequence.compute_from(FlightPoint(altitude=0.0, mass=50000.0))

    assert_allclose(flight_points.mass.iloc[0] - flight_points.mass.iloc[-1], taxi_consumption * 5)
    assert_allclose(flight_points.mass.iloc[-1], 70000.0 - taxi_consumption * 2)
    assert_allclose(sequence.consumed_mass_before_input_weight, taxi_consumption * 3)
