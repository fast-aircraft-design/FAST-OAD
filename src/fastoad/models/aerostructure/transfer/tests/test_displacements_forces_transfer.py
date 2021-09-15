"""
Test of transfer matrix, displacements and forces transfer groups
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
from ..displacements_transfer import DisplacementsTransfer
from ..forces_transfer import ForcesTransfer
from ..transfer_matrices import TransferMatrices


def _test_matrix(n_points, delta_x):
    test_mat = np.zeros((n_points * 3, n_points * 6))
    for i in range(n_points):
        test_mat[i * 3 : i * 3 + 3, i * 6 : i * 6 + 3] = np.identity(3)
        test_mat[i * 3 : i * 3 + 3, i * 6 + 3 : i * 6 + 6] = np.array(
            [[0.0, 0.0, 0.0], [0.0, 0.0, delta_x], [0.0, -delta_x, 0.0]]
        )
    return test_mat


def _test_displacements(n_points, delta_x):
    disp = np.zeros((n_points, 3))
    for i in range(n_points):
        disp[i, :] = np.array([1, 1 + delta_x, 1 - delta_x])
    return disp


def _test_forces(n_points, delta_x, delta_y, delta_z):
    forces = np.zeros((n_points, 6))
    for i in range(n_points):
        forces[i, :3] = 1
        forces[i, 3] = delta_y - delta_z
        forces[i, 4] = -delta_x + delta_z
        forces[i, 5] = delta_x - delta_y
    forces[n_points - 1, :] = 0.0
    return forces


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "transfer_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_transfer_matrices():
    comps = ["wing", "horizontal_tail", "vertical_tail", "fuselage"]
    sects = [5, 5, 5, 4]
    interp = ["linear", "linear", "linear", "rigid"]

    #  Rectangular wing and surfaces geometry from inputs file
    input_list = [
        "data:aerostructural:structure:wing:nodes",
        "data:aerostructural:structure:horizontal_tail:nodes",
        "data:aerostructural:structure:vertical_tail:nodes",
        "data:aerostructural:structure:fuselage:nodes",
        "data:aerostructural:aerodynamic:wing:nodes",
        "data:aerostructural:aerodynamic:horizontal_tail:nodes",
        "data:aerostructural:aerodynamic:vertical_tail:nodes",
        "data:aerostructural:aerodynamic:fuselage:nodes",
    ]
    ivc = get_indep_var_comp(input_list)

    problem = run_system(
        TransferMatrices(
            coupled_components=comps,
            aerodynamic_components_sections=sects,
            structural_components_sections=sects,
            coupled_components_interpolations=interp,
        ),
        ivc,
    )
    t_mat_wing = problem["data:aerostructural:transfer:wing:matrix"]
    t_mat_htp = problem["data:aerostructural:transfer:horizontal_tail:matrix"]
    t_mat_vtp = problem["data:aerostructural:transfer:vertical_tail:matrix"]
    t_mat_fuse = problem["data:aerostructural:transfer:fuselage:matrix"]
    assert t_mat_wing == approx(_test_matrix(12, 2.0), abs=1e-5)
    assert t_mat_htp == approx(_test_matrix(12, 1.0), abs=1e-5)
    assert t_mat_vtp == approx(_test_matrix(6, 1.0), abs=1e-5)
    assert t_mat_fuse == approx(np.zeros((36, 30)), abs=1e-5)


def test_displacements_transfer():
    comps = ["wing", "horizontal_tail", "vertical_tail"]
    nb_sections = [5, 5, 5]

    input_list = [
        "data:aerostructural:aerodynamic:wing:nodes",
        "data:aerostructural:aerodynamic:horizontal_tail:nodes",
        "data:aerostructural:aerodynamic:vertical_tail:nodes",
        "data:aerostructural:structure:wing:nodes",
        "data:aerostructural:structure:horizontal_tail:nodes",
        "data:aerostructural:structure:vertical_tail:nodes",
    ]

    ivc = get_indep_var_comp(input_list)

    # Transfer matrices
    t_mat_wing = _test_matrix(12, 2.0)
    t_mat_htp = _test_matrix(12, 1.0)
    t_mat_vtp = _test_matrix(6, 1.0)
    ivc.add_output("data:aerostructural:transfer:wing:matrix", val=t_mat_wing)
    ivc.add_output("data:aerostructural:transfer:horizontal_tail:matrix", val=t_mat_htp)
    ivc.add_output("data:aerostructural:transfer:vertical_tail:matrix", val=t_mat_vtp)

    #  Unitary displacements
    disp_wing = np.ones((12, 6))
    disp_htp = np.ones((12, 6))
    disp_vtp = np.ones((6, 6))
    ivc.add_output("data:aerostructural:structure:wing:displacements", val=disp_wing)
    ivc.add_output("data:aerostructural:structure:horizontal_tail:displacements", val=disp_htp)
    ivc.add_output("data:aerostructural:structure:vertical_tail:displacements", val=disp_vtp)

    problem = run_system(
        DisplacementsTransfer(
            coupled_components=comps, aerodynamic_components_sections=nb_sections
        ),
        ivc,
    )
    assert problem["data:aerostructural:aerodynamic:wing:displacements"] == approx(
        _test_displacements(12, 2.0), abs=1e-5
    )
    assert problem["data:aerostructural:aerodynamic:horizontal_tail:displacements"] == approx(
        _test_displacements(12, 1.0), abs=1e-5
    )
    assert problem["data:aerostructural:aerodynamic:vertical_tail:displacements"] == approx(
        _test_displacements(6, 1.0), abs=1e-5
    )


def test_forces_transfer():
    comps = ["wing", "horizontal_tail", "vertical_tail"]
    sects = [5, 5, 5]

    #  Rectangular wing and surfaces geometry from inputs file
    input_list = [
        "data:aerostructural:structure:wing:nodes",
        "data:aerostructural:structure:horizontal_tail:nodes",
        "data:aerostructural:structure:vertical_tail:nodes",
        "data:aerostructural:aerodynamic:wing:nodes",
        "data:aerostructural:aerodynamic:horizontal_tail:nodes",
        "data:aerostructural:aerodynamic:vertical_tail:nodes",
        "data:geometry:wing:MAC:at25percent:x",
    ]
    ivc = get_indep_var_comp(input_list)

    #  Unitary forces
    f_a_wing = np.hstack((np.ones((10, 3)), np.zeros((10, 3))))
    f_a_htp = np.hstack((np.ones((10, 3)), np.zeros((10, 3))))
    f_a_vtp = np.hstack((np.ones((5, 3)), np.zeros((5, 3))))

    ivc.add_output("data:aerostructural:aerodynamic:wing:forces", val=f_a_wing)
    ivc.add_output("data:aerostructural:aerodynamic:horizontal_tail:forces", val=f_a_htp)
    ivc.add_output("data:aerostructural:aerodynamic:vertical_tail:forces", val=f_a_vtp)

    problem = run_system(
        ForcesTransfer(coupled_components=comps, structural_components_sections=sects), ivc
    )

    f_s_wing = problem["data:aerostructural:structure:wing:forces"]
    f_s_htp = problem["data:aerostructural:structure:horizontal_tail:forces"]
    f_s_vtp = problem["data:aerostructural:structure:vertical_tail:forces"]

    assert f_s_wing[:6, :] == approx(_test_forces(6, -1.0, 1.5, 0.0))
    assert f_s_htp[:6, :] == approx(_test_forces(6, -17.0, 0.5, 0.0))
    assert f_s_vtp == approx(_test_forces(6, -16.0, 0.0, 0.5))
