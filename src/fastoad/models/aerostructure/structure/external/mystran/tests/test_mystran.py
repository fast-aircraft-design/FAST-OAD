#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from fastoad.io import VariableIO
from tests.testing_utilities import run_system
from ..mystran_static import MystranStatic


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mystran_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_simple_wing():
    input_list = [
        "data:aerostructural:structure:wing:nodes",
        "data:aerostructural:structure:wing:forces",
        "data:geometry:wing:MAC:at25percent:x",
        "data:aerostructural:load_case:load_factor",
        "data:aerostructural:structure:wing:beam_properties",
        "data:aerostructural:structure:wing:material:E",
        "data:aerostructural: structure:wing:material:mu",
        "data:aerostructural:structure:wing:material:density",
    ]
    test_displacements = np.zeros((8, 6))
    test_displacements[:, 2] = np.array(
        [0.0, 2.223793e-1, 7.814701e-1, 1.511161, 0.0, 2.223793e-1, 7.814701e-1, 1.511161]
    )
    test_displacements[:, 3] = np.array(
        [0.0, 8.359426e-2, 1.345050e-1, 1.516548e-1, 0.0, -8.359426e-2, -1.345050e-1, -1.516548e-1]
    )
    ivc = get_indep_var_comp(input_list)
    problem = run_system(
        MystranStatic(structural_components=["wing"], structural_components_sections=[3]), ivc
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"], test_displacements, rtol=1e-3
    )


def test_strut_braced_wing():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:aerostructural:load_case:load_factor",
        "data:aerostructural:structure:wing:material:E",
        "data:aerostructural: structure:wing:material:mu",
        "data:aerostructural:structure:wing:material:density",
        "data:aerostructural:structure:strut:nodes",
        "data:aerostructural:structure:strut:forces",
        "data:aerostructural:structure:strut:beam_properties",
        "data:aerostructural:structure:strut:material:E",
        "data:aerostructural:structure:strut:material:mu",
        "data:aerostructural:structure:strut:material:density",
    ]
    nodes_wing_strut = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 5.0, 0.0],
            [1.0, 10.0, 0.0],
            [1.0, 12.5, 0.0],
            [1.0, 15.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, -5.0, 0.0],
            [1.0, -10.0, 0.0],
            [1.0, -12.5, 0.0],
            [1.0, -15.0, 0.0],
        ]
    )
    forces_wing_strut = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
        ]
    )
    props_wing_strut = np.array(
        [
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
        ]
    )
    test_displacements_wing = np.zeros((10, 6))
    test_displacements_wing[:, 1] = np.array(
        [
            0.0,
            -1.921505e-3,
            -3.843009e-3,
            -4.803762e-3,
            -4.803762e-3,
            0.0,
            1.921505e-3,
            3.843009e-3,
            4.803762e-3,
            4.803762e-3,
        ]
    )
    test_displacements_wing[:, 2] = np.array(
        [
            0.0,
            5.378144e-3,
            3.368895e-2,
            6.114170e-2,
            1.009775e-1,
            0.0,
            5.378144e-3,
            3.368895e-2,
            6.114170e-2,
            1.009775e-1,
        ]
    )
    test_displacements_wing[:, 3] = np.array(
        [
            0.0,
            2.804969e-3,
            8.993496e-3,
            1.305357e-2,
            1.737469e-2,
            0.0,
            -2.804969e-3,
            -8.993496e-3,
            -1.305357e-2,
            -1.737469e-2,
        ]
    )
    test_displacements_strut = np.zeros((8, 6))
    test_displacements_strut[:, 1] = np.array(
        [
            [
                0.0,
                1.126011e-3,
                -1.395019e-3,
                -4.803762e-3,
                0.0,
                -1.126011e-3,
                1.395019e-3,
                4.803762e-3,
            ]
        ]
    )
    test_displacements_strut[:, 2] = np.array(
        [[0.0, 5.402987e-3, 3.360894e-2, 6.114170e-2, 0.0, 5.402987e-3, 3.360894e-2, 6.114170e-2]]
    )
    test_displacements_strut[:, 3] = np.array(
        [
            [
                0.0,
                2.713916e-3,
                8.936931e-3,
                1.305357e-2,
                0.0,
                -2.713916e-3,
                -8.936931e-3,
                -1.305357e-2,
            ]
        ]
    )
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:forces", forces_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:beam_properties", props_wing_strut)
    problem = run_system(
        MystranStatic(
            structural_components=["wing", "strut"], structural_components_sections=[4, 3],
        ),
        ivc,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"],
        test_displacements_wing,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:strut:displacements"],
        test_displacements_strut,
        rtol=1e-3,
        atol=1e-5,
    )


