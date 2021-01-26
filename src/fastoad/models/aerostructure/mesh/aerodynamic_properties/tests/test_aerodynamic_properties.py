"""
Test module for aerodynamic sections properties (chords, twist, t/c)
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

import openmdao.api as om
import os.path as pth

from ...nodes.aerodynamic_nodes_htail import AerodynamicNodesHtail
from ...nodes.aerodynamic_nodes_wing import AerodynamicNodesWing
from ...nodes.aerodynamic_nodes_vtail import AerodynamicNodesVtail
from ..aerodynamic_chords_htail import AerodynamicChordsHtail
from ..aerodynamic_chords_vtail import AerodynamicChordsVtail
from ..aerodynamic_chords_wing import AerodynamicChordsWing
from ..aerodynamic_twist_wing import AerodynamicTwistWing
from ..aerodynamic_thickness_ratios_wing import AerodynamicThicknessRatiosWing
from fastoad.io import VariableIO
from tests.testing_utilities import run_system

from pytest import approx


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "aerodynamic_prop_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


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


def test_wing_twist():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:root:twist",
        "data:geometry:wing:kink:twist",
        "data:geometry:wing:tip:twist",
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
    group.add_subsystem("WingChords", AerodynamicTwistWing(number_of_sections=12), promotes=["*"])
    problem = run_system(group, ivc)
    twist = problem["data:aerostructural:aerodynamic:wing:twist"]

    assert twist[0] == approx(3.5, abs=1e-5)  # Check root twist
    assert twist[2] == approx(2.5, abs=1e-5)  # Check intermediate inner twist
    assert twist[4] == approx(0.5, abs=1e-5)  # Check kink twist
    assert twist[10] == approx(0.35, abs=1e-5)  # Check intermediate outer twist
    assert twist[12] == approx(0.3, abs=1e-5)  # Check tip twist
    assert twist[:13] == approx(twist[13:], abs=1e-9)  # Check symmetry


def test_wing_thickness_ratio():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:tip:thickness_ratio",
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
    group.add_subsystem(
        "WingChords", AerodynamicThicknessRatiosWing(number_of_sections=12), promotes=["*"]
    )
    problem = run_system(group, ivc)
    t_c = problem["data:aerostructural:aerodynamic:wing:thickness_ratios"]

    assert t_c[0] == approx(0.15921, abs=1e-5)  # Check root twist
    assert t_c[2] == approx(0.14637, abs=1e-5)  # Check intermediate inner twist
    assert t_c[4] == approx(0.12069, abs=1e-5)  # Check kink twist
    assert t_c[10] == approx(0.11299, abs=1e-5)  # Check intermediate outer twist
    assert t_c[12] == approx(0.11042, abs=1e-5)  # Check tip twist
    assert t_c[:13] == approx(t_c[13:], abs=1e-9)  # Check symmetry
