#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.segments.altitude_change import AltitudeChangeSegment
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.speed_change import SpeedChangeSegment
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from fastoad.openmdao.variables import Variable
from ..exceptions import FastMissionFileMissingMissionNameError
from ..mission_builder import InputDefinition, MissionBuilder
from ..schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_input_definition_units():
    inp1 = InputDefinition("anything", input_unit="km")
    inp1.set_value(1.0)
    assert inp1.get_value() == 1.0

    inp1.output_unit = "m"
    assert inp1.get_value() == 1000.0

    # When parameter name is known, its default unit is automatically set.
    inp2 = InputDefinition("ground_distance", input_unit="km")
    inp2.set_value(1.0)
    assert inp2.get_value() == 1000.0
    assert not inp2.is_relative

    inp3 = InputDefinition("delta_time", input_unit="h")
    inp3.set_value(1.0)
    assert inp3.parameter_name == "time"
    assert inp3.is_relative

    assert inp3.get_value() == 3600.0


def test_initialization():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    assert mission_builder._structure == _get_expected_structure()


def test_inputs():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )
    with pytest.raises(FastMissionFileMissingMissionNameError):
        mission_builder.get_input_variables()

    assert set(mission_builder.get_input_variables("sizing")) == {
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
    }

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
        Variable("data:propulsion:initial_climb:thrust_rate", val=1.0),
        Variable("data:propulsion:climb:thrust_rate", val=np.nan),
        Variable("data:propulsion:descent:thrust_rate", val=np.nan),
    }


