"""
Test module for geometry functions of cg components
"""
#  This file is part of FAST-OAD_CS25
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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures

import os.path as pth

import pytest
import numpy as np
from fastoad._utils.testing import run_system
from fastoad.io import VariableIO
from scipy.optimize import fsolve

from ..speed_altitude_diagram import SpeedAltitudeDiagram


@pytest.fixture(scope="module")
def input_xml() -> VariableIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return VariableIO(pth.join(pth.dirname(__file__), "data", "data_post_processing.xml"))


def test_speed_altitude_diagram(input_xml):
    # Doit contenir toutes les entrees dont le modèle a besoin
    input_list = [
        "data:geometry:wing:area",
        "data:weight:aircraft:MTOW",
        "data:aerodynamics:aircraft:cruise:CL",
        "data:propulsion:rubber_engine:bypass_ratio",
        "data:propulsion:rubber_engine:overall_pressure_ratio",
        "data:propulsion:rubber_engine:turbine_inlet_temperature",
        "data:propulsion:MTO_thrust",
        "data:propulsion:rubber_engine:maximum_mach",
        "data:propulsion:rubber_engine:design_altitude",
        "data:aerodynamics:aircraft:cruise:CD"
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    expected_v_stall = np.array(
        [
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
            0.00789064,
        ]
    )

    problem = run_system(SpeedAltitudeDiagram(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars)
    assert problem["data:performance:speed_altitude_diagram:v_stall"] == pytest.approx(expected_v_stall, abs=1e-5)
