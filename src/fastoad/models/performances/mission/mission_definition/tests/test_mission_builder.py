#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

import os.path as pth
from unittest.mock import Mock

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.segments.altitude_change import AltitudeChangeSegment
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.speed_change import SpeedChangeSegment
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from ..mission_builder import MissionBuilder
from ..schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_inputs():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"), Mock(IPropulsion), 100.0
    )
    input_definition = {}
    mission_builder.identify_inputs(input_definition)
    assert input_definition == {
        "data:TLAR:cruise_mach": None,
        "data:TLAR:range": "m",
        "data:aerodynamics:aircraft:cruise:CD": None,
        "data:aerodynamics:aircraft:cruise:CL": None,
        "data:aerodynamics:aircraft:takeoff:CD": None,
        "data:aerodynamics:aircraft:takeoff:CL": None,
        "data:mission:sizing:climb:thrust_rate": None,
        "data:mission:sizing:descent:thrust_rate": None,
        "data:mission:sizing:diversion:distance": "m",
        "data:mission:sizing:holding:duration": "s",
        "data:mission:sizing:taxi_in:duration": "s",
        "data:mission:sizing:taxi_in:thrust_rate": None,
    }


def test_build():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(mission_definition, Mock(IPropulsion), 100.0)

    cl = np.linspace(0.0, 1.0, 11)
    cd = 0.5 * cl ** 2

    inputs = {
        "data:TLAR:cruise_mach": 0.78,
        "data:TLAR:range": 8.0e6,
        "initial_climb:final_altitude": 500,
        "initial_climb:final_equivalent_airspeed": 130.0,
        "data:aerodynamics:aircraft:cruise:CD": cd,
        "data:aerodynamics:aircraft:cruise:CL": cl,
        "data:aerodynamics:aircraft:low_speed:CD": cd,
        "data:aerodynamics:aircraft:low_speed:CL": cl,
        "data:aerodynamics:aircraft:takeoff:CD": cd,
        "data:aerodynamics:aircraft:takeoff:CL": cl,
        "data:mission:sizing:climb:thrust_rate": 0.9,
        "data:mission:sizing:descent:thrust_rate": 0.5,
        "data:mission:sizing:diversion:distance": 1.0e6,
        "data:mission:sizing:holding:duration": 2000.0,
        "data:mission:sizing:taxi_in:duration": 300.0,
        "data:mission:sizing:taxi_in:thrust_rate": 0.5,
    }
    mission = mission_builder.build(inputs)

    assert len(mission.flight_sequence) == 4
    assert mission.flight_sequence[0].name == "sizing:main"
    assert mission.flight_sequence[1].name == "sizing:diversion"
    assert mission.flight_sequence[2].name == "sizing:holding"
    assert mission.flight_sequence[3].name == "sizing:taxi_in"

    main_route = mission.flight_sequence[0]
    assert isinstance(main_route, FlightSequence)
    assert len(main_route.flight_sequence) == 4
    assert main_route.flight_sequence[0].name == "sizing:main:initial_climb"
    assert main_route.flight_sequence[1].name == "sizing:main:climb"
    assert main_route.flight_sequence[2].name == "sizing:main:cruise"
    assert main_route.flight_sequence[3].name == "sizing:main:descent"

    initial_climb = main_route.flight_sequence[0]
    assert isinstance(initial_climb, FlightSequence)
    assert len(initial_climb.flight_sequence) == 3

    climb1 = initial_climb.flight_sequence[0]
    assert isinstance(climb1, AltitudeChangeSegment)
    assert climb1.target.altitude == pytest.approx(400 * foot)
    assert climb1.target.equivalent_airspeed == "constant"
    assert_allclose(climb1.polar.definition_cl, [0.0, 0.5, 1.0])
    assert_allclose(climb1.polar.cd(), [0.0, 0.03, 0.12])

    acceleration = initial_climb.flight_sequence[1]
    assert isinstance(acceleration, SpeedChangeSegment)
    assert acceleration.target.equivalent_airspeed == pytest.approx(250 * knot)
    assert_allclose(acceleration.polar.definition_cl, cl)
    assert_allclose(acceleration.polar.cd(), cd)

    climb2 = initial_climb.flight_sequence[2]
    assert isinstance(climb2, AltitudeChangeSegment)
    assert_allclose(climb2.polar.definition_cl, cl)
    assert_allclose(climb2.polar.cd(), cd)

    holding_phase = mission.flight_sequence[2]
    assert isinstance(holding_phase, FlightSequence)
    assert len(holding_phase.flight_sequence) == 1
    holding = holding_phase.flight_sequence[0]
    assert isinstance(holding, HoldSegment)

    taxi_in_phase = mission.flight_sequence[3]
    assert isinstance(taxi_in_phase, FlightSequence)
    assert len(taxi_in_phase.flight_sequence) == 1
    taxi_in = taxi_in_phase.flight_sequence[0]
    assert isinstance(taxi_in, TaxiSegment)
