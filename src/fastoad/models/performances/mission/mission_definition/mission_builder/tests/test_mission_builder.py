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

import os.path as pth
from collections import OrderedDict
from dataclasses import dataclass
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.segments.altitude_change import AltitudeChangeSegment
from fastoad.models.performances.mission.segments.base import (
    AbstractFlightSegment,
    RegisteredSegment,
)
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.mass_input import MassTargetSegment
from fastoad.models.performances.mission.segments.speed_change import SpeedChangeSegment
from fastoad.models.performances.mission.segments.start import Start
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from fastoad.models.performances.mission.segments.transition import DummyTransitionSegment
from fastoad.openmdao.variables import Variable
from ..input_definition import InputDefinition
from ..mission_builder import MissionBuilder
from ...exceptions import FastMissionFileMissingMissionNameError
from ...schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


# For this class, we purposely use the deprecated inheritance mechanism
@dataclass
class TestSegment(AbstractFlightSegment, RegisteredSegment, mission_file_keyword="test_segment_B"):
    scalar_parameter: float = MANDATORY_FIELD
    vector_parameter_1: np.ndarray = MANDATORY_FIELD
    vector_parameter_2: np.ndarray = MANDATORY_FIELD
    vector_parameter_3: np.ndarray = MANDATORY_FIELD
    vector_parameter_4: np.ndarray = MANDATORY_FIELD

    def compute_from_start_to_target(self, start, target) -> pd.DataFrame:
        return pd.DataFrame([start])


def test_input_definition_units():
    inp1 = InputDefinition("anything", 1.0, input_unit="km", prefix="data:mission")
    assert inp1.value == 1.0

    inp1.output_unit = "m"
    assert inp1.value == 1000.0

    # When parameter name is known, its default unit is automatically set.
    inp2 = InputDefinition("ground_distance", 1.0, input_unit="km", prefix="data:mission")
    assert inp2.value == 1000.0
    assert not inp2.is_relative

    inp3 = InputDefinition("delta_time", 1.0, input_unit="h", prefix="data:mission")
    assert inp3.parameter_name == "time"
    assert inp3.is_relative

    assert inp3.value == 3600.0


def test_initialization():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    assert (
        mission_builder._structure_builders["sizing"].structure
        == _get_expected_structure()["sizing"]
    )
    assert (
        mission_builder._structure_builders["operational"].structure
        == _get_expected_structure()["operational"]
    )
    assert (
        mission_builder._structure_builders["fuel_as_objective"].structure
        == _get_expected_structure()["fuel_as_objective"]
    )
    assert (
        mission_builder._structure_builders["test"].structure == _get_expected_structure()["test"]
    )


def test_get_input_weight_variable_name():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )
    assert (
        mission_builder.get_input_weight_variable_name("operational")
        == "data:mission:operational:taxi_out:TOW"
    )

    # No mass input defined in "sizing", so it is completed by the default taxi_out & takeoff phase
    assert mission_builder.get_input_weight_variable_name("sizing") == "data:mission:sizing:TOW"


