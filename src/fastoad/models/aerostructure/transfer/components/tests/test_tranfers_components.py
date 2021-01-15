"""
Test for forces and displacement transfer at component level
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
import numpy as np


from pytest import approx
from tests.testing_utilities import run_system
from ..component_displacements import ComponentDisplacements
from ..component_forces import ComponentForces
from ..component_matrix import ComponentMatrix


def test_transfer_matrix():
    """
    Test transfer matrix generation. First for a rectangular wing, then a swept one.
    :return:
    """
    ivc = om.IndepVarComp()

    #  Rectangular wing
    n_s = np.array(
        [
            [16.0, 2.0, 0.0],
            [16.0, 5.0, 0.0],
            [16.0, 8.0, 0.0],
            [16.0, 11.0, 0.0],
            [16.0, 14.0, 0.0],
            [16.0, 17.0, 0.0],
            [16.0, -2.0, 0.0],
            [16.0, -5.0, 0.0],
            [16.0, -8.0, 0.0],
            [16.0, -11.0, 0.0],
            [16.0, -14.0, 0.0],
            [16.0, -17.0, 0.0],
        ]
    )
    n_a = np.array(
        [
            [14.0, 2.0, 0.0],
            [14.0, 5.0, 0.0],
            [14.0, 8.0, 0.0],
            [14.0, 11.0, 0.0],
            [14.0, 14.0, 0.0],
            [14.0, 17.0, 0.0],
            [14.0, -2.0, 0.0],
            [14.0, -5.0, 0.0],
            [14.0, -8.0, 0.0],
            [14.0, -11.0, 0.0],
            [14.0, -14.0, 0.0],
            [14.0, -17.0, 0.0],
        ]
    )
    ivc.add_output("data:aerostructural:structure:wing:nodes", val=n_s)
    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    comp = "wing"
    n_sects = 5
    problem = run_system(ComponentMatrix(component=comp, number_of_sections=n_sects), ivc)
    t_mat = problem["data:aerostructural:transfer:wing:matrix"]
    for idx in range(n_sects):
        assert t_mat[idx * 3, idx * 6] == approx(1.0)
        assert t_mat[idx * 3 + 1, idx * 6 + 1] == approx(1.0)
        assert t_mat[idx * 3 + 2, idx * 6 + 2] == approx(1.0)
        assert t_mat[idx * 3 + 1, idx * 6 + 5] == approx(2.0)
        assert t_mat[idx * 3 + 2, idx * 6 + 4] == approx(-2.0)

    #  Swept back wing

    n_s = np.array(
        [
            [16.0, 2.0, 0.0],
            [17.5, 5.0, 0.0],
            [19.0, 8.0, 0.0],
            [20.5, 11.0, 0.0],
            [22.0, 14.0, 0.0],
            [23.5, 17.0, 0.0],
            [16.0, -2.0, 0.0],
            [17.5, -5.0, 0.0],
            [19.0, -8.0, 0.0],
            [20.5, -11.0, 0.0],
            [22.0, -14.0, 0.0],
            [23.5, -17.0, 0.0],
        ]
    )
    n_a = np.array(
        [
            [14.0, 2.0, 0.0],
            [15.5, 5.0, 0.0],
            [17.0, 8.0, 0.0],
            [18.5, 11.0, 0.0],
            [20.0, 14.0, 0.0],
            [21.5, 17.0, 0.0],
            [14.0, -2.0, 0.0],
            [15.5, -5.0, 0.0],
            [17.0, -8.0, 0.0],
            [18.5, -11.0, 0.0],
            [20.0, -14.0, 0.0],
            [21.5, -17.0, 0.0],
        ]
    )
    ivc = om.IndepVarComp()
    ivc.add_output("data:aerostructural:structure:wing:nodes", val=n_s)
    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    comp = "wing"
    n_sects = 5
    problem = run_system(ComponentMatrix(component=comp, number_of_sections=n_sects), ivc)
    t_mat = problem["data:aerostructural:transfer:wing:matrix"]
    for idx in range(1, n_sects + 1):
        assert t_mat[idx * 3, idx * 6] == approx(0.73333, abs=1e-5)
        assert t_mat[idx * 3 + 1, idx * 6 + 1] == approx(0.73333, abs=1e-5)
        assert t_mat[idx * 3 + 2, idx * 6 + 2] == approx(0.73333, abs=1e-5)
        assert t_mat[idx * 3, idx * 6 + 5] == approx(0.58666, abs=1e-5)
        assert t_mat[idx * 3 + 1, idx * 6 + 5] == approx(1.17333, abs=1e-5)
        assert t_mat[idx * 3 + 2, idx * 6 + 3] == approx(-0.58666, abs=1e-5)
        assert t_mat[idx * 3 + 2, idx * 6 + 4] == approx(-1.17333, abs=1e-5)
        if idx < n_sects:
            assert t_mat[(idx + 1) * 3, idx * 6] == approx(0.26666, abs=1e-5)
            assert t_mat[(idx + 1) * 3 + 1, idx * 6 + 1] == approx(0.26666, abs=1e-5)
            assert t_mat[(idx + 1) * 3 + 2, idx * 6 + 2] == approx(0.26666, abs=1e-5)
            assert t_mat[(idx + 1) * 3, idx * 6 + 5] == approx(0.21333, abs=1e-5)
            assert t_mat[(idx + 1) * 3 + 1, idx * 6 + 5] == approx(0.42666, abs=1e-5)
            assert t_mat[(idx + 1) * 3 + 2, idx * 6 + 3] == approx(-0.21333, abs=1e-5)
            assert t_mat[(idx + 1) * 3 + 2, idx * 6 + 4] == approx(-0.42666, abs=1e-5)


def test_displacement_transfer():
    """
    Test displacements transfer from structure to aerodynamic at component level
    Test is only run for wings as other surfaces rely on the same method
    and same transfer formulation.
    :return:
    """
    #  Rectangular wing
    ivc = om.IndepVarComp()
    disp_s = np.ones((12, 6))  #  Unitary displacements
    t_mat = np.zeros((36, 72))
    idx = np.linspace(0, 12, dtype=int, endpoint=False, num=12)
    for i in idx:
        for j in [0, 1, 2]:
            t_mat[i * 3 + j, i * 6 + j] = 1
        t_mat[i * 3 + 1, i * 6 + 5] = 2
        t_mat[i * 3 + 2, i * 6 + 4] = -2
    n_a = np.array(
        [
            [14.0, 2.0, 0.0],
            [15.5, 5.0, 0.0],
            [17.0, 8.0, 0.0],
            [18.5, 11.0, 0.0],
            [20.0, 14.0, 0.0],
            [21.5, 17.0, 0.0],
            [14.0, -2.0, 0.0],
            [15.5, -5.0, 0.0],
            [17.0, -8.0, 0.0],
            [18.5, -11.0, 0.0],
            [20.0, -14.0, 0.0],
            [21.5, -17.0, 0.0],
        ]
    )
    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    ivc.add_output("data:aerostructural:structure:wing:displacements", val=disp_s)
    ivc.add_output("data:aerostructural:transfer:wing:matrix", val=t_mat)
    problem = run_system(ComponentDisplacements(component="wing"), ivc)
    disp_a = problem["data:aerostructural:aerodynamic:wing:displacements"]
    for line in disp_a:
        assert line[0] == approx(1.0, abs=1e-5)
        assert line[1] == approx(3.0, abs=1e-5)
        assert line[2] == approx(-1, abs=1e-5)

    #  Swept wing

    ivc = om.IndepVarComp()
    disp_s = np.ones((12, 6))  # Unitary displacements
    t_mat = np.zeros((36, 72))
    idx = np.linspace(0, 12, dtype=int, endpoint=False, num=12)
    #  Analytic transfer matrix
    for i in idx:
        for j in [0, 1, 2]:
            if i not in [0, 6]:
                t_mat[i * 3 + j, i * 6 + j] = 0.733333
            else:
                t_mat[i * 3 + j, i * 6 + j] = 1
            if i not in [5, 11]:
                t_mat[(i + 1) * 3 + j, i * 6 + j] = 0.266666
        if i not in [0, 6]:
            t_mat[i * 3 + 1, i * 6 + 5] = 1.173333
            t_mat[i * 3 + 2, i * 6 + 3] = -0.586666
            t_mat[i * 3 + 2, i * 6 + 4] = -1.173333
            t_mat[i * 3, i * 6 + 5] = 0.586666
        else:
            t_mat[i * 3 + 1, i * 6 + 5] = 2
            t_mat[i * 3 + 2, i * 6 + 4] = -2
        if i not in [5, 11]:
            t_mat[(i + 1) * 3 + 1, i * 6 + 5] = 0.426666
            t_mat[(i + 1) * 3 + 2, i * 6 + 3] = -0.213333
            t_mat[(i + 1) * 3 + 2, i * 6 + 4] = -0.426666
            t_mat[(i + 1) * 3, i * 6 + 5] = 0.213333

    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    ivc.add_output("data:aerostructural:structure:wing:displacements", val=disp_s)
    ivc.add_output("data:aerostructural:transfer:wing:matrix", val=t_mat)
    problem = run_system(ComponentDisplacements(component="wing"), ivc)
    disp_a = problem["data:aerostructural:aerodynamic:wing:displacements"]
    for idx, line in enumerate(disp_a):
        if idx not in [0, 6]:
            assert line[0] == approx(1.8, abs=1e-5)
            assert line[1] == approx(2.6, abs=1e-5)
            assert line[2] == approx(-1.4, abs=1e-5)


def test_forces_transfer():
    """
    Test forces transfer from aerodynamic to structure at component level
    Test is only perform for wings as other surfaces rely on the same method
    and transfer formulation.
    :return:
    """

    # Rectangular wing

    ivc = om.IndepVarComp()
    n_s = np.array(
        [
            [16.0, 2.0, 0.0],
            [16.0, 5.0, 0.0],
            [16.0, 8.0, 0.0],
            [16.0, 11.0, 0.0],
            [16.0, 14.0, 0.0],
            [16.0, 17.0, 0.0],
            [16.0, -2.0, 0.0],
            [16.0, -5.0, 0.0],
            [16.0, -8.0, 0.0],
            [16.0, -11.0, 0.0],
            [16.0, -14.0, 0.0],
            [16.0, -17.0, 0.0],
        ]
    )
    n_a = np.array(
        [
            [14.0, 2.0, 0.0],
            [14.0, 5.0, 0.0],
            [14.0, 8.0, 0.0],
            [14.0, 11.0, 0.0],
            [14.0, 14.0, 0.0],
            [14.0, 17.0, 0.0],
            [14.0, -2.0, 0.0],
            [14.0, -5.0, 0.0],
            [14.0, -8.0, 0.0],
            [14.0, -11.0, 0.0],
            [14.0, -14.0, 0.0],
            [14.0, -17.0, 0.0],
        ]
    )
    f_a = np.hstack((np.ones((10, 3)), np.zeros((10, 3))))  #  Unitary forces
    f_a[5:10, 1] = -1.0  # symmetrisation
    ivc.add_output("data:aerostructural:structure:wing:nodes", val=n_s)
    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    ivc.add_output("data:aerostructural:aerodynamic:wing:forces", val=f_a)
    ivc.add_output("data:geometry:wing:MAC:at25percent:x", val=15.0)
    problem = run_system(ComponentForces(component="wing", number_of_sections=5), ivc)
    f_s = problem["data:aerostructural:structure:wing:forces"]
    for idx, line in enumerate(f_s[:6, :]):
        if idx not in (0, 5):
            for i in [0, 1, 2, 4]:
                assert line[i] == approx(1.0, abs=1e-5)
            assert line[5] == approx(-1, abs=1e-5)
        else:
            for i in [0, 1, 2]:
                assert line[i] == approx(0.5, abs=1e-5)
            assert line[4] == approx(0.5, abs=1e-5)
            if idx == 0:
                assert line[5] == approx(-1.25, abs=1e-5)
            else:
                assert line[5] == approx(0.25, abs=1e-5)
    for idx, line in enumerate(f_s[6:, :]):
        if idx not in (0, 5):
            for i in [0, 2, 4, 5]:
                assert line[i] == approx(1.0, abs=1e-5)
            assert line[1] == approx(-1, abs=1e-5)
        else:
            for i in [0, 2]:
                assert line[i] == approx(0.5, abs=1e-5)
            assert line[1] == approx(-0.5, abs=1e-5)
            assert line[4] == approx(0.5, abs=1e-5)
            if idx == 0:
                assert line[5] == approx(1.25, abs=1e-5)
            else:
                assert line[5] == approx(-0.25, abs=1e-5)

    #  Swept wing
    ivc = om.IndepVarComp()
    n_s = np.array(
        [
            [16.0, 2.0, 0.0],
            [17.5, 5.0, 0.0],
            [19.0, 8.0, 0.0],
            [20.5, 11.0, 0.0],
            [22.0, 14.0, 0.0],
            [23.5, 17.0, 0.0],
            [16.0, -2.0, 0.0],
            [17.5, -5.0, 0.0],
            [19.0, -8.0, 0.0],
            [20.5, -11.0, 0.0],
            [22.0, -14.0, 0.0],
            [23.5, -17.0, 0.0],
        ]
    )
    n_a = np.array(
        [
            [14.0, 2.0, 0.0],
            [15.5, 5.0, 0.0],
            [17.0, 8.0, 0.0],
            [18.5, 11.0, 0.0],
            [20.0, 14.0, 0.0],
            [21.5, 17.0, 0.0],
            [14.0, -2.0, 0.0],
            [15.5, -5.0, 0.0],
            [17.0, -8.0, 0.0],
            [18.5, -11.0, 0.0],
            [20.0, -14.0, 0.0],
            [21.5, -17.0, 0.0],
        ]
    )
    f_a = np.hstack((np.ones((10, 3)), np.zeros((10, 3))))  # Unitary forces
    f_a[5:10, 1] = -1.0  # symmetrisation
    ivc.add_output("data:aerostructural:structure:wing:nodes", val=n_s)
    ivc.add_output("data:aerostructural:aerodynamic:wing:nodes", val=n_a)
    ivc.add_output("data:aerostructural:aerodynamic:wing:forces", val=f_a)
    ivc.add_output("data:geometry:wing:MAC:at25percent:x", val=15.0)
    problem = run_system(ComponentForces(component="wing", number_of_sections=5), ivc)
    f_s = problem["data:aerostructural:structure:wing:forces"]
    assert f_s[:6, 0] == approx(np.array([0.5, 1.0, 1.0, 1.0, 1.0, 0.5]), abs=1e-5)
    assert f_s[:6, 1] == approx(np.array([0.5, 1.0, 1.0, 1.0, 1.0, 0.5]), abs=1e-5)
    assert f_s[:6, 2] == approx(np.array([0.5, 1.0, 1.0, 1.0, 1.0, 0.5]), abs=1e-5)
    assert f_s[6:, 0] == approx(np.array([0.5, 1.0, 1.0, 1.0, 1.0, 0.5]), abs=1e-5)
    assert f_s[6:, 1] == approx(np.array([-0.5, -1.0, -1.0, -1.0, -1.0, -0.5]), abs=1e-5)
    assert f_s[6:, 2] == approx(np.array([0.5, 1.0, 1.0, 1.0, 1.0, 0.5]), abs=1e-5)
    assert f_s[:6, 4] == approx(np.array([0.5, 2.5, 4.0, 5.5, 7.0, 4.25]), abs=1e-5)
    assert f_s[:6, 5] == approx(np.array([-1.25, -2.5, -4.0, -5.5, -7.0, -3.5]), abs=1e-5)
