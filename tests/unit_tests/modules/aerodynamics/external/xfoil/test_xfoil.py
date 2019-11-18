"""
Test module for XFOIL component
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from fastoad.modules.aerodynamics.external.xfoil import XfoilPolar
from tests.testing_utilities import run_system

XFOIL_RESULTS = pth.join(pth.dirname(__file__), 'results')
INPUT_PROFILE = pth.join(pth.dirname(__file__), 'data', 'BACJ-new.txt')


def test_compute():
    """ Tests a simple XFOIL run"""

    if pth.exists(XFOIL_RESULTS):
        shutil.rmtree(XFOIL_RESULTS)

    ivc = IndepVarComp()
    ivc.add_output('xfoil:reynolds', 18000000)
    ivc.add_output('xfoil:mach', 0.20)
    ivc.add_output('geometry:wing_sweep_25', 25.)

    xfoil_comp = XfoilPolar(profile_path=INPUT_PROFILE)
    problem = run_system(xfoil_comp, ivc)
    assert problem['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    assert problem['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(profile_path=INPUT_PROFILE, result_folder_path=XFOIL_RESULTS)
    problem = run_system(xfoil_comp, ivc)
    assert problem['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    assert problem['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert pth.exists(XFOIL_RESULTS)
    assert pth.exists(pth.join(XFOIL_RESULTS, 'polar_result.txt'))
