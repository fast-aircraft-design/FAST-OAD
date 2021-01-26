"""
Test module for structure beam properties computation
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


import openmdao.api as om
import os.path as pth
import numpy as np

from fastoad.io import VariableIO
from ..structure_beam_wing import WingBeamProps
from ..structure_beam_htail import HtailBeamProps
from ..structure_beam_vtail import VtailBeamProps
from tests.testing_utilities import run_system

from pytest import approx


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "beam_props_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_wing_props_no_spar_no_thickness():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:spar_ratio:front:root",
        "data:geometry:wing:spar_ratio:rear:root",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:spar_ratio:front:kink",
        "data:geometry:wing:spar_ratio:rear:kink",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:spar_ratio:front:tip",
        "data:geometry:wing:spar_ratio:rear:tip",
    ]
    ivc = get_indep_var_comp(input_list)

    nodes = np.zeros((26, 3))
    y = np.hstack(
        (
            np.array([0.0]),
            np.linspace(1.95994, 7.0274095, 3, endpoint=False),
            np.linspace(7.0274095, 17.5685238, 9),
        )
    )
    nodes[:, 1] = np.tile(y, 2)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes)

    problem = run_system(WingBeamProps(number_of_sections=12), ivc)
    a = problem["data:aerostructural:structure:wing:beam_properties"][:, 0]
    i1 = problem["data:aerostructural:structure:wing:beam_properties"][:, 1]
    i2 = problem["data:aerostructural:structure:wing:beam_properties"][:, 2]
    j = problem["data:aerostructural:structure:wing:beam_properties"][:, 3]

    assert a[[0, 4, 11]] == approx(np.array([0.03841, 0.02278, 0.00887]), abs=1e-5)
    assert a[:12] == approx(a[12:], abs=1e-9)
    assert i1[[0, 4, 11]] == approx(np.array([7.7583e-3, 9.4418e-4, 8.9943e-05]), abs=1e-7)
    assert i1[:12] == approx(i1[12:], abs=1e-9)
    assert i2[[0, 4, 11]] == approx(np.array([3.9451e-2, 8.9066e-3, 4.9127e-4]), abs=1e-6)
    assert i2[:12] == approx(i2[12:], abs=1e-9)
    assert j[[0, 4, 11]] == approx(np.array([2.0669e-2, 2.830e-3, 2.43e-4]), abs=1e-6)
    assert j[:12] == approx(j[12:], abs=1e-9)


def test_wing_props_no_spar():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:root:skin_thickness",
        "data:geometry:wing:root:web_thickness",
        "data:geometry:wing:spar_ratio:front:root",
        "data:geometry:wing:spar_ratio:rear:root",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:kink:skin_thickness",
        "data:geometry:wing:kink:web_thickness",
        "data:geometry:wing:spar_ratio:front:kink",
        "data:geometry:wing:spar_ratio:rear:kink",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:tip:skin_thickness",
        "data:geometry:wing:tip:web_thickness",
        "data:geometry:wing:spar_ratio:front:tip",
        "data:geometry:wing:spar_ratio:rear:tip",
    ]
    ivc = get_indep_var_comp(input_list)

    nodes = np.zeros((26, 3))
    y = np.hstack(
        (
            np.array([0.0]),
            np.linspace(1.95994, 7.0274095, 3, endpoint=False),
            np.linspace(7.0274095, 17.5685238, 9),
        )
    )
    nodes[:, 1] = np.tile(y, 2)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes)
    ivc.add_output("data:geometry:wing:tip:skin_thickness", val=0.001)
    ivc.add_output("data:geometry:wing:tip:web_thickness", val=0.001)
    ivc.add_output("data:geometry:wing:kink:skin_thickness", val=0.001)
    ivc.add_output("data:geometry:wing:kink:web_thickness", val=0.001)
    ivc.add_output("data:geometry:wing:root:skin_thickness", val=0.001)
    ivc.add_output("data:geometry:wing:root:web_thickness", val=0.001)

    problem = run_system(WingBeamProps(number_of_sections=12), ivc)
    a = problem["data:aerostructural:structure:wing:beam_properties"][:, 0]
    i1 = problem["data:aerostructural:structure:wing:beam_properties"][:, 1]
    i2 = problem["data:aerostructural:structure:wing:beam_properties"][:, 2]
    j = problem["data:aerostructural:structure:wing:beam_properties"][:, 3]
    assert a[[0, 4, 11]] == approx(np.array([7.682e-3, 4.556e-3, 1.774e-3]), abs=1e-5)
    assert i1[[0, 4, 11]] == approx(np.array([1.5517e-3, 1.8884e-4, 1.7987e-05]), abs=1e-7)
    assert i2[[0, 4, 11]] == approx(np.array([7.8902e-3, 1.7813e-3, 9.8254e-5]), abs=1e-6)
    assert j[[0, 4, 11]] == approx(np.array([4.1338e-3, 5.6600e-4, 4.86e-5]), abs=1e-6)


def test_wing_props_spar():
    input_list = [
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:root:skin_thickness",
        "data:geometry:wing:root:web_thickness",
        "data:geometry:wing:spar_ratio:front:root",
        "data:geometry:wing:spar_ratio:rear:root",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:kink:skin_thickness",
        "data:geometry:wing:kink:web_thickness",
        "data:geometry:wing:spar_ratio:front:kink",
        "data:geometry:wing:spar_ratio:rear:kink",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:tip:skin_thickness",
        "data:geometry:wing:tip:web_thickness",
        "data:geometry:wing:spar_ratio:front:tip",
        "data:geometry:wing:spar_ratio:rear:tip",
    ]
    ivc = get_indep_var_comp(input_list)

    nodes = np.zeros((26, 3))
    y = np.hstack(
        (
            np.array([0.0]),
            np.linspace(1.95994, 7.0274095, 3, endpoint=False),
            np.linspace(7.0274095, 17.5685238, 9),
        )
    )
    nodes[:, 1] = np.tile(y, 2)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes)
    ivc.add_output("settings:aerostructural:wing:n_spar", val=3)
    ivc.add_output("data:geometry:wing:spar_area", val=1e-4)

    problem = run_system(WingBeamProps(number_of_sections=12), ivc)
    a = problem["data:aerostructural:structure:wing:beam_properties"][:, 0]
    i1 = problem["data:aerostructural:structure:wing:beam_properties"][:, 1]
    i2 = problem["data:aerostructural:structure:wing:beam_properties"][:, 2]
    j = problem["data:aerostructural:structure:wing:beam_properties"][:, 3]
    assert a[[0, 4, 11]] == approx(np.array([0.03841, 0.02278, 0.00887]) + 6e-4, abs=1e-5)
    assert i1[[0, 4, 11]] == approx(np.array([7.9046e-3, 9.7269e-4, 9.7238e-05]), abs=1e-7)
    assert i2[[0, 4, 11]] == approx(np.array([4.1893e-2, 9.9245e-3, 6.2446e-4]), abs=1e-6)
    assert j[[0, 4, 11]] == approx(np.array([2.0669e-2, 2.830e-3, 2.43e-4]), abs=1e-6)


def test_htp_props():
    input_list = [
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry:horizontal_tail:thickness_ratio",
    ]
    ivc = get_indep_var_comp(input_list)

    nodes = np.zeros((6, 3))
    y = np.linspace(0.0, 6.13961, 3)
    nodes[:, 1] = np.tile(y, 2)
    ivc.add_output("data:aerostructural:structure:horizontal_tail:nodes", nodes)
    problem = run_system(HtailBeamProps(number_of_sections=2), ivc)
    a = problem["data:aerostructural:structure:horizontal_tail:beam_properties"][:, 0]
    i1 = problem["data:aerostructural:structure:horizontal_tail:beam_properties"][:, 1]
    i2 = problem["data:aerostructural:structure:horizontal_tail:beam_properties"][:, 2]
    j = problem["data:aerostructural:structure:horizontal_tail:beam_properties"][:, 3]

    assert a[:2] == approx(np.array([2.6435e-2, 1.7183e-2]), abs=1e-5)
    assert i1[:2] == approx(np.array([1.1403e-3, 3.1315e-4]), abs=1e-6)
    assert i2[:2] == approx(np.array([1.4254e-2, 3.9144e-3]), abs=1e-6)
    assert j[:2] == approx(np.array([3.5634e-3, 9.7860e-4]), abs=1e-6)


def test_vtp_props():
    input_list = [
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:vertical_tail:thickness_ratio",
        "data:geometry:vertical_tail:span",
        "data:geometry:fuselage:maximum_height",
    ]
    ivc = get_indep_var_comp(input_list)
    nodes = np.zeros((6, 3))
    z = np.linspace(2.02994, 8.93118, 3)
    nodes[:, 2] = np.tile(z, 2)
    ivc.add_output("data:aerostructural:structure:vertical_tail:nodes", nodes)
    problem = run_system(VtailBeamProps(number_of_sections=2), ivc)
    a = problem["data:aerostructural:structure:vertical_tail:beam_properties"][:, 0]
    i1 = problem["data:aerostructural:structure:vertical_tail:beam_properties"][:, 1]
    i2 = problem["data:aerostructural:structure:vertical_tail:beam_properties"][:, 2]
    j = problem["data:aerostructural:structure:vertical_tail:beam_properties"][:, 3]
    assert a[:2] == approx(np.array([3.6514e-2, 2.3734e-2]), abs=1e-5)
    assert i1[:2] == approx(np.array([3.0052e-3, 8.253e-4]), abs=1e-6)
    assert i2[:2] == approx(np.array([3.7565e-2, 1.0316e-2]), abs=1e-6)
    assert j[:2] == approx(np.array([9.3913e-3, 2.5791e-3]), abs=1e-6)