def test_complete_aircraft():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:aerostructural:load_case:load_factor",
        "data:aerostructural:structure:wing:material:E",
        "data:aerostructural: structure:wing:material:mu",
        "data:aerostructural:structure:wing:material:density",
        "data:aerostructural:structure:strut:nodes",
        "data:aerostructural:structure:strut:forces",
        "data:aerostructural:structure:strut:beam_properties",
        "data:aerostructural:structure:strut:material:E",
        "data:aerostructural:structure:strut:material:mu",
        "data:aerostructural:structure:strut:material:density",
        "data:aerostructural:structure:horizontal_tail:nodes",
        "data:aerostructural:structure:horizontal_tail:forces",
        "data:aerostructural:structure:horizontal_tail:beam_properties",
        "data:aerostructural:structure:horizontal_tail:material:E",
        "data:aerostructural:structure:horizontal_tail:material:mu",
        "data:aerostructural:structure:horizontal_tail:material:density",
        "data:aerostructural:structure:vertical_tail:nodes",
        "data:aerostructural:structure:vertical_tail:forces",
        "data:aerostructural:structure:vertical_tail:beam_properties",
        "data:aerostructural:structure:vertical_tail:material:E",
        "data:aerostructural:structure:vertical_tail:material:mu",
        "data:aerostructural:structure:vertical_tail:material:density",
    ]
    nodes_wing_strut = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 5.0, 0.0],
            [1.0, 10.0, 0.0],
            [1.0, 12.5, 0.0],
            [1.0, 15.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, -5.0, 0.0],
            [1.0, -10.0, 0.0],
            [1.0, -12.5, 0.0],
            [1.0, -15.0, 0.0],
        ]
    )
    forces_wing_strut = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
        ]
    )
    props_wing_strut = np.array(
        [
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
        ]
    )
    test_displacements_wing = np.zeros((10, 6))
    test_displacements_wing[:, 1] = np.array(
        [
            0.0,
            -1.921505e-3,
            -3.843009e-3,
            -4.803762e-3,
            -4.803762e-3,
            0.0,
            1.921505e-3,
            3.843009e-3,
            4.803762e-3,
            4.803762e-3,
        ]
    )
    test_displacements_wing[:, 2] = np.array(
        [
            0.0,
            5.378144e-3,
            3.368895e-2,
            6.114170e-2,
            1.009775e-1,
            0.0,
            5.378144e-3,
            3.368895e-2,
            6.114170e-2,
            1.009775e-1,
        ]
    )
    test_displacements_wing[:, 3] = np.array(
        [
            0.0,
            2.804969e-3,
            8.993496e-3,
            1.305357e-2,
            1.737469e-2,
            0.0,
            -2.804969e-3,
            -8.993496e-3,
            -1.305357e-2,
            -1.737469e-2,
        ]
    )
    test_displacements_strut = np.zeros((8, 6))
    test_displacements_strut[:, 1] = np.array(
        [
            [
                0.0,
                1.126011e-3,
                -1.395019e-3,
                -4.803762e-3,
                0.0,
                -1.126011e-3,
                1.395019e-3,
                4.803762e-3,
            ]
        ]
    )
    test_displacements_strut[:, 2] = np.array(
        [[0.0, 5.402987e-3, 3.360894e-2, 6.114170e-2, 0.0, 5.402987e-3, 3.360894e-2, 6.114170e-2]]
    )
    test_displacements_strut[:, 3] = np.array(
        [
            [
                0.0,
                2.713916e-3,
                8.936931e-3,
                1.305357e-2,
                0.0,
                -2.713916e-3,
                -8.936931e-3,
                -1.305357e-2,
            ]
        ]
    )
    test_displacements_vtp = np.zeros((3, 6))
    test_displacements_htp = np.zeros((6, 6))
    test_displacements_htp[:, 2] = np.array(
        [0.0, -4.339697e-4, -1.310141e-3, 0.0, -4.339697e-4, -1.310141e-3]
    )
    test_displacements_htp[:, 3] = np.array(
        [0.0, -2.989905e-4, -3.762077e-4, 0.0, 2.989905e-4, 3.762077e-4]
    )
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:forces", forces_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:beam_properties", props_wing_strut)
    problem = run_system(
        MystranStatic(
            structural_components=["wing", "strut", "horizontal_tail", "vertical_tail"],
            structural_components_sections=[4, 3, 2, 2],
        ),
        ivc,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"],
        test_displacements_wing,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:strut:displacements"],
        test_displacements_strut,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:horizontal_tail:displacements"],
        test_displacements_htp,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:vertical_tail:displacements"],
        test_displacements_vtp,
        rtol=1e-3,
        atol=1e-5,
    )


