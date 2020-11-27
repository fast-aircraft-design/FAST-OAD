"""
Test module for aerostructural groups
"""
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

import os.path as pth
from platform import system

import pytest
from pytest import approx

from fastoad.io import VariableIO
from tests.testing_utilities import run_system
from ..aerodynamic_nodes_htail import AerodynamicNodesHtail
from ..aerodynamic_nodes_wing import AerodynamicNodesWing
from ..aerodynamic_nodes_vtail import AerodynamicNodesVtail
from ..aerodynamic_nodes_fuselage import AerodynamicNodesFuselage
from ..aerodynamic_chords_htail import AerodynamicChordsHtail
from ..aerodynamic_chords_vtail import AerodynamicChordsVtail
from ..aerodynamic_chords_wing import AerodynamicChordsWing
from ..aerodynamic_chords_fuselage import AerodynamicChordsFuselage


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mesh_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_wing_nodes():
    """ Test Aerodynamic wing nodes mesh generation """
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
    ]

    ivc = get_indep_var_comp(input_list)
    component = AerodynamicNodesWing(number_of_sections=12)
    problem = run_system(component, ivc)
    nodes = problem["data:aerostructural:aerodynamic:wing:nodes"]

    assert nodes[0, 0] == approx(12.83803, abs=1e-5)
    assert nodes[12, 0] == approx(20.81736, abs=1e-5)
    assert (nodes[1, 1] - nodes[0, 1]) == approx(1.26687, abs=1e-5)
    assert (nodes[5, 1] - nodes[4, 1]) == approx(1.31764, abs=1e-5)


def test_htail_nodes():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:horizontal_tail:MAC:length",
        "data:geometry:horizontal_tail:MAC:at25percent:x:local",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_0",
    ]

    ivc = get_indep_var_comp(input_list)

    component = AerodynamicNodesHtail(number_of_sections=12)
    problem = run_system(component, ivc)
    nodes = problem["data:aerostructural:aerodynamic:horizontal_tail:nodes"]

    assert nodes[0, 0] == approx(31.60418, abs=1e-5)
    assert nodes[12, 0] == approx(35.63968, abs=1e-5)
    assert (nodes[5, 1] - nodes[4, 1]) == approx(0.51163, abs=1e-5)


def test_vtail_nodes():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:vertical_tail:MAC:at25percent:x:local",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:MAC:length",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_0",
        "data:geometry:fuselage:maximum_height",
    ]

    ivc = get_indep_var_comp(input_list)
    component = AerodynamicNodesVtail(number_of_sections=12)
    problem = run_system(component, ivc)
    nodes = problem["data:aerostructural:aerodynamic:vertical_tail:nodes"]

    assert nodes[0, 0] == approx(29.41577, abs=1e-5)
    assert nodes[-1, 0] == approx(35.31307, abs=1e-5)
    assert nodes[5, 2] - nodes[4, 2] == approx(0.57510, abs=1e-5)
    assert nodes[-1, 2] == approx(8.93118, abs=1e-5)