def test_inputs():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )
    with pytest.raises(FastMissionFileMissingMissionNameError):
        mission_builder.get_input_variables()

    assert sorted(mission_builder.get_input_variables("sizing"), key=lambda v: v.name) == sorted(
        [
            Variable("data:mission:sizing:taxi_out:altitude", val=0.0, units="ft"),
            Variable("data:mission:sizing:taxi_out:true_airspeed", val=0.0, units="m/s"),
            Variable("data:mission:sizing:taxi_out:duration", val=np.nan, units="s"),
            Variable("settings:mission:sizing:taxi_out:time_step", val=60.0, units="s"),
            Variable("data:mission:sizing:taxi_out:thrust_rate", val=np.nan),
            Variable("data:mission:sizing:takeoff:safety_altitude", val=35.0, units="ft"),
            Variable("data:mission:sizing:takeoff:fuel", val=np.nan, units="kg"),
            Variable("data:mission:sizing:takeoff:duration", val=0.0, units="s"),
            Variable("data:mission:sizing:takeoff:V2", val=np.nan, units="m/s"),
            Variable("data:mission:sizing:TOW", val=np.nan, units="kg"),
            Variable("data:TLAR:cruise_mach", val=np.nan),
            Variable("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape_by_conn=True),
            Variable("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape_by_conn=True),
            Variable("data:aerodynamics:aircraft:takeoff:CD", val=np.nan, shape_by_conn=True),
            Variable("data:aerodynamics:aircraft:takeoff:CL", val=np.nan, shape_by_conn=True),
            Variable("data:mission:sizing:diversion:descent:final_altitude", val=np.nan, units="m"),
            Variable("data:mission:sizing:diversion:range", val=np.nan, units="m"),
            Variable("data:mission:sizing:holding:duration", val=np.nan, units="s"),
            Variable("data:mission:sizing:main:descent:final_altitude", val=np.nan, units="m"),
            Variable("data:mission:sizing:main:range", val=np.nan, units="m"),
            Variable("data:mission:sizing:taxi_in:duration", val=np.nan, units="s"),
            Variable("data:mission:sizing:taxi_in:thrust_rate", val=np.nan),
            Variable("data:propulsion:initial_climb:thrust_rate", val=1.0),
            Variable("data:propulsion:climb:thrust_rate", val=np.nan),
            Variable("data:propulsion:descent:thrust_rate", val=np.nan),
            Variable("data:mission:sizing:main:climb:time_step", val=np.nan, units="s"),
            Variable("settings:mission:sizing:main:initial_climb:time_step", val=np.nan, units="s"),
            Variable(
                "settings:mission:sizing:diversion:diversion_climb:t_step", val=np.nan, units="s"
            ),
        ],
        key=lambda v: v.name,
    )

    assert set(mission_builder.get_input_variables("operational")) == {
        Variable("data:TLAR:cruise_mach", val=np.nan),
        Variable("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape_by_conn=True),
        Variable("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape_by_conn=True),
        Variable("data:aerodynamics:aircraft:takeoff:CD", val=np.nan, shape_by_conn=True),
        Variable("data:aerodynamics:aircraft:takeoff:CL", val=np.nan, shape_by_conn=True),
        Variable("data:mission:operational:main:descent:final_altitude", val=np.nan, units="m"),
        Variable("data:mission:operational:main:range", val=np.nan, units="m"),
        Variable("data:mission:operational:taxi_in:duration", val=np.nan, units="s"),
        Variable("data:mission:operational:taxi_in:thrust_rate", val=np.nan),
        Variable("data:mission:operational:taxi_out:duration", val=np.nan, units="s"),
        Variable("data:mission:operational:taxi_out:thrust_rate", val=np.nan),
        Variable("data:mission:operational:taxi_out:TOW", val=np.nan, units="kg"),
        Variable("data:propulsion:initial_climb:thrust_rate", val=1.0),
        Variable("data:propulsion:climb:thrust_rate", val=np.nan),
        Variable("data:propulsion:descent:thrust_rate", val=np.nan),
        Variable("data:mission:operational:main:climb:time_step", val=np.nan, units="s"),
        Variable(
            "settings:mission:operational:main:initial_climb:time_step", val=np.nan, units="s"
        ),
    }


def test_build():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(
        mission_definition, propulsion=Mock(IPropulsion), reference_area=100.0
    )

    # Check of "sizing" mission ################################################
    cl = np.linspace(0.0, 1.0, 11)
    cd = 0.5 * cl ** 2

    inputs = {
        "data:TLAR:cruise_mach": 0.78,
        "data:mission:sizing:main:range": 8000.0e3,
        "data:mission:sizing:diversion:range": 926.0e3,
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
        "data:mission:sizing:holding:duration": 2000.0,
        "data:mission:sizing:taxi_in:duration": 300.0,
        "data:mission:sizing:taxi_in:thrust_rate": 0.5,
    }

    mission = mission_builder.build(inputs, mission_name="sizing")
    # "sizing" mission defines no input mass variable, so it is automatically completed
    # with default taxi_out and takeoff phases, hence the 2 additional elements
    # in mission.flight_sequence (total of 6 instead of 4).
    assert len(mission) == 6
    assert mission[0].name == "sizing:taxi_out"
    assert mission[1].name == "sizing:takeoff"
    assert mission[2].name == "sizing:main"
    assert mission[3].name == "sizing:diversion"
    assert mission[4].name == "sizing:holding"
    assert mission[5].name == "sizing:taxi_in"

    # Taxi-out phase -----------------------------------------------------------
    taxi_out_phase = mission[0]
    assert isinstance(taxi_out_phase, FlightSequence)
    assert taxi_out_phase.name == "sizing:taxi_out"
    assert len(taxi_out_phase) == 2

    start = taxi_out_phase[0]
    assert start.name == "sizing:taxi_out"
    assert isinstance(start, Start)
    taxi_out = taxi_out_phase[1]
    assert start.name == "sizing:taxi_out"
    assert isinstance(taxi_out, TaxiSegment)

    # Takeoff phase -----------------------------------------------------------
    takeoff_phase = mission[1]
    assert isinstance(takeoff_phase, FlightSequence)
    assert takeoff_phase.name == "sizing:takeoff"
    assert len(takeoff_phase) == 2

    takeoff = takeoff_phase[0]
    assert takeoff.name == "sizing:takeoff"
    assert isinstance(takeoff, DummyTransitionSegment)
    mass_input = takeoff_phase[1]
    assert mass_input.name == "sizing:takeoff"
    assert isinstance(mass_input, MassTargetSegment)

    # Main route phase ---------------------------------------------------------
    main_route = mission[2]
    assert isinstance(main_route, FlightSequence)
    assert len(main_route) == 4
    assert main_route.distance_accuracy == 500.0
    assert main_route[0].name == "sizing:main:initial_climb"
    assert main_route[1].name == "sizing:main:climb"
    assert main_route[2].name == "sizing:main:cruise"
    assert main_route[3].name == "sizing:main:descent"

    initial_climb = main_route[0]
    assert isinstance(initial_climb, FlightSequence)
    assert len(initial_climb) == 3
    # Here we test that phase parameter is distributed among segments AND that default
    # value of variable is used.
    assert_allclose([segment.thrust_rate for segment in initial_climb], 1.0)

    climb1 = initial_climb[0]
    assert isinstance(climb1, AltitudeChangeSegment)
    assert climb1.target.altitude == pytest.approx(400 * foot)
    assert climb1.target.equivalent_airspeed == "constant"
    assert_allclose(climb1.polar.definition_cl, [0.0, 0.5, 1.0])
    assert_allclose(climb1.polar.cd(), [0.0, 0.03, 0.12])

    acceleration = initial_climb[1]
    assert isinstance(acceleration, SpeedChangeSegment)
    assert acceleration.target.equivalent_airspeed == pytest.approx(250 * knot)
    assert_allclose(acceleration.polar.definition_cl, cl)
    assert_allclose(acceleration.polar.cd(), cd)

    climb2 = initial_climb[2]
    assert isinstance(climb2, AltitudeChangeSegment)
    assert_allclose(climb2.polar.definition_cl, cl)
    assert_allclose(climb2.polar.cd(), cd)

    # Holding phase ------------------------------------------------------------
    holding_phase = mission[4]
    assert isinstance(holding_phase, FlightSequence)
    assert len(holding_phase) == 1
    holding = holding_phase[0]
    assert isinstance(holding, HoldSegment)

    taxi_in_phase = mission[5]
    assert isinstance(taxi_in_phase, FlightSequence)
    assert len(taxi_in_phase) == 1
    taxi_in = taxi_in_phase[0]
    assert isinstance(taxi_in, TaxiSegment)

    # Check of "test" mission ##################################################
    test_inputs = {
        "some:static:array": [1.0, 2.0, 3.0],
        "some:dynamic:array": np.linspace(0.0, 5.0, 6),
    }
    test_mission = mission_builder.build(test_inputs, mission_name="test")
    assert len(test_mission) == 1
    assert isinstance(test_mission[0], FlightSequence)
    assert len(test_mission[0]) == 2
    segment = test_mission[0][0]
    assert isinstance(segment, TestSegment)
    assert segment.scalar_parameter == 42.0
    assert_allclose(segment.vector_parameter_1, [1.0, 2.0, 3.0])
    assert_allclose(segment.vector_parameter_2, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    assert_allclose(segment.vector_parameter_3, [10.0, 20.0, 30.0])


def test_get_route_ranges():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(
        mission_definition, propulsion=Mock(IPropulsion), reference_area=100.0
    )

    cl = np.linspace(0.0, 1.0, 11)
    cd = 0.5 * cl ** 2

    inputs = {
        "data:TLAR:cruise_mach": 0.78,
        "data:mission:sizing:main:range": 8000.0e3,
        "data:mission:operational:main:range": 500.0e3,
        "data:mission:sizing:diversion:range": 926.0e3,
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
        "data:mission:sizing:holding:duration": 2000.0,
        "data:mission:operational:taxi_out:duration": 300.0,
        "data:mission:operational:taxi_out:thrust_rate": 0.5,
        "data:mission:operational:taxi_in:duration": 300.0,
        "data:mission:operational:taxi_in:thrust_rate": 0.5,
        "data:mission:sizing:taxi_in:duration": 300.0,
        "data:mission:sizing:taxi_in:thrust_rate": 0.5,
    }

    assert_allclose(mission_builder.get_route_ranges(inputs, "sizing"), [8000.0e3, 926.0e3])
    assert_allclose(mission_builder.get_route_ranges(inputs, "operational"), [500.0e3])


def test_get_reserve():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    flight_points = pd.DataFrame(
        dict(
            mass=[70000, 65000, 55000, 45000],
            name=[
                "data:mission:sizing:main:start",
                "data:mission:sizing:main:climb",
                "data:mission:sizing:other:start",
                "data:mission:sizing:other:climb",
            ],
        )
    )
    assert_allclose(mission_builder.get_reserve(flight_points, "sizing"), 5000 * 0.03)

    flight_points.name = [
        "data:mission:sizing:main:start",
        "data:mission:sizing:main:climb",
        "data:mission:sizing:main:cruise",
        "data:mission:sizing:main:cruise",
    ]
    assert_allclose(mission_builder.get_reserve(flight_points, "sizing"), 25000 * 0.03)


def _get_expected_structure():
    # We have to use repr() to provide comparison at InputDefinition fields that are
    # not settable in constructor.
    # This is very inconvenient to read, but it will hopefully help to locate
    # discrepancies that would occur.
    return {
        "operational": OrderedDict(
            [
                (
                    "parts",
                    [
                        {
                            "name": "operational:taxi_out",
                            "parts": [
                                {
                                    "name": "operational:taxi_out",
                                    "segment_type": "taxi",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="operational:taxi_out",
                                            use_opposite=False,
                                            variable_name="data:mission:operational:taxi_out:duration",
                                            prefix="data:mission",
                                        ),
                                        "mass": InputDefinition(
                                            parameter_name="mass",
                                            input_value=None,
                                            input_unit="kg",
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="operational:taxi_out",
                                            use_opposite=False,
                                            variable_name="data:mission:operational:taxi_out:TOW",
                                            prefix="data:mission",
                                        ),
                                    },
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:taxi_out",
                                        use_opposite=False,
                                        variable_name="data:mission:operational:taxi_out:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "true_airspeed": InputDefinition(
                                        parameter_name="true_airspeed",
                                        input_value=0.0,
                                        input_unit="m/s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:taxi_out",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "type": "segment",
                                }
                            ],
                            "type": "phase",
                        },
                        {
                            "climb_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="takeoff",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:initial_climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "operational:main:initial_climb",
                                    "parts": [
                                        {
                                            "name": "operational:main:initial_climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=400.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:initial_climb",
                                            "polar": OrderedDict(
                                                [
                                                    (
                                                        "CL",
                                                        InputDefinition(
                                                            parameter_name="CL",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="operational:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                    (
                                                        "CD",
                                                        InputDefinition(
                                                            parameter_name="CD",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="operational:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:initial_climb",
                                            "polar": {
                                                "CD": InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                                "CL": InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=1500.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": {
                                        "CD": InputDefinition(
                                            parameter_name="CD",
                                            input_value=[0.0, 0.03, 0.12],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="operational:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                        "CL": InputDefinition(
                                            parameter_name="CL",
                                            input_value=[0.0, 0.5, 1.0],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="operational:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                    },
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=1.0,
                                        is_relative=False,
                                        part_identifier="operational:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:initial_climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="settings:mission:operational:main:initial_climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="climb",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "operational:main:climb",
                                    "parts": [
                                        {
                                            "name": "operational:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:climb",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:TLAR:cruise_mach",
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=-20000.0,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:climb",
                                        use_opposite=False,
                                        variable_name="data:mission:operational:main:climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                            ],
                            "cruise_part": {
                                "engine_setting": InputDefinition(
                                    parameter_name="engine_setting",
                                    input_value="cruise",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="operational:main:cruise",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "name": "operational:main:cruise",
                                "polar": OrderedDict(
                                    [
                                        (
                                            "CL",
                                            InputDefinition(
                                                parameter_name="CL",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="operational:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                        (
                                            "CD",
                                            InputDefinition(
                                                parameter_name="CD",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="operational:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                    ]
                                ),
                                "segment_type": "optimal_cruise",
                                "type": "segment",
                            },
                            "descent_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="idle",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:descent",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "operational:main:descent",
                                    "parts": [
                                        {
                                            "name": "operational:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:descent",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "operational:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:mission:operational:main:descent:final_altitude",
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="operational:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:main:descent",
                                        use_opposite=False,
                                        variable_name="data:propulsion:descent:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                }
                            ],
                            "distance_accuracy": InputDefinition(
                                parameter_name="distance_accuracy",
                                input_value=500,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="operational:main",
                                use_opposite=False,
                                variable_name=None,
                                prefix="data:mission",
                            ),
                            "name": "operational:main",
                            "range": InputDefinition(
                                parameter_name="range",
                                input_value=None,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="operational:main",
                                use_opposite=False,
                                variable_name="data:mission:operational:main:range",
                                prefix="data:mission",
                            ),
                            "type": "route",
                        },
                        {
                            "name": "operational:taxi_in",
                            "parts": [
                                {
                                    "name": "operational:taxi_in",
                                    "segment_type": "taxi",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="operational:taxi_in",
                                            use_opposite=False,
                                            variable_name="data:mission:operational:taxi_in:duration",
                                            prefix="data:mission",
                                        )
                                    },
                                    "true_airspeed": InputDefinition(
                                        parameter_name="true_airspeed",
                                        input_value=0.0,
                                        input_unit="m/s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="operational:taxi_in",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "type": "segment",
                                }
                            ],
                            "thrust_rate": InputDefinition(
                                parameter_name="thrust_rate",
                                input_value=None,
                                input_unit=None,
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="operational:taxi_in",
                                use_opposite=False,
                                variable_name="data:mission:operational:taxi_in:thrust_rate",
                                prefix="data:mission",
                            ),
                            "type": "phase",
                        },
                        {
                            "name": "operational",
                            "reserve": {
                                "multiplier": InputDefinition(
                                    parameter_name="multiplier",
                                    input_value=0.02,
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="operational",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "ref": InputDefinition(
                                    parameter_name="ref",
                                    input_value="main",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="operational",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                            },
                        },
                    ],
                ),
                ("name", "operational"),
                ("type", "mission"),
            ]
        ),
        "sizing": OrderedDict(
            [
                (
                    "parts",
                    [
                        OrderedDict(
                            [
                                (
                                    "parts",
                                    [
                                        {
                                            "name": "sizing:taxi_out",
                                            "segment_type": "start",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="ft",
                                                    default_value=0.0,
                                                    is_relative=False,
                                                    part_identifier="sizing:taxi_out",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:taxi_out:altitude",
                                                    prefix="data:mission",
                                                ),
                                                "true_airspeed": InputDefinition(
                                                    parameter_name="true_airspeed",
                                                    input_value=None,
                                                    input_unit="m/s",
                                                    default_value=0.0,
                                                    is_relative=False,
                                                    part_identifier="sizing:taxi_out",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:taxi_out:true_airspeed",
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:taxi_out",
                                            "segment_type": "taxi",
                                            "target": {
                                                "time": InputDefinition(
                                                    parameter_name="time",
                                                    input_value=None,
                                                    input_unit="s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:taxi_out",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:taxi_out:duration",
                                                    prefix="data:mission",
                                                )
                                            },
                                            "thrust_rate": InputDefinition(
                                                parameter_name="thrust_rate",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="sizing:taxi_out",
                                                shape=None,
                                                shape_by_conn=False,
                                                use_opposite=False,
                                                variable_name="data:mission:sizing:taxi_out:thrust_rate",
                                                prefix="data:mission",
                                            ),
                                            "time_step": InputDefinition(
                                                parameter_name="time_step",
                                                input_value=None,
                                                input_unit="s",
                                                default_value=60,
                                                is_relative=False,
                                                part_identifier="sizing:taxi_out",
                                                shape=None,
                                                shape_by_conn=False,
                                                use_opposite=False,
                                                variable_name="settings:mission:sizing:taxi_out:time_step",
                                                prefix="data:mission",
                                            ),
                                            "true_airspeed": InputDefinition(
                                                parameter_name="true_airspeed",
                                                input_value=None,
                                                input_unit="m/s",
                                                default_value=0.0,
                                                is_relative=False,
                                                part_identifier="sizing:taxi_out",
                                                shape=None,
                                                shape_by_conn=False,
                                                use_opposite=False,
                                                variable_name="data:mission:sizing:taxi_out:true_airspeed",
                                                prefix="data:mission",
                                            ),
                                            "type": "segment",
                                        },
                                    ],
                                ),
                                ("name", "sizing:taxi_out"),
                                ("type", "phase"),
                            ]
                        ),
                        OrderedDict(
                            [
                                (
                                    "parts",
                                    [
                                        {
                                            "name": "sizing:takeoff",
                                            "segment_type": "transition",
                                            "target": {
                                                "delta_altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="ft",
                                                    default_value=35,
                                                    is_relative=True,
                                                    part_identifier="sizing:takeoff",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:takeoff:safety_altitude",
                                                    prefix="data:mission",
                                                ),
                                                "delta_mass": InputDefinition(
                                                    parameter_name="mass",
                                                    input_value=None,
                                                    input_unit="kg",
                                                    default_value=np.nan,
                                                    is_relative=True,
                                                    part_identifier="sizing:takeoff",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=True,
                                                    variable_name="data:mission:sizing:takeoff:fuel",
                                                    prefix="data:mission",
                                                ),
                                                "time": InputDefinition(
                                                    parameter_name="time",
                                                    input_value=None,
                                                    input_unit="s",
                                                    default_value=0.0,
                                                    is_relative=False,
                                                    part_identifier="sizing:takeoff",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:takeoff:duration",
                                                    prefix="data:mission",
                                                ),
                                                "true_airspeed": InputDefinition(
                                                    parameter_name="true_airspeed",
                                                    input_value=None,
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:takeoff",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:takeoff:V2",
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:takeoff",
                                            "segment_type": "mass_input",
                                            "target": {
                                                "mass": InputDefinition(
                                                    parameter_name="mass",
                                                    input_value=None,
                                                    input_unit="kg",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:takeoff",
                                                    shape=None,
                                                    shape_by_conn=False,
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:TOW",
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                ),
                                ("name", "sizing:takeoff"),
                                ("type", "phase"),
                            ]
                        ),
                        {
                            "climb_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="takeoff",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:initial_climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "sizing:main:initial_climb",
                                    "parts": [
                                        {
                                            "name": "sizing:main:initial_climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=400.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:initial_climb",
                                            "polar": OrderedDict(
                                                [
                                                    (
                                                        "CL",
                                                        InputDefinition(
                                                            parameter_name="CL",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="sizing:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                    (
                                                        "CD",
                                                        InputDefinition(
                                                            parameter_name="CD",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="sizing:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:initial_climb",
                                            "polar": {
                                                "CD": InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                                "CL": InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=1500.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": {
                                        "CD": InputDefinition(
                                            parameter_name="CD",
                                            input_value=[0.0, 0.03, 0.12],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="sizing:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                        "CL": InputDefinition(
                                            parameter_name="CL",
                                            input_value=[0.0, 0.5, 1.0],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="sizing:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                    },
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=1.0,
                                        is_relative=False,
                                        part_identifier="sizing:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:initial_climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="settings:mission:sizing:main:initial_climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="climb",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "sizing:main:climb",
                                    "parts": [
                                        {
                                            "name": "sizing:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:climb",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:TLAR:cruise_mach",
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=-20000.0,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:climb",
                                        use_opposite=False,
                                        variable_name="data:mission:sizing:main:climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                            ],
                            "cruise_part": {
                                "engine_setting": InputDefinition(
                                    parameter_name="engine_setting",
                                    input_value="cruise",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="sizing:main:cruise",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "name": "sizing:main:cruise",
                                "polar": OrderedDict(
                                    [
                                        (
                                            "CL",
                                            InputDefinition(
                                                parameter_name="CL",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="sizing:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                        (
                                            "CD",
                                            InputDefinition(
                                                parameter_name="CD",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="sizing:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                    ]
                                ),
                                "segment_type": "optimal_cruise",
                                "type": "segment",
                            },
                            "descent_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="idle",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:descent",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "sizing:main:descent",
                                    "parts": [
                                        {
                                            "name": "sizing:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:descent",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:main:descent:final_altitude",
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:main:descent",
                                        use_opposite=False,
                                        variable_name="data:propulsion:descent:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                }
                            ],
                            "distance_accuracy": InputDefinition(
                                parameter_name="distance_accuracy",
                                input_value=500,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="sizing:main",
                                use_opposite=False,
                                variable_name=None,
                                prefix="data:mission",
                            ),
                            "name": "sizing:main",
                            "range": InputDefinition(
                                parameter_name="range",
                                input_value=None,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="sizing:main",
                                use_opposite=False,
                                variable_name="data:mission:sizing:main:range",
                                prefix="data:mission",
                            ),
                            "type": "route",
                        },
                        {
                            "climb_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="climb",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:diversion:diversion_climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "sizing:diversion:diversion_climb",
                                    "parts": [
                                        {
                                            "name": "sizing:diversion:diversion_climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:diversion:diversion_climb",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:diversion:diversion_climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=22000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:diversion_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=0.93,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:diversion:diversion_climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:diversion:diversion_climb",
                                        use_opposite=False,
                                        variable_name="settings:mission:sizing:diversion:diversion_climb:t_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                }
                            ],
                            "cruise_part": {
                                "engine_setting": InputDefinition(
                                    parameter_name="engine_setting",
                                    input_value="cruise",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="sizing:diversion:cruise",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "name": "sizing:diversion:cruise",
                                "polar": OrderedDict(
                                    [
                                        (
                                            "CL",
                                            InputDefinition(
                                                parameter_name="CL",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="sizing:diversion:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                        (
                                            "CD",
                                            InputDefinition(
                                                parameter_name="CD",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="sizing:diversion:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                    ]
                                ),
                                "segment_type": "cruise",
                                "type": "segment",
                            },
                            "descent_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="idle",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:diversion:descent",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "sizing:diversion:descent",
                                    "parts": [
                                        {
                                            "name": "sizing:diversion:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:diversion:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:diversion:descent",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "sizing:diversion:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name="data:mission:sizing:diversion:descent:final_altitude",
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:diversion:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:diversion:descent",
                                        use_opposite=False,
                                        variable_name="data:propulsion:descent:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                }
                            ],
                            "distance_accuracy": InputDefinition(
                                parameter_name="distance_accuracy",
                                input_value=0.1,
                                input_unit="km",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="sizing:diversion",
                                use_opposite=False,
                                variable_name=None,
                                prefix="data:mission",
                            ),
                            "name": "sizing:diversion",
                            "range": InputDefinition(
                                parameter_name="range",
                                input_value=None,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="sizing:diversion",
                                use_opposite=False,
                                variable_name="data:mission:sizing:diversion:range",
                                prefix="data:mission",
                            ),
                            "type": "route",
                        },
                        {
                            "name": "sizing:holding",
                            "parts": [
                                {
                                    "name": "sizing:holding",
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:holding",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="sizing:holding",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "segment_type": "holding",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="sizing:holding",
                                            use_opposite=False,
                                            variable_name="data:mission:sizing:holding:duration",
                                            prefix="data:mission",
                                        )
                                    },
                                    "type": "segment",
                                }
                            ],
                            "type": "phase",
                        },
                        {
                            "name": "sizing:taxi_in",
                            "parts": [
                                {
                                    "name": "sizing:taxi_in",
                                    "segment_type": "taxi",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="sizing:taxi_in",
                                            use_opposite=False,
                                            variable_name="data:mission:sizing:taxi_in:duration",
                                            prefix="data:mission",
                                        )
                                    },
                                    "true_airspeed": InputDefinition(
                                        parameter_name="true_airspeed",
                                        input_value=0.0,
                                        input_unit="m/s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="sizing:taxi_in",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "type": "segment",
                                }
                            ],
                            "thrust_rate": InputDefinition(
                                parameter_name="thrust_rate",
                                input_value=None,
                                input_unit=None,
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="sizing:taxi_in",
                                use_opposite=False,
                                variable_name="data:mission:sizing:taxi_in:thrust_rate",
                                prefix="data:mission",
                            ),
                            "type": "phase",
                        },
                        {
                            "name": "sizing",
                            "reserve": {
                                "multiplier": InputDefinition(
                                    parameter_name="multiplier",
                                    input_value=0.03,
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="sizing",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "ref": InputDefinition(
                                    parameter_name="ref",
                                    input_value="main",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="sizing",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                            },
                        },
                    ],
                ),
                ("name", "sizing"),
                ("type", "mission"),
            ]
        ),
        "fuel_as_objective": OrderedDict(
            [
                (
                    "parts",
                    [
                        {
                            "name": "fuel_as_objective:taxi_out",
                            "parts": [
                                {
                                    "name": "fuel_as_objective:taxi_out",
                                    "segment_type": "taxi",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="fuel_as_objective:taxi_out",
                                            use_opposite=False,
                                            variable_name="data:mission:fuel_as_objective:taxi_out:duration",
                                            prefix="data:mission",
                                        ),
                                        "mass": InputDefinition(
                                            parameter_name="mass",
                                            input_value=None,
                                            input_unit="kg",
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="fuel_as_objective:taxi_out",
                                            use_opposite=False,
                                            variable_name="data:mission:fuel_as_objective:taxi_out:TOW",
                                            prefix="data:mission",
                                        ),
                                    },
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:taxi_out",
                                        use_opposite=False,
                                        variable_name="data:mission:fuel_as_objective:taxi_out:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "true_airspeed": InputDefinition(
                                        parameter_name="true_airspeed",
                                        input_value=0.0,
                                        input_unit="m/s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:taxi_out",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "type": "segment",
                                }
                            ],
                            "type": "phase",
                        },
                        {
                            "climb_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="takeoff",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:initial_climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "fuel_as_objective:main:initial_climb",
                                    "parts": [
                                        {
                                            "name": "fuel_as_objective:main:initial_climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=400.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:initial_climb",
                                            "polar": OrderedDict(
                                                [
                                                    (
                                                        "CL",
                                                        InputDefinition(
                                                            parameter_name="CL",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="fuel_as_objective:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                    (
                                                        "CD",
                                                        InputDefinition(
                                                            parameter_name="CD",
                                                            input_value=None,
                                                            input_unit=None,
                                                            default_value=np.nan,
                                                            is_relative=False,
                                                            part_identifier="fuel_as_objective:main:initial_climb",
                                                            use_opposite=False,
                                                            variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                            shape_by_conn=True,
                                                            prefix="data:mission",
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:initial_climb",
                                            "polar": {
                                                "CD": InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                                "CL": InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=1500.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:initial_climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": {
                                        "CD": InputDefinition(
                                            parameter_name="CD",
                                            input_value=[0.0, 0.03, 0.12],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="fuel_as_objective:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                        "CL": InputDefinition(
                                            parameter_name="CL",
                                            input_value=[0.0, 0.5, 1.0],
                                            input_unit=None,
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="fuel_as_objective:main:initial_climb",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        ),
                                    },
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=1.0,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:initial_climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:initial_climb",
                                        use_opposite=False,
                                        variable_name="settings:mission:fuel_as_objective:main:initial_climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="climb",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:climb",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "fuel_as_objective:main:climb",
                                    "parts": [
                                        {
                                            "name": "fuel_as_objective:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:climb",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:TLAR:cruise_mach",
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:climb",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=-20000.0,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:climb",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:climb",
                                        use_opposite=False,
                                        variable_name="data:propulsion:climb:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "time_step": InputDefinition(
                                        parameter_name="time_step",
                                        input_value=None,
                                        input_unit="s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:climb",
                                        use_opposite=False,
                                        variable_name="data:mission:fuel_as_objective:main:climb:time_step",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                },
                            ],
                            "cruise_part": {
                                "engine_setting": InputDefinition(
                                    parameter_name="engine_setting",
                                    input_value="cruise",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="fuel_as_objective:main:cruise",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "name": "fuel_as_objective:main:cruise",
                                "polar": OrderedDict(
                                    [
                                        (
                                            "CL",
                                            InputDefinition(
                                                parameter_name="CL",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="fuel_as_objective:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                        (
                                            "CD",
                                            InputDefinition(
                                                parameter_name="CD",
                                                input_value=None,
                                                input_unit=None,
                                                default_value=np.nan,
                                                is_relative=False,
                                                part_identifier="fuel_as_objective:main:cruise",
                                                use_opposite=False,
                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                shape_by_conn=True,
                                                prefix="data:mission",
                                            ),
                                        ),
                                    ]
                                ),
                                "segment_type": "optimal_cruise",
                                "type": "segment",
                            },
                            "descent_parts": [
                                {
                                    "engine_setting": InputDefinition(
                                        parameter_name="engine_setting",
                                        input_value="idle",
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:descent",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "name": "fuel_as_objective:main:descent",
                                    "parts": [
                                        {
                                            "name": "fuel_as_objective:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=300,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "mach": InputDefinition(
                                                    parameter_name="mach",
                                                    input_value="constant",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=10000.0,
                                                    input_unit="ft",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:descent",
                                            "segment_type": "speed_change",
                                            "target": {
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value=250.0,
                                                    input_unit="kn",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                )
                                            },
                                            "type": "segment",
                                        },
                                        {
                                            "name": "fuel_as_objective:main:descent",
                                            "segment_type": "altitude_change",
                                            "target": {
                                                "altitude": InputDefinition(
                                                    parameter_name="altitude",
                                                    input_value=None,
                                                    input_unit="m",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:mission:fuel_as_objective:main:descent:final_altitude",
                                                    prefix="data:mission",
                                                ),
                                                "equivalent_airspeed": InputDefinition(
                                                    parameter_name="equivalent_airspeed",
                                                    input_value="constant",
                                                    input_unit="m/s",
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name=None,
                                                    prefix="data:mission",
                                                ),
                                            },
                                            "type": "segment",
                                        },
                                    ],
                                    "polar": OrderedDict(
                                        [
                                            (
                                                "CL",
                                                InputDefinition(
                                                    parameter_name="CL",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                            (
                                                "CD",
                                                InputDefinition(
                                                    parameter_name="CD",
                                                    input_value=None,
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    is_relative=False,
                                                    part_identifier="fuel_as_objective:main:descent",
                                                    use_opposite=False,
                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                    shape_by_conn=True,
                                                    prefix="data:mission",
                                                ),
                                            ),
                                        ]
                                    ),
                                    "thrust_rate": InputDefinition(
                                        parameter_name="thrust_rate",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:main:descent",
                                        use_opposite=False,
                                        variable_name="data:propulsion:descent:thrust_rate",
                                        prefix="data:mission",
                                    ),
                                    "type": "phase",
                                }
                            ],
                            "distance_accuracy": InputDefinition(
                                parameter_name="distance_accuracy",
                                input_value=500,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="fuel_as_objective:main",
                                use_opposite=False,
                                variable_name=None,
                                prefix="data:mission",
                            ),
                            "name": "fuel_as_objective:main",
                            "range": InputDefinition(
                                parameter_name="range",
                                input_value=None,
                                input_unit="m",
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="fuel_as_objective:main",
                                use_opposite=False,
                                variable_name="data:mission:fuel_as_objective:main:range",
                                prefix="data:mission",
                            ),
                            "type": "route",
                        },
                        {
                            "name": "fuel_as_objective:taxi_in",
                            "parts": [
                                {
                                    "name": "fuel_as_objective:taxi_in",
                                    "segment_type": "taxi",
                                    "target": {
                                        "delta_time": InputDefinition(
                                            parameter_name="time",
                                            input_value=None,
                                            input_unit="s",
                                            default_value=np.nan,
                                            is_relative=True,
                                            part_identifier="fuel_as_objective:taxi_in",
                                            use_opposite=False,
                                            variable_name="data:mission:fuel_as_objective:taxi_in:duration",
                                            prefix="data:mission",
                                        )
                                    },
                                    "true_airspeed": InputDefinition(
                                        parameter_name="true_airspeed",
                                        input_value=0.0,
                                        input_unit="m/s",
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="fuel_as_objective:taxi_in",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "type": "segment",
                                }
                            ],
                            "thrust_rate": InputDefinition(
                                parameter_name="thrust_rate",
                                input_value=None,
                                input_unit=None,
                                default_value=np.nan,
                                is_relative=False,
                                part_identifier="fuel_as_objective:taxi_in",
                                use_opposite=False,
                                variable_name="data:mission:fuel_as_objective:taxi_in:thrust_rate",
                                prefix="data:mission",
                            ),
                            "type": "phase",
                        },
                        {
                            "name": "fuel_as_objective",
                            "reserve": {
                                "multiplier": InputDefinition(
                                    parameter_name="multiplier",
                                    input_value=0.02,
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="fuel_as_objective",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                                "ref": InputDefinition(
                                    parameter_name="ref",
                                    input_value="main",
                                    input_unit=None,
                                    default_value=np.nan,
                                    is_relative=False,
                                    part_identifier="fuel_as_objective",
                                    use_opposite=False,
                                    variable_name=None,
                                    prefix="data:mission",
                                ),
                            },
                        },
                    ],
                ),
                (
                    "use_all_block_fuel",
                    InputDefinition(
                        parameter_name="use_all_block_fuel",
                        input_value=True,
                        input_unit=None,
                        default_value=np.nan,
                        is_relative=False,
                        part_identifier="fuel_as_objective",
                        shape=None,
                        shape_by_conn=False,
                        use_opposite=False,
                        variable_name=None,
                        prefix="data:mission",
                    ),
                ),
                (
                    "target_fuel_consumption",
                    InputDefinition(
                        parameter_name="target_fuel_consumption",
                        input_value=None,
                        input_unit="kg",
                        default_value=np.nan,
                        is_relative=False,
                        part_identifier="fuel_as_objective",
                        shape=None,
                        shape_by_conn=False,
                        use_opposite=False,
                        variable_name="data:mission:fuel_as_objective:block_fuel",
                        prefix="data:mission",
                    ),
                ),
                ("name", "fuel_as_objective"),
                ("type", "mission"),
            ]
        ),
        "test": OrderedDict(
            [
                (
                    "parts",
                    [
                        {
                            "name": "test:test_phase",
                            "parts": [
                                {
                                    "name": "test:test_phase",
                                    "scalar_parameter": InputDefinition(
                                        parameter_name="scalar_parameter",
                                        input_value=42.0,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="test:test_phase",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "segment_type": "test_segment_B",
                                    "type": "segment",
                                    "vector_parameter_1": InputDefinition(
                                        parameter_name="vector_parameter_1",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="test:test_phase",
                                        use_opposite=False,
                                        variable_name="some:static:array",
                                        shape_by_conn=True,
                                        prefix="data:mission",
                                    ),
                                    "vector_parameter_2": InputDefinition(
                                        parameter_name="vector_parameter_2",
                                        input_value=None,
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="test:test_phase",
                                        use_opposite=False,
                                        variable_name="some:dynamic:array",
                                        shape_by_conn=True,
                                        prefix="data:mission",
                                    ),
                                    "vector_parameter_3": InputDefinition(
                                        parameter_name="vector_parameter_3",
                                        input_value=[10.0, 20.0, 30.0],
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="test:test_phase",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "vector_parameter_4": InputDefinition(
                                        parameter_name="vector_parameter_4",
                                        input_value=[100.0, 200.0, 300.0],
                                        input_unit=None,
                                        default_value=np.nan,
                                        is_relative=False,
                                        part_identifier="test:test_phase",
                                        use_opposite=False,
                                        variable_name=None,
                                        prefix="data:mission",
                                    ),
                                    "target": {
                                        "altitude": InputDefinition(
                                            parameter_name="altitude",
                                            input_value=0.0,
                                            input_unit="m",
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="test:test_phase",
                                            use_opposite=False,
                                            variable_name=None,
                                            prefix="data:mission",
                                        )
                                    },
                                },
                                {
                                    "name": "test:test_phase",
                                    "segment_type": "mass_input",
                                    "target": {
                                        "mass": InputDefinition(
                                            parameter_name="mass",
                                            input_value=None,
                                            input_unit="kg",
                                            default_value=np.nan,
                                            is_relative=False,
                                            part_identifier="test:test_phase",
                                            shape=None,
                                            shape_by_conn=False,
                                            use_opposite=False,
                                            variable_name="data:mission:test:test_phase:mass",
                                            prefix="data:mission",
                                        )
                                    },
                                    "type": "segment",
                                },
                            ],
                            "type": "phase",
                        },
                    ],
                ),
                ("name", "test"),
                ("type", "mission"),
            ]
        ),
    }