def test_complete_aircraft_vertical_strut():
    input_list = [
        "data:geometry:wing:MAC:at25percent:x",
        "data:aerostructural:load_case:load_factor",
        "data:aerostructural:structure:wing:material:E",
        "data:aerostructural: structure:wing:material:mu",
        "data:aerostructural:structure:wing:material:density",
        "data:aerostructural:structure:strut:material:E",
        "data:aerostructural:structure:strut:material:mu",
        "data:aerostructural:structure:strut:material:density",
        "data:aerostructural:structure:horizontal_tail:nodes",
        "data:aerostructural:structure:horizontal_tail:forces",
        "data:aerostructural:structure:horizontal_tail:beam_properties",
        "data:aerostructural:structure:horizontal_tail:material:E",
        "data:aerostructural:structure:horizontal_tail:material:mu",
        "data:aerostructural:structure:horizontal_tail:material:density",
        "data:aerostructural:structure:vertical_tail:nodes",
        "data:aerostructural:structure:vertical_tail:forces",
        "data:aerostructural:structure:vertical_tail:beam_properties",
        "data:aerostructural:structure:vertical_tail:material:E",
        "data:aerostructural:structure:vertical_tail:material:mu",
        "data:aerostructural:structure:vertical_tail:material:density",
    ]
    nodes_wing_strut = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 5.0, 0.0],
            [1.0, 10.0, 0.0],
            [1.0, 12.5, 0.0],
            [1.0, 15.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, -5.0, 0.0],
            [1.0, -10.0, 0.0],
            [1.0, -12.5, 0.0],
            [1.0, -15.0, 0.0],
        ]
    )
    forces_wing_strut = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 100000.0, 0.0, 0.0, 0.0],
        ]
    )
    props_wing_strut = np.array(
        [
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
        ]
    )
    nodes_strut = np.array(
        [
            [1.0, 0.0, -2.0],
            [1.0, 5.0, -1.8],
            [1.0, 10.0, -1.0],
            [1.0, 12.5, -0.6],
            [1.0, 12.5, -0.0],
            [1.0, 0.0, -2.0],
            [1.0, -5.0, -1.8],
            [1.0, -10.0, -1.0],
            [1.0, -12.5, -0.6],
            [1.0, -12.5, -0.0],
        ]
    )
    forces_strut = np.zeros((10, 6))
    props_strut = np.array(
        [
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
            [0.02268, 9.196e-4, 8.802e-3, 2.763e-3, 0.05, 0.5, -0.05, 0.5, -0.05, -0.5, 0.05, -0.5],
        ]
    )
    test_displacements_wing = np.zeros((10, 6))
    test_displacements_wing[:, 1] = np.array(
        [
            0.0,
            -1.50351e-3,
            -3.007032e-3,
            -3.758790e-3,
            -3.758790e-3,
            0.0,
            1.50351e-3,
            3.007032e-3,
            3.758790e-3,
            3.758790e-3,
        ]
    )
    test_displacements_wing[:, 2] = np.array(
        [
            0.0,
            1.324824e-2,
            4.057894e-2,
            5.269606e-2,
            6.994236e-2,
            0.0,
            1.324824e-2,
            4.057894e-2,
            5.269606e-2,
            6.994236e-2,
        ]
    )
    test_displacements_wing[:, 3] = np.array(
        [
            0.0,
            4.723487e-3,
            5.453415e-3,
            4.017770e-3,
            8.338895e-3,
            0.0,
            -4.723487e-3,
            -5.453415e-3,
            -4.017770e-3,
            -8.338895e-3,
        ]
    )
    test_displacements_strut = np.zeros((10, 6))
    test_displacements_strut[:, 1] = np.array(
        [
            [
                0.0,
                6.066109e-4,
                -1.407311e-3,
                -1.854932e-3,
                -3.758790e-3,
                0.0,
                -6.066109e-4,
                1.407311e-3,
                1.854932e-3,
                3.758790e-3,
            ]
        ]
    )
    test_displacements_strut[:, 2] = np.array(
        [
            [
                0.0,
                2.266691e-2,
                4.499611e-2,
                5.266820e-2,
                5.269606e-2,
                0.0,
                2.266691e-2,
                4.499611e-2,
                5.266820e-2,
                5.269606e-2,
            ]
        ]
    )
    test_displacements_strut[:, 3] = np.array(
        [
            [
                0.0,
                5.878086e-3,
                3.324686e-3,
                2.773204e-3,
                4.017770e-3,
                0.0,
                -5.878086e-3,
                -3.324686e-3,
                -2.773204e-3,
                -4.017770e-3,
            ]
        ]
    )
    test_displacements_vtp = np.zeros((3, 6))
    test_displacements_htp = np.zeros((6, 6))
    test_displacements_htp[:, 2] = np.array(
        [0.0, -4.339697e-4, -1.310141e-3, 0.0, -4.339697e-4, -1.310141e-3]
    )
    test_displacements_htp[:, 3] = np.array(
        [0.0, -2.989905e-4, -3.762077e-4, 0.0, 2.989905e-4, 3.762077e-4]
    )
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:aerostructural:structure:wing:nodes", nodes_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:forces", forces_wing_strut)
    ivc.add_output("data:aerostructural:structure:wing:beam_properties", props_wing_strut)
    ivc.add_output("data:aerostructural:structure:strut:nodes", nodes_strut)
    ivc.add_output("data:aerostructural:structure:strut:forces", forces_strut)
    ivc.add_output("data:aerostructural:structure:strut:beam_properties", props_strut)
    problem = run_system(
        MystranStatic(
            structural_components=["wing", "strut", "horizontal_tail", "vertical_tail"],
            structural_components_sections=[4, 4, 2, 2],
            has_vertical_strut=True,
        ),
        ivc,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"],
        test_displacements_wing,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:strut:displacements"],
        test_displacements_strut,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:horizontal_tail:displacements"],
        test_displacements_htp,
        rtol=1e-3,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:vertical_tail:displacements"],
        test_displacements_vtp,
        rtol=1e-3,
        atol=1e-5,
    )
