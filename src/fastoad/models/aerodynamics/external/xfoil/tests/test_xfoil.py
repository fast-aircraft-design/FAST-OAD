"""
Test module for XFOIL component
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

# pylint: disable=redefined-outer-name  # needed for fixtures

import os.path as pth
import shutil

import pytest
from openmdao.core.indepvarcomp import IndepVarComp

from tests.testing_utilities import run_system
from .. import XfoilPolar

XFOIL_RESULTS = pth.join(pth.dirname(__file__), 'results')


def test_compute():
    """ Tests a simple XFOIL run"""

    if pth.exists(XFOIL_RESULTS):
        shutil.rmtree(XFOIL_RESULTS)

    ivc = IndepVarComp()
    ivc.add_output('xfoil:reynolds', 18000000)
    ivc.add_output('xfoil:mach', 0.20)
    ivc.add_output('data:geometry:wing:sweep_25', 25.)
    ivc.add_output('data:geometry:wing:thickness_ratio', 0.1284)

    xfoil_comp = XfoilPolar(alpha_start=15., alpha_end=25.)
    problem = run_system(xfoil_comp, ivc)
    assert problem['xfoil:Cl_max_2D'] == pytest.approx(1.94, 1e-2)
    assert problem['xfoil:CL_max_clean'] == pytest.approx(1.58, 1e-2)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(alpha_start=12., alpha_end=20.)  # will stop before real max CL
    problem = run_system(xfoil_comp, ivc)
    assert problem['xfoil:Cl_max_2D'] == pytest.approx(1.92, 1e-2)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(result_folder_path=XFOIL_RESULTS)
    problem = run_system(xfoil_comp, ivc)
    assert problem['xfoil:Cl_max_2D'] == pytest.approx(1.94, 1e-2)
    assert problem['xfoil:CL_max_clean'] == pytest.approx(1.58, 1e-2)
    assert pth.exists(XFOIL_RESULTS)
    assert pth.exists(pth.join(XFOIL_RESULTS, 'polar_result.txt'))


def test_compute_with_provided_path():
    """ Test that option "use_exe_path" works """
    ivc = IndepVarComp()
    ivc.add_output('xfoil:reynolds', 18000000)
    ivc.add_output('xfoil:mach', 0.20)
    ivc.add_output('data:geometry:wing:sweep_25', 25.)
    ivc.add_output('data:geometry:wing:thickness_ratio', 0.1284)

    xfoil_comp = XfoilPolar(alpha_start=18., alpha_end=21.)
    xfoil_comp.options['xfoil_exe_path'] = 'Dummy'  # bad name
    with pytest.raises(ValueError):
        problem = run_system(xfoil_comp, ivc)

    xfoil_comp.options['xfoil_exe_path'] = pth.join(pth.dirname(__file__),
                                                    pth.pardir,
                                                    'xfoil699',
                                                    'xfoil.exe')
    problem = run_system(xfoil_comp, ivc)
    assert problem['xfoil:Cl_max_2D'] == pytest.approx(1.94, 1e-2)
    assert problem['xfoil:CL_max_clean'] == pytest.approx(1.58, 1e-2)
