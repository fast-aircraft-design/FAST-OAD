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
import plotly
import plotly.graph_objects as go
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
        "data:aerodynamics:aircraft:cruise:CD",
        "data:aerodynamics:aircraft:landing:CL_max_clean"
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    expected_v_min = np.array(
        [77.18234811, 77.63599466, 78.09357142, 78.55512347, 79.02069651,
         79.4903369, 79.96409165, 80.44200849, 80.92413578, 81.41052263,
         81.90121884, 82.39627495, 82.89574221, 83.39967265, 83.90811905,
         84.42113497, 84.93877477, 85.46109361, 85.98814745, 86.51999312,
         87.05668828, 87.59829144, 88.14486202, 88.69646033, 89.25314756,
         89.81498587, 90.38203834, 90.95436903, 91.53204296, 92.11512616,
         92.70368568, 93.29778961, 93.89750707, 94.50290828, 95.11406453,
         95.73104826, 96.35393301, 96.9827935, 97.61770561, 98.25874644,
         98.90599429, 99.55952874,100.21943062,100.88578204,101.55866647,
         102.23816868, 102.92437486, 103.61737255, 104.31725075, 105.02409989]
    )

    expected_v_max = np.array(
        [274.12559654,  273.20557056,  272.24596139,  271.23221257,  270.16172495,
         269.02435625,  267.80279079,  266.48719043,  265.07339343,  263.54463461,
         261.88868924,  260.10603589,  258.17144995,  256.09135484,  253.84611214,
         251.43890588,  248.84953426,  246.08613967,  243.13331096,  239.98444622,
         236.63907261,  233.08869289,  229.32418445,  225.33544568,  221.11097442,
         216.62083793,  211.849006,  206.73931655,199.816497, 190.93046232,
         180.76512191,  166.57651838,  158.12179024,  159.18574879,  160.19237479,
         161.27536557,  162.21258323,  163.53636155,  164.40046104,  165.5489149,
         31.00585816, - 177.44327045,  168.997043,  169.8262961,  170.99272184,
         172.3410293,  173.4030226, 174.39985932,175.75737366,  177.22599971]
    )



    problem = run_system(SpeedAltitudeDiagram(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars)
    assert problem["data:performance:speed_altitude_diagram:v_min"] == pytest.approx(expected_v_min, abs=1e-5)
    assert problem["data:performance:speed_altitude_diagram:v_max"] == pytest.approx(expected_v_max, abs=1e-5)
