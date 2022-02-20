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
from ..exceptions import FastMissionFileMissingMissionNameError
from ..mission_builder import InputDefinition, MissionBuilder
from ..schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_input_definition_units():
    inp1 = InputDefinition("anything", value=1.0, unit="km")
    assert inp1.value == 1.0

    inp1.default_unit = "m"
    assert inp1.value == 1000.0

    # When parameter name is known, its default unit is automatically set.
    inp2 = InputDefinition("ground_distance", value=1.0, unit="km")
    assert inp2.value == 1000.0
    assert not inp2.is_relative

    inp3 = InputDefinition("delta_time", value=1.0, unit="h")
    assert inp3.parameter_name == "time"
    assert inp3.is_relative

    assert inp3.value == 3600.0


def test_initialization():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    assert mission_builder._structure == OrderedDict(
        [
            (
                "sizing",
                OrderedDict(
                    [
                        (
                            "mission",
                            InputDefinition(
                                parameter_name="mission",
                                value="sizing",
                                unit=None,
                                default_value=None,
                                variable_name=None,
                                use_opposite=False,
                                is_relative=False,
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
                                                value="main",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                value="data:mission:sizing:main:range",
                                                unit="m",
                                                default_value=None,
                                                variable_name="data:mission:sizing:main:range",
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                value=500,
                                                unit="m",
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
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
                                                                value="initial_climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="takeoff",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": InputDefinition(
                                                                    parameter_name="CD",
                                                                    value=[0.0, 0.03, 0.12],
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name=None,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                                "CL": InputDefinition(
                                                                    parameter_name="CL",
                                                                    value=[0.0, 0.5, 1.0],
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name=None,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                            },
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value=1.0,
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=400.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                                                    value="data:aerodynamics:aircraft:takeoff:CL",
                                                                                    unit=None,
                                                                                    default_value=None,
                                                                                    variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                InputDefinition(
                                                                                    parameter_name="CD",
                                                                                    value="data:aerodynamics:aircraft:takeoff:CD",
                                                                                    unit=None,
                                                                                    default_value=None,
                                                                                    variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=250,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:takeoff:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "CL": InputDefinition(
                                                                            parameter_name="CL",
                                                                            value="data:aerodynamics:aircraft:takeoff:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=1500.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                                value="climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value="data:propulsion:climb:thrust_rate",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:propulsion:climb:thrust_rate",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="data:TLAR:cruise_mach",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:TLAR:cruise_mach",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=-20000.0,
                                                                            unit="m",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="constant",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                    value="cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                value="data:aerodynamics:aircraft:cruise:CL",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                value="data:aerodynamics:aircraft:cruise:CD",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    value="optimal_cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
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
                                                                value="descent",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="idle",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value="data:propulsion:descent:thrust_rate",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:propulsion:descent:thrust_rate",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="constant",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=250.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value="data:mission:sizing:main:descent:final_altitude",
                                                                            unit="m",
                                                                            default_value=None,
                                                                            variable_name="data:mission:sizing:main:descent:final_altitude",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                value="diversion",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                value="data:mission:sizing:diversion:range",
                                                unit="m",
                                                default_value=None,
                                                variable_name="data:mission:sizing:diversion:range",
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                value=0.1,
                                                unit="km",
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
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
                                                                value="diversion_climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value=0.93,
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "time_step",
                                                            InputDefinition(
                                                                parameter_name="time_step",
                                                                value=5.0,
                                                                unit="s",
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=22000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                    value="cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                value="data:aerodynamics:aircraft:cruise:CL",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                value="data:aerodynamics:aircraft:cruise:CD",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    value="cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
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
                                                                value="descent",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="idle",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value="data:propulsion:descent:thrust_rate",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:propulsion:descent:thrust_rate",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="constant",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=250.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value="data:mission:sizing:diversion:descent:final_altitude",
                                                                            unit="m",
                                                                            default_value=None,
                                                                            variable_name="data:mission:sizing:diversion:descent:final_altitude",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                value="holding",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
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
                                                                    value="data:aerodynamics:aircraft:cruise:CL",
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                            ),
                                                            (
                                                                "CD",
                                                                InputDefinition(
                                                                    parameter_name="CD",
                                                                    value="data:aerodynamics:aircraft:cruise:CD",
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                            ),
                                                        ]
                                                    ),
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        value="holding",
                                                        unit=None,
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            value="data:mission:sizing:holding:duration",
                                                            unit="s",
                                                            default_value=None,
                                                            variable_name="data:mission:sizing:holding:duration",
                                                            use_opposite=False,
                                                            is_relative=True,
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
                                                value="taxi_in",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "thrust_rate",
                                            InputDefinition(
                                                parameter_name="thrust_rate",
                                                value="data:mission:sizing:taxi_in:thrust_rate",
                                                unit=None,
                                                default_value=None,
                                                variable_name="data:mission:sizing:taxi_in:thrust_rate",
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        value="taxi",
                                                        unit=None,
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            value="data:mission:sizing:taxi_in:duration",
                                                            unit="s",
                                                            default_value=None,
                                                            variable_name="data:mission:sizing:taxi_in:duration",
                                                            use_opposite=False,
                                                            is_relative=True,
                                                        )
                                                    },
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        value=0.0,
                                                        unit="m/s",
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
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
                                            value=0.03,
                                            unit=None,
                                            default_value=None,
                                            variable_name=None,
                                            use_opposite=False,
                                            is_relative=False,
                                        ),
                                        "ref": InputDefinition(
                                            parameter_name="ref",
                                            value="main",
                                            unit=None,
                                            default_value=None,
                                            variable_name=None,
                                            use_opposite=False,
                                            is_relative=False,
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
                                value="operational",
                                unit=None,
                                default_value=None,
                                variable_name=None,
                                use_opposite=False,
                                is_relative=False,
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
                                                value="taxi_out",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        value="taxi",
                                                        unit=None,
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            value="data:mission:operational:taxi_out:duration",
                                                            unit="s",
                                                            default_value=None,
                                                            variable_name="data:mission:operational:taxi_out:duration",
                                                            use_opposite=False,
                                                            is_relative=True,
                                                        )
                                                    },
                                                    "thrust_rate": InputDefinition(
                                                        parameter_name="thrust_rate",
                                                        value="data:mission:operational:taxi_out:thrust_rate",
                                                        unit=None,
                                                        default_value=None,
                                                        variable_name="data:mission:operational:taxi_out:thrust_rate",
                                                        use_opposite=False,
                                                        is_relative=False,
                                                    ),
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        value=0.0,
                                                        unit="m/s",
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
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
                                                value="main",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "range",
                                            InputDefinition(
                                                parameter_name="range",
                                                value="data:mission:operational:main:range",
                                                unit="m",
                                                default_value=None,
                                                variable_name="data:mission:operational:main:range",
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "distance_accuracy",
                                            InputDefinition(
                                                parameter_name="distance_accuracy",
                                                value=500,
                                                unit="m",
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
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
                                                                value="initial_climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="takeoff",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": InputDefinition(
                                                                    parameter_name="CD",
                                                                    value=[0.0, 0.03, 0.12],
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name=None,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                                "CL": InputDefinition(
                                                                    parameter_name="CL",
                                                                    value=[0.0, 0.5, 1.0],
                                                                    unit=None,
                                                                    default_value=None,
                                                                    variable_name=None,
                                                                    use_opposite=False,
                                                                    is_relative=False,
                                                                ),
                                                            },
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value=1.0,
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=400.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                                                    value="data:aerodynamics:aircraft:takeoff:CL",
                                                                                    unit=None,
                                                                                    default_value=None,
                                                                                    variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                InputDefinition(
                                                                                    parameter_name="CD",
                                                                                    value="data:aerodynamics:aircraft:takeoff:CD",
                                                                                    unit=None,
                                                                                    default_value=None,
                                                                                    variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                                    use_opposite=False,
                                                                                    is_relative=False,
                                                                                ),
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=250,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:takeoff:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:takeoff:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "CL": InputDefinition(
                                                                            parameter_name="CL",
                                                                            value="data:aerodynamics:aircraft:takeoff:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:takeoff:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=1500.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                                value="climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="climb",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value="data:propulsion:climb:thrust_rate",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:propulsion:climb:thrust_rate",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="data:TLAR:cruise_mach",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:TLAR:cruise_mach",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=-20000.0,
                                                                            unit="m",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="constant",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                    value="cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
                                                ),
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            InputDefinition(
                                                                parameter_name="CL",
                                                                value="data:aerodynamics:aircraft:cruise:CL",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "CD",
                                                            InputDefinition(
                                                                parameter_name="CD",
                                                                value="data:aerodynamics:aircraft:cruise:CD",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                "segment": InputDefinition(
                                                    parameter_name="segment",
                                                    value="optimal_cruise",
                                                    unit=None,
                                                    default_value=None,
                                                    variable_name=None,
                                                    use_opposite=False,
                                                    is_relative=False,
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
                                                                value="descent",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "engine_setting",
                                                            InputDefinition(
                                                                parameter_name="engine_setting",
                                                                value="idle",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name=None,
                                                                use_opposite=False,
                                                                is_relative=False,
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
                                                                            value="data:aerodynamics:aircraft:cruise:CL",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CL",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        InputDefinition(
                                                                            parameter_name="CD",
                                                                            value="data:aerodynamics:aircraft:cruise:CD",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name="data:aerodynamics:aircraft:cruise:CD",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            InputDefinition(
                                                                parameter_name="thrust_rate",
                                                                value="data:propulsion:descent:thrust_rate",
                                                                unit=None,
                                                                default_value=None,
                                                                variable_name="data:propulsion:descent:thrust_rate",
                                                                use_opposite=False,
                                                                is_relative=False,
                                                            ),
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=300,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "mach": InputDefinition(
                                                                            parameter_name="mach",
                                                                            value="constant",
                                                                            unit=None,
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value=10000.0,
                                                                            unit="ft",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="speed_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value=250.0,
                                                                            unit="kn",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        )
                                                                    },
                                                                },
                                                                {
                                                                    "segment": InputDefinition(
                                                                        parameter_name="segment",
                                                                        value="altitude_change",
                                                                        unit=None,
                                                                        default_value=None,
                                                                        variable_name=None,
                                                                        use_opposite=False,
                                                                        is_relative=False,
                                                                    ),
                                                                    "target": {
                                                                        "altitude": InputDefinition(
                                                                            parameter_name="altitude",
                                                                            value="data:mission:operational:main:descent:final_altitude",
                                                                            unit="m",
                                                                            default_value=None,
                                                                            variable_name="data:mission:operational:main:descent:final_altitude",
                                                                            use_opposite=False,
                                                                            is_relative=False,
                                                                        ),
                                                                        "equivalent_airspeed": InputDefinition(
                                                                            parameter_name="equivalent_airspeed",
                                                                            value="constant",
                                                                            unit="m/s",
                                                                            default_value=None,
                                                                            variable_name=None,
                                                                            use_opposite=False,
                                                                            is_relative=False,
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
                                                value="taxi_in",
                                                unit=None,
                                                default_value=None,
                                                variable_name=None,
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "thrust_rate",
                                            InputDefinition(
                                                parameter_name="thrust_rate",
                                                value="data:mission:operational:taxi_in:thrust_rate",
                                                unit=None,
                                                default_value=None,
                                                variable_name="data:mission:operational:taxi_in:thrust_rate",
                                                use_opposite=False,
                                                is_relative=False,
                                            ),
                                        ),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": InputDefinition(
                                                        parameter_name="segment",
                                                        value="taxi",
                                                        unit=None,
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
                                                    ),
                                                    "target": {
                                                        "delta_time": InputDefinition(
                                                            parameter_name="time",
                                                            value="data:mission:operational:taxi_in:duration",
                                                            unit="s",
                                                            default_value=None,
                                                            variable_name="data:mission:operational:taxi_in:duration",
                                                            use_opposite=False,
                                                            is_relative=True,
                                                        )
                                                    },
                                                    "true_airspeed": InputDefinition(
                                                        parameter_name="true_airspeed",
                                                        value=0.0,
                                                        unit="m/s",
                                                        default_value=None,
                                                        variable_name=None,
                                                        use_opposite=False,
                                                        is_relative=False,
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
                                            value=0.02,
                                            unit=None,
                                            default_value=None,
                                            variable_name=None,
                                            use_opposite=False,
                                            is_relative=False,
                                        ),
                                        "ref": InputDefinition(
                                            parameter_name="ref",
                                            value="main",
                                            unit=None,
                                            default_value=None,
                                            variable_name=None,
                                            use_opposite=False,
                                            is_relative=False,
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


def test_inputs():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )
    with pytest.raises(FastMissionFileMissingMissionNameError):
        mission_builder.get_input_variables()

    assert mission_builder.get_input_variables("sizing") == {
        "data:TLAR:cruise_mach": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CL": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CL": (None, "Input defined by the mission."),
        "data:mission:sizing:diversion:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:sizing:diversion:range": ("m", "Input defined by the mission."),
        "data:mission:sizing:holding:duration": ("s", "Input defined by the mission."),
        "data:mission:sizing:main:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:sizing:main:range": ("m", "Input defined by the mission."),
        "data:mission:sizing:taxi_in:duration": ("s", "Input defined by the mission."),
        "data:mission:sizing:taxi_in:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:climb:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:descent:thrust_rate": (None, "Input defined by the mission."),
    }
    assert mission_builder.get_input_variables("operational") == {
        "data:TLAR:cruise_mach": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CL": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CL": (None, "Input defined by the mission."),
        "data:mission:operational:main:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:operational:main:range": ("m", "Input defined by the mission."),
        "data:mission:operational:taxi_in:duration": ("s", "Input defined by the mission."),
        "data:mission:operational:taxi_in:thrust_rate": (None, "Input defined by the mission."),
        "data:mission:operational:taxi_out:duration": ("s", "Input defined by the mission."),
        "data:mission:operational:taxi_out:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:climb:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:descent:thrust_rate": (None, "Input defined by the mission."),
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
