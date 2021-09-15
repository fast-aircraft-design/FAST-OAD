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


import os.path as pth

import numpy as np
from pytest import approx

from fastoad.io import VariableIO
from tests.testing_utilities import run_system
from ..structure_beam_htail import HtailBeamProps
from ..structure_beam_vtail import VtailBeamProps
from ..structure_beam_wing import WingBeamProps


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

    assert a[[0, 4, 11]] == approx(np.array([0.03831, 0.02268, 0.00877]), abs=1e-5)
    assert a[:12] == approx(a[12:], abs=1e-9)
    assert i1[[0, 4, 11]] == approx(np.array([7.6639e-3, 9.196e-4, 8.52e-05]), abs=1e-7)
    assert i1[:12] == approx(i1[12:], abs=1e-9)
    assert i2[[0, 4, 11]] == approx(np.array([3.9178e-2, 8.802e-3, 4.77e-4]), abs=1e-6)
    assert i2[:12] == approx(i2[12:], abs=1e-9)
    assert j[[0, 4, 11]] == approx(np.array([2.0442e-2, 2.763e-3, 2.32e-4]), abs=1e-6)
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
    assert i1[[0, 4, 11]] == approx(np.array([1.5479e-3, 1.878e-4, 1.78e-05]), abs=1e-7)
    assert i2[[0, 4, 11]] == approx(np.array([7.879e-3, 1.777e-3, 9.8e-5]), abs=1e-6)
    assert j[[0, 4, 11]] == approx(np.array([4.125e-3, 5.63e-4, 4.8e-5]), abs=1e-6)


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
    assert a[[0, 4, 11]] == approx(np.array([0.03891, 0.02328, 0.00937]), abs=1e-5)
    assert i1[[0, 4, 11]] == approx(np.array([7.8102e-3, 9.481e-4, 9.25e-05]), abs=1e-7)
    assert i2[[0, 4, 11]] == approx(np.array([4.1620e-2, 9.8205e-3, 6.10e-4]), abs=1e-6)
    assert j[[0, 4, 11]] == approx(np.array([2.0442e-2, 2.763e-3, 2.32e-4]), abs=1e-6)


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

    assert a[:2] == approx(np.array([2.633e-2, 1.708e-2]), abs=1e-5)
    assert i1[:2] == approx(np.array([1.111e-3, 3.01e-4]), abs=1e-6)
    assert i2[:2] == approx(np.array([1.4109e-2, 3.853e-3]), abs=1e-6)
    assert j[:2] == approx(np.array([3.48e-3, 9.44e-4]), abs=1e-6)


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
    assert a[:2] == approx(np.array([3.6414e-2, 2.3634e-2]), abs=1e-5)
    assert i1[:2] == approx(np.array([2.950e-3, 8.02e-4]), abs=1e-6)
    assert i2[:2] == approx(np.array([3.7288e-2, 1.0199e-2]), abs=1e-6)
    assert j[:2] == approx(np.array([9.233e-3, 2.512e-3]), abs=1e-6)
