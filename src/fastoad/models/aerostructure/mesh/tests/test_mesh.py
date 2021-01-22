"""
Test for aerodynamic and structural mesh computations
"""
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

import os.path as pth
import openmdao.api as om
import numpy as np

import pytest
from pytest import approx
from fastoad.io import VariableIO
from tests.testing_utilities import run_system
from ..aerodynamic_mesh import AerodynamicMesh
from ..structure_mesh import StructureMesh


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mesh_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_aerodynamic_mesh():
    input_list = [
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:leading_edge:x:local",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:z",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:z",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:z",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:root:twist",
        "data:geometry:wing:kink:twist",
        "data:geometry:wing:tip:twist",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:horizontal_tail:MAC:at25percent:x:local",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:MAC:length",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_0",
        "data:geometry:horizontal_tail:root:z",
        "data:geometry:horizontal_tail:tip:z",
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry:vertical_tail:MAC:at25percent:x:local",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:MAC:length",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_0",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:rear_length",
        "data:geometry:fuselage:length",
    ]

    ivc = get_indep_var_comp(input_list)
    comps = ["wing", "fuselage", "horizontal_tail", "vertical_tail"]
    sections = [12, 12, 12, 12]
    problem = run_system(AerodynamicMesh(components=comps, components_sections=sections), ivc)
    wing_nodes = problem["data:aerostructural:aerodynamic:wing:nodes"]
    htp_nodes = problem["data:aerostructural:aerodynamic:horizontal_tail:nodes"]
    vtp_nodes = problem["data:aerostructural:aerodynamic:vertical_tail:nodes"]

    assert np.size(wing_nodes, axis=0) == approx(26, abs=1)
    assert np.size(htp_nodes, axis=0) == approx(26, abs=1)
    assert np.size(vtp_nodes, axis=0) == approx(13, abs=1)
    assert np.size(wing_nodes, axis=1) == approx(3, abs=1)
    assert np.size(htp_nodes, axis=1) == approx(3, abs=1)
    assert np.size(vtp_nodes, axis=1) == approx(3, abs=1)

    sections = [24, 12, 10, 5]
    problem = run_system(AerodynamicMesh(components=comps, components_sections=sections), ivc)
    wing_nodes = problem["data:aerostructural:aerodynamic:wing:nodes"]
    htp_nodes = problem["data:aerostructural:aerodynamic:horizontal_tail:nodes"]
    vtp_nodes = problem["data:aerostructural:aerodynamic:vertical_tail:nodes"]

    assert np.size(wing_nodes, axis=0) == approx(50, abs=1)
    assert np.size(htp_nodes, axis=0) == approx(22, abs=1)
    assert np.size(vtp_nodes, axis=0) == approx(6, abs=1)
