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
import openmdao.api as om
import numpy as np

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
from ..structure_nodes_wing import StructureNodesWing
from ..structure_nodes_htail import StructureNodesHtail
from ..structure_nodes_vtail import StructureNodesVtail


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
    assert (nodes[1, 1] - nodes[0, 1]) == approx(1.95994, abs=1e-5)
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


def test_wing_chords():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:leading_edge:x:local",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:root:z",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:kink:z",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:tip:z",
    ]

    ivc = get_indep_var_comp(input_list)
    group = om.Group()
    group.add_subsystem("WingNodes", AerodynamicNodesWing(number_of_sections=12), promotes=["*"])
    group.add_subsystem("WingChords", AerodynamicChordsWing(number_of_sections=12), promotes=["*"])

    problem = run_system(group, ivc)
    chord = problem["data:aerostructural:aerodynamic:wing:chords"]

    assert chord[0] == approx(6.20243, abs=1e-5)  # Check root chord
    assert chord[2] == approx(5.33890, abs=1e-5)  # Check intermediate inner chord
    assert chord[4] == approx(3.61186, abs=1e-5)  # Check kink chord
    assert chord[8] == approx(2.66513, abs=1e-5)  # Check intermediate outer chord
    assert chord[12] == approx(1.71840, abs=1e-5)  # Check tip chord
    assert chord[15] == approx(5.33890, abs=1e-5)  # Check symmetry intermediate inner chord
    assert chord[21] == approx(2.66513, abs=1e-5)  # Check symmetry intermediate outer chord


def test_htail_chords():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:horizontal_tail:MAC:length",
        "data:geometry:horizontal_tail:MAC:at25percent:x:local",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_0",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
    ]

    ivc = get_indep_var_comp(input_list)
    group = om.Group()
    group.add_subsystem("HtailNodes", AerodynamicNodesHtail(number_of_sections=12), promotes=["*"])
    group.add_subsystem(
        "HtailChords", AerodynamicChordsHtail(number_of_sections=12), promotes=["*"]
    )
    problem = run_system(group, ivc)
    chord = problem["data:aerostructural:aerodynamic:horizontal_tail:chords"]

    assert chord[0] == approx(4.40580, abs=1e-5)  # Check root chord
    assert chord[6] == approx(2.86377, abs=1e-5)  # Check intermediate chord
    assert chord[12] == approx(1.32174, abs=1e-5)  # Check tip chord
    assert chord[19] == approx(2.86377, abs=1e-5)  # Check symmetry intermediate chord


def test_vtail_chords():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:vertical_tail:MAC:at25percent:x:local",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:MAC:length",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_0",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
    ]

    ivc = get_indep_var_comp(input_list)
    group = om.Group()
    group.add_subsystem("VtailNodes", AerodynamicNodesVtail(number_of_sections=12), promotes=["*"])
    group.add_subsystem(
        "VtailChords", AerodynamicChordsVtail(number_of_sections=12), promotes=["*"]
    )
    problem = run_system(group, ivc)
    chord = problem["data:aerostructural:aerodynamic:vertical_tail:chords"]

    assert chord[0] == approx(6.08571, abs=1e-5)  # Check root chord
    assert chord[6] == approx(3.95571, abs=1e-5)  # Check intermediate chord
    assert chord[12] == approx(1.82571, abs=1e-5)  # Check tip chord


def test_fuselage_chords():
    input_list = [
        "data:geometry:fuselage:maximum_height",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:length",
        "data:geometry:fuselage:rear_length",
    ]

    ivc = get_indep_var_comp(input_list)
    group = om.Group()
    group.add_subsystem("FuseNodes", AerodynamicNodesFuselage(), promotes=["*"])
    group.add_subsystem("FuseChords", AerodynamicChordsFuselage(), promotes=["*"])
    problem = run_system(group, ivc)
    chord = problem["data:aerostructural:aerodynamic:fuselage:chords"]

    assert chord[0] == approx(37.50736, abs=1e-5)  # Check centreline
    assert chord[1] == approx(30.19958, abs=1e-5)  # Check mid width line (rear cone)
    assert chord[2] == approx(15.99, abs=1e-5)  # Check max width line (rear cone + non-cyl front)
    assert chord[4] == approx(30.19958, abs=1e-5)  # Check symmetry mid width
    assert chord[7] == approx(37.50736, abs=1e-5)  # Check top mid height
    assert chord[8] == approx(30.60557, abs=1e-5)  # Check top max height (non-cyl front)
    assert chord[10] == approx(30.19958, abs=1e-5)  # Check bottom mid height (rear cone)
    assert chord[11] == approx(
        15.99, abs=1e-5
    )  # Check bottom max height (rear cone + non-cyl front)


def test_structure_wing_nodes():
    input_list = [
        "data:geometry:wing:span",
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:z",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:spar_ratio:front:root",
        "data:geometry:wing:spar_ratio:rear:root",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:z",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:spar_ratio:front:kink",
        "data:geometry:wing:spar_ratio:rear:kink",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:z",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:spar_ratio:front:tip",
        "data:geometry:wing:spar_ratio:rear:tip",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:leading_edge:x:local",
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(StructureNodesWing(number_of_sections=4), ivc)
    assert problem["data:aerostructural:structure:wing:nodes"][:5, 1] == approx(
        np.array([0.0, 1.95994, 7.0274095, 12.29797, 17.56852]), abs=1e-5
    )
    assert problem["data:aerostructural:structure:wing:nodes"][5:, 1] == approx(
        np.array([-0.0, -1.95994, -7.0274095, -12.29797, -17.56852]), abs=1e-5
    )
    assert problem["data:aerostructural:structure:wing:nodes"][:5, 0] == approx(
        np.array([14.94685, 14.94685, 16.89139, 19.210949, 21.53049]), abs=1e-5
    )


def test_structure_htail_nodes():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:horizontal_tail:MAC:at25percent:x:local",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:MAC:length",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_0",
        "data:geometry:horizontal_tail:root:z",
        "data:geometry:horizontal_tail:tip:z",
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(StructureNodesHtail(number_of_sections=4), ivc)
    assert problem["data:aerostructural:structure:horizontal_tail:nodes"][:5, 1] == approx(
        np.array([0.0, 1.5349, 3.06980, 4.6047, 6.1396]), abs=1e-5
    )
    assert problem["data:aerostructural:structure:horizontal_tail:nodes"][5:, 1] == approx(
        np.array([-0.0, -1.5349, -3.06980, -4.6047, -6.1396]), abs=1e-5
    )
    assert problem["data:aerostructural:structure:horizontal_tail:nodes"][:5, 0] == approx(
        np.array([34.59222, 35.21558, 35.83895, 36.46232, 37.08568]), abs=1e-5
    )


def test_structure_vtail_nodes():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:vertical_tail:sweep_0",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:MAC:at25percent:x:local",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(StructureNodesVtail(number_of_sections=4), ivc)
    assert problem["data:aerostructural:structure:vertical_tail:nodes"][:, 0] == approx(
        np.array([33.54314, 34.48496, 35.42679, 36.36861, 37.310437])
    )
    assert problem["data:aerostructural:structure:vertical_tail:nodes"][:, 2] == approx(
        np.array([2.02994, 3.75525, 5.48056, 7.20587, 8.93118])
    )