def test_build():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(
        mission_definition, propulsion=Mock(IPropulsion), reference_area=100.0
    )

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

    assert len(mission.flight_sequence) == 4
    assert mission.flight_sequence[0].name == "sizing:main"
    assert mission.flight_sequence[1].name == "sizing:diversion"
    assert mission.flight_sequence[2].name == "sizing:holding"
    assert mission.flight_sequence[3].name == "sizing:taxi_in"

    main_route = mission.flight_sequence[0]
    assert isinstance(main_route, FlightSequence)
    assert len(main_route.flight_sequence) == 4
    assert main_route.distance_accuracy == 500.0
    assert main_route.flight_sequence[0].name == "sizing:main:initial_climb"
    assert main_route.flight_sequence[1].name == "sizing:main:climb"
    assert main_route.flight_sequence[2].name == "sizing:main:cruise"
    assert main_route.flight_sequence[3].name == "sizing:main:descent"

    initial_climb = main_route.flight_sequence[0]
    assert isinstance(initial_climb, FlightSequence)
    assert len(initial_climb.flight_sequence) == 3
    # Here we test that phase parameter is distributed among segments AND that default
    # value of variable is used.
    assert_allclose([segment.thrust_rate for segment in initial_climb.flight_sequence], 1.0)

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
    return OrderedDict(
        [
            (
                "sizing",
                OrderedDict(
                    [
                        (
                            "mission",
                            InputDefinition(
                                parameter_name="mission",
                                input_unit=None,
                                default_value=np.nan,
                                use_opposite=False,
                                is_relative=False,
                                _value="sizing",
                                _variable_name=None,
                            ),
                        ),
                        (
                            "parts",
                            [
                                OrderedDict(
                                    [
                                        (
                                            "route",
                                            InputDefinition(
                                                parameter_name="route",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="main",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                input_unit="m",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=None,
                                                _variable_name="data:mission:sizing:main:range",
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                input_unit="m",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=500,
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="initial_climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="takeoff",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": InputDefinition(
                                                                    parameter_name="CD",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=[0.0, 0.03, 0.12],
                                                                    _variable_name=None,
                                                                ),
                                                                "CL": InputDefinition(
                                                                    parameter_name="CL",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=[0.0, 0.5, 1.0],
                                                                    _variable_name=None,
                                                                ),
                                                            },
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=1.0,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:initial_climb:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=400.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "polar": OrderedDict(
                                                                        [
                                                                            (
                                                                                "CL",
                                                                                InputDefinition(
                                                                                    parameter_name="CL",
                                                                                    input_unit=None,
                                                                                    default_value=np.nan,
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                    _value=None,
                                                                                    _variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                InputDefinition(
                                                                                    parameter_name="CD",
                                                                                    input_unit=None,
                                                                                    default_value=np.nan,
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                    _value=None,
                                                                                    _variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=250,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                        ),
                                                                        "CL": InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                        ),
                                                                    },
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=1500.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:climb:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:TLAR:cruise_mach",
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="m",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=-20000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": InputDefinition(
                                                    parameter_name="engine_setting",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="cruise",
                                                    _variable_name=None,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="optimal_cruise",
                                                    _variable_name=None,
                                                ),
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="descent",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="idle",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:descent:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=250.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="m",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:mission:sizing:main:descent:final_altitude",
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        (
                                            "route",
                                            InputDefinition(
                                                parameter_name="route",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="diversion",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                input_unit="m",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=None,
                                                _variable_name="data:mission:sizing:diversion:range",
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                input_unit="km",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=0.1,
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="diversion_climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=0.93,
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "time_step",
                                                            InputDefinition(
                                                                parameter_name="time_step",
                                                                input_unit="s",
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=5.0,
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=22000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": InputDefinition(
                                                    parameter_name="engine_setting",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="cruise",
                                                    _variable_name=None,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="cruise",
                                                    _variable_name=None,
                                                ),
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="descent",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="idle",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:descent:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=250.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="m",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:mission:sizing:diversion:descent:final_altitude",
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        (
                                            "phase",
                                            InputDefinition(
                                                parameter_name="phase",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="holding",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "polar": OrderedDict(
                                                        [
                                                            (
                                                                "CL",
                                                                InputDefinition(
                                                                    parameter_name="CL",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=None,
                                                                    _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                ),
                                                            ),
                                                            (
                                                                "CD",
                                                                InputDefinition(
                                                                    parameter_name="CD",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=None,
                                                                    _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                ),
                                                            ),
                                                        ]
                                                    ),
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        input_unit=None,
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value="holding",
                                                        _variable_name=None,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            input_unit="s",
                                                            default_value=np.nan,
                                                            use_opposite=False,
                                                            is_relative=True,
                                                            _value=None,
                                                            _variable_name="data:mission:sizing:holding:duration",
                                                        )
                                                    },
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        (
                                            "phase",
                                            InputDefinition(
                                                parameter_name="phase",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="taxi_in",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "thrust_rate",
                                            InputDefinition(
                                                parameter_name="thrust_rate",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=None,
                                                _variable_name="data:mission:sizing:taxi_in:thrust_rate",
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        input_unit=None,
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value="taxi",
                                                        _variable_name=None,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            input_unit="s",
                                                            default_value=np.nan,
                                                            use_opposite=False,
                                                            is_relative=True,
                                                            _value=None,
                                                            _variable_name="data:mission:sizing:taxi_in:duration",
                                                        )
                                                    },
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        input_unit="m/s",
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value=0.0,
                                                        _variable_name=None,
                                                    ),
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                {
                                    "reserve": {
                                        "multiplier": InputDefinition(
                                            parameter_name="multiplier",
                                            input_unit=None,
                                            default_value=np.nan,
                                            use_opposite=False,
                                            is_relative=False,
                                            _value=0.03,
                                            _variable_name=None,
                                        ),
                                        "ref": InputDefinition(
                                            parameter_name="ref",
                                            input_unit=None,
                                            default_value=np.nan,
                                            use_opposite=False,
                                            is_relative=False,
                                            _value="main",
                                            _variable_name=None,
                                        ),
                                    }
                                },
                            ],
                        ),
                    ]
                ),
            ),
            (
                "operational",
                OrderedDict(
                    [
                        (
                            "mission",
                            InputDefinition(
                                parameter_name="mission",
                                input_unit=None,
                                default_value=np.nan,
                                use_opposite=False,
                                is_relative=False,
                                _value="operational",
                                _variable_name=None,
                            ),
                        ),
                        (
                            "parts",
                            [
                                OrderedDict(
                                    [
                                        (
                                            "phase",
                                            InputDefinition(
                                                parameter_name="phase",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="taxi_out",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        input_unit=None,
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value="taxi",
                                                        _variable_name=None,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            input_unit="s",
                                                            default_value=np.nan,
                                                            use_opposite=False,
                                                            is_relative=True,
                                                            _value=None,
                                                            _variable_name="data:mission:operational:taxi_out:duration",
                                                        )
                                                    },
                                                    "thrust_rate": InputDefinition(
                                                        parameter_name="thrust_rate",
                                                        input_unit=None,
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value=None,
                                                        _variable_name="data:mission:operational:taxi_out:thrust_rate",
                                                    ),
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        input_unit="m/s",
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value=0.0,
                                                        _variable_name=None,
                                                    ),
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        (
                                            "route",
                                            InputDefinition(
                                                parameter_name="route",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="main",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                input_unit="m",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=None,
                                                _variable_name="data:mission:operational:main:range",
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                input_unit="m",
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=500,
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="initial_climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="takeoff",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": InputDefinition(
                                                                    parameter_name="CD",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=[0.0, 0.03, 0.12],
                                                                    _variable_name=None,
                                                                ),
                                                                "CL": InputDefinition(
                                                                    parameter_name="CL",
                                                                    input_unit=None,
                                                                    default_value=np.nan,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                    _value=[0.0, 0.5, 1.0],
                                                                    _variable_name=None,
                                                                ),
                                                            },
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=1.0,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:initial_climb:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=400.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "polar": OrderedDict(
                                                                        [
                                                                            (
                                                                                "CL",
                                                                                InputDefinition(
                                                                                    parameter_name="CL",
                                                                                    input_unit=None,
                                                                                    default_value=np.nan,
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                    _value=None,
                                                                                    _variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                InputDefinition(
                                                                                    parameter_name="CD",
                                                                                    input_unit=None,
                                                                                    default_value=np.nan,
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                    _value=None,
                                                                                    _variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=250,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                        ),
                                                                        "CL": InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                        ),
                                                                    },
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=1500.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="climb",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:climb:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:TLAR:cruise_mach",
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="m",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=-20000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": InputDefinition(
                                                    parameter_name="engine_setting",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="cruise",
                                                    _variable_name=None,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    input_unit=None,
                                                    default_value=np.nan,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                    _value="optimal_cruise",
                                                    _variable_name=None,
                                                ),
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        (
                                                            "phase",
                                                            InputDefinition(
                                                                parameter_name="phase",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="descent",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value="idle",
                                                                _variable_name=None,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        InputDefinition(
                                                                            parameter_name="CL",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                input_unit=None,
                                                                default_value=np.nan,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                                _value=None,
                                                                _variable_name="data:propulsion:descent:thrust_rate",
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=300,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            input_unit=None,
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="ft",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=10000.0,
                                                                            _variable_name=None,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="speed_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="kn",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=250.0,
                                                                            _variable_name=None,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        input_unit=None,
                                                                        default_value=np.nan,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                        _value="altitude_change",
                                                                        _variable_name=None,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            input_unit="m",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value=None,
                                                                            _variable_name="data:mission:operational:main:descent:final_altitude",
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            input_unit="m/s",
                                                                            default_value=np.nan,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                            _value="constant",
                                                                            _variable_name=None,
                                                                        ),
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        (
                                            "phase",
                                            InputDefinition(
                                                parameter_name="phase",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value="taxi_in",
                                                _variable_name=None,
                                            ),
                                        ),
                                        (
                                            "thrust_rate",
                                            InputDefinition(
                                                parameter_name="thrust_rate",
                                                input_unit=None,
                                                default_value=np.nan,
                                                use_opposite=False,
                                                is_relative=False,
                                                _value=None,
                                                _variable_name="data:mission:operational:taxi_in:thrust_rate",
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        input_unit=None,
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value="taxi",
                                                        _variable_name=None,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            input_unit="s",
                                                            default_value=np.nan,
                                                            use_opposite=False,
                                                            is_relative=True,
                                                            _value=None,
                                                            _variable_name="data:mission:operational:taxi_in:duration",
                                                        )
                                                    },
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        input_unit="m/s",
                                                        default_value=np.nan,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                        _value=0.0,
                                                        _variable_name=None,
                                                    ),
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                {
                                    "reserve": {
                                        "multiplier": InputDefinition(
                                            parameter_name="multiplier",
                                            input_unit=None,
                                            default_value=np.nan,
                                            use_opposite=False,
                                            is_relative=False,
                                            _value=0.02,
                                            _variable_name=None,
                                        ),
                                        "ref": InputDefinition(
                                            parameter_name="ref",
                                            input_unit=None,
                                            default_value=np.nan,
                                            use_opposite=False,
                                            is_relative=False,
                                            _value="main",
                                            _variable_name=None,
                                        ),
                                    }
                                },
                            ],
                        ),
                    ]
                ),
            ),
        ]
    )
